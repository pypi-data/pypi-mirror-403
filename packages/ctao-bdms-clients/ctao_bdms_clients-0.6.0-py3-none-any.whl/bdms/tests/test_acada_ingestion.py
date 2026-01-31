"""Tests for onsite ingestion and replication into the BDMS system using the IngestionClient.

This module contains tests for the IngestionClient class, focusing on the conversion of ACADA paths to Logical File Names (LFNs), the registration of replicas in Rucio,
and the replication of data between Rucio storage elements (RSEs).
"""

import logging
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from urllib.error import URLError

import numpy as np
import pytest
from astropy.io import fits
from astropy.table import Table
from rucio.client import Client
from rucio.client.downloadclient import DownloadClient
from rucio.client.replicaclient import ReplicaClient
from rucio.client.ruleclient import RuleClient
from rucio.common.checksum import adler32

from bdms import acada_ingestion
from bdms.acada_ingestion import (
    TRIGGER_SUFFIX,
    Ingest,
    IngestionClient,
    SkipReason,
    process_file,
)
from bdms.tests.conftest import (
    acada_write_test_files,
    deployment_scale,
    get_unique_day_for_tests,
)
from bdms.tests.utils import (
    fetch_ingestion_daemon_metrics,
    reset_xrootd_permissions,
    wait_for_replicas,
    wait_for_replication_status,
    wait_for_trigger_file_removal,
)

LOGGER = logging.getLogger(__name__)

ONSITE_RSE = "STORAGE-1"
OFFSITE_RSE_1 = "STORAGE-2"
OFFSITE_RSE_2 = "STORAGE-3"

RNG = np.random.default_rng(seed=42)


def setup_ingest(data_root_dir, vo, scope, top_dir, lock_base_path, num_workers=1):
    ingestion_client = IngestionClient(
        data_path=data_root_dir,
        rse=ONSITE_RSE,
        vo=vo,
    )
    return Ingest(
        client=ingestion_client,
        top_dir=top_dir,
        lock_file_path=lock_base_path / "bdms_ingest.lock",
        polling_interval=0.5,
    )


def test_shared_storage(storage_mount_path: Path):
    """Test that the shared storage path is available."""

    msg = f"Shared storage {storage_mount_path} is not available on the client"
    assert storage_mount_path.exists(), msg


def trigger_judge_repairer() -> None:
    """Trigger the rucio-judge-repairer daemon to run once and fix any STUCK rules."""

    try:
        cmd = [
            ".toolkit/bin/kubectl",
            "exec",
            "deployment/bdms-rucio-daemons-judge-evaluator",
            "--",
            "/usr/local/bin/rucio-judge-repairer",
            "--run-once",
        ]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        LOGGER.info("Triggered rucio-judge-repairer daemon: %s", result.stdout)
    except FileNotFoundError as e:
        LOGGER.error("kubectl command not found: %s", str(e))
        raise RuntimeError(
            "kubectl command not found. Ensure kubectl is in the PATH or working directory."
        ) from e
    except subprocess.CalledProcessError as e:
        LOGGER.error("Failed to trigger rucio-judge-repairer daemon: %s", e.stderr)
        raise


def test_acada_to_lfn(storage_mount_path: Path, test_vo: str):
    """Test the acada_to_lfn method of IngestionClient with valid and invalid inputs."""

    ingestion_client = IngestionClient(storage_mount_path, ONSITE_RSE, vo=test_vo)

    # Test Case 1: valid acada_path
    expected_lfn = f"/{test_vo}/acada/DL0/LSTN-01/events/2023/10/13/example.fits.fz"
    acada_path = ingestion_client.data_path / str(expected_lfn).lstrip("/")
    lfn = ingestion_client.acada_to_lfn(acada_path=acada_path)

    msg = f"Expected {expected_lfn}, got {lfn}"
    assert lfn == expected_lfn, msg

    # Test Case 2: Non-absolute acada_path (empty string)
    with pytest.raises(ValueError, match="acada_path must be absolute"):
        ingestion_client.acada_to_lfn(acada_path="")

    # Test Case 3: Non-absolute acada_path (relative path)
    with pytest.raises(ValueError, match="acada_path must be absolute"):
        ingestion_client.acada_to_lfn(acada_path="./test.fits")

    # Test Case 4: acada_path not within data_path
    invalid_acada_path = "/invalid/path/file.fits.fz"
    with pytest.raises(ValueError, match="is not within data_path"):
        ingestion_client.acada_to_lfn(acada_path=invalid_acada_path)

    # Test Case 5: acada_path does not start with <vo>/
    wrong_prefix_path = (
        f"{ingestion_client.data_path}/wrong_vo/acada/DL0/LSTN-01/file.fits.fz"
    )
    with pytest.raises(ValueError, match="must start with"):
        ingestion_client.acada_to_lfn(acada_path=wrong_prefix_path)


@pytest.mark.usefixtures("_auth_proxy")
def test_check_replica_exists(
    storage_mount_path: Path, test_scope: str, test_vo: str, request
):
    """Test the check_replica_exists method of IngestionClient."""

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    acada_path, _, _ = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    # Generate the LFN
    lfn = ingestion_client.acada_to_lfn(acada_path)

    # Test Case 1: No replica exists yet
    msg = f"Expected no replica for LFN {lfn} before registration"
    assert not ingestion_client.check_replica_exists(lfn, test_scope), msg

    # Register the replica in Rucio
    ingestion_client.add_onsite_replica(acada_path)

    # Test Case 2: Replica exists with a valid PFN
    msg = f"Expected replica to exist for LFN {lfn} after registration"
    assert ingestion_client.check_replica_exists(lfn, test_scope), msg

    # Test Case 3: Non-existent LFN
    nonexistent_lfn = lfn + ".nonexistent"
    msg = f"Expected no replica for nonexistent LFN {nonexistent_lfn}"
    assert not ingestion_client.check_replica_exists(nonexistent_lfn, test_scope), msg


def create_hierarchical_acada_path(file_location, storage_mount_path, vo, scope):
    """Create hierarchical path structure for test file."""

    file_location = Path(file_location)
    filename = file_location.name

    match = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    if not match:
        raise ValueError(f"No date in filename: {filename}")
    year, month, day = match.groups()

    if filename.startswith("SUB"):
        telescope = "ARRAY"
    else:
        dl0_index = file_location.parts.index("DL0")
        telescope = file_location.parts[dl0_index + 1]

    return (
        storage_mount_path
        / vo
        / scope
        / "DL0"
        / telescope
        / "ctao-north"
        / "event"
        / year
        / month
        / day
        / filename
    )


@pytest.fixture
def file_location(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    ("file_location", "metadata_dict"),
    [
        (
            "subarray_test_file",
            {
                "observatory": "CTA",
                "start_time": "2025-02-04T21:34:05",
                "end_time": "2025-02-04T21:43:12",
                "subarray_id": 0,
                "sb_id": 2000000066,
                "obs_id": 2000000200,
            },
        ),
        (
            "tel_trigger_test_file",
            {
                "observatory": "CTA",
                "start_time": "2025-02-04T21:34:05",
                "end_time": "2025-02-04T21:43:11",
                "tel_ids": [1],
                "sb_id": 2000000066,
                "obs_id": 2000000200,
            },
        ),
        (
            "tel_events_test_file",
            {
                "observatory": "CTA",
                "start_time": "2025-04-01T15:25:02",
                "end_time": "2025-04-01T15:25:03",
                "sb_id": 0,
                "obs_id": 0,
            },
        ),
    ],
    indirect=["file_location"],
)
@pytest.mark.usefixtures("_auth_proxy")
@pytest.mark.verifies_usecase("UC-110-1.1.1")
def test_add_onsite_replica_with_acada_files(
    file_location: str,
    metadata_dict: dict,
    test_scope: str,
    tmp_path: Path,
    storage_mount_path,
    test_vo: str,
    caplog,
):
    """Test the add_onsite_replica method of IngestionClient using test files from ACADA integration tests."""

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    acada_path = create_hierarchical_acada_path(
        file_location=Path(file_location),
        storage_mount_path=storage_mount_path,
        vo=test_vo,
        scope=test_scope,
    )

    acada_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_location, str(acada_path))
    reset_xrootd_permissions(storage_mount_path)

    # Use add_onsite_replica to register the replica
    result = ingestion_client.add_onsite_replica(acada_path=acada_path)
    assert result.file_size == os.stat(acada_path).st_size

    # Verify the LFN matches the expected LFN
    expected_lfn = ingestion_client.acada_to_lfn(acada_path)
    msg = f"Expected LFN {expected_lfn}, got {result.lfn}"
    assert result.lfn == expected_lfn, msg

    msg = f"Expected reason for skipping to be None, but it was set to {result.skip_reason}"
    assert result.skip_reason is None, msg

    # Download the file using the LFN
    download_spec = {
        "did": f"{result.scope}:{result.lfn}",
        "base_dir": str(tmp_path),
        "no_subdir": True,
    }
    download_client = DownloadClient()
    download_client.download_dids([download_spec])

    # Verify the downloaded file
    download_path = tmp_path / result.lfn.lstrip("/")
    msg = f"Download failed at {download_path}"
    assert download_path.is_file(), msg

    msg = "Downloaded file content does not match the original."
    assert adler32(download_path) == adler32(file_location), msg

    # Check for don't ingest again if its already registered
    caplog.clear()
    second_result = ingestion_client.add_onsite_replica(acada_path=acada_path)
    msg = f"LFN mismatch on second ingestion attempt: expected {second_result.lfn}, got {result.lfn}"
    assert second_result.scope == test_scope
    assert second_result.lfn == result.lfn, msg
    assert second_result.file_size == 0, "Expected size 0 for skipped file"

    msg = f"Expected reason for skipping to be 'REPLICA_EXISTS', got {second_result.skip_reason}"
    assert second_result.skip_reason == SkipReason.REPLICA_EXISTS, msg

    expected_msg = f"Replica already exists for lfn '{result.lfn}', skipping"
    msg = f"'Replica already exists for lfn '{result.lfn}', skipping' in caplog records"
    assert expected_msg in [r.message for r in caplog.records], msg

    # Retrieve metadata using the DIDClient
    did_client = Client()
    retrieved_metadata = did_client.get_metadata(
        scope=result.scope, name=result.lfn, plugin="JSON"
    )

    # Verify the metadata matches the expected metadata
    for key, value in metadata_dict.items():
        msg = (
            f"Metadata mismatch for key '{key}'. "
            f"Expected: {value}, Got: {retrieved_metadata.get(key)}"
        )
        assert retrieved_metadata.get(key) == value, msg


def test_rses():
    """Test that the expected RSEs are configured."""
    client = Client()
    result = list(client.list_rses())

    rses = [r["rse"] for r in result]
    msg = f"Expected RSE {ONSITE_RSE} not found in {rses}"
    assert ONSITE_RSE in rses, msg

    msg = f"Expected RSE {OFFSITE_RSE_1} not found in {rses}"
    assert OFFSITE_RSE_1 in rses, msg

    msg = f"Expected RSE {OFFSITE_RSE_2} not found in {rses}"
    assert OFFSITE_RSE_2 in rses, msg


def create_single_test_file(storage_mount_path, test_vo, test_scope, request):
    """Create test file with hierarchical path and trigger file."""
    day = get_unique_day_for_tests(request)
    test_files, test_file_content = acada_write_test_files(
        storage_mount_path, test_vo, test_scope, n_files=1, day=day
    )
    acada_path = test_files[0]
    trigger = Path(str(acada_path) + TRIGGER_SUFFIX)
    trigger.symlink_to(acada_path)
    return acada_path, trigger, test_file_content


@pytest.fixture
def pre_existing_dataset(
    storage_mount_path: Path,
    test_scope: str,
    test_vo: str,
    request,
) -> tuple[str, str, str]:
    """Fixture to provide a dataset with an attached file."""

    acada_path, _, test_file_content = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    # This call will create containers, dataset and its attachment to the parent container, registers file
    # replica and sets file metadata, and finally attaches the file to dataset
    result = client.add_onsite_replica(acada_path)
    lfn_file = result.lfn

    dataset = str(Path(lfn_file).parent)

    return dataset, lfn_file, test_file_content


@pytest.mark.usefixtures("_auth_proxy")
@pytest.mark.verifies_usecase("UC-110-1.6")
def test_add_offsite_replication_rules(
    pre_existing_dataset: tuple[str, str, str],
    test_scope: str,
    test_vo: str,
    storage_mount_path: Path,
    tmp_path: Path,
):
    """Test the add_offsite_replication_rules method of IngestionClient."""

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    dataset, lfn_file, test_file_content = pre_existing_dataset

    # Create replication rules for transfer to two offsite RSEs on the dataset
    # Rules on the dataset applies to all attached files

    offsite_rse_expression = "OFFSITE"
    copies = 2
    rule_ids = ingestion_client.add_offsite_replication_rules(
        dataset=dataset,
        offsite_rse_expression=offsite_rse_expression,
        copies=copies,
        lifetime=None,
    )

    rule_id_offsite_1 = rule_ids[0]
    rule_id_offsite_2 = rule_ids[1]
    rule_client = RuleClient()

    # Wait for the first offsite rule to complete (OFFSITE_RSE_1)
    wait_for_replication_status(rule_client, rule_id_offsite_1, expected_status="OK")

    # Verify the replica exists on either OFFSITE_RSE_1 or OFFSITE_RSE_2 after the first rule
    did = {"scope": test_scope, "name": lfn_file}
    replica_client = ReplicaClient()
    replicas = next(replica_client.list_replicas(dids=[did]))
    states = replicas.get("states", {})
    msg = f"Expected replica on either {OFFSITE_RSE_1} or {OFFSITE_RSE_2} to be AVAILABLE after first rule: {states}"
    assert (
        states.get(OFFSITE_RSE_1) == "AVAILABLE"
        or states.get(OFFSITE_RSE_2) == "AVAILABLE"
    ), msg

    # Manually trigger the judge-repairer to ensure the second rule doesn't get stuck
    trigger_judge_repairer()

    # Wait for the second offsite rule to complete (OFFSITE_RSE_2)
    wait_for_replication_status(rule_client, rule_id_offsite_2, expected_status="OK")

    # Verify the replica exists on all RSEs
    replicas = next(replica_client.list_replicas(dids=[did]))
    states = replicas.get("states", {})
    LOGGER.info(
        "Replica states for DID %s in test_replicate_acada_data_to_offsite: %s",
        did,
        states,
    )

    msg = f"Expected replica on {ONSITE_RSE} to be AVAILABLE: {states}"
    assert states.get(ONSITE_RSE) == "AVAILABLE", msg

    msg = f"Expected replica on {OFFSITE_RSE_1} to be AVAILABLE: {states}"
    assert states.get(OFFSITE_RSE_1) == "AVAILABLE", msg

    msg = f"Expected replica on {OFFSITE_RSE_2} to be AVAILABLE: {states}"
    assert states.get(OFFSITE_RSE_2) == "AVAILABLE", msg

    # Download the file from OFFSITE_RSE_2 to verify its content
    download_spec = {
        "did": f"{test_scope}:{lfn_file}",
        "base_dir": str(tmp_path),
        "no_subdir": True,
        "rse": OFFSITE_RSE_2,
    }
    download_client = DownloadClient()
    download_client.download_dids([download_spec])

    # Verify the downloaded file content
    download_path = tmp_path / lfn_file.lstrip("/")
    msg = f"Download failed at {download_path}"
    assert download_path.is_file(), msg

    downloaded_content = download_path.read_text()
    msg = (
        f"Downloaded file content does not match the original. "
        f"Expected: {test_file_content}, Got: {downloaded_content}"
    )
    assert downloaded_content == test_file_content, msg


@pytest.mark.usefixtures("_auth_proxy")
@pytest.mark.verifies_usecase("UC-110-1.6")
def test_add_offsite_replication_rules_single_copy(
    pre_existing_dataset: str,
    test_scope: str,
    test_vo: str,
    storage_mount_path: Path,
    tmp_path: Path,
    caplog,
):
    """Test the add_offsite_replication_rules method of IngestionClient with a single copy (copies=1)."""

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    dataset, lfn_file, test_file_content = pre_existing_dataset

    offsite_rse_expression = "OFFSITE"
    copies = 1
    rule_ids = ingestion_client.add_offsite_replication_rules(
        dataset=dataset,
        offsite_rse_expression=offsite_rse_expression,
        copies=copies,
        lifetime=None,
    )

    # Verify that only one rule was created
    msg = f"Expected exactly 1 rule ID, got {len(rule_ids)}: {rule_ids}"
    assert len(rule_ids) == 1, msg

    rule_id_offsite_1 = rule_ids[0]
    rule_client = RuleClient()

    # Wait for the offsite rule to complete
    wait_for_replication_status(rule_client, rule_id_offsite_1, expected_status="OK")

    # Verify the replica exists on exactly one of the offsite RSEs (either OFFSITE_RSE_1 or OFFSITE_RSE_2)
    did = {"scope": test_scope, "name": lfn_file}
    replica_client = ReplicaClient()
    replicas = next(replica_client.list_replicas(dids=[did]))
    states = replicas.get("states", {})
    LOGGER.info(
        "Replica states for DID %s in test_add_offsite_replication_rules_single_copy: %s",
        did,
        states,
    )
    # Check that the replica exists on exactly one offsite RSE
    offsite_replica_count = sum(
        1 for rse in [OFFSITE_RSE_1, OFFSITE_RSE_2] if states.get(rse) == "AVAILABLE"
    )
    msg = f"Expected exactly 1 offsite replica (on either {OFFSITE_RSE_1} or {OFFSITE_RSE_2}), got {offsite_replica_count}: {states}"
    assert offsite_replica_count == 1, msg

    # Determine which offsite RSE the replica was created on
    target_offsite_rse = (
        OFFSITE_RSE_1 if states.get(OFFSITE_RSE_1) == "AVAILABLE" else OFFSITE_RSE_2
    )

    # Download the file from the target offsite RSE to verify its content
    download_spec = {
        "did": f"{test_scope}:{lfn_file}",
        "base_dir": str(tmp_path),
        "no_subdir": True,
        "rse": target_offsite_rse,
    }
    download_client = DownloadClient()
    download_client.download_dids([download_spec])

    # Verify the downloaded file content
    download_path = tmp_path / lfn_file.lstrip("/")
    msg = f"Download failed at {download_path}"
    assert download_path.is_file(), msg
    downloaded_content = download_path.read_text()
    msg = (
        f"Downloaded file content does not match the original. "
        f"Expected: {test_file_content}, Got: {downloaded_content}"
    )
    assert downloaded_content == test_file_content, msg


def test_verify_fits_file(tel_events_test_file):
    from bdms.acada_ingestion import verify_fits_checksum

    with fits.open(tel_events_test_file) as hdul:
        verify_fits_checksum(hdul)


@pytest.fixture
def broken_checksum(tmp_path):
    # create a fits file with a broken checksum
    path = tmp_path / "invalid.fits"

    table = Table({"foo": [1, 2, 3], "bar": [4.0, 5.0, 6.0]})
    hdul = fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU(table)])
    hdul.writeto(path, checksum=True)

    # break it
    with path.open("rb+") as f:
        # FITS files are stored in blocks of 2880 bytes
        # first chunk should be the primary header
        # second chunk the header of the bintable
        # third chunk the payload of the bintable
        # we write garbage somewhere into the payload of the table
        f.seek(2 * 2880 + 10)
        f.write(b"\x12\x34\xff")
    return path


def test_verify_fits_file_invalid_checksum(broken_checksum):
    from bdms.acada_ingestion import FITSVerificationError, verify_fits_checksum

    with fits.open(broken_checksum) as hdul:
        with pytest.raises(FITSVerificationError, match="CHECKSUM verification failed"):
            verify_fits_checksum(hdul)


def test_ingest_init(storage_mount_path):
    """Test that Ingest initializes correctly with given parameters."""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
    )

    ingest = Ingest(
        client=ingestion_client,
        top_dir=storage_mount_path,
        lock_file_path=storage_mount_path / "lockfile.lock",
        polling_interval=0.5,
    )
    assert ingest.client == ingestion_client
    assert ingest.top_dir == storage_mount_path
    assert ingest.lock_file_path == storage_mount_path / "lockfile.lock"
    assert abs(ingest.polling_interval - 0.5) < 0.001
    assert not ingest.stop_event.is_set()  # check stop_event initial state
    assert hasattr(ingest, "task_counter")
    assert hasattr(ingest, "submitted_tasks")
    assert ingest.task_counter == 0
    assert len(ingest.submitted_tasks) == 0


def test_check_directory_valid(storage_mount_path, tmp_path, caplog):
    """Test _check_directory with a valid, readable directory."""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
    )

    ingest = Ingest(
        client=ingestion_client,
        top_dir=tmp_path,
        lock_file_path=storage_mount_path / "bdms_ingest.lock",
        polling_interval=0.5,
    )
    ingest._check_directory()


def test_check_directory_invalid(storage_mount_path, tmp_path, caplog):
    """Test _check_directory with an invalid directory."""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
        logger=LOGGER,
    )

    invalid_dir = tmp_path / "nonexistent"

    ingest = Ingest(
        client=ingestion_client,
        top_dir=invalid_dir,
        lock_file_path=storage_mount_path / "bdms_ingest.lock",
        polling_interval=0.5,
    )

    with pytest.raises(RuntimeError, match=f"Cannot read directory {invalid_dir}"):
        ingest._check_directory()
    assert f"Cannot read directory {invalid_dir}" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_process_file_success(storage_mount_path, caplog, test_vo, test_scope, request):
    """Test for checking successful ingestion with trigger file clean-up, depends on IngestionClient"""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    test_file, trigger_file, test_file_content = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    result = process_file(ingestion_client, str(test_file))

    assert result.file_size == len(test_file_content)
    assert result.skip_reason is None
    assert not trigger_file.exists()
    assert "Successfully registered the replica for lfn" in caplog.text
    assert "Created 2 offsite replication rule(s) for dataset" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_process_file_skipped(storage_mount_path, caplog, test_vo, test_scope, request):
    """Test for checking skipped ingestion when replica already exists"""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    test_file, _, test_file_content = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    # process file for the first time
    result = process_file(ingestion_client, str(test_file))
    assert result.skip_reason is None
    assert result.file_size == len(test_file_content)

    caplog.clear()
    # process file second time to verify it is skipped
    result = process_file(ingestion_client, str(test_file))
    assert result.skip_reason == SkipReason.REPLICA_EXISTS
    assert result.file_size == 0
    assert "Replica already exists" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_process_file_failure(storage_mount_path, tmp_path):
    """Test for checking failure for invalid file paths"""
    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
    )

    invalid_file = tmp_path / "invalid_file.fits"
    invalid_file.write_text("dummy content")
    trigger_file = Path(str(invalid_file) + TRIGGER_SUFFIX)
    trigger_file.symlink_to(invalid_file)

    # The file path is outside the data_path causing a ValueError in acada_to_lfn
    with pytest.raises(ValueError, match="is not within data_path"):
        process_file(ingestion_client, str(invalid_file))

    # Trigger file should still exist since ingestion failed
    msg = "Trigger file should not be removed when ingestion fails"
    assert trigger_file.is_symlink(), msg
    trigger_file.unlink()


def test_sequential_exclusion_lock_prevention(storage_mount_path, tmp_path):
    """Test that a second daemon instance cannot start when first is already running.

    This test validates sequential exclusion: when one ingestion daemon is already
    running and has acquired the lock, any subsequent attempt to start another
    daemon instance should fail with a clear error message.
    """
    lock_file = tmp_path / "sequential_test.pid"

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
    )

    # Create two identical instances
    kwargs = dict(
        client=ingestion_client,
        top_dir=tmp_path,
        lock_file_path=lock_file,
        polling_interval=30.0,  # to avoid lots of logs for scanning
    )
    ingest1 = Ingest(**kwargs)
    ingest2 = Ingest(**kwargs)

    try:
        # start first instance
        ingest1.run(block=False)

        # Verify first instance has acquired lock with content validation
        msg = "First instance should have created PID file"
        assert lock_file.exists(), msg

        # Verify the lock file contains current process PID or a valid PID
        current_pid = os.getpid()
        stored_pid = int(lock_file.read_text().strip())

        # The stored PID should be current process since we're running in same process
        msg = f"Expected PID {current_pid}, got {stored_pid}"
        assert stored_pid == current_pid, msg

        # Starting a second instance should error acquiring the lock
        with pytest.raises(
            RuntimeError, match="Another ingestion process is already running"
        ):
            ingest2.run(block=False)

    finally:
        ingest1.shutdown()

    assert not lock_file.exists(), msg


def test_concurrent_exclusion_lock_prevention(storage_mount_path, tmp_path):
    """Test FileLock behavior under true concurrent access - simultaneous daemon startup attempts.

    This test validates real concurrent scenario where multiple daemon instances
    attempt to acquire the same lock simultaneously, simulating race conditions
    that occur in production environments.
    """
    lock_file = tmp_path / "concurrent_test.pid"

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo="ctao",
    )

    # Create two identical instances
    kwargs = dict(
        client=ingestion_client,
        top_dir=tmp_path,
        lock_file_path=lock_file,
        polling_interval=30.0,  # to avoid lots of logs for scanning
    )
    ingest1 = Ingest(**kwargs)
    ingest2 = Ingest(**kwargs)
    results = {}

    # Synchronization barrier - both threads wait here until released
    start_barrier = threading.Barrier(3)  # 2 worker threads + 1 main thread

    def run_instance(instance_id, instance):
        """Run instance - both will try to start simultaneously."""
        try:
            # synchronize with other threads
            start_barrier.wait()

            instance.run(block=False)
            results[instance_id] = "success"
        except RuntimeError as e:
            if "Another ingestion process is already running" in str(e):
                results[instance_id] = f"lock_conflict: {str(e)}"
            else:
                results[instance_id] = f"unexpected_error: {str(e)}"
        except Exception as e:
            results[instance_id] = f"error: {str(e)}"

    # Create both threads
    thread1 = threading.Thread(
        target=run_instance, args=("first", ingest1), daemon=False
    )
    thread2 = threading.Thread(
        target=run_instance, args=("second", ingest2), daemon=False
    )

    # Start both threads - they will wait at the barrier
    thread1.start()
    thread2.start()

    # Release the barrier - both threads start simultaneously
    start_barrier.wait()

    # Wait for both to complete the lock acquisition attempt
    thread1.join(timeout=15)
    thread2.join(timeout=15)

    LOGGER.debug("True Concurrency tests: %s", results)

    # Shutdown both. Shutdown works even when not started.
    for ingest in (ingest1, ingest2):
        ingest.shutdown()

    # Verify results - Exactly ONE should succeed, ONE should fail
    msg = f"Both instances should complete, got: {results}"
    assert len(results) == 2, msg

    success_count = sum(1 for result in results.values() if result == "success")
    conflict_count = sum(1 for result in results.values() if "lock_conflict" in result)

    msg = f"Exactly ONE instance should succeed, got {success_count}: {results}"
    assert success_count == 1, msg

    msg = f"Exactly ONE instance should get lock conflict, got {conflict_count}: {results}"
    assert conflict_count == 1, msg

    # Verify the lock conflict has correct error message
    conflict_result = [r for r in results.values() if "lock_conflict" in r][0]
    msg = "Expected 'Another ingestion process is already running' message in conflict result"
    assert "Another ingestion process is already running" in conflict_result, msg

    msg = "Lock file should be cleaned up"
    assert not lock_file.exists(), msg


def acada_create_trigger_symlink(data_file):
    """Represents creating a trigger symlink for a given data file."""

    try:
        trigger_file = Path(str(data_file) + TRIGGER_SUFFIX)
        trigger_file.symlink_to(data_file)
        LOGGER.info("Created trigger file: %s -> %s", trigger_file, data_file)
        return trigger_file

    except Exception as e:
        raise RuntimeError(f"Failed to create trigger for {data_file}: {e}") from e


def create_unique_test_dir(storage_mount_path, test_vo, test_scope):
    """Create a unique test directory."""
    return storage_mount_path / test_vo / test_scope / f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def create_test_file_with_trigger():
    """Create a test FITS file and its trigger file and also cleanup."""

    data_file = None
    trigger_file = None

    def _create_files(test_dir, filename="test_file.fits"):
        nonlocal data_file, trigger_file
        data_file = test_dir / filename
        hdu = fits.PrimaryHDU(RNG.random((10, 10)))
        hdu.writeto(data_file, overwrite=True, checksum=True)

        trigger_file = Path(str(data_file) + TRIGGER_SUFFIX)
        trigger_file.symlink_to(data_file)

        return data_file, trigger_file

    yield _create_files

    if trigger_file is not None and trigger_file.is_symlink():
        trigger_file.unlink()


@pytest.fixture
def setup_test_files_with_triggers(storage_mount_path, test_vo, persistent_test_scope):
    """Create test files with triggers using persistent scope and clean up after test."""
    data_files = []
    trigger_files = []
    expected_lfns = []

    try:
        data_files, _ = acada_write_test_files(
            storage_mount_path, test_vo, persistent_test_scope, n_files=5
        )

        for data_file in data_files:
            trigger_file = acada_create_trigger_symlink(data_file)
            trigger_files.append(trigger_file)
            expected_lfns.append(f"/{data_file.relative_to(storage_mount_path)}")

        yield data_files, trigger_files, expected_lfns

    finally:
        # Clean up
        for trigger_file in trigger_files:
            if trigger_file.is_symlink():
                trigger_file.unlink()


@pytest.fixture
def ingest_daemon_test(storage_mount_path, test_vo, test_scope, tmp_path):
    """Create and manage ingest daemon for tests."""
    test_data_dir = create_unique_test_dir(storage_mount_path, test_vo, test_scope)
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path, test_vo, test_scope, test_data_dir, tmp_path
    )

    yield ingest, test_data_dir

    ingest.shutdown()


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "disable_ingestion_daemon"
)
@pytest.mark.verifies_usecase("UC-110-1.1.4")
def test_ingest_parallel_submission(
    storage_mount_path, caplog, test_vo, test_scope, request
):
    """Test parallel file processing: creates multiple FITS files simultaneously and verifies that the
    daemon can detect, process, and ingest them efficiently using celery workers."""

    ingestion_client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    ingest = Ingest(
        client=ingestion_client,
        top_dir=storage_mount_path,
        lock_file_path=storage_mount_path / "bdms_ingest.lock",
        polling_interval=0.5,
    )

    day = get_unique_day_for_tests(request)
    data_files, _ = acada_write_test_files(
        storage_mount_path, test_vo, test_scope, n_files=7, day=day
    )

    n_data_files = len(data_files)

    try:
        ingest.run(block=False)

        # Create trigger files and also track
        trigger_files = []
        for data_file in data_files:
            trigger_file = data_file.with_name(data_file.name + TRIGGER_SUFFIX)
            trigger_file.symlink_to(data_file.relative_to(data_file.parent))
            trigger_files.append(trigger_file)

        # Wait for processing with concurrency monitoring
        processing_timeout = 120.0
        processing_start = time.perf_counter()
        processed_files = 0

        while time.perf_counter() - processing_start < processing_timeout:
            # Check processing completion
            processed_files = sum(
                1
                for df in data_files
                if f"Processed file {df} with result" in caplog.text
            )

            # an error occurred
            if "Fatal error in result monitoring thread" in caplog.text:
                break

            # all done
            if processed_files == n_data_files:
                break

            time.sleep(0.5)

        duration = time.perf_counter() - processing_start
        error = f"Only {processed_files} of {n_data_files} files processed successfully in {duration}"
        assert processed_files == 7, error

        # Record ingestion workflow completion time
    finally:
        # Stop the daemon
        ingest.shutdown()

    # Verify results
    assert "Result monitoring thread started" in caplog.text

    # Verify trigger files were cleaned up during successful processing
    remaining_triggers = sum(1 for tf in trigger_files if tf.exists())
    error = f"Expected all trigger files to be cleaned up, {remaining_triggers} remain"
    assert remaining_triggers == 0, error

    # Verify clean shutdown
    assert not ingest.lock_file_path.exists()
    assert "Stopped ingestion daemon" in caplog.text
    assert "Result monitoring thread stopped" in caplog.text

    # Test daemon restart with new file
    caplog.clear()

    # Create new file while ingestion daemon is not running
    new_data_file, new_trigger_file, _ = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    # Restart daemon
    try:
        ingest.run(block=False)

        # Wait for new file processing
        new_start = time.perf_counter()

        while time.perf_counter() - new_start < 30.0:
            if f"Processed file {new_data_file} with result" in caplog.text:
                break
            time.sleep(0.5)
        else:
            pytest.fail("New file was not processed after restart")

        new_file_processing_time = time.perf_counter() - new_start
        assert not new_trigger_file.exists(), "New trigger file not cleaned up"
    finally:
        shutdown_start = time.perf_counter()
        ingest.shutdown()
        ingest_end = time.perf_counter()
        shutdown_duration = time.perf_counter() - shutdown_start

    error = "Re-started daemon did not terminate within timeout of 10 s"
    assert shutdown_duration < 10, error

    # Statistics
    detection_to_completion_time = ingest_end - processing_start
    processing_rate = (
        processed_files / detection_to_completion_time
        if detection_to_completion_time > 0
        else 0
    )

    total_submitted = ingest.task_counter
    tasks_cleaned_up = len(ingest.submitted_tasks) == 0
    LOGGER.info("=== Parallel Ingestion Test Results ===")
    LOGGER.info(
        "Files processed: %d/7 in %.1fs",
        processed_files,
        detection_to_completion_time,
    )
    LOGGER.info("Processing rate: %.1f files/sec", processing_rate)
    LOGGER.info("Total tasks submitted: %d", total_submitted)
    LOGGER.info("Task cleanup successful: %s", tasks_cleaned_up)
    LOGGER.info("New file after restart: processed in %.1fs", new_file_processing_time)


@pytest.mark.usefixtures("_auth_proxy")
def test_scan_for_triggers_success(
    caplog, ingest_daemon_test, create_test_file_with_trigger
):
    """Test _scan_for_triggers detects new trigger files and tracks them."""

    ingest, test_data_dir = ingest_daemon_test
    data_file, trigger_file = create_test_file_with_trigger(test_data_dir)

    original_task = acada_ingestion.process_acada_file
    mock_task = MockCeleryTask()
    acada_ingestion.process_acada_file = mock_task

    try:
        with caplog.at_level(logging.DEBUG, logger="bdms.acada_ingestion.Ingest"):
            ingest.run(block=False)
            time.sleep(1.0)  # Allow one scanning cycle
    finally:
        ingest.shutdown()
        acada_ingestion.process_acada_file = original_task

    assert "Scanned for triggers: found 1 total, 1 new" in caplog.text
    assert (
        f"Processing trigger file {trigger_file}, submitting data file {data_file}"
        in caplog.text
    )
    assert f"Submitting task test-task-0 for file {data_file}" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_scan_for_triggers_no_new_triggers(
    caplog, ingest_daemon_test, create_test_file_with_trigger
):
    """Test that daemon does not resubmit already known triggers."""
    ingest, test_data_dir = ingest_daemon_test

    with caplog.at_level(logging.DEBUG, logger="bdms.acada_ingestion.Ingest"):
        _, trigger_file = create_test_file_with_trigger(test_data_dir)
        # Add trigger to known_triggers to simulate it was already processed
        ingest.known_triggers.add(trigger_file)

        try:
            # perform scan manually
            ingest._scan_for_triggers()

            assert "Scanned for triggers: found 1 total, 0 new" in caplog.text
            msg = "No trigger files should be processed"
            assert "Processing trigger file" not in caplog.text, msg
            assert len(ingest.submitted_tasks) == 0
            assert len(ingest.known_triggers) == 1
        finally:
            trigger_file.unlink()


class MockQueue(list):
    def submit(self, path):
        self.append(path)


class MockAsyncResult:
    """Mock Celery AsyncResult used in tests supporting SUCCESS, FAILURE and REVOKED states."""

    def __init__(self, task_id, state="SUCCESS", result=None):
        self.id = task_id
        self.state = state
        self.result = result or {
            "lfn": f"mock_lfn_{task_id}",
            "file_size": 100,
            "skip_reason": None,
        }
        self.traceback = None

    def ready(self):
        return self.state in ("SUCCESS", "FAILURE", "REVOKED")

    def successful(self):
        return self.state == "SUCCESS"

    def failed(self):
        return self.state == "FAILURE"

    def get(self, *args, **kwargs):
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result

    def revoke(self, terminate=False):
        self.state = "REVOKED"


class MockCeleryTask:
    """Mock Celery task used in place of process_acada_file in daemon tests."""

    def __init__(self, *, fail_with=None):
        self.calls = []
        self.call_count = 0
        self.fail_with = fail_with

    def delay(self, **kwargs):
        task_id = f"test-task-{self.call_count}"
        self.calls.append(kwargs)
        self.call_count += 1

        if self.fail_with:
            return MockAsyncResult(task_id, state="FAILURE", result=self.fail_with)
        else:
            return MockAsyncResult(task_id, state="SUCCESS")


def wait_for_ingestion_daemon(max_tries=15):
    """Wait for ingestion daemon to be ready ."""
    for _ in range(max_tries):
        try:
            fetch_ingestion_daemon_metrics()
            return
        except URLError:
            time.sleep(2)
    raise TimeoutError("Ingestion daemon not ready")


@pytest.mark.usefixtures("_auth_proxy")
def test_process_trigger_file_success(
    storage_mount_path,
    test_vo,
    test_scope,
    caplog,
    tmp_path,
    create_test_file_with_trigger,
):
    """Test that _process_trigger_file submits the task and logs correctly."""
    test_data_dir = create_unique_test_dir(storage_mount_path, test_vo, test_scope)
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path, test_vo, test_scope, test_data_dir, tmp_path
    )

    data_file, trigger_file = create_test_file_with_trigger(test_data_dir)

    original_task = acada_ingestion.process_acada_file
    mock_task = MockCeleryTask()
    acada_ingestion.process_acada_file = mock_task

    try:
        with caplog.at_level(logging.DEBUG, logger="bdms.acada_ingestion.Ingest"):
            ingest._process_trigger_file(trigger_file)

        assert (
            f"Processing trigger file {trigger_file}, submitting data file {data_file}"
            in caplog.text
        )
        assert f"Submitting task test-task-0 for file {data_file}" in caplog.text
        assert f"Successfully processed trigger {trigger_file}" in caplog.text

        assert mock_task.call_count == 1
        assert mock_task.calls[0]["file_path"] == str(data_file)

        with ingest.task_lock:
            assert len(ingest.submitted_tasks) == 1
            assert "test-task-0" in ingest.submitted_tasks
    finally:
        acada_ingestion.process_acada_file = original_task


@pytest.mark.usefixtures("_auth_proxy")
def test_polling_loop_success(
    storage_mount_path,
    test_vo,
    test_scope,
    caplog,
    tmp_path,
    create_test_file_with_trigger,
):
    """Test _polling_loop runs and processes trigger files until stopped."""
    test_data_dir = (
        storage_mount_path / test_vo / test_scope / f"test_{uuid.uuid4().hex[:8]}"
    )
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path, test_vo, test_scope, test_data_dir, tmp_path
    )

    data_file, trigger_file = create_test_file_with_trigger(test_data_dir)

    # mock submitting files so we do not actually do anything
    submitted_files = MockQueue()
    ingest._submit_file = submitted_files.submit

    with caplog.at_level(logging.DEBUG, logger="bdms.acada_ingestion.Ingest"):
        try:
            ingest.run(block=False)
            time.sleep(1.5)
        finally:
            ingest.shutdown()

    assert submitted_files == [str(data_file)]
    assert (
        f"Starting polling of directory {test_data_dir} every 0.5 seconds"
        in caplog.text
    )
    assert (
        f"Processing trigger file {trigger_file}, submitting data file {data_file}"
        in caplog.text
    )
    assert "Stopped polling for new trigger files" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_create_container_hierarchy_is_idempotent(
    storage_mount_path, test_vo, test_scope
):
    """Test creation of containers and their hierarchy with parent-child attachments and idempotency."""

    client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    container_path = f"/{test_vo}/{test_scope}/DL0/LSTN-01/ctao-north/event/2025/12"

    # The first call creates the full container hierarchy
    client.create_container_hierarchy(container_path)

    # Build expected container list
    p = Path(container_path)
    containers = [str(parent) for parent in reversed(p.parents) if str(parent) != "/"]
    containers.append(container_path)
    containers = containers[2:]

    # Verify each container exists in the hierarchy
    for container in containers:
        did = client.did_client.get_did(scope=test_scope, name=container)
        assert did["type"] == "CONTAINER"

    # Verify parent-child relationships and their attachment
    for i in range(len(containers) - 1):
        parent = containers[i]
        child = containers[i + 1]
        child_names = [
            item["name"]
            for item in client.did_client.list_content(scope=test_scope, name=parent)
        ]
        assert child in child_names

    # The second call does nothing, idempotent, containers already exists and raises no errors
    client.create_container_hierarchy(container_path)

    # Verify the container hierarchy remains unchanged
    for container in containers:
        did = client.did_client.get_did(scope=test_scope, name=container)
        assert did["type"] == "CONTAINER"


@pytest.mark.usefixtures("_auth_proxy")
def test_add_onsite_replica_multiple_files_same_dataset(
    storage_mount_path, test_vo, test_scope
):
    """Test to check ingesting multiple files on the same day creates dataset only once."""
    client = IngestionClient(
        data_path=storage_mount_path,
        rse=ONSITE_RSE,
        vo=test_vo,
    )

    data_files, _ = acada_write_test_files(
        storage_mount_path, test_vo, test_scope, n_files=2
    )

    result1 = client.add_onsite_replica(data_files[0])
    assert result1.skip_reason is None

    result2 = client.add_onsite_replica(data_files[1])
    assert result2.skip_reason is None

    dataset1 = str(Path(result1.lfn).parent)
    dataset2 = str(Path(result2.lfn).parent)

    assert dataset1 == dataset2

    # Verify dataset is attached to its parent container
    container = str(Path(result1.lfn).parents[1])
    child_name = [
        item["name"]
        for item in client.did_client.list_content(scope=test_scope, name=container)
    ]
    assert dataset1 in child_name


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "enable_ingestion_daemon"
)
@pytest.mark.verifies_usecase("UC-110-1.1.4")
def test_ingest_parallel_submission_with_live_daemon(setup_test_files_with_triggers):
    """Test parallel file processing with an already running daemon."""

    # Wait for daemon to be ready before fetching metrics
    wait_for_ingestion_daemon()

    metrics_before_test = fetch_ingestion_daemon_metrics()
    # metrics should be 0 as we restart the daemon
    for k in ("success", "processed", "skipped"):
        assert metrics_before_test[f"n_tasks_{k}_total"] == 0

    data_files, trigger_files, expected_lfns = setup_test_files_with_triggers

    try:
        wait_for_trigger_file_removal(trigger_files, timeout=120.0)
        wait_for_replicas(expected_lfns)

        # make sure that metrics are available from the daemon
        metrics = fetch_ingestion_daemon_metrics()

        def difference(key):
            return metrics[key] - metrics_before_test[key]

        assert metrics["n_tasks_success_created"] < time.time()
        assert difference("n_tasks_processed_total") == len(data_files)

        n_skipped_or_success = (
            metrics["n_tasks_success_total"] + metrics["n_tasks_skipped_total"]
        )
        error = "Ingestion daemon metrics do not match expected values"
        assert difference("n_tasks_processed_total") == n_skipped_or_success, error

    finally:
        deployment_scale("ingestion-daemon", 0)


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "disable_ingestion_daemon"
)
def test_ingest_detects_existing_files_with_live_daemon(
    storage_mount_path, test_vo, setup_test_files_with_triggers
):
    """Test for ingestion daemon detecting and processing already existing files created before it started running."""

    test_scope = "test_scope_persistent"

    data_files, trigger_files, expected_lfns = setup_test_files_with_triggers

    LOGGER.info(
        "Created %d files and triggers while daemon is not running", len(data_files)
    )

    # Verify trigger files exist before starting daemon
    existing_triggers = list(
        (storage_mount_path / test_vo / test_scope).glob("*.trigger")
    )
    if existing_triggers:
        LOGGER.info("Trigger files created: %d", len(existing_triggers))
        for tf in existing_triggers:
            LOGGER.info("Created: %s", tf)

    try:
        # Start the ingestion daemon pod once files are created
        deployment_scale("ingestion-daemon", 1)

        wait_for_trigger_file_removal(trigger_files, timeout=120.0)
        wait_for_replicas(expected_lfns)

        LOGGER.info(
            "Ingestion daemon successfully detected and processed existing files"
        )

        # make sure that metrics are available from the daemon
        n_tasks_metrics = fetch_ingestion_daemon_metrics()

        files_processed = n_tasks_metrics["n_tasks_processed_total"]
        files_success = n_tasks_metrics["n_tasks_success_total"]
        files_skipped = n_tasks_metrics["n_tasks_skipped_total"]
        msg = f"Expected {len(data_files)} files processed, got {files_processed}"
        assert files_processed == len(data_files), msg

        LOGGER.info(
            "Ingestion daemon metrics verified: processed %d files (%d success, %d skipped)",
            files_processed,
            files_success,
            files_skipped,
        )

    finally:
        # Stop daemon: shutdown
        deployment_scale("ingestion-daemon", 0)


@pytest.mark.parametrize(
    "expected_message",
    [
        "empty data file name",
        "data path {data_path} missing",
        "data path {data_path} is not a file",
    ],
)
def test_invalid_trigger_files(
    expected_message,
    storage_mount_path,
    test_vo,
    test_scope,
    caplog,
    tmp_path,
):
    """
    Regression test for bug #131, ingestion of a trigger link just named .trigger

    In case of a file just called ".trigger" pointing to an existing file
    in the link itself was ingested. While this should never happen in production,
    this is a clear bug.
    """

    test_data_dir = (
        storage_mount_path / test_vo / test_scope / f"test_{uuid.uuid4().hex[:8]}"
    )
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path,
        test_vo,
        test_scope,
        top_dir=test_data_dir,
        lock_base_path=tmp_path,
    )

    # mock submitting files, we only want to check the behavior of the submission logic
    submitted_files = MockQueue()
    ingest._submit_file = submitted_files.submit

    # create dummy data path / trigger file for expected_message
    if "empty" in expected_message:
        data_path = test_data_dir / "test.dat"
        data_path.write_text("test")
        trigger_file = test_data_dir / ".trigger"
    elif "missing" in expected_message:
        data_path = test_data_dir / "test.dat"
        trigger_file = data_path.with_name(data_path.name + TRIGGER_SUFFIX)
    else:
        data_path = test_data_dir / "subdir"
        data_path.mkdir()
        trigger_file = data_path.with_name(data_path.name + TRIGGER_SUFFIX)

    trigger_file.symlink_to(data_path.relative_to(test_data_dir))

    try:
        with caplog.at_level(logging.ERROR, logger="bdms.acada_ingestion.Ingest"):
            caplog.clear()
            # scan for files once, manually.
            ingest._scan_for_triggers()

        assert len(submitted_files) == 0
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"

        trigger_part = f"Ignoring trigger file: {trigger_file}, "
        data_part = expected_message.format(data_path=data_path)
        assert caplog.records[0].message == trigger_part + data_part
    finally:
        trigger_file.unlink()
        if data_path.is_dir():
            data_path.rmdir()
        elif data_path.is_file():
            data_path.unlink()


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "enable_ingestion_daemon"
)
def test_celery_retry_with_rucio_outage(
    storage_mount_path, test_vo, persistent_test_scope
):
    """Integration test with Celery workers retrying tasks when Rucio server is temporarily unavailable."""

    n_files = 5
    test_files, _ = acada_write_test_files(
        storage_mount_path, test_vo, persistent_test_scope, n_files=n_files
    )

    # Wait for daemon to be ready before fetching metrics
    wait_for_ingestion_daemon()
    metrics_before = fetch_ingestion_daemon_metrics()
    LOGGER.info("Disabling Rucio server to simulate outage")
    deployment_scale("rucio-server", 0)

    trigger_files = []
    for test_file in test_files:
        trigger = acada_create_trigger_symlink(test_file)
        trigger_files.append(trigger)

    LOGGER.info("Created %d triggers for parallel processing", n_files)

    # Wait a bit for daemon to detect and submit task
    time.sleep(5.0)

    # Task should be failing/retrying
    metrics_during = fetch_ingestion_daemon_metrics()
    tasks_queued = metrics_during["n_tasks_queued"]
    LOGGER.info("Tasks in queue while Rucio is unavailable: %d", tasks_queued)

    # Wait for Celery to attempt retries
    LOGGER.info("Waiting 30s for Celery retry attempts while Rucio is down")
    time.sleep(30.0)

    # Making Rucio server active again and also giving it time to initialize
    deployment_scale("rucio-server", 1)
    time.sleep(10.0)

    start = time.time()
    while time.time() - start < 120.0:
        remaining = sum(1 for t in trigger_files if t.exists())
        if remaining == 0:
            break
        time.sleep(2.0)

    processing_time = time.time() - start

    # Verify all processed
    remaining = [t for t in trigger_files if t.exists()]
    assert (
        len(remaining) == 0
    ), f"{len(remaining)} triggers remain after {processing_time:.1f}s"

    # Verify all ingested
    client = IngestionClient(storage_mount_path, ONSITE_RSE, test_vo)
    for test_file in test_files:
        lfn = client.acada_to_lfn(test_file)
        assert client.check_replica_exists(lfn, persistent_test_scope)

    time.sleep(5.0)
    metrics_after = fetch_ingestion_daemon_metrics()

    tasks_processed = (
        metrics_after["n_tasks_processed_total"]
        - metrics_before["n_tasks_processed_total"]
    )
    tasks_success = (
        metrics_after["n_tasks_success_total"] - metrics_before["n_tasks_success_total"]
    )

    msg = f"Expected {n_files} tasks processed, got {tasks_processed}"
    assert tasks_processed == n_files, msg

    msg = f"Expected {n_files} tasks successful, got {tasks_success}"
    assert tasks_success == n_files, msg

    avg_time = processing_time / n_files
    LOGGER.info(
        "Processed %d files in %.1fs (avg %.1fs/file)",
        n_files,
        processing_time,
        avg_time,
    )


def test_ingestion_dl0_missing_metadata(
    dummy_dl0_files,
    invalid_dl0_files_base,
    altered_metadata_schemas,
    storage_mount_path,
    test_vo,
    test_scope,
    caplog,
):
    """
    Testing a DL0 file, with missing required metadata, is not ingested and moved to
    a dedicated on-site folder.
    """
    subarray_file_path = dummy_dl0_files["subarray_file_path"]
    ingestion_client = IngestionClient(storage_mount_path, ONSITE_RSE, vo=test_vo)
    # trying to ingest the file
    ingest_result = process_file(ingestion_client, str(subarray_file_path))

    assert ingest_result.skip_reason == SkipReason.MISSING_REQUIRED_METADATA

    # getting the list of files in the invalid directory destination in order to check
    # that the processed file was moved inside the expected directory
    files_invalid_dl0 = [
        p.name for p in invalid_dl0_files_base["subarray_dir"].glob("*")
    ]

    assert subarray_file_path.name in files_invalid_dl0
    assert subarray_file_path.name + TRIGGER_SUFFIX in files_invalid_dl0

    # checking the logs content in order to verify the WARNING and the ERROR log messages ones are sent
    log_info = [[r.levelname, r.message] for r in caplog.records]

    msg = "Missing warning log for a required metadata not found"
    assert [
        "WARNING",
        f"The replica for lfn '{ingest_result.lfn}' was not registered as not all the required metadata were set in the file '{subarray_file_path}'",
    ] in log_info, msg

    msg = "Missing error log of not ingested file]"
    assert [
        "ERROR",
        f"File not ingested because of missing required metadata: {subarray_file_path}",
    ] in log_info, msg


@pytest.mark.usefixtures("_auth_proxy")
def test_process_acada_file_task_success(
    storage_mount_path, caplog, test_vo, test_scope, request
):
    """Test for executing the task function directly"""

    test_file, trigger_file, test_file_content = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    result = acada_ingestion.process_acada_file(
        file_path=str(test_file),
        data_path=str(storage_mount_path),
        rse=ONSITE_RSE,
        vo=test_vo,
        copies=2,
    )

    # verify ingestion success
    assert result["skip_reason"] is None
    assert result["file_size"] == len(test_file_content)
    assert result["lfn"].startswith(f"/{test_vo}/{test_scope}/")
    assert not trigger_file.exists()

    # Verify replica registration
    assert "Successfully registered the replica for lfn" in caplog.text
    assert "Created 2 offsite replication rule(s) for dataset" in caplog.text


@pytest.mark.usefixtures("_auth_proxy")
def test_process_acada_file_task_file_skipped(
    storage_mount_path, caplog, test_vo, test_scope, request
):
    """Test task skips ingestion when replica already exists."""
    test_file, _, test_file_content = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    # Task to process a file for the first time
    result = acada_ingestion.process_acada_file(
        file_path=str(test_file),
        data_path=str(storage_mount_path),
        rse=ONSITE_RSE,
        vo=test_vo,
        copies=2,
    )
    assert result["skip_reason"] is None
    assert result["file_size"] == len(test_file_content)

    caplog.clear()

    # Task to process a file for the second time to verify it should be skipped
    result = acada_ingestion.process_acada_file(
        file_path=str(test_file),
        data_path=str(storage_mount_path),
        rse=ONSITE_RSE,
        vo=test_vo,
        copies=2,
    )
    assert result["skip_reason"] == "REPLICA_EXISTS"
    assert result["file_size"] == 0
    assert "Replica already exists" in caplog.text


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "disable_ingestion_daemon"
)
def test_handle_task_cancelled(
    storage_mount_path, test_vo, test_scope, tmp_path, create_test_file_with_trigger
):
    """Test daemon handles cancelled tasks."""
    test_data_dir = create_unique_test_dir(storage_mount_path, test_vo, test_scope)
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path, test_vo, test_scope, test_data_dir, tmp_path
    )

    _, trigger_file = create_test_file_with_trigger(test_data_dir)

    mock = MockCeleryTask()
    original = acada_ingestion.process_acada_file
    acada_ingestion.process_acada_file = mock

    try:
        ingest.run(block=False)
        time.sleep(0.5)

        with ingest.task_lock:
            for task_info in ingest.submitted_tasks.values():
                task_info["async_result"].revoke(terminate=True)

        time.sleep(2.0)

        from bdms.acada_ingestion import N_TASKS_CANCELLED

        assert N_TASKS_CANCELLED._value._value > 0

        with ingest.task_lock:
            assert len(ingest.submitted_tasks) == 0

        assert trigger_file.exists()

    finally:
        acada_ingestion.process_acada_file = original
        ingest.shutdown()


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "disable_ingestion_daemon"
)
def test_handle_task_failed(
    storage_mount_path, test_vo, test_scope, tmp_path, create_test_file_with_trigger
):
    """Test daemon handles failed tasks by simulating worker raising exception."""
    test_data_dir = create_unique_test_dir(storage_mount_path, test_vo, test_scope)
    test_data_dir.mkdir(parents=True, exist_ok=True)

    ingest = setup_ingest(
        storage_mount_path, test_vo, test_scope, test_data_dir, tmp_path
    )

    _, trigger_file = create_test_file_with_trigger(test_data_dir)

    # Mock for task failure
    mock = MockCeleryTask(fail_with=RuntimeError("simulate worker crash"))
    original = acada_ingestion.process_acada_file
    acada_ingestion.process_acada_file = mock

    try:
        ingest.run(block=False)
        time.sleep(
            2.0
        )  # time for scan, submit, and result thread processing the failure

        from bdms.acada_ingestion import N_TASKS_FAILED

        assert N_TASKS_FAILED._value._value > 0

        with ingest.task_lock:
            assert len(ingest.submitted_tasks) == 0

        assert trigger_file.exists()

    finally:
        acada_ingestion.process_acada_file = original
        ingest.shutdown()


@pytest.mark.usefixtures("lock_for_ingestion_daemon", "disable_ingestion_daemon")
def test_celery_task_retries_invalid_to_valid_config_success(
    storage_mount_path,
    test_vo,
    test_scope,
    invalid_rucio_config,
    caplog,
    monkeypatch,
    request,
):
    """Test celery for tasks retry on failure (due to invalid rucio config) and success after config is fixed (tasks run synchronously in the same process)."""

    from rucio.common.config import get_config

    from bdms.ingest_tasks import AUTORETRY_EXCEPTIONS, app, process_acada_file

    data_file, trigger_file, _ = create_single_test_file(
        storage_mount_path, test_vo, test_scope, request
    )

    task_kwargs = {
        "file_path": str(data_file),
        "data_path": str(storage_mount_path),
        "rse": ONSITE_RSE,
        "vo": test_vo,
        "copies": 2,
    }

    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = False

    try:
        with pytest.raises(AUTORETRY_EXCEPTIONS):
            process_acada_file.apply_async(kwargs=task_kwargs).get(
                timeout=10, propagate=True
            )

        assert "retry" in caplog.text.lower()
        assert trigger_file.exists()

        caplog.clear()
        # Remove invalid rucio config restoring default
        monkeypatch.delenv("RUCIO_CONFIG", raising=False)

        # Make rucio reload the default config file
        get_config.cache_clear()

        result = process_acada_file.apply_async(kwargs=task_kwargs)
        result_data = result.get(timeout=30)

        assert result_data["skip_reason"] is None
        assert not trigger_file.exists()
        assert "Successfully registered the replica" in caplog.text

    finally:
        app.conf.task_always_eager = False
        app.conf.task_eager_propagates = True
