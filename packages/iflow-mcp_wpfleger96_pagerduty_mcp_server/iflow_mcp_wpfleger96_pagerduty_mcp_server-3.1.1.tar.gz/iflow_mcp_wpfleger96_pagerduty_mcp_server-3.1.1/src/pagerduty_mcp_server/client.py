import logging
import os
from importlib.metadata import version
from typing import Optional
from unittest.mock import MagicMock

import pagerduty
from dotenv import load_dotenv
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class PagerDutyClient:
    _env_client: Optional[pagerduty.RestApiV2Client] = None
    _mock_client: Optional[MagicMock] = None

    @staticmethod
    def _is_test_mode() -> bool:
        """Check if running in test mode."""
        return os.environ.get("PAGERDUTY_TEST_MODE") == "true"

    @staticmethod
    def _get_header_token() -> Optional[str]:
        """Try to get auth token from HTTP headers.

        Returns:
            Optional[str]: The token if found in headers, None otherwise
        """
        try:
            request: Request = get_http_request()
            return request.headers.get("X-Goose-Token")
        except RuntimeError:
            return None

    @staticmethod
    def _get_env_token() -> Optional[str]:
        """Try to get auth token from environment variable.

        Returns:
            Optional[str]: The token if found in environment, None otherwise
        """
        return os.environ.get("PAGERDUTY_API_TOKEN")

    @staticmethod
    def _create_client_with_token(token: str) -> pagerduty.RestApiV2Client:
        """Create a new PagerDuty client with the given token.

        Args:
            token: The authentication token to use

        Returns:
            pagerduty.RestApiV2Client: A configured client
        """
        client = pagerduty.RestApiV2Client(token)
        client.headers["User-Agent"] = (
            f"pagerduty_mcp_server/{version('pagerduty_mcp_server')}"
        )
        return client

    @staticmethod
    def _create_mock_client() -> MagicMock:
        """Create a mock client for testing purposes.

        Returns:
            MagicMock: A mock client that returns empty results
        """
        mock_client = MagicMock()
        mock_client.list.return_value = []
        mock_client.get.return_value = {}
        mock_client.find.return_value = []
        return mock_client

    def get_client(self):
        """Get a PagerDuty API client.

        If a Goose token is present in the request headers, creates a new client.
        Otherwise, returns or creates a singleton client using the environment token.
        If in test mode, returns a mock client.

        Returns:
            pagerduty.RestApiV2Client or MagicMock: A configured client

        Raises:
            Exception: If no valid auth token is found and not in test mode
        """
        # Test mode - return mock client
        if self._is_test_mode():
            if self._mock_client is None:
                self._mock_client = self._create_mock_client()
            return self._mock_client

        # Try header token first - always create new client if present
        if token := self._get_header_token():
            return self._create_client_with_token(token)

        # Use existing env client if we have one
        if self._env_client is not None:
            return self._env_client

        # Try to create env client if we don't have one
        if token := self._get_env_token():
            self._env_client = self._create_client_with_token(token)
            return self._env_client

        # No valid token found
        logger.error("No auth token found in headers or environment variables")
        raise Exception("No auth token found in headers or environment variables")


# Singleton instance
client = PagerDutyClient()


def create_client():
    """Get a PagerDuty API client.

    Creates a new client for each request with a Goose token header,
    or reuses a singleton client when using environment variable token.
    Header tokens take precedence over environment variable.
    If in test mode, returns a mock client.

    Returns:
        pagerduty.RestApiV2Client or MagicMock: A configured client

    Raises:
        Exception: If no valid auth token is found and not in test mode
    """
    return client.get_client()