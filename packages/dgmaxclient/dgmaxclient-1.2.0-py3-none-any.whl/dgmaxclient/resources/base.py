"""
Base resource classes for the DGMax client.

This module provides base classes for API resources that handle
CRUD operations and document-specific functionality.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from dgmaxclient.models.documents import (
    DocumentCreateRequest,
    DocumentFilters,
    ElectronicDocument,
)
from dgmaxclient.models.pagination import PaginatedResponse, PaginationParams
from dgmaxclient.retrying import retry_request

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient

T = TypeVar("T")
CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")

# UUID v4 pattern for resource ID validation
_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class BaseResource(Generic[T]):
    """Base resource class for API operations.

    Provides common CRUD operations for API resources.

    Attributes:
        client: The DGMax client instance
        endpoint: The API endpoint for this resource
        model_class: The Pydantic model class for response parsing
    """

    def __init__(
        self,
        client: DGMaxClient,
        endpoint: str,
        model_class: type[T],
    ) -> None:
        """Initialize the resource.

        Args:
            client: The DGMax client instance
            endpoint: The API endpoint for this resource
            model_class: The Pydantic model class for response parsing
        """
        self.client = client
        self.endpoint = endpoint
        self.model_class = model_class

    def _get_endpoint(self, resource_id: str | None = None) -> str:
        """Get the full endpoint URL.

        Args:
            resource_id: Optional resource ID for specific resource endpoints

        Returns:
            The full endpoint URL

        Raises:
            ValueError: If resource_id is provided but has invalid format
        """
        if resource_id:
            if not _UUID_PATTERN.match(resource_id):
                raise ValueError(
                    f"Invalid resource ID format: '{resource_id}'. "
                    "Expected UUID format."
                )
            return f"{self.endpoint}/{resource_id}"
        return self.endpoint

    @retry_request
    def list(
        self,
        params: PaginationParams | None = None,
        **kwargs: Any,
    ) -> PaginatedResponse[T]:
        """List resources with pagination.

        Args:
            params: Pagination parameters
            **kwargs: Additional query parameters

        Returns:
            Paginated response with resources
        """
        query_params: dict[str, Any] = {}

        # Track pagination params for has_more calculation
        offset = 0
        limit = 100
        if params:
            query_params.update(params.to_query_params())
            offset = params.offset
            limit = params.limit

        query_params.update(kwargs)

        response = self.client.get(self.endpoint, params=query_params)

        paginated_response = PaginatedResponse[T](
            count=response.get("count", 0),
            results=[self.model_class(**item) for item in response.get("results", [])],
        )
        # Set pagination tracking for has_more calculation
        paginated_response._offset = offset
        paginated_response._limit = limit
        return paginated_response

    @retry_request
    def get(self, resource_id: str) -> T:
        """Get a specific resource by ID.

        Args:
            resource_id: The resource identifier

        Returns:
            The resource instance
        """
        endpoint = self._get_endpoint(resource_id)
        response = self.client.get(endpoint)
        return self.model_class(**response)

    @retry_request
    def create(self, data: dict[str, Any] | CreateT) -> T:
        """Create a new resource.

        Args:
            data: The resource data (dict or Pydantic model)

        Returns:
            The created resource
        """
        if hasattr(data, "model_dump"):
            payload = data.model_dump(exclude_none=True)
        else:
            payload = data

        response = self.client.post(self.endpoint, json=payload)
        return self.model_class(**response)

    @retry_request
    def update(self, resource_id: str, data: dict[str, Any] | UpdateT) -> T:
        """Update an existing resource.

        Args:
            resource_id: The resource identifier
            data: The update data (dict or Pydantic model)

        Returns:
            The updated resource
        """
        endpoint = self._get_endpoint(resource_id)

        if hasattr(data, "model_dump"):
            payload = data.model_dump(exclude_none=True)
        else:
            payload = data

        response = self.client.patch(endpoint, json=payload)
        return self.model_class(**response)

    @retry_request
    def delete(self, resource_id: str) -> None:
        """Delete a resource.

        Args:
            resource_id: The resource identifier
        """
        endpoint = self._get_endpoint(resource_id)
        self.client.delete(endpoint)


class DocumentResource(BaseResource[ElectronicDocument]):
    """Resource class for electronic document operations.

    Extends BaseResource with document-specific functionality
    like filtering by status, date range, and search.
    """

    def __init__(
        self,
        client: DGMaxClient,
        endpoint: str,
    ) -> None:
        """Initialize the document resource.

        Args:
            client: The DGMax client instance
            endpoint: The API endpoint for this document type
        """
        super().__init__(client, endpoint, ElectronicDocument)

    def list(
        self,
        params: PaginationParams | None = None,
        filters: DocumentFilters | None = None,
        **kwargs: Any,
    ) -> PaginatedResponse[ElectronicDocument]:
        """List documents with pagination and filtering.

        Args:
            params: Pagination parameters
            filters: Document filters (status, search, date range)
            **kwargs: Additional query parameters

        Returns:
            Paginated response with documents

        Examples:
            >>> # List all invoices
            >>> invoices = client.invoices.list()

            >>> # List with pagination
            >>> invoices = client.invoices.list(
            ...     params=PaginationParams(limit=50, offset=0)
            ... )

            >>> # List with filters
            >>> invoices = client.invoices.list(
            ...     filters=DocumentFilters(
            ...         status=DocumentStatus.COMPLETED,
            ...         date_from="2024-01-01"
            ...     )
            ... )
        """
        if filters:
            kwargs.update(filters.to_query_params())

        return super().list(params=params, **kwargs)

    @retry_request
    def create(
        self, data: dict[str, Any] | DocumentCreateRequest
    ) -> ElectronicDocument:
        """Create and submit a new electronic document.

        Args:
            data: The ECF document data (dict or DocumentCreateRequest)

        Returns:
            The created document with processing status

        Examples:
            >>> # Using dict
            >>> invoice = client.invoices.create({
            ...     "company": {"id": "..."},
            ...     "ecf": {"encabezado": {...}, "detalles_items": {...}}
            ... })
            >>> print(f"Document ID: {invoice.id}")

            >>> # Using model
            >>> from dgmaxclient import DocumentCreateRequest
            >>> invoice = client.invoices.create(
            ...     DocumentCreateRequest(
            ...         company={"id": "..."},
            ...         ecf={"encabezado": {...}, "detalles_items": {...}}
            ...     )
            ... )
        """
        if hasattr(data, "model_dump"):
            payload = data.model_dump(exclude_none=True)
        else:
            payload = data

        response = self.client.post(self.endpoint, json=payload)
        return self.model_class(**response)
