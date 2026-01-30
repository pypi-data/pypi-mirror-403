from pathlib import Path

import pytest
from rucio.client import Client
from rucio.common.exception import CannotAuthenticate

from bdms.tests.conftest import USER_CERT, USER_KEY

# Certificate/key paths mounted in the test environment
NON_DPPS_CERT = "/opt/rucio/etc/nondppsusercert.pem"
NON_DPPS_KEY = "/opt/rucio/etc/nondppsuserkey.pem"
UNPRIV_CERT = "/opt/rucio/etc/unprivilegedusercert.pem"
UNPRIV_KEY = "/opt/rucio/etc/unprivilegeduserkey.pem"
NON_CTAO_CERT = "/opt/rucio/etc/nonctaousercert.pem"
NON_CTAO_KEY = "/opt/rucio/etc/nonctaouserkey.pem"
# DPPS user cert/key are the same as USER_CERT/USER_KEY defined in conftest
DPPS_CERT = USER_CERT
DPPS_KEY = USER_KEY
TOKEN_DIR = Path("/tmp/root/.rucio_root")


@pytest.fixture(autouse=True)
def purge_rucio_auth_tokens():
    """
    Remove any cached Rucio auth token before each test to force fresh authentication.
    """
    if not TOKEN_DIR.exists():
        return
    for token in TOKEN_DIR.glob("auth_token_for_account_*"):
        try:
            token.unlink()
        except FileNotFoundError:
            pass


def test_authentication_non_dpps():
    """Verify authentication fails with a user that does not belong to group ctao_dpps_test."""
    with pytest.raises(CannotAuthenticate, match=r"Cannot authenticate"):
        Client(
            account="ctao_dpps_test",
            auth_type="x509",
            creds={"client_cert": NON_DPPS_CERT, "client_key": NON_DPPS_KEY},
        ).whoami()


def test_authentication_dpps_user():
    """Verify authentication succeeds with DPPS group"""
    client = Client(
        account="ctao_dpps_test",
        auth_type="x509",
        creds={"client_cert": DPPS_CERT, "client_key": DPPS_KEY},
    )
    result = client.whoami()
    assert result["account"] == "ctao_dpps_test"


def test_authentication_unprivileged():
    """Verify authentication succeeds with another DPPS group"""
    client = Client(
        account="alt_ctao_dpps_test",
        auth_type="x509",
        creds={"client_cert": UNPRIV_CERT, "client_key": UNPRIV_KEY},
    )
    result = client.whoami()
    assert result["account"] == "alt_ctao_dpps_test"


def test_authentication_nonctao():
    """Verify authentication fails with a user that is not exported from IAM"""
    with pytest.raises(CannotAuthenticate, match=r"Cannot authenticate"):
        Client(
            account="non-ctao_test",
            auth_type="x509",
            creds={"client_cert": NON_CTAO_CERT, "client_key": NON_CTAO_KEY},
        ).whoami()
