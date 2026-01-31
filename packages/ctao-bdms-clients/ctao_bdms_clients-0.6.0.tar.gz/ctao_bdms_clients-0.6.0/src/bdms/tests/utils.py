"""Utility functions for BDMS tests."""

import logging
import os
import time
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

import boto3
from dotenv import load_dotenv
from rucio.client.replicaclient import ReplicaClient
from rucio.client.ruleclient import RuleClient
from rucio.common.exception import RucioException
from rucio.common.utils import extract_scope

# Default timeout and polling interval (in seconds) for waiting for replication
DEFAULT_TIMEOUT = 150
DEFAULT_POLL_INTERVAL = 5
XROOTD_UID = int(os.getenv("XROOTD_UID", 194))
XROOTD_GID = int(os.getenv("XROOTD_GID", 194))
LOGGER = logging.getLogger(__name__)


def reset_xrootd_permissions(path):
    recursive_chown(path, uid=XROOTD_UID, gid=XROOTD_GID)


def recursive_chown(path: Path, uid: int, gid: int):
    """Equivalent of unix chmod -R <uid>:<gid> <path>."""
    os.chown(path, uid, gid)

    for root, dirs, files in os.walk(path):
        root = Path(root)
        for d in dirs:
            os.chown(root / d, uid, gid)

        for f in files:
            # skip temporary files created by rucio
            # they should already have correct ownership and might go away
            # between finding them and executing chown
            if f.endswith(".rucio.upload"):
                continue

            try:
                os.chown(root / f, uid, gid)
            except Exception as e:
                LOGGER.warning("Failed to chown file %s: %s", root / f, e)


def wait_for_replication_status(
    rule_client: RuleClient,
    rule_id: str,
    expected_status: str = "OK",
    timeout: int = DEFAULT_TIMEOUT,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    error_on: Optional[set[str]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    if logger is None:
        logger = LOGGER

    start_time = time.perf_counter()
    current_status = None
    result = None
    max_retries = 3

    while (time.perf_counter() - start_time) < timeout:
        retries = 0
        while retries < max_retries:
            try:
                result = rule_client.get_replication_rule(rule_id)
                current_status = result["state"]
                break
            except RucioException as e:
                retries += 1
                if retries == max_retries:
                    raise RuntimeError(
                        f"Failed to check replication rule status for rule {rule_id} after {max_retries} retries: {str(e)}"
                    ) from e
                logger.warning(
                    "Failed to check rule %s status (attempt %s/%s): %s. Retrying...",
                    rule_id,
                    retries,
                    max_retries,
                    str(e),
                )
                time.sleep(1)

        if current_status == expected_status:
            logger.info(
                "Replication rule %s reached status '%s'", rule_id, expected_status
            )
            return

        if error_on is not None and current_status in error_on:
            raise ValueError(
                f"Replication rule {rule_id} entered error state {current_status}."
            )

        logger.info(
            "Rule %s is in state %s, waiting for %s (elapsed: %.2f seconds)",
            rule_id,
            current_status,
            expected_status,
            time.perf_counter() - start_time,
        )
        time.sleep(poll_interval)

    msg = (
        f"Replication rule {rule_id} did not reach status '{expected_status}' within {timeout} seconds. "
        f"Current status is '{current_status}'.\nFull output: {result}"
    )
    logger.error(msg)
    raise TimeoutError(msg)


TEST_DATA_DIR = Path(os.getenv("BDMS_TEST_DATA_DIR", "test_data")).absolute()


def download_test_file(path):
    """Get a FITS file from the test data server"""

    load_dotenv()

    access_key = os.environ["MINIO_ACCESS_KEY"]
    secret_key = os.environ["MINIO_SECRET_KEY"]

    output_path = TEST_DATA_DIR / path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not output_path.exists():
        client = boto3.client(
            "s3",
            endpoint_url="https://minio-cta.zeuthen.desy.de",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        LOGGER.info("Downloading %s", path)
        client.download_file(
            Bucket="dpps-data-private",
            Key=path,
            Filename=str(output_path),
        )

    else:
        LOGGER.info("File %s already exists, skipping download", output_path)

    return output_path


def has_replicas(client: ReplicaClient, lfn):
    """Check that there is at least 1 replica for given did."""
    scope, _ = extract_scope(lfn, scopes=None)

    replicas = next(client.list_replicas(dids=[dict(scope=scope, name=lfn)]), None)
    return replicas is not None


def wait_for_replicas(lfns, timeout_s=120, interval=1.0):
    """Ensure that all files are ingested by checking the IngestStatus."""

    replica_client = ReplicaClient()
    timeout_at = time.perf_counter() + timeout_s
    missing_lfns = set(lfns)

    LOGGER.info("Waiting for at least one replica to appear for all given files.")
    while len(missing_lfns) > 0:
        if time.perf_counter() > timeout_at:
            raise TimeoutError(
                f"Not all replicas found for lfns: {lfns} within {timeout_s} s."
                f" Missing: {missing_lfns}."
            )

        for lfn in set(missing_lfns):
            try:
                if has_replicas(replica_client, lfn):
                    LOGGER.info("Replica found for %s", lfn)
                    missing_lfns.remove(lfn)
                else:
                    LOGGER.info("No replica found for %s", lfn)
            except Exception:
                LOGGER.exception("Error while checking for replicas of lfn %s", lfn)

        time.sleep(interval)
    LOGGER.info("Replicas found for all lfns.")


def wait_for_trigger_file_removal(trigger_files, timeout=10.0, interval=1.0):
    """Wait until all given files no longer exist or timeout is reached."""
    existing_files = set(trigger_files)

    start = time.perf_counter()

    while len(existing_files) > 0:
        if (time.perf_counter() - start) > timeout:
            raise TimeoutError(
                f"Not all files removed within {timeout} s, remaining: {existing_files}"
            )

        for trigger_file in list(existing_files):
            if not trigger_file.exists():
                existing_files.remove(trigger_file)

        time.sleep(interval)


def fetch_ingestion_daemon_metrics():
    """Fetch metrics from the ingestion daemon to verify its operation."""

    response = urlopen("http://bdms-ingestion-daemon:8000/")

    msg = "Ingestion daemon metrics are not responding"
    assert response.status == 200, msg

    n_tasks_metrics = {}
    for line in response.readlines():
        line = line.decode("utf-8").strip()
        if line.startswith("n_tasks_"):
            LOGGER.info("Ingestion daemon metrics: %s", line)
            key, value = line.split(" ", 1)
            n_tasks_metrics[key] = float(value)

    return n_tasks_metrics
