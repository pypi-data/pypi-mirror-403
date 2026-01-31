import time
import requests

from azure.core.credentials import AccessToken
from ..logger import logger


__all__ = [
    "ResourceOwnerPasswordCredential"
]


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class ResourceOwnerPasswordCredential:
    """Handles token generation and refresh using Resource Owner Password Grant."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ) -> None:
        """
        Initialize TokenManager for ROPC flow.

        :param tenant_id: Directory (tenant) ID.
        :param client_id: Application (client) ID.
        :param client_secret: Application (client) secret.
        :param username: The username for ROPC flow.
        :param password: The password for ROPC flow.
        """
        self._access_token: str = ""
        self._expires_on: float = 0

        self._url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        # Payload for ROPC flow
        self._payload = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": None,
            "username": username,
            "password": password,
        }

    def get_token(self, *scopes: str) -> AccessToken:
        """
        Get the current access token. Refreshes it if expired.

        :param scopes: The scopes for the token request.
        :return: The access token.
        :raises AuthenticationError: If token refresh fails.
        """
        buffer_seconds = 300  # 5 minutes
        if time.time() >= (self._expires_on - buffer_seconds):
            logger.debug("Token expired or nearing expiry, refreshing...")
            self._refresh_token(*scopes)
        return AccessToken(self._access_token, self._expires_on)

    def _refresh_token(self, *scopes: str) -> None:
        """
        Refresh the access token using the ROPC flow and update expiry time.

        :param scopes: The scopes for the token request.
        :raises AuthenticationError: If the token request fails.
        """
        if len(scopes) == 0:
            raise ValueError("At least one scope is required.")
        logger.debug(f"Requesting token from: {self._url}")
        logger.debug(f"Using scope: {' '.join(scopes)}")
        self._payload["scope"] = " ".join(scopes)
        response = requests.post(self._url, data=self._payload)

        if response.ok:
            response_data = response.json()
            self._access_token = response_data["access_token"]
            self._expires_on = time.time() + int(response_data["expires_in"])
            logger.debug(
                f"Token refreshed successfully. Expires at: {time.ctime(self._expires_on)}"
            )
        else:
            error_details = response.text
            try:
                error_json = response.json()
                error_details = error_json
            except requests.exceptions.JSONDecodeError:
                pass
            logger.error(
                f"Authentication failed. Status: {response.status_code}, Details: {error_details}"
            )
            raise AuthenticationError(
                f"Authentication failed (status {response.status_code}).", error_details
            )

    def close(self) -> None:
        """Placeholder for TokenCredential protocol compliance."""
        logger.info("ResourceOwnerPasswordCredential: Close called (no-op).")

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Exit context manager."""
        self.close()
