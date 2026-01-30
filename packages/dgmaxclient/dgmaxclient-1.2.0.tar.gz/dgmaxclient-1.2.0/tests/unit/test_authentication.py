"""Unit tests for DGMax authentication."""

from __future__ import annotations

import pytest

from dgmaxclient.authentication import ApiKeyAuthentication


class TestApiKeyAuthentication:
    """Tests for ApiKeyAuthentication class."""

    def test_get_headers(self) -> None:
        """Test that API key is added to headers."""
        auth = ApiKeyAuthentication(api_key="dgmax_test_key")

        headers = auth.get_headers()

        assert headers == {"X-API-Key": "dgmax_test_key"}

    def test_perform_initial_auth(self) -> None:
        """Test that initial auth does nothing (stateless)."""
        auth = ApiKeyAuthentication(api_key="dgmax_test_key")

        # Should not raise any exceptions
        auth.perform_initial_auth(None)

    def test_different_api_keys(self) -> None:
        """Test with different API keys."""
        auth1 = ApiKeyAuthentication(api_key="dgmax_key_one")
        auth2 = ApiKeyAuthentication(api_key="sk-dgmax-key_two")

        assert auth1.get_headers()["X-API-Key"] == "dgmax_key_one"
        assert auth2.get_headers()["X-API-Key"] == "sk-dgmax-key_two"

    def test_invalid_api_key_format(self) -> None:
        """Test that invalid API key format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid API key format"):
            ApiKeyAuthentication(api_key="invalid_key")

    def test_empty_api_key(self) -> None:
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            ApiKeyAuthentication(api_key="")

    def test_repr_masks_key(self) -> None:
        """Test that repr masks the API key."""
        auth = ApiKeyAuthentication(api_key="dgmax_secret_key_12345")

        repr_str = repr(auth)

        assert "dgmax_secr***" in repr_str
        assert "secret_key_12345" not in repr_str
