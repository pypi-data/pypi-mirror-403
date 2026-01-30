"""
DGMax client models.

This module exports all public models for the DGMax SDK.
"""

from __future__ import annotations

from dgmaxclient.models.base import (
    APIResponse,
    DGMaxBaseModel,
    ErrorDetail,
    ErrorResponse,
    IdentifiableMixin,
    TimestampMixin,
)
from dgmaxclient.models.certification import (
    CertificationCommercialApprovalBatchStatus,
    CertificationCommercialApprovalProgress,
    CertificationCommercialApprovalPublic,
    CertificationCommercialApprovalStatus,
    CertificationProviderInfoResponse,
    CertificationTestCasePublic,
    CertificationTestSuiteCreate,
    CertificationTestSuitePublic,
    CertificationTestType,
    DocumentStatusSummary,
    EnvironmentSwitchResponse,
    MensajePublic,
    ProviderInfo,
    TestItem,
    TestSuiteStatus,
    XMLSigningResponse,
)
from dgmaxclient.models.companies import (
    CertificateCreate,
    CertificatePublic,
    CertificationStatus,
    CompanyCreate,
    CompanyPublic,
    CompanyType,
    CompanyUpdate,
    CompanyURLs,
    DGIIAuthorizationResponse,
    DGIIEnvironment,
)
from dgmaxclient.models.documents import (
    ApproveDocumentRequest,
    CommercialApproval,
    CommercialApprovalAction,
    CommercialApprovalActionResponse,
    CommercialApprovalDirection,
    CommercialApprovalSubmissionStatus,
    CompanyRef,
    DocumentCreateRequest,
    DocumentFilters,
    DocumentStatus,
    DocumentType,
    ElectronicDocument,
    ExternalDocumentStatus,
    Mensaje,
    ReceivedDocument,
    ReceivedDocumentStatus,
    RejectDocumentRequest,
)
from dgmaxclient.models.pagination import PaginatedResponse, PaginationParams

__all__ = [
    # Base models
    "APIResponse",
    "DGMaxBaseModel",
    "ErrorDetail",
    "ErrorResponse",
    "IdentifiableMixin",
    "TimestampMixin",
    # Pagination
    "PaginatedResponse",
    "PaginationParams",
    # Certification models
    "CertificationCommercialApprovalBatchStatus",
    "CertificationCommercialApprovalProgress",
    "CertificationCommercialApprovalPublic",
    "CertificationCommercialApprovalStatus",
    "CertificationProviderInfoResponse",
    "CertificationTestCasePublic",
    "CertificationTestSuiteCreate",
    "CertificationTestSuitePublic",
    "CertificationTestType",
    "DocumentStatusSummary",
    "EnvironmentSwitchResponse",
    "MensajePublic",
    "ProviderInfo",
    "TestItem",
    "TestSuiteStatus",
    "XMLSigningResponse",
    # Request models
    "CompanyRef",
    "DocumentCreateRequest",
    # Response models
    "ApproveDocumentRequest",
    "CommercialApproval",
    "CommercialApprovalAction",
    "CommercialApprovalActionResponse",
    "CommercialApprovalDirection",
    "CommercialApprovalSubmissionStatus",
    "DocumentFilters",
    "DocumentStatus",
    "DocumentType",
    "ElectronicDocument",
    "ExternalDocumentStatus",
    "Mensaje",
    "ReceivedDocument",
    "ReceivedDocumentStatus",
    "RejectDocumentRequest",
    # Companies
    "CertificateCreate",
    "CertificatePublic",
    "CertificationStatus",
    "CompanyCreate",
    "CompanyPublic",
    "CompanyType",
    "CompanyUpdate",
    "CompanyURLs",
    "DGIIAuthorizationResponse",
    "DGIIEnvironment",
]
