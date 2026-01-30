"""
Certification models for the DGMax client.

This module provides models for the DGII certification workflow,
including test suite management and environment transitions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field

from dgmaxclient.models.base import DGMaxBaseModel


class TestSuiteStatus(str, Enum):
    """Status of certification test suite progress.

    Attributes:
        GENERATING: Documents being generated
        READY_FOR_UPLOAD: ZIPs ready for download
        UPLOADED_TO_DGII: User uploaded to DGII portal
        AWAITING_APPROVAL: Waiting for DGII approval
        APPROVED: DGII approved test documents
        REJECTED: DGII rejected test documents
    """

    GENERATING = "generating"
    READY_FOR_UPLOAD = "ready_for_upload"
    UPLOADED_TO_DGII = "uploaded_to_dgii"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class CertificationCommercialApprovalStatus(str, Enum):
    """Status of individual certification commercial approval.

    Attributes:
        PENDING: Approval not yet submitted
        SENT: Approval successfully submitted to DGII
        FAILED: Approval submission failed
    """

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class CertificationCommercialApprovalBatchStatus(str, Enum):
    """Status of certification commercial approval batch.

    Attributes:
        PENDING: Batch not started
        SUBMITTING: Batch is being submitted
        COMPLETED: All approvals in batch submitted
        FAILED: Batch submission failed
    """

    PENDING = "pending"
    SUBMITTING = "submitting"
    COMPLETED = "completed"
    FAILED = "failed"


class CertificationTestType(str, Enum):
    """DGII certification test document types.

    Main documents (10) and resúmenes.
    """

    # Main documents (10)
    E31_CREDITO_FISCAL = "e31"
    E32_CONSUMO = "e32_consumo"  # >= 250k
    E33_NOTA_DEBITO = "e33"
    E34_NOTA_CREDITO = "e34"
    E41_COMPRAS = "e41"
    E43_GASTOS_MENORES = "e43"
    E44_REGIMENES_ESPECIALES = "e44"
    E45_GUBERNAMENTAL = "e45"
    E46_EXPORTACIONES = "e46"
    E47_PAGOS_EXTERIOR = "e47"

    # Resúmenes (10)
    E32_RESUMEN_CONSUMO = "e32_resumen_consumo"  # < 250k (RFCE)


class TestItem(DGMaxBaseModel):
    """Test item structure aligned with DGII/XSD item specification.

    The indicador_facturacion determines tax calculation:
    - 1: Gravado 18% ITBIS
    - 2: Gravado 16% ITBIS
    - 3: Gravado 0% ITBIS
    - 4: Exento (no ITBIS)

    Attributes:
        indicador_facturacion: Billing indicator (1=18%, 2=16%, 3=0%, 4=Exento)
        nombre_item: Item name
        descripcion_item: Optional item description
        indicador_bien_o_servicio: 1=Good, 2=Service
        cantidad_item: Item quantity
        precio_unitario_item: Unit price before tax
    """

    indicador_facturacion: int = Field(..., ge=1, le=4)
    nombre_item: str = Field(..., min_length=1, max_length=255)
    descripcion_item: str | None = Field(default=None, max_length=500)
    indicador_bien_o_servicio: int = Field(default=1, ge=1, le=2)
    cantidad_item: str = Field(default="1")
    precio_unitario_item: Decimal = Field(..., gt=0)


class CertificationTestSuiteCreate(DGMaxBaseModel):
    """Request model for creating a certification test suite.

    Attributes:
        company_id: Company to create test suite for
        test_item: Single test item that generates all documents
        start_sequence: Starting sequence number for documents
    """

    company_id: str
    test_item: TestItem
    start_sequence: int = Field(default=1, ge=1, le=9999999980)


class MensajePublic(DGMaxBaseModel):
    """DGII response message.

    Attributes:
        valor: Message value/code
        mensaje: Message text
    """

    valor: str | None = None
    mensaje: str | None = None


class DocumentStatusSummary(DGMaxBaseModel):
    """Summary of document status for test case list views.

    Attributes:
        status: Internal document status
        external_estado: DGII response estado (e.g., 'Aceptado', 'Rechazado')
        external_codigo: DGII response code
        mensajes: DGII response messages (errors/warnings)
    """

    status: str
    external_estado: str | None = None
    external_codigo: str | None = None
    mensajes: list[MensajePublic] = Field(default_factory=list)


class CertificationTestCasePublic(DGMaxBaseModel):
    """Public representation of a certification test case.

    Attributes:
        id: Test case identifier
        test_type: Type of document being tested
        test_number: Sequential test number (1-20)
        notes: Optional notes
        created_at: When the test case was created
        electronic_document_id: ID of the generated document (if created)
        document_status: Document status summary (if document exists)
    """

    id: str
    test_type: CertificationTestType
    test_number: int
    notes: str | None = None
    created_at: datetime
    electronic_document_id: str | None = None
    document_status: DocumentStatusSummary | None = None


class CertificationTestSuitePublic(DGMaxBaseModel):
    """Public representation of a certification test suite.

    Attributes:
        id: Test suite identifier
        company_id: Company the test suite belongs to
        test_item: The test item used to generate documents
        start_sequence: Starting sequence number
        status: Current status of the test suite
        certification_mode: Certification mode (PROPIO or EXTERNO)
        postulation_xml_signed: Signed postulation XML storage key
        postulation_signed_at: When postulation was signed
        declaracion_jurada_xml_signed: Signed declaration XML storage key
        declaracion_signed_at: When declaration was signed
        main_documents_zip: Storage key for main documents ZIP
        resumenes_zip: Storage key for resúmenes ZIP
        created_at: When the test suite was created
        completed_at: When the test suite completed
        test_cases: List of test cases in the suite
    """

    id: str
    company_id: str
    test_item: TestItem
    start_sequence: int
    status: TestSuiteStatus
    certification_mode: str | None = None
    postulation_xml_signed: str | None = None
    postulation_signed_at: datetime | None = None
    declaracion_jurada_xml_signed: str | None = None
    declaracion_signed_at: datetime | None = None
    main_documents_zip: str | None = None
    resumenes_zip: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    test_cases: list[CertificationTestCasePublic] = Field(default_factory=list)


class ProviderInfo(DGMaxBaseModel):
    """Provider information for DGII portal registration.

    Attributes:
        rnc: Provider RNC
        name: Provider legal name
        trade_name: Provider commercial name
    """

    rnc: str
    name: str
    trade_name: str


class CertificationProviderInfoResponse(DGMaxBaseModel):
    """Response model for provider info endpoint.

    Attributes:
        software_type: Certification software type (PROPIO or EXTERNO)
        software_name: Software name
        software_version: Software version
        provider: Provider information (only for EXTERNO mode)
    """

    software_type: str
    software_name: str
    software_version: str
    provider: ProviderInfo | None = None


class XMLSigningResponse(DGMaxBaseModel):
    """Response model for XML signing operations.

    Attributes:
        signed_xml: Signed URL to download the signed XML file
        security_code: First 6 characters of signature for verification
        signature_date: ISO timestamp when document was signed
        file_name: Suggested filename for the signed document
        signed_xml_key: Storage key for the signed XML file (optional)
    """

    signed_xml: str
    security_code: str
    signature_date: str
    file_name: str
    signed_xml_key: str | None = None


class EnvironmentSwitchResponse(DGMaxBaseModel):
    """Response model for certification step acceptance (environment switches).

    Attributes:
        message: Success message describing the action
        company_id: UUID of the company
        previous_environment: DGII environment before the switch
        current_environment: DGII environment after the switch
        certification_status: Current certification status
        switched_at: ISO timestamp when the switch occurred (optional)
    """

    message: str
    company_id: str
    previous_environment: str
    current_environment: str
    certification_status: str
    switched_at: str | None = None


class CertificationCommercialApprovalPublic(DGMaxBaseModel):
    """Public representation of a certification commercial approval.

    Attributes:
        id: Approval identifier
        company_id: Company the approval belongs to
        batch_id: Batch identifier (if part of a batch)
        rnc_emisor: Issuer RNC
        e_ncf: Electronic fiscal number
        fecha_emision: Issue date
        monto_total: Total amount
        approve: Whether to approve the document
        rejection_reason: Reason for rejection (if not approved)
        status: Approval submission status
        acecf_xml: ACECF XML content (if generated)
        dgii_response: DGII response (if submitted)
        error_detail: Error details (if failed)
        created_at: When the approval was created
        submitted_at: When the approval was submitted
    """

    id: str
    company_id: str
    batch_id: str | None = None
    rnc_emisor: str
    e_ncf: str
    fecha_emision: str
    monto_total: str
    approve: bool
    rejection_reason: str | None = None
    status: CertificationCommercialApprovalStatus
    acecf_xml: str | None = None
    dgii_response: str | None = None
    error_detail: dict[str, Any] | None = None
    created_at: datetime
    submitted_at: datetime | None = None


class CertificationCommercialApprovalProgress(DGMaxBaseModel):
    """Progress report for certification commercial approvals.

    Attributes:
        batch_id: Batch identifier (if processing as batch)
        batch_status: Overall batch status
        total: Total number of approvals
        pending: Number of pending approvals
        sent: Number of successfully sent approvals
        failed: Number of failed approvals
        approvals: List of individual approvals
    """

    batch_id: str | None = None
    batch_status: CertificationCommercialApprovalBatchStatus | None = None
    total: int
    pending: int
    sent: int
    failed: int
    approvals: list[CertificationCommercialApprovalPublic] = Field(default_factory=list)
