"""Unit tests for DGMax endpoints."""

from __future__ import annotations

from dgmaxclient.endpoints import create_endpoints


class TestCreateEndpoints:
    """Tests for the create_endpoints factory function with @endpoint decorator."""

    def test_create_endpoints_returns_class(self) -> None:
        """Test that create_endpoints returns a class."""
        endpoints = create_endpoints("https://api.dgmax.do")
        assert isinstance(endpoints, type)

    def test_create_endpoints_full_urls(self) -> None:
        """Test full endpoint URLs using @endpoint decorator."""
        Endpoints = create_endpoints("https://api.dgmax.do")

        assert Endpoints.companies == "https://api.dgmax.do/api/v1/companies"
        assert (
            Endpoints.fiscal_invoices == "https://api.dgmax.do/api/v1/fiscal-invoices"
        )
        assert Endpoints.invoices == "https://api.dgmax.do/api/v1/invoices"
        assert Endpoints.debit_notes == "https://api.dgmax.do/api/v1/debit-notes"
        assert Endpoints.credit_notes == "https://api.dgmax.do/api/v1/credit-notes"
        assert Endpoints.purchases == "https://api.dgmax.do/api/v1/purchases"
        assert Endpoints.minor_expenses == "https://api.dgmax.do/api/v1/minor-expenses"
        assert (
            Endpoints.special_regimes == "https://api.dgmax.do/api/v1/special-regimes"
        )
        assert Endpoints.governmental == "https://api.dgmax.do/api/v1/governmental"
        assert Endpoints.exports == "https://api.dgmax.do/api/v1/exports"
        assert (
            Endpoints.payments_abroad == "https://api.dgmax.do/api/v1/payments-abroad"
        )
        assert (
            Endpoints.received_documents
            == "https://api.dgmax.do/api/v1/received-documents"
        )
        assert (
            Endpoints.commercial_approvals
            == "https://api.dgmax.do/api/v1/received-documents/commercial-approvals"
        )

    def test_create_endpoints_trailing_slash_removal(self) -> None:
        """Test that trailing slash is removed from base URL."""
        Endpoints = create_endpoints("https://api.dgmax.do/")
        assert Endpoints.companies == "https://api.dgmax.do/api/v1/companies"

    def test_create_endpoints_custom_base_url(self) -> None:
        """Test with custom base URL."""
        Endpoints = create_endpoints("https://staging.dgmax.do")
        assert Endpoints.companies == "https://staging.dgmax.do/api/v1/companies"
        assert Endpoints.invoices == "https://staging.dgmax.do/api/v1/invoices"

    def test_endpoints_can_be_used_for_specific_resource(self) -> None:
        """Test that endpoints can be used for specific resource URLs."""
        Endpoints = create_endpoints("https://api.dgmax.do")
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        # Build specific resource URL
        url = f"{Endpoints.companies}/{company_id}"
        assert url == f"https://api.dgmax.do/api/v1/companies/{company_id}"
