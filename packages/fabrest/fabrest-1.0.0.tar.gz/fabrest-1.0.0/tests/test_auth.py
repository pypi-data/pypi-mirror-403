import pytest
from unittest.mock import patch, MagicMock
import time

from fabrest.api.auth import ResourceOwnerPasswordCredential, AuthenticationError

class DummyResponse:
    def __init__(self, ok=True, json_data=None, status_code=200, text=""):
        self.ok = ok
        self._json = json_data or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json

@pytest.fixture
def credential():
    return ResourceOwnerPasswordCredential(
        tenant_id="tenant",
        client_id="client",
        client_secret="secret",
        username="user",
        password="pass"
    )

def test_get_token_refreshes_when_expired(credential):
    credential._access_token = "old_token"
    credential._expires_on = time.time() - 10  # expired

    with patch("requests.post") as mock_post:
        mock_post.return_value = DummyResponse(
            ok=True,
            json_data={"access_token": "new_token", "expires_in": 3600}
        )
        token = credential.get_token("scope1")
        assert token.token == "new_token"
        assert credential._access_token == "new_token"
        assert credential._expires_on > time.time()

def test_get_token_raises_on_failure(credential):
    credential._expires_on = time.time() - 10  # expired

    with patch("requests.post") as mock_post:
        mock_post.return_value = DummyResponse(
            ok=False,
            status_code=400,
            text="fail"
        )
        with pytest.raises(AuthenticationError):
            credential.get_token("scope1")

def test_get_token_requires_scope(credential):
    with pytest.raises(ValueError):
        credential.get_token()