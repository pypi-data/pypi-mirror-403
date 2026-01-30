"""
Authentication methods for the DGMax client.

This module provides API key authentication for the DGMax API.
"""

from __future__ import annotations

from typing import Any

from apiclient.authentication_methods import BaseAuthenticationMethod


class ApiKeyAuthentication(BaseAuthenticationMethod):
    """API Key authentication method for DGMax API.

    This authentication method adds the API key to the X-API-Key header
    for every request made to the DGMax API.

    Examples:
        >>> auth = ApiKeyAuthentication(api_key="dgmax_xxx")
        >>> # Used internally by DGMaxClient
    """

    # Valid API key prefixes
    _VALID_PREFIXES = ("dgmax_", "sk-dgmax-")

    def __init__(self, api_key: str) -> None:
        """Initialize the API key authentication.

        Args:
            api_key: The DGMax API key for authentication

        Raises:
            ValueError: If the API key is empty or has invalid format
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        if not api_key.startswith(self._VALID_PREFIXES):
            raise ValueError(
                f"Invalid API key format. Key must start with one of: "
                f"{', '.join(self._VALID_PREFIXES)}"
            )

        self._api_key = api_key

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers.

        Returns:
            Dictionary containing the X-API-Key header
        """
        return {"X-API-Key": self._api_key}

    def __repr__(self) -> str:
        """Return a string representation with masked API key."""
        # Show first 10 chars and mask the rest
        masked = self._api_key[:10] + "***" if len(self._api_key) > 10 else "***"
        return f"ApiKeyAuthentication(api_key='{masked}')"

    def perform_initial_auth(self, client: Any) -> None:
        """Perform initial authentication.

        API key authentication is stateless, so no initial
        authentication is needed.

        Args:
            client: The API client instance (unused)
        """
        # API key auth is stateless - no initial auth needed
        pass
