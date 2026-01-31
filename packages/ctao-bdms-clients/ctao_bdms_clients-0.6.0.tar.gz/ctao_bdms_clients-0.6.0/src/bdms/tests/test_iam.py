"""
Tests for the IAM service access from BDMS.
"""

import base64
import json
import logging

import requests


def get_session():
    """Get a requests session with retries."""

    session = requests.Session()
    session.verify = "/etc/grid-security/certificates"

    return session


# note that this code is also present in dpps-iam, it could be reused as a library
def get_token():
    """Get an access token from the IAM service."""

    r = get_session().post(
        "https://iam.test.example/token",
        auth=("dpps-test-client", "secret"),
        data={
            "username": "admin-user",
            "password": "test-password",
            "grant_type": "password",
            "scope": "scim:write openid profile iam:admin.read scim:read offline_access",
        },
    )

    r.raise_for_status()

    token = r.json().get("access_token")

    return token


def decoded_token(token):
    """Decode the JWT token."""
    try:
        _, payload, _ = token.split(".")
        decoded_payload = base64.b64decode(payload + "==").decode("utf-8")
        return json.loads(decoded_payload)
    except RuntimeError as e:
        logging.error("Failed to decode token: %s", e)
        return None


def test_list_accounts():
    """Test listing accounts in the IAM service."""

    token = get_token()

    logging.info("Using token: %s, %s", token, decoded_token(token))

    r = get_session().get(
        "https://iam.test.example/scim/Me",
        headers={"Authorization": f"Bearer {token}"},
    )

    logging.info("Response: %s", r.text)

    r = get_session().get(
        "https://iam.test.example/scim/Users",
        headers={"Authorization": f"Bearer {token}"},
    )

    r.raise_for_status()

    assert r.json().get("totalResults", 0) > 0, "No accounts found"

    expected_users = ["test-user", "admin-user"]

    certs = []
    for user in r.json().get("Resources", []):
        logging.info("User: %s %s", user["userName"], json.dumps(user, indent=2))
        assert "id" in user
        assert "userName" in user
        assert "name" in user
        assert "emails" in user
        assert len(user["emails"]) > 0
        assert "value" in user["emails"][0]

        if user["urn:indigo-dc:scim:schemas:IndigoUser"] != {}:
            certs.extend(
                user["urn:indigo-dc:scim:schemas:IndigoUser"].get("certificates", [])
            )

        if user["userName"] in expected_users:
            expected_users.remove(user["userName"])

    assert len(expected_users) == 0, f"Expected users not found: {expected_users}"

    logging.info("Certificates: %s", certs)

    assert len(certs) > 0, "No certificates found"
