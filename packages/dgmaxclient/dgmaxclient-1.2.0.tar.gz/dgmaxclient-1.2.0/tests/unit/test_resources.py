"""Unit tests for DGMax resources."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from dgmaxclient import DGMaxClient
from dgmaxclient.models import CompanyURLs
from dgmaxclient.resources.companies import CompaniesResource


class TestCompaniesResource:
    """Tests for CompaniesResource methods."""

    def test_get_urls(self, client: DGMaxClient) -> None:
        """Test get_urls method returns CompanyURLs."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_response = {
            "reception": "https://receptor.example.com/receive",
            "approval": "https://receptor.example.com/approve",
            "authentication": "https://auth.example.com/login",
        }

        with patch.object(client, "get", return_value=mock_response):
            urls = client.companies.get_urls(company_id)

        assert isinstance(urls, CompanyURLs)
        assert urls.reception == "https://receptor.example.com/receive"
        assert urls.approval == "https://receptor.example.com/approve"
        assert urls.authentication == "https://auth.example.com/login"

    def test_get_urls_invalid_company_id(self, client: DGMaxClient) -> None:
        """Test get_urls with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.get_urls("invalid-id")

    def test_get_urls_builds_correct_endpoint(self, client: DGMaxClient) -> None:
        """Test that get_urls calls the correct endpoint."""
        company_id = "abc12345-e89b-12d3-a456-426614174000"
        mock_response = {
            "reception": "https://example.com/r",
            "approval": "https://example.com/a",
            "authentication": "https://example.com/auth",
        }

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.companies.get_urls(company_id)

        expected_endpoint = f"https://api.dgmax.do/api/v1/companies/{company_id}/urls"
        mock_get.assert_called_once_with(expected_endpoint)

    def test_get_urls_has_retry_decorator(self, client: DGMaxClient) -> None:
        """Test that get_urls method has retry decorator applied."""
        # The retry decorator wraps the method with tenacity
        method = CompaniesResource.get_urls
        # Tenacity-wrapped functions have a 'retry' attribute
        assert hasattr(method, "retry")
