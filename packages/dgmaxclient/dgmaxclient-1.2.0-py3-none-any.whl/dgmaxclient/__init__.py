"""
DGMaxClient - Python SDK for DGMax API.

A Python SDK for interacting with the DGMax electronic fiscal document
API for the Dominican Republic.

Examples:
    >>> from dgmaxclient import DGMaxClient
    >>>
    >>> # Initialize the client
    >>> client = DGMaxClient(api_key="dgmax_xxx")
    >>>
    >>> # List companies
    >>> companies = client.companies.list()
    >>>
    >>> # Create an invoice
    >>> invoice = client.invoices.create({...})
    >>>
    >>> # List received documents
    >>> received = client.received_documents.list()
"""

from __future__ import annotations

from dgmaxclient.client import DGMaxClient
from dgmaxclient.exceptions import (
    DGMaxAuthenticationError,
    DGMaxConnectionError,
    DGMaxError,
    DGMaxRateLimitError,
    DGMaxRequestError,
    DGMaxServerError,
    DGMaxTimeoutError,
    DGMaxValidationError,
)
from dgmaxclient.models import (  # Pagination; Documents; Companies
    CertificateCreate,
    CertificatePublic,
    CertificationStatus,
    CommercialApproval,
    CompanyCreate,
    CompanyPublic,
    CompanyRef,
    CompanyType,
    CompanyUpdate,
    DGIIEnvironment,
    DocumentCreateRequest,
    DocumentFilters,
    DocumentStatus,
    DocumentType,
    ElectronicDocument,
    ExternalDocumentStatus,
    Mensaje,
    PaginatedResponse,
    PaginationParams,
    ReceivedDocument,
)

__version__ = "1.0.2"
__author__ = "DGMax"
__email__ = "support@dgmax.do"

__all__ = [
    # Client
    "DGMaxClient",
    # Exceptions
    "DGMaxError",
    "DGMaxAuthenticationError",
    "DGMaxValidationError",
    "DGMaxRequestError",
    "DGMaxServerError",
    "DGMaxTimeoutError",
    "DGMaxConnectionError",
    "DGMaxRateLimitError",
    # Pagination
    "PaginatedResponse",
    "PaginationParams",
    # Request models
    "CompanyRef",
    "DocumentCreateRequest",
    # Response models
    "DocumentFilters",
    "DocumentStatus",
    "DocumentType",
    "ElectronicDocument",
    "ExternalDocumentStatus",
    "Mensaje",
    "ReceivedDocument",
    "CommercialApproval",
    # Company models
    "CertificateCreate",
    "CertificatePublic",
    "CertificationStatus",
    "CompanyCreate",
    "CompanyPublic",
    "CompanyType",
    "CompanyUpdate",
    "DGIIEnvironment",
]
