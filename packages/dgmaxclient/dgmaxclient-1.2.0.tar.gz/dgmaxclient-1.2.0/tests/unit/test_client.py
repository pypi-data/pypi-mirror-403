"""Unit tests for the DGMaxClient class."""

from __future__ import annotations

from dgmaxclient import DGMaxClient


class TestDGMaxClientInit:
    """Tests for DGMaxClient initialization."""

    def test_client_initialization(self, api_key: str) -> None:
        """Test basic client initialization."""
        client = DGMaxClient(api_key=api_key)

        assert client is not None
        assert client.base_url == "https://api.dgmax.do"
        assert client.timeout == 30

    def test_client_custom_base_url(self, api_key: str) -> None:
        """Test client with custom base URL."""
        custom_url = "https://staging.dgmax.do"
        client = DGMaxClient(api_key=api_key, base_url=custom_url)

        assert client.base_url == custom_url

    def test_client_custom_timeout(self, api_key: str) -> None:
        """Test client with custom timeout."""
        client = DGMaxClient(api_key=api_key, timeout=60)

        assert client.timeout == 60

    def test_client_strips_trailing_slash(self, api_key: str) -> None:
        """Test that trailing slash is stripped from base URL."""
        client = DGMaxClient(
            api_key=api_key,
            base_url="https://api.dgmax.do/",
        )

        assert client.base_url == "https://api.dgmax.do"

    def test_client_repr(self, client: DGMaxClient) -> None:
        """Test client string representation (masked for security)."""
        assert repr(client) == "DGMaxClient()"


class TestDGMaxClientResources:
    """Tests for DGMaxClient resource initialization."""

    def test_companies_resource(self, client: DGMaxClient) -> None:
        """Test companies resource is initialized."""
        assert client.companies is not None
        assert hasattr(client.companies, "list")
        assert hasattr(client.companies, "get")
        assert hasattr(client.companies, "create")
        assert hasattr(client.companies, "update")

    def test_fiscal_invoices_resource(self, client: DGMaxClient) -> None:
        """Test fiscal invoices resource is initialized."""
        assert client.fiscal_invoices is not None
        assert hasattr(client.fiscal_invoices, "list")
        assert hasattr(client.fiscal_invoices, "get")
        assert hasattr(client.fiscal_invoices, "create")

    def test_invoices_resource(self, client: DGMaxClient) -> None:
        """Test invoices resource is initialized."""
        assert client.invoices is not None
        assert hasattr(client.invoices, "list")
        assert hasattr(client.invoices, "get")
        assert hasattr(client.invoices, "create")

    def test_debit_notes_resource(self, client: DGMaxClient) -> None:
        """Test debit notes resource is initialized."""
        assert client.debit_notes is not None

    def test_credit_notes_resource(self, client: DGMaxClient) -> None:
        """Test credit notes resource is initialized."""
        assert client.credit_notes is not None

    def test_purchases_resource(self, client: DGMaxClient) -> None:
        """Test purchases resource is initialized."""
        assert client.purchases is not None

    def test_minor_expenses_resource(self, client: DGMaxClient) -> None:
        """Test minor expenses resource is initialized."""
        assert client.minor_expenses is not None

    def test_special_regimes_resource(self, client: DGMaxClient) -> None:
        """Test special regimes resource is initialized."""
        assert client.special_regimes is not None

    def test_governmental_resource(self, client: DGMaxClient) -> None:
        """Test governmental resource is initialized."""
        assert client.governmental is not None

    def test_exports_resource(self, client: DGMaxClient) -> None:
        """Test exports resource is initialized."""
        assert client.exports is not None

    def test_payments_abroad_resource(self, client: DGMaxClient) -> None:
        """Test payments abroad resource is initialized."""
        assert client.payments_abroad is not None

    def test_received_documents_resource(self, client: DGMaxClient) -> None:
        """Test received documents resource is initialized."""
        assert client.received_documents is not None
        assert hasattr(client.received_documents, "approve")
        assert hasattr(client.received_documents, "reject")
        assert hasattr(client.received_documents, "list_commercial_approvals")


class TestDGMaxClientEndpoints:
    """Tests for DGMaxClient endpoint configuration."""

    def test_companies_endpoint(self, client: DGMaxClient) -> None:
        """Test companies endpoint URL."""
        assert client.endpoints.companies == "https://api.dgmax.do/api/v1/companies"

    def test_fiscal_invoices_endpoint(self, client: DGMaxClient) -> None:
        """Test fiscal invoices endpoint URL."""
        assert (
            client.endpoints.fiscal_invoices
            == "https://api.dgmax.do/api/v1/fiscal-invoices"
        )

    def test_invoices_endpoint(self, client: DGMaxClient) -> None:
        """Test invoices endpoint URL."""
        assert client.endpoints.invoices == "https://api.dgmax.do/api/v1/invoices"

    def test_received_documents_endpoint(self, client: DGMaxClient) -> None:
        """Test received documents endpoint URL."""
        assert (
            client.endpoints.received_documents
            == "https://api.dgmax.do/api/v1/received-documents"
        )

    def test_approve_document_endpoint(self, client: DGMaxClient) -> None:
        """Test approve document endpoint URL."""
        doc_id = "123e4567-e89b-12d3-a456-426614174000"
        expected = f"https://api.dgmax.do/api/v1/received-documents/{doc_id}/approve"
        assert client.endpoints.approve_document.format(id=doc_id) == expected

    def test_reject_document_endpoint(self, client: DGMaxClient) -> None:
        """Test reject document endpoint URL."""
        doc_id = "123e4567-e89b-12d3-a456-426614174000"
        expected = f"https://api.dgmax.do/api/v1/received-documents/{doc_id}/reject"
        assert client.endpoints.reject_document.format(id=doc_id) == expected
