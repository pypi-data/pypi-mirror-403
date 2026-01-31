"""Sync IAM users and identities into Rucio accounts."""

import logging
import os
import re
import time
from configparser import ConfigParser
from typing import Optional

import requests
from rucio.client.accountclient import AccountClient
from rucio.common.exception import AccountNotFound, RucioException

CONFIG_ENV_VAR = "BDMS_SYNC_CONFIG"
LOG = logging.getLogger(__name__)


def load_config(config_path):
    """Load configuration from file and environment variables."""
    cfg = ConfigParser()
    read = cfg.read(config_path)

    if len(read) != 1:
        raise ValueError(f"Failed to read config file {config_path}")

    if not cfg.has_section("IAM"):
        raise ValueError("Config is missing IAM section")

    section = cfg["IAM"]
    return dict(
        iam_server=section["iam-server"],
        client_id=section["client-id"],
        client_secret=section["client-secret"],
        max_retries=section.getint("max-retries", fallback=5),
        retry_delay=section.getfloat("delay", fallback=10.0),
        allowed_groups=[
            g.strip() for g in section.get("allowed-groups", "").split(",") if g.strip()
        ],
    )


def with_retry(f, max_retries, retry_delay, exceptions=Exception, log=LOG):
    """Retry a function up to max_retries, sleep retry_delay before trying again."""
    attempt = 1
    while True:
        try:
            return f()
        except exceptions as e:
            msg = "Failed in attempt %d with error %s, waiting %f s"
            log.error(msg, attempt, e, retry_delay)
            if attempt >= max_retries:
                raise
            time.sleep(retry_delay)
            attempt += 1


class IAMRucioSync:
    """Synchronize IAM accounts, identities into Rucio."""

    TOKEN_URL = "/token"

    def __init__(
        self,
        *,
        iam_server: str,
        client_id: str,
        client_secret: str,
        max_retries: int = 5,
        retry_delay: float = 10.0,
        allowed_groups: list[str],
    ):
        """Initialize the syncer and load configuration."""
        self.iam_server = iam_server
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.allowed_groups = allowed_groups
        self._allowed_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.allowed_groups
        ]

        self.account_client = with_retry(
            AccountClient,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )

    def _get_token(self) -> str:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "scim:read",
        }
        r = requests.post(
            self.iam_server + self.TOKEN_URL,
            data=data,
            timeout=30,
        )
        r.raise_for_status()  # exception is status!=200
        js = r.json()
        if "access_token" not in js:
            raise RuntimeError(f"No access_token in response: {js}")
        return js["access_token"]

    def get_token(self) -> str:
        """Obtain an access token from the IAM server."""
        LOG.info(
            "Requesting IAM token from %s using the client_id %s",
            self.iam_server + self.TOKEN_URL,
            self.client_id,
        )
        return with_retry(
            self._get_token, max_retries=self.max_retries, retry_delay=self.retry_delay
        )

    def get_users(self, token: str) -> list[dict]:
        """Fetch users from IAM using SCIM API."""
        start = 1
        count = 100
        headers = {"Authorization": f"Bearer {token}"}
        all_users = []
        processed = 0
        while True:
            params = {"startIndex": start, "count": count}
            r = requests.get(
                f"{self.iam_server}/scim/Users",
                headers=headers,
                params=params,
                timeout=30,
            )
            data = r.json()
            all_users.extend(data.get("Resources", []))
            processed += data.get("itemsPerPage", 0)
            if processed < data.get("totalResults", 0):
                start += count
            else:
                break
        LOG.info("Fetched %d IAM users", len(all_users))
        return all_users

    def filter_ctao_users(self, all_users: list[dict]) -> list[dict]:
        """Filter users belonging to configured allowed-groups."""
        users = []
        for user in all_users:
            groups = [
                g.get("display") for g in user.get("groups", []) if g.get("display")
            ]
            if any(
                any(p.fullmatch(grp) for p in self._allowed_patterns) for grp in groups
            ):
                users.append(user)

        LOG.debug("Filtered users: %s", users)
        return users

    def ensure_group_account(self, account_name: str) -> bool:
        """Ensure a Rucio account exists for the given user and allowed groups."""
        try:
            self.account_client.get_account(account_name)
            return False
        except AccountNotFound:
            if not any(p.fullmatch(account_name) for p in self._allowed_patterns):
                LOG.debug(
                    "Group %s does not match allowed patterns; skipping account creation",
                    account_name,
                )
                return False
            LOG.info("Creating Rucio GROUP account: %s", account_name)
            self.account_client.add_account(account_name, "GROUP", email="")
            return True

    def existing_identities(self, account: str) -> set[str]:
        """Return the existing identities for a given account."""
        try:
            return {i["identity"] for i in self.account_client.list_identities(account)}
        except RucioException as e:
            LOG.error("List identities failed %s: %s", account, e)
            return set()

    def sync_users(self, users: list[dict]) -> None:
        """Create Rucio accounts and identities for given IAM users."""
        for user in users:
            try:
                self.sync_user(user)
            except Exception:
                LOG.exception("Error syncing user: %s", user)

    def sync_user(self, user: dict) -> None:
        """Create account and identities for a given IAM user."""
        email = self._get_user_email(user)

        LOG.info("Syncing groups for user %s", email)
        for group in user.get("groups", []):
            groupname = group["display"]
            # skip groups not matching configured allowed patterns
            if not any(p.fullmatch(groupname) for p in self._allowed_patterns):
                LOG.debug(
                    "Group %s does not match allowed patterns; skipping", groupname
                )
                continue
            account_name = self.iam_to_rucio_groupname(groupname)

            self.ensure_group_account(account_name)
            certificates = self._get_user_certificates(user)
            existing_identities = self.existing_identities(account_name)
            self._sync_group_certificates(
                account_name, email, certificates, existing_identities
            )
            self._sync_group_oidc_identities(
                account_name, user, email, existing_identities
            )

    def _get_user_email(self, user: dict) -> str:
        return user.get("emails", [{}])[0].get("value", "")

    def _get_user_certificates(self, user: dict) -> list[dict]:
        indigo = user.get("urn:indigo-dc:scim:schemas:IndigoUser", {})
        return indigo.get("certificates", [])

    def _sync_group_certificates(
        self,
        groupname: str,
        email: str,
        certificates: list[dict],
        existing_identities: set[str],
    ) -> None:
        for cert in certificates:
            dn = self._extract_dn(cert)
            if not dn:
                continue
            if dn in existing_identities:
                LOG.info("Identity %s already exists for group %s", dn, groupname)
                continue
            self._add_x509_identity(dn, groupname, email)

    def _sync_group_oidc_identities(
        self, groupname: str, user: dict, email: str, existing_identities: set[str]
    ):
        issuer = self.iam_server
        sub = user["id"]
        identity = f"SUB={sub}, ISS={issuer}"
        if identity in existing_identities:
            LOG.debug(
                "OIDC identity %s already exists for account %s", identity, groupname
            )
            return
        self._add_oidc_identity(identity, account=groupname, email=email)

    def _extract_dn(self, cert: dict) -> Optional[str]:
        dn = cert.get("subjectDn")
        if not dn:
            LOG.error("Missing subjectDn in %s", cert)
            return None
        return self.to_gridmap(dn)

    def _add_identity(
        self, authtype: str, identity: str, account: str, email: str
    ) -> None:
        try:
            self.account_client.add_identity(
                identity=identity,
                authtype=authtype,
                account=account,
                email=email,
                default=True,
            )
            LOG.info("Added %s identity %s to account %s", authtype, identity, account)
        except Exception as e:
            LOG.error(
                "Failed to add %s identity %s to account %s: %s",
                authtype,
                identity,
                account,
                e,
            )

    def _add_x509_identity(self, dn: str, account: str, email: str) -> None:
        self._add_identity("X509", dn, account, email)

    def _add_oidc_identity(self, identity: str, account: str, email: str) -> None:
        self._add_identity("OIDC", identity, account, email)

    @staticmethod
    def to_gridmap(dn: str) -> str:
        """Convert a DN string into gridmap format."""
        parts = dn.split(",")
        parts.reverse()
        return "/".join(parts)

    @staticmethod
    def iam_to_rucio_groupname(groupname: str):
        """Convert iam group name to rucio account name, replacing invalid chars."""
        return groupname.replace(".", "_")


def main():
    """Entry point: run the IAM → Rucio synchronization."""
    config_path = os.environ.get(CONFIG_ENV_VAR)
    logging.basicConfig(level=logging.INFO)

    if not config_path:
        raise SystemExit("Config path required. Set %s.", CONFIG_ENV_VAR)
    if not os.path.isfile(config_path):
        raise SystemExit(f"Config file not found: {config_path}")

    config = load_config(config_path)
    syncer = IAMRucioSync(**config)
    token = syncer.get_token()
    all_users = syncer.get_users(token)
    users = syncer.filter_ctao_users(all_users)
    syncer.sync_users(users)
    LOG.info("Sync done.")


if __name__ == "__main__":
    main()
