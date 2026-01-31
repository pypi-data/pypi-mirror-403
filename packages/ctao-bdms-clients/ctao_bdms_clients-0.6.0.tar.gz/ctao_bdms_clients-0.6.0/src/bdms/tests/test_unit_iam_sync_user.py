import logging
import re
from textwrap import dedent
from uuid import uuid4

import pytest
import requests  # added for RequestException in retry tests
from rucio.common.exception import AccountNotFound

import bdms.sync_iam_rucio as sync_iam_rucio


@pytest.fixture
def fake_account_client():
    """Lightweight fake of Rucio AccountClient."""

    class FakeAccountClient:
        def __init__(self):
            self.accounts = {}
            self.identities = {}
            self.add_account_calls = []
            self.get_account_calls = []
            self.add_identity_calls = []
            self.list_id_calls = []

        def get_account(self, name):
            self.get_account_calls.append(name)
            if name not in self.accounts:
                raise AccountNotFound(f"{name} missing")
            return {"account": name}

        def add_account(self, name, atype, email):
            self.add_account_calls.append((name, atype, email))
            self.accounts[name] = {"type": atype, "email": email}

        def list_identities(self, account):
            self.list_id_calls.append(account)
            return self.identities.get(account, [])

        def add_identity(self, identity, authtype, account, email, default):
            self.add_identity_calls.append(
                dict(
                    identity=identity,
                    authtype=authtype,
                    account=account,
                    email=email,
                    default=default,
                )
            )
            self.identities.setdefault(account, []).append(
                {"identity": identity, "email": email, "type": authtype}
            )

    return FakeAccountClient()


@pytest.fixture
def syncer(fake_account_client):
    """Instantiate IAMRucioSync with a fake AccountClient."""
    iam_sync = sync_iam_rucio.IAMRucioSync(
        iam_server="https://iam.test",
        client_id="test-client",
        client_secret="s3cr3t",
        allowed_groups=["ctao.dpps.test", "alt_ctao.dpps.test"],
    )
    iam_sync.account_client = fake_account_client
    return iam_sync


def test_ensure_group_account(syncer, fake_account_client):
    """
    Test that ensure_group_account creates a group account if it does not exist,
    returns True on creation, and False if the account already exists or does not match allowed patterns.
    """
    createda = syncer.ensure_group_account("ctao_dpps_test")
    assert createda is True
    againa = syncer.ensure_group_account("ctao_dpps_test")
    assert againa is False
    createdb = syncer.ensure_group_account("grpB")
    assert createdb is False  # does not match allowed patterns


def test_existing_identities(syncer, fake_account_client):
    fake_account_client.identities["acc1"] = [{"identity": "I1"}, {"identity": "I2"}]
    ids = syncer.existing_identities("acc1")
    assert ids == {"I1", "I2"}


def test_sync_x509_adds_only_new(syncer, fake_account_client):
    syncer.allowed_groups = ["grpA"]
    syncer._allowed_patterns = [
        re.compile(re.escape(g), re.IGNORECASE) for g in syncer.allowed_groups
    ]

    fake_account_client.identities["grpA"] = [{"identity": "C=CH/O=Org/CN=User"}]
    users = [
        {
            "id": "00cdf93b-6a20-46e2-bea1-a330ac69e5f6",
            "userName": "u1",
            "emails": [{"value": "u1@e"}],
            "groups": [{"display": "grpA"}],
            "urn:indigo-dc:scim:schemas:IndigoUser": {
                "certificates": [
                    {"subjectDn": "CN=User,O=Org,C=CH"},
                    {"subjectDn": "CN=New,O=Org,C=CH"},
                ]
            },
        }
    ]
    syncer.sync_users(users)
    added_identities = [c["identity"] for c in fake_account_client.add_identity_calls]
    assert "C=CH/O=Org/CN=New" in added_identities
    assert "C=CH/O=Org/CN=User" not in added_identities
    assert (
        "SUB=00cdf93b-6a20-46e2-bea1-a330ac69e5f6, ISS=https://iam.test"
        in added_identities
    )


def test_error_during_sync(syncer, fake_account_client, caplog):
    fake_account_client.identities["grpA"] = [{"identity": "C=CH/O=Org/CN=User"}]
    users = [
        {
            "id": str(uuid4()),
            "userName": "u1",
            "emails": [{"value": "u1@e"}],
            "groups": [{}],
        }
    ]
    with caplog.at_level(logging.ERROR):
        syncer.sync_users(users)

    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith("Error syncing user")


def test_extract_dn_and_gridmap(syncer):
    dn = "CN=Alice,OU=Dept,O=Org,C=FR"
    grid = syncer.to_gridmap(dn)
    assert grid == "C=FR/O=Org/OU=Dept/CN=Alice"


def test_get_users_pagination(syncer, monkeypatch):
    pages = [
        {
            "Resources": [{"userName": "u1"}, {"userName": "u2"}],
            "itemsPerPage": 2,
            "totalResults": 5,
        },
        {
            "Resources": [{"userName": "u3"}, {"userName": "u4"}],
            "itemsPerPage": 2,
            "totalResults": 5,
        },
        {"Resources": [{"userName": "u5"}], "itemsPerPage": 1, "totalResults": 5},
    ]
    calls = {"i": 0}

    class R:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def fake_get(url, headers, params, timeout):
        i = calls["i"]
        calls["i"] += 1
        return R(pages[i])

    monkeypatch.setattr(sync_iam_rucio.requests, "get", fake_get)
    users = syncer.get_users("TOK")
    assert [u["userName"] for u in users] == ["u1", "u2", "u3", "u4", "u5"]
    assert calls["i"] == 3


def test_filter_ctao_users(syncer, fake_account_client):
    all_users = [
        {
            "id": "73a4ea45-d353-437c-b080-9a32792638a7",
            "userName": "u1",
            "groups": [{"display": "ctao.dpps.test"}],
        },
        {
            "id": "73a4ea45-d353-437c-b080-9a32792638a7",
            "userName": "u2",
            "groups": [{"display": "random.group"}, {"display": "ctao.dpps.test"}],
        },
        {
            "id": "2d8442ba-de67-47a7-bce4-140062e3ea16",
            "userName": "u3",
            "groups": [{"display": "alt_ctao.dpps.test"}],
        },
        {
            "id": "fbdb29ef-12aa-45bd-b96a-6e87ff9b5015",
            "userName": "u4",
            "groups": [{"display": "other.group"}],
        },
    ]
    filtered = syncer.filter_ctao_users(all_users)
    assert [u["userName"] for u in filtered] == ["u1", "u2", "u3"]

    syncer.sync_users(filtered)

    created_accounts = {call[0] for call in fake_account_client.add_account_calls}
    assert created_accounts == {"ctao_dpps_test", "alt_ctao_dpps_test"}
    assert len(fake_account_client.add_account_calls) == 2


# New fixture: real object (no AccountClient monkeypatch). Only reads config file.
@pytest.fixture
def real_syncer(tmp_path):
    return sync_iam_rucio.IAMRucioSync(
        iam_server="https://iam.test",
        client_id="real-client",
        client_secret="real-secret",
        retry_delay=1.0,
        max_retries=4,
        allowed_groups=["ctao.dpps.test", "alt_ctao.dpps.test"],
    )


def test_get_token_retries_all_fail(real_syncer, monkeypatch):
    """
    Retry logic using the real IAMRucioSync instance (no AccountClient mock).
    All attempts fail -> raises after max_retries.
    """
    attempts = {"n": 0}
    monkeypatch.setattr(sync_iam_rucio.time, "sleep", lambda *_: None)

    def failing_post(*_, **__):
        attempts["n"] += 1
        raise requests.RequestException("IAM down")

    monkeypatch.setattr(sync_iam_rucio.requests, "post", failing_post)
    with pytest.raises(requests.RequestException, match="IAM down"):
        real_syncer.get_token()
    assert attempts["n"] == real_syncer.max_retries  # uses config value (4)


def test_get_token_eventual_success(real_syncer, monkeypatch):
    """
    Real object: first failures then success before exhausting retries.
    """
    attempts = {"n": 0}
    monkeypatch.setattr(sync_iam_rucio.time, "sleep", lambda *_: None)
    sequence = [
        requests.RequestException("t1"),
        requests.RequestException("t2"),
        {"access_token": "TOKEN_OK"},
    ]

    def post(*_, **__):
        attempts["n"] += 1
        ev = sequence.pop(0)
        if isinstance(ev, Exception):
            raise ev

        class R:
            def raise_for_status(self):
                return None

            def json(self):
                return ev

        return R()

    monkeypatch.setattr(sync_iam_rucio.requests, "post", post)
    token = real_syncer.get_token()
    assert token == "TOKEN_OK"
    assert attempts["n"] == 3


def test_load_config(tmp_path):
    cfg = dedent("""\
       [IAM]
       iam-server = https://iam.test
       client-id = real-client
       client-secret = real-secret
       delay = 1
       max-retries = 4
       allowed-groups= alt_ctao.dpps.test , ctao.dpps.test
    """)
    cfg_path = tmp_path / "iam-sync.cfg"
    cfg_path.write_text(cfg)
    expected = dict(
        iam_server="https://iam.test",
        client_id="real-client",
        client_secret="real-secret",
        retry_delay=1.0,
        max_retries=4,
        allowed_groups=["alt_ctao.dpps.test", "ctao.dpps.test"],
    )
    assert sync_iam_rucio.load_config(cfg_path) == expected

    with pytest.raises(ValueError, match="Failed to read config file"):
        sync_iam_rucio.load_config(tmp_path / "does-not-exist.cfg")

    config_path = tmp_path / "invalid.cfg"
    config_path.write_text("")
    with pytest.raises(ValueError, match="Config is missing IAM section"):
        sync_iam_rucio.load_config(config_path)


def test_translate_group_name():
    assert (
        sync_iam_rucio.IAMRucioSync.iam_to_rucio_groupname("dpps.test.foo")
        == "dpps_test_foo"
    )


def test_sync_vo_group(syncer, fake_account_client):
    user = {
        "userName": "u1",
        "id": "00cdf93b-6a20-46e2-bea1-a330ac69e5f6",
        "emails": [{"value": "u1@e"}],
        "groups": [{"display": "ctao.dpps.test"}],
        "urn:indigo-dc:scim:schemas:IndigoUser": {
            "certificates": [
                {"subjectDn": "CN=User,O=Org,C=CH"},
                {"subjectDn": "CN=New,O=Org,C=CH"},
            ]
        },
    }
    syncer.sync_user(user)
    assert fake_account_client.add_account_calls == [("ctao_dpps_test", "GROUP", "")]
    added_identities = {c["identity"] for c in fake_account_client.add_identity_calls}
    assert added_identities == {
        "C=CH/O=Org/CN=New",
        "C=CH/O=Org/CN=User",
        "SUB=00cdf93b-6a20-46e2-bea1-a330ac69e5f6, ISS=https://iam.test",
    }
