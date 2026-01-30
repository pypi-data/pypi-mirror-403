"""Unit tests for DGMax models."""

from __future__ import annotations

import pytest

from dgmaxclient.models import (
    CompanyCreate,
    CompanyPublic,
    CompanyType,
    CompanyURLs,
    DocumentFilters,
    DocumentStatus,
    DocumentType,
    ElectronicDocument,
    PaginatedResponse,
    PaginationParams,
)


class TestPaginationParams:
    """Tests for PaginationParams model."""

    def test_default_values(self) -> None:
        """Test default pagination values."""
        params = PaginationParams()

        assert params.limit == 100
        assert params.offset == 0

    def test_custom_values(self) -> None:
        """Test custom pagination values."""
        params = PaginationParams(limit=50, offset=100)

        assert params.limit == 50
        assert params.offset == 100

    def test_to_query_params(self) -> None:
        """Test conversion to query parameters."""
        params = PaginationParams(limit=25, offset=50)

        query = params.to_query_params()

        assert query == {"limit": 25, "offset": 50}

    def test_limit_validation(self) -> None:
        """Test limit validation (1-1000)."""
        with pytest.raises(ValueError):
            PaginationParams(limit=0)

        with pytest.raises(ValueError):
            PaginationParams(limit=1001)

    def test_offset_validation(self) -> None:
        """Test offset validation (>= 0)."""
        with pytest.raises(ValueError):
            PaginationParams(offset=-1)


class TestPaginatedResponse:
    """Tests for PaginatedResponse model."""

    def test_basic_response(self) -> None:
        """Test basic paginated response."""
        response = PaginatedResponse[str](count=10, results=["a", "b", "c"])

        assert response.count == 10
        assert len(response.results) == 3

    def test_iteration(self) -> None:
        """Test iteration over results."""
        response = PaginatedResponse[str](count=3, results=["a", "b", "c"])

        items = list(response)

        assert items == ["a", "b", "c"]

    def test_len(self) -> None:
        """Test len() on response."""
        response = PaginatedResponse[str](count=100, results=["a", "b", "c"])

        assert len(response) == 3

    def test_getitem(self) -> None:
        """Test indexing results."""
        response = PaginatedResponse[str](count=3, results=["a", "b", "c"])

        assert response[0] == "a"
        assert response[2] == "c"

    def test_is_empty(self) -> None:
        """Test is_empty property."""
        empty = PaginatedResponse[str](count=0, results=[])
        not_empty = PaginatedResponse[str](count=1, results=["a"])

        assert empty.is_empty is True
        assert not_empty.is_empty is False

    def test_has_more(self) -> None:
        """Test has_more property."""
        has_more = PaginatedResponse[str](count=100, results=["a"])
        no_more = PaginatedResponse[str](count=0, results=[])

        assert has_more.has_more is True
        assert no_more.has_more is False


class TestDocumentStatus:
    """Tests for DocumentStatus enum."""

    def test_all_statuses(self) -> None:
        """Test all document status values."""
        assert DocumentStatus.REGISTERED == "REGISTERED"
        assert DocumentStatus.PROCESSING == "PROCESSING"
        assert DocumentStatus.COMPLETED == "COMPLETED"
        assert DocumentStatus.FAILED == "FAILED"
        assert DocumentStatus.QUEUED == "QUEUED"


class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_all_document_types(self) -> None:
        """Test all document type values."""
        assert DocumentType.E31 == "E31"
        assert DocumentType.E32 == "E32"
        assert DocumentType.E33 == "E33"
        assert DocumentType.E34 == "E34"
        assert DocumentType.E41 == "E41"
        assert DocumentType.E43 == "E43"
        assert DocumentType.E44 == "E44"
        assert DocumentType.E45 == "E45"
        assert DocumentType.E46 == "E46"
        assert DocumentType.E47 == "E47"


class TestDocumentFilters:
    """Tests for DocumentFilters model."""

    def test_empty_filters(self) -> None:
        """Test empty filters."""
        filters = DocumentFilters()

        params = filters.to_query_params()

        assert params == {}

    def test_status_filter(self) -> None:
        """Test status filter."""
        filters = DocumentFilters(status=DocumentStatus.COMPLETED)

        params = filters.to_query_params()

        assert params == {"document_status": "COMPLETED"}

    def test_search_filter(self) -> None:
        """Test search filter."""
        filters = DocumentFilters(search="E31000")

        params = filters.to_query_params()

        assert params == {"search": "E31000"}

    def test_date_filters(self) -> None:
        """Test date filters."""
        filters = DocumentFilters(
            date_from="2024-01-01",
            date_to="2024-12-31",
        )

        params = filters.to_query_params()

        assert params == {
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
        }

    def test_all_filters(self) -> None:
        """Test all filters combined."""
        filters = DocumentFilters(
            status=DocumentStatus.COMPLETED,
            search="123456789",
            date_from="2024-01-01",
            date_to="2024-12-31",
        )

        params = filters.to_query_params()

        assert params == {
            "document_status": "COMPLETED",
            "search": "123456789",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
        }


class TestElectronicDocument:
    """Tests for ElectronicDocument model."""

    def test_parse_document(self, sample_document: dict) -> None:
        """Test parsing a document response."""
        doc = ElectronicDocument(**sample_document)

        assert doc.id == "456e7890-e89b-12d3-a456-426614174000"
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.rnc == "123456789"
        assert doc.encf == "E310000000001"
        assert doc.security_code == "ABC123"


class TestCompanyPublic:
    """Tests for CompanyPublic model."""

    def test_parse_company(self, sample_company: dict) -> None:
        """Test parsing a company response."""
        company = CompanyPublic(**sample_company)

        assert company.id == "123e4567-e89b-12d3-a456-426614174000"
        assert company.name == "Test Company SRL"
        assert company.rnc == "123456789"
        assert company.type == CompanyType.PRIMARY


class TestCompanyCreate:
    """Tests for CompanyCreate model."""

    def test_create_company(self) -> None:
        """Test creating company data."""
        company = CompanyCreate(
            name="Mi Empresa SRL",
            trade_name="Mi Empresa",
            rnc="123456789",
            address="Calle Principal #123",
        )

        assert company.name == "Mi Empresa SRL"
        assert company.rnc == "123456789"
        assert company.email is None
        assert company.certificate is None

    def test_create_company_validation(self) -> None:
        """Test company creation validation."""
        with pytest.raises(ValueError):
            CompanyCreate(
                name="",  # Empty name should fail
                trade_name="Test",
                rnc="123",
                address="Test Address",
            )


class TestCompanyURLs:
    """Tests for CompanyURLs model."""

    def test_parse_urls(self) -> None:
        """Test parsing company URLs response."""
        urls = CompanyURLs(
            reception="https://example.com/reception",
            approval="https://example.com/approval",
            authentication="https://example.com/auth",
        )

        assert urls.reception == "https://example.com/reception"
        assert urls.approval == "https://example.com/approval"
        assert urls.authentication == "https://example.com/auth"

    def test_parse_urls_from_dict(self) -> None:
        """Test parsing company URLs from dict (API response)."""
        data = {
            "reception": "https://api.example.com/receive",
            "approval": "https://api.example.com/approve",
            "authentication": "https://api.example.com/authenticate",
        }

        urls = CompanyURLs(**data)

        assert urls.reception == "https://api.example.com/receive"
        assert urls.approval == "https://api.example.com/approve"
        assert urls.authentication == "https://api.example.com/authenticate"

    def test_missing_field_raises_error(self) -> None:
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValueError):
            CompanyURLs(
                reception="https://example.com/reception",
                approval="https://example.com/approval",
                # authentication missing
            )
