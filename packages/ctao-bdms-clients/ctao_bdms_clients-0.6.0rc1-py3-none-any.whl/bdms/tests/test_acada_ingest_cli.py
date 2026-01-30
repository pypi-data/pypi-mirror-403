import logging
import os
import signal
import time
from datetime import datetime
from multiprocessing import Process
from pathlib import Path
from shutil import copy2

import pytest
import yaml
from astropy.tests.runner import shlex
from rucio.client.downloadclient import DownloadClient
from rucio.common.checksum import adler32

from bdms.acada_ingest_cli import main as ingest_cli
from bdms.acada_ingest_cli import parse_args_and_config
from bdms.tests.utils import (
    reset_xrootd_permissions,
    wait_for_replicas,
    wait_for_trigger_file_removal,
)

LOGGER = logging.getLogger(__name__)
ONSITE_RSE = "STORAGE-1"


def terminate_and_check(process: Process, timeout=30.0, how=signal.SIGTERM):
    LOGGER.info("Terminating process %s", process.pid)
    if how == signal.SIGTERM:
        process.terminate()
    else:
        os.kill(process.pid, how)

    process.join(timeout)
    if process.is_alive():
        process.kill()
        process.join(timeout)
        pytest.fail(f"Process did not terminate gracefully in {timeout} s")
    else:
        LOGGER.info("Process finished successfully.")


def parse_args_and_check_error(args, error_message):
    """
    Helper function to run the CLI and check for expected errors.
    """
    if error_message:
        with pytest.raises(SystemExit) as e:
            parse_args_and_config(args=args)
        assert error_message in e.value.__context__.message
    else:
        # Run without exceptions
        return parse_args_and_config(args=args)


@pytest.mark.parametrize(
    ("port", "error_message"),
    [
        (1234, None),
        (80, "Metrics port must be between 1024"),
        ("invalid_metrics", "Metrics port must be an integer"),
    ],
    ids=["valid_port", "low_port", "invalid_port"],
)
def test_cli_metrics_port_validation(port, error_message):
    """
    Test CLI ACADA ingestion exceptions.
    """

    parse_args_and_check_error(
        [
            f"--metrics-port={port}",
        ],
        error_message,
    )


@pytest.mark.parametrize(
    ("polling_interval", "error_message"),
    [
        (1, None),
        (0, "Polling interval must be positive"),
        ("invalid", "Polling interval must be a number, got"),
    ],
    ids=["valid_offsite", "negative_offsite", "invalid_offsite"],
)
def test_cli_polling_interval(polling_interval, error_message):
    """
    Test CLI ACADA ingestion with offsite copies.
    """
    parse_args_and_check_error(
        [
            f"--polling-interval={polling_interval}",
        ],
        error_message,
    )


def test_parse_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    with config_path.open("w") as f:
        yaml.dump({"polling_interval": 60.0}, f)

    args = parse_args_and_config([f"--config={config_path}", "--polling-interval=30.0"])
    # config is parsed
    # but cli args override config
    assert args.polling_interval == 30.0


def test_cli_dry_run(tmp_path, storage_mount_path, test_vo):
    """Test that cli runs successfully with --dry-run and terminates quickly."""
    lock_file = tmp_path / "cli_test.lock"
    args = [
        f"--data-path={storage_mount_path}",
        f"--rse={ONSITE_RSE}",
        f"--vo={test_vo}",
        f"--lock-file={lock_file}",
        "--polling-interval=0.5",
        "--disable-metrics",
        f"--log-file={tmp_path / 'daemon.log'}",
        "--dry-run",
    ]

    with pytest.raises(SystemExit) as e:
        ingest_cli(args)

    assert e.value.code == 0


@pytest.mark.usefixtures("_auth_proxy", "lock_for_ingestion_daemon")
def test_cli_ingestion(
    storage_mount_path, test_vo, test_scope, subarray_test_file, tmp_path
):
    """
    Test CLI ACADA ingestion.
    """
    filename = Path(subarray_test_file).name

    current_date = datetime.now()
    acada_path = (
        storage_mount_path
        / test_vo
        / test_scope
        / "DL0"
        / "ARRAY"
        / "ctao-north"
        / "event"
        / f"{current_date.year}"
        / f"{current_date.month:02d}"
        / f"{current_date.day:02d}"
        / filename
    )

    acada_path.parent.mkdir(parents=True, exist_ok=True)

    copy2(subarray_test_file, str(acada_path))
    reset_xrootd_permissions(storage_mount_path)

    expected_lfn = f"/{acada_path.relative_to(storage_mount_path)}"
    lock_file = tmp_path / "cli_test.lock"

    args = [
        f"--data-path={storage_mount_path}",
        f"--rse={ONSITE_RSE}",
        f"--vo={test_vo}",
        f"--lock-file={lock_file}",
        "--polling-interval=0.5",
        "--disable-metrics",
        f"--log-file={tmp_path / 'daemon.log'}",
    ]

    LOGGER.info("Starting %s", shlex.join(args))
    # Start daemon
    ingest_process = Process(target=ingest_cli, kwargs=dict(args=args))
    ingest_process.start()

    try:
        LOGGER.info("Creating trigger file")
        trigger_file = Path(str(acada_path) + ".trigger")
        trigger_file.symlink_to(acada_path.relative_to(acada_path.parent))

        LOGGER.info("Waiting for replica to appear")
        wait_for_replicas(lfns=[expected_lfn])
        LOGGER.info("Waiting for removal of trigger file")
        wait_for_trigger_file_removal([trigger_file])
    finally:
        terminate_and_check(ingest_process)

    assert (
        ingest_process.exitcode == 0
    )  # graceful shutdown should result in exit code 0
    assert not lock_file.exists(), "Shutdown should have cleaned up lock file."

    # verify download
    download_spec = {
        "did": f"{test_scope}:{expected_lfn}",
        "base_dir": str(tmp_path),
        "no_subdir": True,
    }

    download_client = DownloadClient()
    download_client.download_dids([download_spec])

    download_path = tmp_path / expected_lfn.lstrip("/")
    assert download_path.is_file(), f"Download failed at {download_path}"
    assert adler32(str(download_path)) == adler32(
        str(subarray_test_file)
    ), "Downloaded file content does not match the original."


@pytest.mark.usefixtures(
    "_auth_proxy", "lock_for_ingestion_daemon", "disable_ingestion_daemon"
)
def test_cli_ingestion_parallel(
    storage_mount_path, test_vo, test_scope, tmp_path, request
):
    """Test CLI with 7 files for parallel ingestion."""

    from bdms.tests.conftest import (
        acada_write_test_files,
        deployment_scale,
        get_unique_day_for_tests,
    )

    day = get_unique_day_for_tests(request)

    test_files, _ = acada_write_test_files(
        storage_mount_path, test_vo, test_scope, n_files=7, day=day
    )

    expected_lfns = [
        f"/{test_file.relative_to(storage_mount_path)}" for test_file in test_files
    ]

    reset_xrootd_permissions(storage_mount_path)

    lock_file = tmp_path / "ingestion_queue_test.lock"

    args = [
        f"--data-path={storage_mount_path}",
        f"--rse={ONSITE_RSE}",
        f"--vo={test_vo}",
        f"--lock-file={lock_file}",
        "--polling-interval=2",
        "--client-retry-interval=5",
        "--disable-metrics",
    ]

    LOGGER.info("Disabling Rucio server to simulate outage")
    deployment_scale("rucio-server", 0)

    # Start daemon
    ingest_process = Process(target=ingest_cli, kwargs=dict(args=args))
    ingest_process.start()

    try:
        # Create trigger files with tracking
        trigger_files = []
        for test_file in test_files:
            trigger_file = test_file.with_name(test_file.name + ".trigger")
            trigger_file.symlink_to(test_file.relative_to(test_file.parent))
            trigger_files.append(trigger_file)

        # Scale Rucio server back up
        LOGGER.info("Scaling Rucio server back up")
        deployment_scale("rucio-server", 1)
        time.sleep(10)

        # wait for daemon to start processing the file
        wait_for_replicas(expected_lfns)
        wait_for_trigger_file_removal(trigger_files)
    finally:
        terminate_and_check(ingest_process, how=signal.SIGINT)

    assert not lock_file.exists()
