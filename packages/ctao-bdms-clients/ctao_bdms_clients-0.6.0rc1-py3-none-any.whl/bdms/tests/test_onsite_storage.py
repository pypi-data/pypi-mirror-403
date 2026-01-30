import subprocess as sp
from pathlib import Path

import pytest
from rucio.client.rseclient import RSEClient

from .conftest import STORAGE_HOSTNAME, STORAGE_PROTOCOL, acada_write_test_files

# Constants for RSEs and expected attributes
RSE_CONFIG = {
    "STORAGE-1": {"ONSITE": True, "OFFSITE": None},
    "STORAGE-2": {"ONSITE": None, "OFFSITE": True},
    "STORAGE-3": {"ONSITE": None, "OFFSITE": True},
}


def test_shared_storage(storage_mount_path: Path) -> Path:
    """Ensure shared storage directory exists before any test runs"""
    assert (
        storage_mount_path.exists()
    ), f"Shared storage {storage_mount_path} is not available on the client"


def test_file_access_from_onsite_storage_using_gfal(
    storage_mount_path: Path,
    test_vo: str,
    test_scope: str,
):
    """Verify that the file is accessible from the onsite storage pod using gfal-ls"""

    test_files, _ = acada_write_test_files(
        storage_mount_path, test_vo, test_scope, n_files=1
    )

    test_file_path = test_files[0]

    test_file_lfn = f"/{test_file_path.relative_to(storage_mount_path)}"
    test_file_name = test_file_path.name

    gfal_url = f"{STORAGE_PROTOCOL}://{STORAGE_HOSTNAME}/rucio/{test_file_lfn}"
    cmd = ["gfal-ls", gfal_url]

    ret = sp.run(cmd, capture_output=True, text=True)
    stdout = ret.stdout.strip()
    stderr = ret.stderr.strip()
    msg = f"gfal-ls failed for {gfal_url}:\nSTDERR: {stderr}\nSTDOUT: {stderr}"
    assert ret.returncode == 0, msg

    msg = f"File {test_file_name} not accessible; gfal-ls output: {stdout!r}"
    assert any(test_file_name in line for line in stdout.splitlines()), msg


@pytest.mark.usefixtures("_auth_proxy")
def test_rse_attributes():
    """Verify onsite and offsite RSE attributes set by setup_rucio.sh during the bootstrap job deployment

    Ensures:
    - STORAGE-1 has onsite=True and no offsite=True
    - STORAGE-2 and STORAGE-3 have offsite=True and no onsite=True

    Raises:
        pytest.fail: If RSE details cannot be retrieved (in case of RSEs not found or Rucio server connectivity issues)
        AssertionError: If attribute values don't match the expected ones
    """

    rse_client = RSEClient()

    for rse_name, expected_attrs in RSE_CONFIG.items():
        try:
            # Verify RSE exists
            rse_details = rse_client.get_rse(rse_name)
            print(f"{rse_name} metadata: {rse_details}")

            # Fetch attributes
            attrs = rse_client.list_rse_attributes(rse_name)
            print(f"{rse_name} attributes: {attrs}")

            # Verify RSE onsite attribute
            onsite_value = attrs.get("ONSITE")
            expected_onsite = expected_attrs["ONSITE"]
            assert onsite_value == expected_onsite, (
                f"{rse_name} onsite attribute mismatch: "
                f"expected {expected_onsite!r}, got {onsite_value!r}. "
                f"Full attributes: {attrs}"
            )

            # Verify RSE offsite attribute
            offsite_value = attrs.get("OFFSITE")
            expected_offsite = expected_attrs["OFFSITE"]
            if expected_offsite is None:
                assert offsite_value is not True, (
                    f"{rse_name} should not have offsite=True, "
                    f"got {offsite_value!r}. Full attributes: {attrs}"
                )
            else:
                assert offsite_value == expected_offsite, (
                    f"{rse_name} offsite attribute mismatch: "
                    f"expected {expected_offsite!r}, got {offsite_value!r}. "
                    f"Full attributes: {attrs}"
                )

            print(f"{rse_name} passed attribute tests")

        except Exception as e:
            pytest.fail(
                f"Failed to retrieve RSE details for {rse_name}: {str(e)}. "
                "Check Rucio server connectivity or RSE existence"
            )
