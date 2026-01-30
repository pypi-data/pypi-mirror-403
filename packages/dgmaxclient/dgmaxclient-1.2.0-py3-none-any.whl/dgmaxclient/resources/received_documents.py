"""
Received documents resource for the DGMax client.

This module provides the resource class for received document operations
(receptor module).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dgmaxclient.models.documents import (
    ApproveDocumentRequest,
    CommercialApproval,
    CommercialApprovalActionResponse,
    ReceivedDocument,
    RejectDocumentRequest,
)
from dgmaxclient.models.pagination import PaginatedResponse, PaginationParams
from dgmaxclient.resources.base import BaseResource
from dgmaxclient.retrying import retry_request

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class ReceivedDocumentsResource(BaseResource[ReceivedDocument]):
    """Resource for received document operations.

    Provides functionality for managing documents received from
    other contribuyentes, including approval and rejection actions.

    Examples:
        >>> # List received documents
        >>> documents = client.received_documents.list()

        >>> # Get a specific received document
        >>> document = client.received_documents.get("document-uuid")

        >>> # Approve a document
        >>> response = client.received_documents.approve("document-uuid")

        >>> # Reject a document
        >>> response = client.received_documents.reject(
        ...     "document-uuid",
        ...     rejection_reason="Invoice amount incorrect"
        ... )
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the received documents resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.received_documents,
            model_class=ReceivedDocument,
        )

    def list(
        self,
        params: PaginationParams | None = None,
        status_filter: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        **kwargs: Any,
    ) -> PaginatedResponse[ReceivedDocument]:
        """List received documents with filtering.

        Args:
            params: Pagination parameters
            status_filter: Filter by document status
            search: Search by eNCF or RNC emisor
            date_from: Filter by start date (ISO format)
            date_to: Filter by end date (ISO format)
            **kwargs: Additional query parameters

        Returns:
            Paginated response with received documents
        """
        if status_filter:
            kwargs["status_filter"] = status_filter
        if search:
            kwargs["search"] = search
        if date_from:
            kwargs["date_from"] = date_from
        if date_to:
            kwargs["date_to"] = date_to

        return super().list(params=params, **kwargs)

    @retry_request
    def approve(
        self,
        document_id: str,
        notes: str | None = None,
    ) -> CommercialApprovalActionResponse:
        """Approve a received document.

        Sends ACECF (commercial approval) to the issuer and DGII.

        Args:
            document_id: The document identifier
            notes: Optional approval notes

        Returns:
            Approval action response

        Examples:
            >>> response = client.received_documents.approve("document-uuid")
            >>> if response.success:
            ...     print(f"Approved: {response.approval_id}")
        """
        endpoint = self.client.endpoints.approve_document.format(id=document_id)
        request = ApproveDocumentRequest(notes=notes)

        response = self.client.post(
            endpoint, json=request.model_dump(exclude_none=True)
        )
        return CommercialApprovalActionResponse(**response)

    @retry_request
    def reject(
        self,
        document_id: str,
        rejection_reason: str,
    ) -> CommercialApprovalActionResponse:
        """Reject a received document.

        Sends ACECF (commercial rejection) to the issuer and DGII.

        Args:
            document_id: The document identifier
            rejection_reason: Reason for rejection (required)

        Returns:
            Rejection action response

        Examples:
            >>> response = client.received_documents.reject(
            ...     "document-uuid",
            ...     rejection_reason="Invoice amount does not match purchase order"
            ... )
            >>> if response.success:
            ...     print(f"Rejected: {response.approval_id}")
        """
        endpoint = self.client.endpoints.reject_document.format(id=document_id)
        request = RejectDocumentRequest(rejection_reason=rejection_reason)

        response = self.client.post(endpoint, json=request.model_dump())
        return CommercialApprovalActionResponse(**response)

    @retry_request
    def list_commercial_approvals(
        self,
        params: PaginationParams | None = None,
        status_filter: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        **kwargs: Any,
    ) -> PaginatedResponse[CommercialApproval]:
        """List commercial approvals received.

        Args:
            params: Pagination parameters
            status_filter: Filter by submission status
            search: Search by eNCF or RNC emisor
            date_from: Filter by start date (ISO format)
            date_to: Filter by end date (ISO format)
            **kwargs: Additional query parameters

        Returns:
            Paginated response with commercial approvals
        """
        query_params: dict[str, Any] = {}

        # Track pagination params for has_more calculation
        offset = 0
        limit = 100
        if params:
            query_params.update(params.to_query_params())
            offset = params.offset
            limit = params.limit

        if status_filter:
            query_params["status_filter"] = status_filter
        if search:
            query_params["search"] = search
        if date_from:
            query_params["date_from"] = date_from
        if date_to:
            query_params["date_to"] = date_to

        query_params.update(kwargs)

        response = self.client.get(
            self.client.endpoints.commercial_approvals,
            params=query_params,
        )

        paginated_response = PaginatedResponse[CommercialApproval](
            count=response.get("count", 0),
            results=[
                CommercialApproval(**item) for item in response.get("results", [])
            ],
        )
        # Set pagination tracking for has_more calculation
        paginated_response._offset = offset
        paginated_response._limit = limit
        return paginated_response
