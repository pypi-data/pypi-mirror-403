import json
import logging
import os
import shutil
import subprocess as sp
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from secrets import token_hex

import numpy as np
import pytest
from astropy.time import Time
from filelock import FileLock
from protozfits import DL0v1_Subarray_pb2 as DL0_Subarray
from protozfits import DL0v1_Telescope_pb2 as DL0_Telescope
from protozfits import DL0v1_Trigger_pb2 as DL0_Trigger
from protozfits import ProtobufZOFits
from protozfits.anyarray import numpy_to_any_array
from rucio.client.scopeclient import ScopeClient
from rucio.common.utils import signal

from bdms.acada_ingestion import TRIGGER_SUFFIX
from bdms.extract_fits_metadata import METADATA_SCHEMAS
from bdms.tests.utils import download_test_file, reset_xrootd_permissions

USER_CERT = os.getenv("RUCIO_CFG_CLIENT_CERT", "/opt/rucio/etc/usercert.pem")
USER_KEY = os.getenv("RUCIO_CFG_CLIENT_KEY", "/opt/rucio/etc/userkey.pem")

# Define on-site storage related variables
STORAGE_MOUNT_PATH = Path(os.getenv("STORAGE_MOUNT_PATH", "/storage-1"))
STORAGE_PROTOCOL = "root"  # e.g., root, davs, gsiftp
STORAGE_HOSTNAME = "rucio-storage-1"  # on-site storage container hostname

DL0_TELESCOPE_SCHEMA = "DL0v1.Telescope.DataStream"
DL0_SUBARRAY_SCHEMA = "DL0v1.Subarray.DataStream"
DL0_TRIGGER_SCHEMA = "DL0v1.Trigger.DataStream"
DUMMY_REQ_HEAD_VALUE = "DataStream.DUMMY_REQ_HEAD"
DUMMY_REQ_PAY_VALUE = "DataStream.DUMMY_REQ_PAY"
DUMMY_OPT_HEAD_VALUE = "DataStream.DUMMY_OPT_HEAD"
DUMMY_OPT_PAY_VALUE = "DataStream.DUMMY_OPT_PAY"


def pytest_addoption(parser):
    parser.addoption(
        "--prod-config", default=None, help="json configuration to run prod tests"
    )


def pytest_configure():
    # gfal is overly verbose on info (global default), reduce a bit
    logging.getLogger("gfal2").setLevel(logging.WARNING)


def pytest_runtest_setup(item):
    """Customize test collection

    - Skip prod test unless --prod is given
    """
    markers = [mark.name for mark in item.iter_markers()]

    if "prod" in markers and item.config.getoption("--prod-config") is None:
        pytest.skip("skipping prod test, --prod-config not given")


@pytest.fixture
def storage_mount_path():
    """Provide the STORAGE_MOUNT_PATH as a fixture"""
    yield STORAGE_MOUNT_PATH
    reset_xrootd_permissions(STORAGE_MOUNT_PATH)


@pytest.fixture(scope="session")
def test_user():
    return "root"


@pytest.fixture(scope="session")
def _auth_proxy(tmp_path_factory):
    """Auth proxy needed for accessing RSEs"""
    # Key has to have 0o600 permissions, but due to the way we
    # we create and mount it, it does not. We copy to a tmp file
    # set correct permissions and then create the proxy

    try:
        sp.run(
            [
                "voms-proxy-init",
                "-valid",
                "9999:00",
                "-cert",
                USER_CERT,
                "-key",
                USER_KEY,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    except sp.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise pytest.fail(f"VOMS proxy failed: {error_msg}")


@pytest.fixture(scope="session")
def test_vo():
    return "ctao.dpps.test"


@pytest.fixture(scope="session")
def test_scope(test_user):
    """To avoid name conflicts and old state, use a unique scope for the tests"""
    # length of scope is limited to 25 characters
    random_hash = token_hex(2)
    date_str = f"{datetime.now():%Y%m%d_%H%M%S}"
    scope = f"t_{date_str}_{random_hash}"

    sc = ScopeClient()
    sc.add_scope(test_user, scope)
    return scope


@pytest.fixture(scope="session")
def persistent_test_scope():
    return "test_scope_persistent"


@pytest.fixture(scope="session")
def subarray_test_file():
    """Fixture to download a subarray test file"""
    path = "acada-small/DL0/ARRAY/ctao-n-acada/acada-adh/triggers/2025/02/04/SUB000_SWAT000_20250204T213405_SBID0000000002000000066_OBSID0000000002000000200_SUBARRAY_CHUNK000.fits.fz"
    return download_test_file(path)


@pytest.fixture(scope="session")
def tel_trigger_test_file():
    """Fixture to download a telescope trigger test file"""
    path = "acada-small/DL0/ARRAY/ctao-n-acada/acada-adh/triggers/2025/02/04/SUB000_SWAT000_20250204T213405_SBID0000000002000000066_OBSID0000000002000000200_TEL_CHUNK000.fits.fz"
    return download_test_file(path)


@pytest.fixture(scope="session")
def tel_events_test_file():
    """Fixture to download a telescope events test file"""
    path = "acada-small/DL0/LSTN-01/ctao-n-acada/acada-adh/events/2025/02/04/TEL001_SDH0000_20250204T213354_SBID0000000002000000066_OBSID0000000002000000200_CHUNK001.fits.fz"
    return download_test_file(path)


def acada_write_test_files(
    storage_mount_path,
    test_vo,
    test_scope,
    n_files=7,
    day=None,
) -> tuple[list[Path], str]:
    """Represents ACADA writing test files to the storage mount path."""

    current_date = datetime.now(timezone.utc)
    year = str(current_date.year)
    month = f"{current_date.month:02d}"
    timestamp = current_date.strftime("%Y%m%dT%H%M%S")
    unique_id = token_hex(8)
    actual_day = day if day is not None else current_date.day
    day_str = f"{actual_day:02d}"

    # create hierarchical dir structure
    test_dir = (
        storage_mount_path
        / test_vo
        / test_scope
        / "DL0"
        / "LSTN-01"
        / "ctao-north"
        / "event"
        / year
        / month
        / day_str
    )
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file_content = f"Test file with random content: {unique_id}"
    # Create n_files dummy FITS files
    data_files = []
    for i in range(n_files):
        filename = f"TEL001_SDH{i:04d}_{timestamp}_SBID{i:019d}_OBSID{i:019d}_CHUNK{i:03d}.fits"
        data_file = test_dir / filename
        data_file.write_text(test_file_content)
        data_files.append(data_file)

    # Move permission reset before daemon start to avoid timing issues
    reset_xrootd_permissions(storage_mount_path)
    return data_files, test_file_content


def get_unique_day_for_tests(request) -> int:
    """Get unique day derived from the test name using the request fixture from pytest."""
    import hashlib

    test_hash = int(hashlib.sha512(request.node.name.encode()).hexdigest()[:8], 16)
    return (
        (test_hash % 28) + 1
    )  # we want unique dataset names for replication rules tests so this fixture accommodates different days


@pytest.fixture
def dl0_dir_base(storage_mount_path, test_vo, test_scope):
    """DL0 base dir fixture, used to store dummy DL0 files."""
    yield storage_mount_path / test_vo / test_scope
    # recursively delete its directory tree
    shutil.rmtree(str(storage_mount_path), ignore_errors=True)


@pytest.fixture
def dl0_files_base(dl0_dir_base):
    """DL0 Directory structure for dummy dl0 files."""
    dl0 = dl0_dir_base / "DL0"
    date_pattern = "2025/02/04"
    # define a directory for the array files as well as one for an array element (ie LSTN-01),
    # for simplicity, the ctao-north is used as a location
    # it follows the newer directory structure
    subarray_dir = dl0 / "ARRAY" / "ctao-north" / "event" / date_pattern
    tel_event_dir = dl0 / "LSTN-01" / "ctao-north" / "event" / date_pattern
    for directory in (subarray_dir, tel_event_dir):
        directory.mkdir(exist_ok=True, parents=True)

    dl0_dir_paths = {"subarray_dir": subarray_dir, "tel_event_dir": tel_event_dir}

    return dl0_dir_paths


@pytest.fixture
def invalid_dl0_files_base(dl0_dir_base):
    """INVALID_DL0 Directory Structure."""
    invalid_dl0 = dl0_dir_base / "INVALID_DL0"

    date_pattern = "2025/02/04"
    # define a directory for the array files as well as one for an array element (ie LSTN-01),
    # for simplicity, the ctao-north is used as a location
    # it follows the newer directory structure
    subarray_dir = invalid_dl0 / "ARRAY" / "ctao-north" / "event" / date_pattern
    tel_event_dir = invalid_dl0 / "LSTN-01" / "ctao-north" / "event" / date_pattern
    for directory in (subarray_dir, tel_event_dir):
        directory.mkdir(exist_ok=True, parents=True)

    invalid_dl0_dir_paths = {
        "subarray_dir": subarray_dir,
        "tel_event_dir": tel_event_dir,
    }

    return invalid_dl0_dir_paths


@pytest.fixture
def dummy_dl0_files(dl0_files_base, invalid_dl0_files_base):
    """Generate three dummy DL0 files, using a number of classes
    from the protozfits library."""
    obs_start = Time("2023-08-02T02:15:31")
    sb_id = 123
    obs_id = 456
    proto_kwargs = dict()
    event_id = 1
    trigger_id = 1
    tel_id = 1
    tel_ids = np.arange(1, 19).astype(np.uint16)
    subarray_dir = dl0_files_base["subarray_dir"]
    tel_event_dir = dl0_files_base["tel_event_dir"]

    obs_start_path_string = f"{obs_start.to_datetime(timezone.utc):%Y%m%dT%H%M%S}"

    # dummy sub-array event fits file
    subarray_file_pattern = f"SUB001_SWAT001_{obs_start_path_string}_SBID{sb_id:019d}_OBSID{obs_id:019d}_SUBARRAY_CHUNK000.fits.fz"
    subarray_file_path = subarray_dir / subarray_file_pattern

    # dummy sub-array trigger event fits file
    trigger_event_pattern = f"SUB001_SDH000_{obs_start_path_string}_SBID{sb_id:019d}_OBSID{obs_id:019d}_TEL_CHUNK000.fits.fz"
    trigger_event_path = subarray_dir / trigger_event_pattern

    # dummy telescope event fits file
    tel_event_pattern = f"TEL001_SDH000_{obs_start_path_string}_SBID{sb_id:019d}_OBSID{obs_id:019d}_CHUNK001.fits.fz"
    tel_event_path = tel_event_dir / tel_event_pattern

    ctx = ExitStack()
    with ctx:
        # writing dummy subarray fits file
        subarray_file = ctx.enter_context(ProtobufZOFits(**proto_kwargs))
        subarray_file.open(str(subarray_file_path))
        subarray_file.move_to_new_table("DataStream")
        subarray_file.write_message(
            DL0_Subarray.DataStream(
                subarray_id=1,
                sb_id=sb_id,
                obs_id=obs_id,
            )
        )
        subarray_file.move_to_new_table("SubarrayEvents")
        subarray_file.write_message(
            DL0_Subarray.Event(
                sb_id=sb_id,
                obs_id=obs_id,
                event_id=event_id,
            )
        )
        # define relative trigger file
        subarray_file_trigger = Path(str(subarray_file_path) + TRIGGER_SUFFIX)
        subarray_file_trigger.symlink_to(subarray_file_path)

        # writing dummy telescope event fits file
        tel_event_file = ctx.enter_context(ProtobufZOFits(**proto_kwargs))
        tel_event_file.open(str(tel_event_path))
        tel_event_file.move_to_new_table("DataStream")
        tel_event_file.write_message(
            DL0_Telescope.DataStream(
                sb_id=sb_id,
                obs_id=obs_id,
            )
        )
        tel_event_file.move_to_new_table("Events")
        tel_event_file.write_message(
            DL0_Telescope.Event(event_id=event_id, tel_id=tel_id)
        )
        # define relative trigger file
        tel_event_file_trigger = Path(str(tel_event_path) + TRIGGER_SUFFIX)
        tel_event_file_trigger.symlink_to(tel_event_path)

        # writing dummy trigger event fits file
        trigger_event_file = ctx.enter_context(ProtobufZOFits(**proto_kwargs))
        trigger_event_file.open(str(trigger_event_path))
        trigger_event_file.move_to_new_table("DataStream")
        trigger_event_file.write_message(
            DL0_Trigger.DataStream(
                sb_id=sb_id, obs_id=obs_id, tel_ids=numpy_to_any_array(tel_ids)
            )
        )
        trigger_event_file.move_to_new_table("Triggers")
        trigger_event_file.write_message(
            DL0_Trigger.Trigger(trigger_id=trigger_id, tel_id=tel_id)
        )
        # define relative trigger file
        trigger_event_file_trigger = Path(str(trigger_event_path) + TRIGGER_SUFFIX)
        trigger_event_file_trigger.symlink_to(trigger_event_path)

    files_dict = {
        "subarray_file_path": subarray_file_path,
        "tel_event_path": tel_event_path,
        "trigger_event_path": trigger_event_path,
    }
    return files_dict


@pytest.fixture(scope="session")
def altered_metadata_schemas():
    """Alter the default metadata schema, inserting a required and an optional metadata for the payload as
    well as one required and one optional for the header. This new metadata is added to each group of metadata."""
    metadata_schemas = METADATA_SCHEMAS
    # insert dummy required metadata
    metadata_schemas[DL0_TELESCOPE_SCHEMA]["HEADER"]["required"]["dummy_req_head"] = (
        DUMMY_REQ_HEAD_VALUE
    )
    metadata_schemas[DL0_TELESCOPE_SCHEMA]["PAYLOAD"]["required"]["dummy_req_pay"] = (
        DUMMY_REQ_PAY_VALUE
    )
    metadata_schemas[DL0_SUBARRAY_SCHEMA]["HEADER"]["required"]["dummy_req_head"] = (
        DUMMY_REQ_HEAD_VALUE
    )
    metadata_schemas[DL0_SUBARRAY_SCHEMA]["PAYLOAD"]["required"]["dummy_req_pay"] = (
        DUMMY_REQ_PAY_VALUE
    )
    metadata_schemas[DL0_TRIGGER_SCHEMA]["HEADER"]["required"]["dummy_req_head"] = (
        DUMMY_REQ_HEAD_VALUE
    )
    metadata_schemas[DL0_TRIGGER_SCHEMA]["PAYLOAD"]["required"]["dummy_req_pay"] = (
        DUMMY_REQ_PAY_VALUE
    )
    # insert dummy optional metadata
    metadata_schemas[DL0_TELESCOPE_SCHEMA]["HEADER"]["optional"]["dummy_opt_head"] = (
        DUMMY_OPT_HEAD_VALUE
    )
    metadata_schemas[DL0_TELESCOPE_SCHEMA]["PAYLOAD"]["optional"]["dummy_opt_pay"] = (
        DUMMY_OPT_PAY_VALUE
    )
    metadata_schemas[DL0_SUBARRAY_SCHEMA]["HEADER"]["optional"]["dummy_opt_head"] = (
        DUMMY_OPT_HEAD_VALUE
    )
    metadata_schemas[DL0_SUBARRAY_SCHEMA]["PAYLOAD"]["optional"]["dummy_opt_pay"] = (
        DUMMY_OPT_PAY_VALUE
    )
    metadata_schemas[DL0_TRIGGER_SCHEMA]["HEADER"]["optional"]["dummy_opt_head"] = (
        DUMMY_OPT_HEAD_VALUE
    )
    metadata_schemas[DL0_TRIGGER_SCHEMA]["PAYLOAD"]["optional"]["dummy_opt_pay"] = (
        DUMMY_OPT_PAY_VALUE
    )

    return metadata_schemas


def run_kubectl(args: list[str]) -> str:
    """Run a kubectl command with the given arguments and return the output."""
    result = sp.run(
        [".toolkit/bin/kubectl"] + args,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl command failed: {result.stderr}")

    return result.stdout.strip()


def wait_for_deployment_ready(deployment_name, replicas):
    """Wait for a deployment to be ready with the specified number of replicas."""

    timeout_stop_at = time.time() + 300
    while True:
        result = run_kubectl(["get", deployment_name, "-o", "json"])
        ready_replicas = json.loads(result)["status"].get("readyReplicas", 0)

        if ready_replicas >= replicas:
            logging.info(
                "%s deployment is ready with %s replicas.",
                deployment_name,
                ready_replicas,
            )
            break

        if time.time() > timeout_stop_at:
            raise TimeoutError(
                f"Timeout while waiting for {deployment_name} deployment to be ready."
            )

        logging.info(
            "Waiting for %s deployment to be ready. Current ready replicas: %s, expected: %s till timeout in %s s",
            deployment_name,
            ready_replicas,
            replicas,
            int(timeout_stop_at - time.time()),
        )

        time.sleep(1)


def deployment_scale(daemon_name: str, replicas: int = 1) -> None:
    """Scale a deployment to a specific number of replicas."""

    deployment_name = "deployment/bdms-" + daemon_name

    run_kubectl(
        [
            "scale",
            deployment_name,
            f"--replicas={replicas}",
        ]
    )

    if replicas > 0:
        wait_for_deployment_ready(deployment_name, replicas)

    # there is a delay between demon writing lock file and the daemon starting to process trigger files
    time.sleep(3)

    # wait for any terminating pods to finish.
    # they tend to linger around and while they do not count as replicas, they may still interfere with tests by modifying the trigger files.
    while True:
        result = run_kubectl(["get", "pods"])

        if "Terminating" not in result:
            break

        logging.info("Waiting for any Terminating pods to disappear...")
        time.sleep(5)


@pytest.fixture
def enable_ingestion_daemon():
    """Fixture to enable the ingestion daemon during tests."""

    deployment_scale("ingestion-daemon", 1)
    yield
    deployment_scale("ingestion-daemon", 0)


@pytest.fixture
def disable_ingestion_daemon():
    """Fixture to suspend the ingestion daemon during tests."""
    deployment_scale("ingestion-daemon", 0)


@pytest.fixture
def lock_for_ingestion_daemon():
    """Fixture to prevent daemon tests from running simultaneously."""

    with FileLock(STORAGE_MOUNT_PATH / "ingestion_daemon.lock"):
        yield


@pytest.fixture(autouse=True)
def unblock_signals():
    """GFAL seems to blocks most POSIX signals, undo.

    See https://github.com/rucio/rucio/issues/8012 for details.
    """
    signal.pthread_sigmask(signal.SIG_UNBLOCK, signal.valid_signals())
    yield
    signal.pthread_sigmask(signal.SIG_UNBLOCK, signal.valid_signals())


invalid_rucio_cfg = """
[client]
rucio_host = https://invalid-rucio-server:443
auth_host = https://invalid-rucio-server:443
ca_cert = /etc/grid-security/ca.pem
auth_type = userpass
username = dpps
password = secret
account = root
"""


@pytest.fixture
def invalid_rucio_config(tmp_path, monkeypatch):
    """Create an invalid Rucio config that will cause connection failures."""
    from rucio.common.config import get_config

    get_config.cache_clear()
    rucio_cfg = tmp_path / "rucio.cfg"
    rucio_cfg.write_text(invalid_rucio_cfg)
    monkeypatch.setenv("RUCIO_CONFIG", str(rucio_cfg))

    return "invalid_host"
