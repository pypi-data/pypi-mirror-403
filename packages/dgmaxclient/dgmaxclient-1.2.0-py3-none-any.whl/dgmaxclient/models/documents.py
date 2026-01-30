"""
Document models for the DGMax client.

This module provides models for electronic fiscal documents (E31-E47)
and related data structures.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from dgmaxclient.models.base import DGMaxBaseModel


class DocumentStatus(str, Enum):
    """Status of an electronic document.

    Attributes:
        REGISTERED: Document has been registered but not yet processed
        PROCESSING: Document is being processed by DGII
        COMPLETED: Document has been successfully processed
        FAILED: Document processing failed
        QUEUED: Document queued for retry when DGII unavailable
    """

    REGISTERED = "REGISTERED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED = "QUEUED"


class DocumentType(str, Enum):
    """Type of electronic fiscal document.

    Attributes:
        E31: Factura de Crédito Fiscal Electrónica
        E32: Factura de Consumo Electrónica
        E33: Nota de Débito Electrónica
        E34: Nota de Crédito Electrónica
        E41: Comprobante Electrónico de Compras
        E43: Comprobante Electrónico para Gastos Menores
        E44: Comprobante Electrónico para Regímenes Especiales
        E45: Comprobante Electrónico Gubernamental
        E46: Comprobante Electrónico para Exportaciones
        E47: Comprobante Electrónico para Pagos al Exterior
    """

    E31 = "E31"
    E32 = "E32"
    E33 = "E33"
    E34 = "E34"
    E41 = "E41"
    E43 = "E43"
    E44 = "E44"
    E45 = "E45"
    E46 = "E46"
    E47 = "E47"


# =============================================================================
# Request Models
# =============================================================================


class CompanyRef(DGMaxBaseModel):
    """Reference to a company for document creation.

    Attributes:
        id: Company UUID
    """

    id: UUID


class DocumentCreateRequest(DGMaxBaseModel):
    """Request model for creating electronic documents (E31-E47).

    Attributes:
        company: Reference to the company
        ecf: ECF document payload (encabezado, detalles_items, etc.)
    """

    company: CompanyRef
    ecf: dict[str, Any] = Field(..., description="ECF document payload")

    @field_validator("ecf")
    @classmethod
    def validate_ecf_structure(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate required top-level ECF fields."""
        if "encabezado" not in v:
            raise ValueError("ECF must contain 'encabezado'")
        if "detalles_items" not in v:
            raise ValueError("ECF must contain 'detalles_items'")
        return v


# =============================================================================
# Response Models
# =============================================================================


class Mensaje(DGMaxBaseModel):
    """Message from DGII response.

    Attributes:
        valor: Message content
        codigo: Message code
    """

    valor: str | None = None
    codigo: int | None = None


class ExternalDocumentStatus(DGMaxBaseModel):
    """External status information from DGII.

    Attributes:
        codigo: Status code
        estado: Status state
        rnc: RNC of the issuer
        encf: eNCF identifier
        secuencia_utilizada: Whether the sequence was used
        fecha_recepcion: Reception date
        mensajes: List of messages
    """

    codigo: str | None = None
    estado: str | None = None
    rnc: str
    encf: str | None = None
    secuencia_utilizada: bool = False
    fecha_recepcion: str | None = None
    mensajes: list[Mensaje] = Field(default_factory=list)


class ElectronicDocument(DGMaxBaseModel):
    """Electronic document response model.

    This model represents the data returned by the API for
    electronic document operations.

    Attributes:
        id: Unique identifier
        status: Current document status
        rnc: RNC of the issuer
        encf: eNCF identifier
        document_stamp_url: URL to the document stamp
        security_code: Security code for verification
        signature_date: Date when document was signed
        signed_xml: Object key for signed XML file
        resume_xml: Object key for resume XML file
        pdf: Object key for PDF file
        queued_at: Timestamp when queued for retry
        stale_retry_count: Number of automatic retries for stale documents
        created_at: Creation timestamp
        updated_at: Last update timestamp
        external_status: Status information from DGII
    """

    id: str
    status: DocumentStatus
    rnc: str
    encf: str
    document_stamp_url: str | None = None
    security_code: str | None = None
    signature_date: str | None = None
    signed_xml: str | None = None
    resume_xml: str | None = None
    pdf: str | None = None
    queued_at: datetime | None = None
    referenced_document_id: str | None = None
    stale_retry_count: int = 0
    created_at: datetime
    updated_at: datetime
    external_status: ExternalDocumentStatus | None = None


class DocumentFilters(DGMaxBaseModel):
    """Filters for document list queries.

    Attributes:
        status: Filter by document status
        search: Search by eNCF or RNC
        date_from: Filter by start date (ISO format)
        date_to: Filter by end date (ISO format)
    """

    status: DocumentStatus | None = Field(default=None, alias="document_status")
    search: str | None = None
    date_from: str | None = None
    date_to: str | None = None

    def to_query_params(self) -> dict[str, Any]:
        """Convert filters to query parameters.

        Returns:
            Dictionary of non-None filter values
        """
        params: dict[str, Any] = {}
        if self.status:
            # With use_enum_values=True, status is already a string value
            params["document_status"] = self.status
        if self.search:
            params["search"] = self.search
        if self.date_from:
            params["date_from"] = self.date_from
        if self.date_to:
            params["date_to"] = self.date_to
        return params


class ReceivedDocumentStatus(str, Enum):
    """Status of a received document.

    Attributes:
        PENDING: Document pending approval/rejection
        APPROVED: Document approved
        REJECTED: Document rejected
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReceivedDocument(DGMaxBaseModel):
    """Received document response model.

    Attributes:
        id: Unique identifier
        company_id: Company that received the document
        rnc_emisor: RNC of the issuer
        rnc_comprador: RNC of the buyer
        e_ncf: eNCF identifier
        status: Document status (PENDING, APPROVED, REJECTED)
        received_at: Reception timestamp
        xml_url: Signed URL for XML download
        arecf_xml_url: Signed URL for ARECF XML download
    """

    id: str
    company_id: str | None = None
    rnc_emisor: str
    rnc_comprador: str
    e_ncf: str
    status: ReceivedDocumentStatus
    received_at: datetime
    xml_url: str | None = None
    arecf_xml_url: str | None = None


class CommercialApprovalDirection(str, Enum):
    """Direction of commercial approval flow.

    Attributes:
        SENT: We approve/reject document from another party
        RECEIVED: Others approve/reject our document
    """

    SENT = "SENT"
    RECEIVED = "RECEIVED"


class CommercialApprovalAction(str, Enum):
    """Action taken on commercial approval.

    Attributes:
        APPROVED: Document approved
        REJECTED: Document rejected
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CommercialApprovalSubmissionStatus(str, Enum):
    """Status of commercial approval submission to third parties.

    Attributes:
        PENDING: Not yet submitted
        SENT_TO_THIRD_PARTY: Sent to the other party
        SENT_TO_DGII: Sent to DGII
        COMPLETED: Successfully submitted to all parties
        FAILED: Submission failed
        QUEUED_FOR_RETRY: Queued for retry
    """

    PENDING = "PENDING"
    SENT_TO_THIRD_PARTY = "SENT_TO_THIRD_PARTY"
    SENT_TO_DGII = "SENT_TO_DGII"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED_FOR_RETRY = "QUEUED_FOR_RETRY"


class CommercialApproval(DGMaxBaseModel):
    """Commercial approval response model.

    Attributes:
        id: Unique identifier
        company_id: Company that created this approval
        direction: Direction (SENT or RECEIVED)
        rnc_emisor: RNC of original document issuer
        rnc_comprador: RNC of original document buyer
        e_ncf: eNCF identifier of document being approved
        emission_date: Original document emission date (DD-MM-YYYY)
        approval_action: Action taken (APPROVED or REJECTED)
        rejection_reason: Reason for rejection (if rejected)
        commercial_approval_date: Commercial approval timestamp
        submission_status: Status of submission to third parties
        third_party_response: Response from third party
        external_error_detail: Structured error details from failed submissions
        received_document_id: Related received document ID (for SENT approvals)
        electronic_document_id: Related electronic document ID (for RECEIVED approvals)
        acecf_xml_url: Signed URL for ACECF XML download
    """

    id: str
    company_id: str | None = None
    direction: CommercialApprovalDirection
    rnc_emisor: str
    rnc_comprador: str
    e_ncf: str
    emission_date: str
    approval_action: CommercialApprovalAction
    rejection_reason: str | None = None
    commercial_approval_date: datetime | None = None
    submission_status: CommercialApprovalSubmissionStatus = (
        CommercialApprovalSubmissionStatus.PENDING
    )
    third_party_response: str | None = None
    external_error_detail: dict | None = None
    received_document_id: str | None = None
    electronic_document_id: str | None = None
    acecf_xml_url: str | None = None


class ApproveDocumentRequest(DGMaxBaseModel):
    """Request model for approving a document.

    Attributes:
        notes: Optional approval notes
    """

    notes: str | None = None


class RejectDocumentRequest(DGMaxBaseModel):
    """Request model for rejecting a document.

    Attributes:
        rejection_reason: Reason for rejection (required)
    """

    rejection_reason: str


class CommercialApprovalActionResponse(DGMaxBaseModel):
    """Response model for approval/rejection actions.

    Attributes:
        success: Whether the action succeeded
        message: Response message
        approval_id: ID of the created approval record
        dgii_track_id: Track ID from DGII submission
        submission_status: Current submission status
    """

    success: bool
    message: str
    approval_id: str | None = None
    dgii_track_id: str | None = None
    submission_status: str | None = None
