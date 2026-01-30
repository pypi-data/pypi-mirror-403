"""Module for ACADA data ingestion (onsite) into the BDMS system using the IngestionClient.

This module provides the IngestionClient class to manage the ingestion of ACADA data into the BDMS system.
It includes functionality for constructing FITS file paths, converting ACADA paths to Logical File Names (LFNs),
registering replicas in Rucio, extracting metadata and adding metadata to registered replicas. Furthermore, the Ingest class asynchronously
processes ACADA data using a process pool, managing file discovery, queuing, and distribution to worker processes for ingestion using a continuous
polling-based approach.
"""

import logging
import os
import shutil
import threading
import time
from contextlib import ExitStack
from enum import Enum
from pathlib import Path
from typing import NamedTuple, Optional, Union

from astropy.io import fits
from filelock import FileLock, Timeout
from prometheus_client import Counter, Gauge
from rucio.client.accountclient import AccountClient
from rucio.client.client import Client, DIDClient
from rucio.client.replicaclient import ReplicaClient
from rucio.client.rseclient import RSEClient
from rucio.client.ruleclient import RuleClient
from rucio.client.scopeclient import ScopeClient
from rucio.common.checksum import adler32
from rucio.common.exception import (
    DataIdentifierAlreadyExists,
    Duplicate,
    DuplicateContent,
    DuplicateRule,
    RucioException,
)
from rucio.common.utils import extract_scope

from bdms.extract_fits_metadata import (
    extract_metadata_from_data,
    extract_metadata_from_headers,
)
from bdms.ingest_tasks import process_acada_file

LOGGER = logging.getLogger(__name__)

__all__ = [
    "IngestionClient",
    "FITSVerificationError",
    "Ingest",
    "IngestResult",
    "SkipReason",
]

INGEST_RUNNING_MESSAGE = "Another ingestion process is already running"
TRIGGER_SUFFIX = ".trigger"

CONNECTION_RETRY_INTERVAL = 300

# Prometheus Metrics for monitoring
N_TASKS_SUCCESS = Counter("n_tasks_success", "Number of successfully finished tasks.")
N_TASKS_FAILED = Counter("n_tasks_failed", "Number of failed tasks.")
N_TASKS_CANCELLED = Counter("n_tasks_cancelled", "Number of cancelled tasks.")
N_TASKS_SKIPPED = Counter("n_tasks_skipped", "Number of skipped tasks.")
N_TASKS_PROCESSED = Counter(
    "n_tasks_processed", "Total number of tasks processed by the Ingest daemon"
)
TASKS_IN_QUEUE = Gauge("n_tasks_queued", "Current number of queued tasks")
BYTES_INGESTED = Counter("bytes_ingested", "Total ingested file size")


class SkipReason(Enum):
    """Enumeration of reasons for skipping the ingestion of a file."""

    #: The file is missing required metadata
    MISSING_REQUIRED_METADATA = 1
    #: File has already been ingested
    REPLICA_EXISTS = 2


class IngestResult(NamedTuple):
    """Result of the ingestion of a single file.

    Attributes
    ----------
    lfn : str
        The Logical File Name of the processed file.
    scope : str
        Extracted scope.
    file_size : int
        Size of the file in bytes.
    skip_reason : SkipReason
        The reason the file was skipped, or None if not skipped.
    """

    lfn: str
    scope: str
    file_size: int
    skip_reason: Optional[SkipReason]


class IngestionClient:
    """A client for BDMS ingestion and replication.

    This class provides methods to ingest ACADA data into the BDMS system, including converting ACADA paths to
    Logical File Names (LFNs), registering replicas in Rucio, extracting metadata and adding metadata to registered replicas, and
    replicating data to offsite RSEs.

    Parameters
    ----------
    data_path : str
        Path to data directory. This is a required argument.
    rse : str
        Rucio Storage Element (RSE) name. This is a required argument.
    vo : str, optional
        Virtual organization name prefix. Defaults to "ctao".
    logger : logging.Logger, optional
        Logger instance. If None, a new logger is created.

    Raises
    ------
    FileNotFoundError
        If the specified data directory does not exist.
    ValueError
        If the specified RSE is not available in Rucio.
    RuntimeError
        If there is an error communicating with Rucio while:

        - Checking RSE availability.
        - Initializing Rucio clients (related to configuration and authentication issues).
        - Managing the Rucio scope.
    """

    def __init__(
        self,
        data_path: Union[str, os.PathLike],
        rse: str,
        vo="ctao",
        logger=None,
    ) -> None:
        self.logger = logger or LOGGER.getChild(self.__class__.__name__)
        self.vo = vo

        if data_path is None:
            raise ValueError("data_path must be provided and cannot be None")

        # Set data path (Prefix)
        self.data_path = Path(data_path)
        if not self.data_path.is_dir():
            raise FileNotFoundError(f"Data directory not found at {self.data_path}")

        self.rse = rse

        # Check RSE availability before proceeding to next steps
        self._check_rse_availability()

        # Initialize Rucio clients
        try:
            self.client = Client()
            self.replica_client = ReplicaClient()
            self.scope_client = ScopeClient()
            self.account_client = AccountClient()
            self.rse_client = RSEClient()
            self.rule_client = RuleClient()
            self.did_client = DIDClient()
        except RucioException as e:
            self.logger.error("Failed to initialize Rucio clients: %s", str(e))
            raise

        # Set the scope and ensure it exists in Rucio
        self.user = self.account_client.whoami()["account"]

    def _check_rse_availability(self) -> None:
        """Check if the specified RSE is available in Rucio.

        Raises
        ------
        ValueError
            If the RSE is not found in Rucio.
        rucio.common.exception.RucioException
            If there is an error communicating with Rucio (e.g., network issues, authentication errors).
        """
        rse_client = RSEClient()
        available_rses = [rse["rse"] for rse in rse_client.list_rses()]
        if self.rse not in available_rses:
            raise ValueError(
                f"RSE '{self.rse}' is not available in Rucio. Available RSEs: {available_rses}"
            )
        self.logger.info("RSE '%s' is available in Rucio", self.rse)

    def _add_scope(self, scope: str) -> None:
        """Add the specified scope to Rucio if it doesn't already exist.

        Raises
        ------
        RuntimeError
            If the scope cannot be created or managed in Rucio.
        """
        try:
            self.scope_client.add_scope(self.user, scope)
        except Duplicate:
            # Scope already exists
            return
        except RucioException as e:
            self.logger.error(
                "Failed to manage scope '%s' in Rucio: %s",
                scope,
                str(e),
            )
            raise

    def acada_to_lfn(self, acada_path) -> str:
        """Convert an ACADA path to a BDMS Logical File Name (LFN).

        Parameters
        ----------
        acada_path : str or Path
            The ACADA file path to convert.

        Returns
        -------
        str
            The generated BDMS LFN (e.g., '/ctao/acada/DL0/LSTN-01/events/YYYY/MM/DD/file.fits.fz').

        Raises
        ------
        ValueError
            If ``acada_path`` is not an absolute path or is not within the BDMS data path (prefix) or
            does not start with the expected '<vo>/<scope>' prefix under the data path.
        """
        acada_path = Path(acada_path)

        # Validate that the path is absolute
        if not acada_path.is_absolute():
            raise ValueError("acada_path must be absolute")

        # Validate that acada_path is within data_path
        try:
            rel_path = acada_path.relative_to(self.data_path)
        except ValueError:
            raise ValueError(
                f"acada_path {acada_path} is not within data_path {self.data_path}"
            )

        # Validate that acada_path starts with <data_path>/<vo>/
        expected_prefix = self.data_path / self.vo
        if not acada_path.is_relative_to(expected_prefix):
            raise ValueError(
                f"acada_path {acada_path} must start with {expected_prefix} (vo: {self.vo})"
            )

        bdms_lfn = f"/{rel_path}"
        return bdms_lfn

    def create_container_hierarchy(self, container_path: str) -> None:
        """Create container hierarchy and attach parent-child relationships."""
        p = Path(container_path)

        # Containers from root to leaf, excluding '/'
        # As Rucio API requires strings thus converting PosixPath objects to strings
        containers = [str(parent) for parent in list(reversed(p.parents))[1:]]
        containers.append(container_path)

        # Starting at index 3: /vo/scope/data_level is the root container
        containers = containers[2:]

        prev_container = None
        prev_scope = None
        for container in containers:
            scope, _ = extract_scope(container)
            try:
                self.did_client.add_container(scope=scope, name=container)
                self.logger.debug("Created container: %s", container)
            except (Duplicate, DataIdentifierAlreadyExists):
                pass  # Container already exists

            # Attach current container to its parent, skipping attachment for root container as it doesn't have a parent
            if prev_container:
                try:
                    self.did_client.attach_dids(
                        scope=prev_scope,
                        name=prev_container,
                        dids=[{"scope": scope, "name": container}],
                    )
                except (Duplicate, DataIdentifierAlreadyExists, DuplicateContent):
                    pass  # Already attached

            prev_container = container
            prev_scope = scope

    def check_replica_exists(self, lfn: str, scope: str) -> bool:
        """Check if a replica already exists for the given LFN on the specified RSE.

        Parameters
        ----------
        lfn : str
            The Logical File Name (LFN) to check.
        scope : str
            Extracted rucio scope of the LFN.

        Returns
        -------
        bool
            True if the replica exists and has a valid PFN, False otherwise.

        Raises
        ------
        RuntimeError
            If a replica exists but has no PFN for the RSE, indicating an invalid replica state.
        """
        replicas = list(
            self.replica_client.list_replicas(
                dids=[{"scope": scope, "name": lfn}],
                rse_expression=self.rse,
            )
        )

        self.logger.debug("Existing Replicas for lfn '%r'", replicas)
        if replicas:
            replica = replicas[0]
            pfns = replica["rses"].get(self.rse, [])
            if not pfns:
                raise RuntimeError(
                    f"No PFN found for existing replica with LFN {lfn} on {self.rse}"
                )
            return True
        return False

    def add_onsite_replica(self, acada_path: Union[str, Path]) -> IngestResult:
        """Register a file as a replica in Rucio on the specified RSE and return the ingestion result.

        Parameters
        ----------
        acada_path : str or Path
            The ACADA path where the file is located.

        Returns
        -------
        IngestResult
            Result of the replica registration.

        Raises
        ------
        FileNotFoundError
            If the file does not exist at ``acada_path``.
        RuntimeError
            In the following cases:
            - If a replica already exists but has no PFN for the RSE (raised by `check_replica_exists`).
            - If the replica registration fails (e.g., due to a Rucio server issue).
        """
        acada_path = Path(acada_path)
        self.logger.debug("Starting ingestion for path '%s'", acada_path)

        # Validate file existence
        if not acada_path.is_file():
            raise FileNotFoundError(f"File does not exist at {acada_path}")

        # Generate LFN
        lfn = self.acada_to_lfn(acada_path=str(acada_path))
        scope, _ = extract_scope(lfn)

        self.logger.info(
            "Using LFN '%s' with scope '%s' for path '%s'", lfn, scope, acada_path
        )

        self._add_scope(scope)

        # Check if the replica already exists
        if self.check_replica_exists(lfn, scope):
            self.logger.info("Replica already exists for lfn '%s', skipping", lfn)
            return IngestResult(
                lfn=lfn,
                scope=scope,
                file_size=0,
                skip_reason=SkipReason.REPLICA_EXISTS,
            )

        # Proceed with registering the replica if check_replica_exists returns False
        valid, metadata = verify_and_extract_metadata(acada_path)
        metadata["valid_fits_checksum"] = valid

        missing_required_metadata = metadata.get("missing_required_metadata", False)
        if missing_required_metadata:
            self.logger.warning("Missing required metadata in the file '%s'", lfn)
        missing_optional_metadata = metadata.get("missing_optional_metadata", False)
        if missing_optional_metadata:
            self.logger.info("Missing optional metadata in the file '%s'", lfn)

        if missing_required_metadata:
            self.logger.warning(
                "The replica for lfn '%s' was not registered as not all the required metadata were set in the file '%s'",
                lfn,
                acada_path,
            )
            return IngestResult(
                lfn=lfn,
                scope=scope,
                file_size=0,
                skip_reason=SkipReason.MISSING_REQUIRED_METADATA,
            )

        lfn_path = Path(lfn)
        dataset = str(lfn_path.parents[0])
        dataset_scope, _ = extract_scope(dataset)
        container = str(lfn_path.parents[1])
        container_scope, _ = extract_scope(container)

        # Create full container hierarchy
        self.create_container_hierarchy(container)

        # Create dataset
        try:
            self.did_client.add_dataset(scope=dataset_scope, name=dataset)
            self.logger.info("Created dataset: %s", dataset)
        except (Duplicate, DataIdentifierAlreadyExists):
            self.logger.debug("Dataset already exists: %s", dataset)

        # Attach dataset to parent container
        try:
            self.did_client.attach_dids(
                scope=container_scope,
                name=container,
                dids=[{"scope": dataset_scope, "name": dataset}],
            )
            self.logger.debug("Attached dataset to container")
        except (Duplicate, DataIdentifierAlreadyExists, DuplicateContent):
            pass

        # Compute rucio file metadata
        file_size = acada_path.stat().st_size
        checksum = adler32(acada_path)

        # Register the replica in Rucio if there is no missing metadata
        try:
            success = self.replica_client.add_replica(
                rse=self.rse,
                scope=scope,
                name=lfn,
                bytes_=file_size,
                adler32=checksum,
            )
            if not success:
                raise RuntimeError(
                    f"Failed to register replica for LFN {lfn} on {self.rse}"
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to register replica for LFN {lfn} on {self.rse}: {str(e)}"
            )
        self.logger.info("Successfully registered the replica for lfn '%s'", lfn)

        # Set file-level metadata
        if len(metadata) > 0:
            self.did_client.set_metadata_bulk(scope=scope, name=lfn, meta=metadata)
            self.logger.info("Set metadata of %r to %r", lfn, metadata)

        # Attach file to dataset
        self.did_client.attach_dids(
            scope=scope,
            name=dataset,
            dids=[{"scope": scope, "name": lfn}],
        )
        self.logger.debug("Attached file %s to dataset %s", lfn, dataset)

        return IngestResult(lfn=lfn, scope=scope, file_size=file_size, skip_reason=None)

    def add_offsite_replication_rules(
        self,
        dataset: str,
        copies: int = 1,
        lifetime: Optional[int] = None,
        offsite_rse_expression: str = "OFFSITE",
    ) -> list[str]:
        """Replicate an already-ingested ACADA data product to offsite RSEs.

        This method assumes the data product has already been ingested into the onsite RSE and is identified by the given LFN.
        It creates one or two replication rules to offsite RSEs, depending on the number of copies requested:
        - First rule: Always creates exactly 1 replica to prevent parallel transfers from the onsite RSE.
        - Second rule (if copies > 1): Creates additional replicas (equal to the requested copies), sourcing data from offsite RSEs to avoid further transfers from the onsite RSE.

        Parameters
        ----------
        dataset : str
            Dataset name.
        copies : int, optional
            The total number of offsite replicas to create. Defaults to 1.
            - If copies == 1, only one rule is created with 1 replica.
            - If copies > 1, a second rule is created with the requested number of copies, sourcing from offsite RSEs.
        lifetime : int, optional
            The lifetime of the replication rules in seconds. If None, the rules are permanent.
        offsite_rse_expression : str, optional
            The RSE expression identifying offsite Rucio Storage Elements (RSEs). Defaults to "OFFSITE".

        Returns
        -------
        List[str]
            The list of replication rule IDs created (1 or 2 rules, depending on the copies parameter).

        Raises
        ------
        RuntimeError
            If there is an error interacting with Rucio, including:
            - Failure to create a new replication rule (e.g., DuplicateRule).
        """
        # Create the DID for replication
        scope, _ = extract_scope(dataset)
        did = {"scope": scope, "name": dataset}
        dids = [did]

        # Initialize the list of rule IDs
        rule_ids = []

        # First rule: Always create exactly 1 replica to prevent parallel transfers from onsite RSE
        try:
            rule_id_offsite_1 = self.rule_client.add_replication_rule(
                dids=dids,
                rse_expression=offsite_rse_expression,
                copies=1,
                lifetime=lifetime,
                source_replica_expression=None,  # Let Rucio choose the source (onsite RSE)
            )[0]
            self.logger.debug(
                "Created first replication rule %s for DID %s to RSE expression '%s' with 1 copy, lifetime %s",
                rule_id_offsite_1,
                did,
                offsite_rse_expression,
                lifetime if lifetime is not None else "permanent",
            )
            rule_ids.append(rule_id_offsite_1)
        except DuplicateRule:
            self.logger.debug("Rule already exists for dataset %s", dataset)

        except RucioException as e:
            self.logger.error(
                "Failed to create first offsite replication rule for DID %s to RSE expression '%s': %s",
                did,
                offsite_rse_expression,
                str(e),
            )
            raise

        # Second rule: If more than one copy is requested, create a second rule sourcing from offsite RSEs
        if copies > 1:
            # Exclude the onsite RSE to ensure the data is sourced from an offsite RSE
            # source_replica_expression = f"*\\{onsite_rse}" (we could also consider this expression)
            source_replica_expression = offsite_rse_expression
            self.logger.debug(
                "Creating second offsite replication rule to RSE expression '%s' with %d copies, sourcing from offsite RSEs",
                offsite_rse_expression,
                copies,
            )
            try:
                rule_id_offsite_2 = self.rule_client.add_replication_rule(
                    dids=dids,
                    rse_expression=offsite_rse_expression,
                    copies=copies,  # Use requested number of copies
                    lifetime=lifetime,
                    source_replica_expression=source_replica_expression,
                )[0]
                self.logger.debug(
                    "Created second replication rule %s for DID %s to RSE expression '%s' with %d copies, source_replica_expression '%s', lifetime %s",
                    rule_id_offsite_2,
                    did,
                    offsite_rse_expression,
                    copies,
                    source_replica_expression,
                    lifetime if lifetime is not None else "permanent",
                )
                rule_ids.append(rule_id_offsite_2)
            except DuplicateRule:
                self.logger.debug(
                    "Rule already exists for dataset %s (second rule)", dataset
                )
            except RucioException as e:
                self.logger.error(
                    "Failed to create second offsite replication rule for DID %s to RSE expression '%s': %s",
                    did,
                    offsite_rse_expression,
                    str(e),
                )
                raise

        self.logger.info(
            "Created %d offsite replication rule(s) for dataset '%s' to RSE expression '%s': %s",
            len(rule_ids),
            dataset,
            offsite_rse_expression,
            rule_ids,
        )
        return rule_ids


class FITSVerificationError(Exception):
    """Raised when a FITS file does not pass verification."""


def verify_fits_checksum(hdul: fits.HDUList):
    """
    Verify all present checksums in the given HDUList.

    Goes through all HDUs and verifies DATASUM and CHECKSUM if
    present in the given HDU.

    Verifies DATASUM before CHECKSUM to distinguish failure
    in data section vs. failure in header section.

    Raises
    ------
    FITSVerificationError: in case any of the checks are not passing
    """
    for pos, hdu in enumerate(hdul):
        name = hdu.name or ""

        checksum_result = hdu.verify_checksum()
        if checksum_result == 0:
            msg = f"CHECKSUM verification failed for HDU {pos} with name {name!r}"
            raise FITSVerificationError(msg)
        elif checksum_result == 2 and pos != 0:  # ignore primary for warning
            LOGGER.warning("No CHECKSUM in HDU %d with name %r", pos, name)


def verify_and_extract_metadata(fits_path):
    """Verify checksums and extract metadata from FITS files.

    This wrapper transforms exceptions into log errors and minimizes
    the number of times the FITS file has to be opened.
    """
    # this context manager allows elegant handling
    # of conditionally present context managers
    # which allows better handling of exceptions below
    context = ExitStack()
    metadata = {}
    with context:
        try:
            hdul = context.enter_context(fits.open(fits_path))
        except Exception as e:
            LOGGER.error("Failed to open FITS file %r: %s", fits_path, e)
            return False, metadata

        try:
            verify_fits_checksum(hdul)
        except FITSVerificationError as e:
            LOGGER.error("File %r failed FITS checksum verification: %s", fits_path, e)
            return False, metadata

        try:
            metadata = extract_metadata_from_headers(hdul, fits_path)
            metadata.update(extract_metadata_from_data(fits_path))
            return True, metadata
        except Exception as e:
            LOGGER.error("Failed to extract metadata from %r: %s", fits_path, e)
            return False, metadata


def process_file(
    client: IngestionClient, file_path: str, logger=None, copies: int = 2
) -> IngestResult:
    """Process a single file with IngestionClient, clean up the trigger file, and return the ingestion result.

    Parameters
    ----------
    client : IngestionClient
        The IngestionClient instance to handle replica registration and replication.
    file_path : str
        The path to the file to process.
    logger : logging.Logger, optional
        Logger instance. If None, uses the client's logger or a default logger.
    copies: int
        The number of offsite copies to create. Defaults to 2.

    Returns
    -------
    IngestResult
        Result of the ingestion process.
    """
    logger = logger or LOGGER.getChild("Ingest")

    result = client.add_onsite_replica(file_path)
    trigger_file = Path(file_path + TRIGGER_SUFFIX)

    if result.skip_reason is None:
        dataset = str(Path(result.lfn).parent)
        scope = extract_scope(dataset)
        filters = {"scope": scope, "name": dataset}

        rules = client.rule_client.list_replication_rules(filters)
        has_rule = next(rules, None) is not None

        if not has_rule:
            client.add_offsite_replication_rules(dataset=dataset, copies=copies)
            logger.info("Created replication rules for dataset %s", dataset)
        else:
            logger.debug("Dataset %s already has replication rules", dataset)

        if trigger_file.exists():
            trigger_file.unlink()
            logger.debug("Removed trigger file %s", trigger_file)

    elif result.skip_reason == SkipReason.MISSING_REQUIRED_METADATA:
        logger.error(
            "File not ingested because of missing required metadata: %s", file_path
        )
        # change acada path, and move the file to a different path
        acada_path = Path(file_path)
        # change one of the parts
        parts = list(acada_path.parts)
        # to confirm it is correct
        parts[4] = "INVALID_DL0"
        acada_path = Path(*parts)
        shutil.move(file_path, str(acada_path))

        parts = list(trigger_file.parts)
        # to confirm it is correct
        parts[4] = "INVALID_DL0"
        trigger_file = Path(*parts)
        shutil.move(file_path + TRIGGER_SUFFIX, str(trigger_file))

    else:
        if trigger_file.exists():
            trigger_file.unlink()
            logger.debug("Removed trigger file %s", trigger_file)

    return result


class Ingest:
    """Ingestion daemon service to process ACADA data products using Celery workers with result handling.

    Monitors a specified directory for trigger files using a polling loop, submitting each file for ingestion to
    Celery workers for parallel processing. The daemon ensures compatibility with shared filesystems through polling
    and prevents multiple instances using a lock file.
    """

    def __init__(
        self,
        client,
        top_dir: Union[str, Path],
        lock_file_path: Union[str, Path, None] = None,
        polling_interval: float = 1.0,
        offsite_copies: int = 2,
    ) -> None:
        """Initialize the ingestion daemon with configuration parameters.

        Sets up the client, directory, worker count, intervals, and initializes
        a process-safe queue and daemon state.
        """
        self.logger = LOGGER.getChild(self.__class__.__name__)
        self.stop_event = threading.Event()

        self.client = client
        self.top_dir = Path(top_dir)

        self.lock_file_path = (
            Path(lock_file_path)
            if lock_file_path
            else self.top_dir / "bdms_ingest.lock"
        )
        # Lock instance to be held during entire daemon execution
        self.lock = FileLock(self.lock_file_path, timeout=10, thread_local=False)

        self.polling_interval = polling_interval
        self.offsite_copies = offsite_copies
        self.polling_thread = None
        self.result_thread = None

        # Result handling
        self.task_counter = 0
        self.submitted_tasks = {}  # Track submitted tasks, task_id -> {'file_path': str, 'async_result': AsyncResult}

        # Track already processed triggers
        self.known_triggers = set()

        self.task_lock = threading.Lock()

    def _submit_file(self, file_path: str):
        """Submit a file to celery for processing.

        Parameters
        ----------
        file_path : str
            Path to the data file to be processed.
        """
        try:
            result = process_acada_file.delay(
                file_path=str(file_path),
                data_path=str(self.client.data_path),
                rse=self.client.rse,
                vo=self.client.vo,
                copies=self.offsite_copies,
            )

            with self.task_lock:
                self.task_counter += 1
                self.submitted_tasks[result.id] = {
                    "file_path": str(file_path),
                    "async_result": result,
                }
                # Update max concurrent tasks tracking
                current_concurrent = len(self.submitted_tasks)

                # Increment queue counter when task is submitted
                TASKS_IN_QUEUE.inc()

            self.logger.debug(
                "Submitting task %s for file %s (concurrent: %d)",
                result.id,
                file_path,
                current_concurrent,
            )

        except Exception as e:
            self.logger.exception(
                "Failed to submit task for file %s: %s", file_path, str(e)
            )

    def _monitor_results(self):
        """Poll task results and update metrics."""
        self.logger.info("Result monitoring thread started")

        while not self.stop_event.is_set():
            try:
                self._check_all_tasks()
            except Exception:
                self.logger.exception("Error in result monitoring")

            self.stop_event.wait(1.0)

        self.logger.info("Processing remaining tasks")
        self._check_all_tasks()
        self.logger.info("Result monitoring thread stopped")

    def _check_all_tasks(self):
        """Check status of all tracked tasks."""
        with self.task_lock:
            task_ids = list(self.submitted_tasks.keys())

        if not task_ids:
            return

        self.logger.debug("Checking %d tasks", len(task_ids))

        for task_id in task_ids:
            with self.task_lock:
                if task_id not in self.submitted_tasks:
                    continue
                task_info = self.submitted_tasks[task_id]

            async_result = task_info["async_result"]
            if async_result.ready():
                self._handle_task_result(task_id, task_info, async_result)

    def _handle_task_result(self, task_id: str, task_info: dict, async_result) -> None:
        """Handle the result of a completed task and update metrics."""
        file_path = task_info["file_path"]

        # Clean up task tracking
        with self.task_lock:
            self.submitted_tasks.pop(task_id, None)
            TASKS_IN_QUEUE.dec()

        current_concurrent = len(self.submitted_tasks)
        self.logger.debug(
            "Task %s completed, remaining concurrent: %d", task_id, current_concurrent
        )

        if async_result.state == "REVOKED":
            N_TASKS_CANCELLED.inc()
            self.logger.warning("Task %s cancelled for %s", task_id, file_path)
            status = "cancelled"

        elif async_result.failed():
            self.logger.exception(
                "Task %s failed for %s: %s:\n %s",
                task_id,
                file_path,
                async_result.result,
                async_result.traceback,
            )  # to check
            N_TASKS_FAILED.inc()
            status = "failed"

        elif async_result.successful():
            try:
                result = async_result.get(timeout=0.1)

                if result["skip_reason"] is not None:
                    N_TASKS_SKIPPED.inc()
                    skip_reason = result["skip_reason"]
                    self.logger.info(
                        "File %s already existed (%s), reason: %s",
                        file_path,
                        result["lfn"],
                        skip_reason,
                    )
                    status = "skipped"
                else:
                    N_TASKS_SUCCESS.inc()
                    BYTES_INGESTED.inc(result["file_size"])
                    self.logger.info(
                        "Ingested %s -> %s (%d bytes)",
                        file_path,
                        result["lfn"],
                        result["file_size"],
                    )
                    status = "success"
            except Exception as e:
                self.logger.error("Couldn't read result for %s: %s", task_id, str(e))
                N_TASKS_FAILED.inc()
                status = "failed"
        else:
            self.logger.warning(
                "Task %s in state %s for %s", task_id, async_result.state, file_path
            )
            N_TASKS_FAILED.inc()
            status = "unknown"

        N_TASKS_PROCESSED.inc()
        self.logger.info("Processed file %s with result %s.", file_path, status)

    def _scan_for_triggers(self):
        """Scan directory for new .trigger files and submit them for processing."""
        # Find all .trigger files in the directory
        self.logger.info("Starting scan for new trigger files")
        start_time = time.time()
        current_triggers = set(self.top_dir.rglob("*.trigger"))
        scan_time = time.time() - start_time
        self.logger.debug(
            "Found %d trigger files in %.2fs", len(current_triggers), scan_time
        )

        # Find new triggers that we have not seen before
        new_triggers = current_triggers.difference(self.known_triggers)

        # Find triggers that disappeared (processed and deleted)
        disappeared_triggers = self.known_triggers.difference(current_triggers)

        self.logger.info(
            "Scanned for triggers: found %d total, %d new, %d disappeared",
            len(current_triggers),
            len(new_triggers),
            len(disappeared_triggers),
        )

        # Process new trigger files
        for trigger_file in new_triggers:
            self._process_trigger_file(trigger_file)

        # Update known_triggers to match currently existing trigger files
        self.known_triggers = current_triggers

    def _process_trigger_file(self, trigger_file: Path):
        """Process a trigger file by submitting its data file for ingestion."""
        data_file = trigger_file.with_suffix("")

        # pathological case of a link just called ".trigger"
        if trigger_file.name == TRIGGER_SUFFIX:
            self.logger.error(
                "Ignoring trigger file: %s, empty data file name", trigger_file
            )
            return

        if not data_file.exists():
            self.logger.error(
                "Ignoring trigger file: %s, data path %s missing",
                trigger_file,
                data_file,
            )
            return

        if not data_file.is_file():
            self.logger.error(
                "Ignoring trigger file: %s, data path %s is not a file",
                trigger_file,
                data_file,
            )
            return

        self.logger.info(
            "Processing trigger file %s, submitting data file %s",
            trigger_file,
            data_file,
        )

        try:
            self._submit_file(str(data_file))
        except Exception:
            self.logger.exception(
                "Failed to submit data file %s for processing", data_file
            )
            return

        self.logger.debug("Successfully processed trigger %s", trigger_file)

    def _polling_loop(self):
        """Continuously scan for trigger files until daemon stops."""
        self.logger.info(
            "Starting polling of directory %s every %.1f seconds",
            self.top_dir,
            self.polling_interval,
        )

        while not self.stop_event.is_set():
            try:
                self._scan_for_triggers()
            except Exception:
                self.logger.exception("Exception in polling loop")

            self.stop_event.wait(self.polling_interval)

        self.logger.info("Stopped polling for new trigger files")

    def _check_directory(self) -> None:
        """Check if the directory is readable.

        Raises
        ------
        RuntimeError
            If the top directory is not accessible.
        """
        if not self.top_dir.is_dir() or not os.access(self.top_dir, os.R_OK):
            self.logger.error("Cannot read directory %s", self.top_dir)
            raise RuntimeError(f"Cannot read directory {self.top_dir}")

    def run(self, block=True) -> None:
        """Run the ingestion daemon, submitting file ingestion tasks to celery.

        Initializes and runs the complete ingestion system including:

        1. Validates directory access
        2. Process checks (lock file acquisition and hold for entire runtime)
        3. Result monitoring thread startup
        4. File system monitoring with polling loop
        5. Graceful shutdown handling

        The method blocks until a shutdown signal is received (KeyboardInterrupt)
        or the stop_event is set. All components are properly shut down and
        cleaned up before the method returns.

        The daemon submits tasks to Celery workers via Redis. Workers run independently
        in separate Kubernetes pods and continue processing even if the daemon restarts.

        Parameters
        ----------
        block : bool
            If True (the default), this function will block forever
            running the ingest until another thread sets the stop event.
            If block is false, this function will return once ingest
            is running.
            In this case, the caller has to make sure to call the shutdown
            method to stop threads and free the corresponding
            resources.

        Raises
        ------
        RuntimeError
            If another ingestion process is running or the directory is unreadable.
        """
        self._check_directory()

        # Acquire lock for the entire daemon execution, preventing multiple instances
        try:
            # Acquire the lock - this will be held for the entire daemon runtime
            self.lock.acquire(poll_interval=0.1)
            self.logger.info("Acquired lock %s", self.lock.lock_file)
        except Timeout:
            raise RuntimeError(INGEST_RUNNING_MESSAGE)

        # Write PID to the original lock file for reference
        self.lock_file_path.write_text(str(os.getpid()))
        self.logger.info("Wrote PID %d to %s", os.getpid(), self.lock_file_path)

        self._start_polling()

        if not block:
            return

        try:
            self.stop_event.wait(timeout=None)
        finally:
            self.shutdown()

    def _start_polling(self):
        """Start the ingestion by starting polling and result monitoring threads."""
        self.stop_event.clear()

        if self.polling_thread is not None or self.result_thread is not None:
            raise ValueError("Ingest is already running")

        # Start the result monitoring thread
        self.result_thread = threading.Thread(target=self._monitor_results, daemon=True)
        self.result_thread.start()

        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.logger.info("Started polling")
        self.polling_thread.start()

    def shutdown(self):
        """Stop the daemon for ingesting, workers continue independently."""
        self.logger.info("Shutting down ingest daemon")
        self.stop_event.set()

        # shutdown the poller first, so we don't queue more files for ingestion
        if self.polling_thread is not None and self.polling_thread.is_alive():
            self.logger.info("Stopping Polling thread")
            self.polling_thread.join(timeout=30.0)
            if self.polling_thread.is_alive():
                self.logger.warning("File polling did not shutdown within 30s0")
            else:
                self.logger.info("Polling thread stopped")
        else:
            self.logger.info("Polling thread was not running")
        self.polling_thread = None

        # shutdown the reporting thread.
        if self.result_thread is not None and self.result_thread.is_alive():
            self.logger.info("Stopping result monitoring thread")
            self.result_thread.join()
        else:
            self.logger.info("Result monitoring thread was not running")
        self.result_thread = None

        with self.task_lock:
            current_concurrent = len(self.submitted_tasks)
            if current_concurrent > 0:
                self.logger.info(
                    "%d tasks still in queue - worker pods will continue processing them",
                    current_concurrent,
                )

        if self.lock.is_locked:
            self.lock.release()
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
            self.logger.info("Released lock file: %s", self.lock_file_path)
        else:
            self.logger.info("Lock was not held")
        self.logger.info("Stopped ingestion daemon")
