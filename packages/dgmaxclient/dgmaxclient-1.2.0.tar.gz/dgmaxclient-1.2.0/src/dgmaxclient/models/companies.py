"""
Company models for the DGMax client.

This module provides models for company management operations.
"""

from __future__ import annotations

from enum import Enum

from pydantic import EmailStr, Field, SecretStr, field_serializer

from dgmaxclient.models.base import DGMaxBaseModel


class CertificationStatus(str, Enum):
    """Certification workflow status for company.

    Attributes:
        NOT_STARTED: Certification process not started
        POSTULATION_ACCEPTED: Postulation accepted (TEST -> CERT)
        CERTIFIED: Company is certified (CERT -> PRD)
    """

    NOT_STARTED = "not_started"
    POSTULATION_ACCEPTED = "postulation_accepted"
    CERTIFIED = "certified"


class CompanyType(str, Enum):
    """Company type in the B2B hierarchy.

    Attributes:
        PRIMARY: Primary company (root level)
        SUBSIDIARY: Subsidiary company (has parent)
    """

    PRIMARY = "primary"
    SUBSIDIARY = "subsidiary"


class DGIIEnvironment(str, Enum):
    """DGII environment for document submission.

    Attributes:
        TEST: Integration testing environment
        CERT: Certification environment
        PRD: Production environment
    """

    TEST = "test"
    CERT = "cert"
    PRD = "prd"


class CertificatePublic(DGMaxBaseModel):
    """Public representation of a company certificate.

    Attributes:
        id: Certificate identifier
        name: Certificate filename
        extension: File extension
        issuer_name: Certificate issuer
        subject_name: Certificate subject
        start_date: Certificate start date (ISO format)
        end_date: Certificate end date (ISO format)
        serial_number: Certificate serial number
    """

    id: str
    name: str
    extension: str
    issuer_name: str
    subject_name: str
    start_date: str
    end_date: str
    serial_number: str


class CompanyPublic(DGMaxBaseModel):
    """Public representation of a company.

    Attributes:
        id: Company identifier
        name: Legal name (razón social)
        trade_name: Commercial name (nombre comercial)
        rnc: Tax identification number
        email: Contact email
        address: Company address
        branch: Branch identifier
        municipality: Municipality
        province: Province
        phone: Contact phone
        website: Company website
        logo: Signed URL for logo download
        type: Company type (primary/subsidiary)
        certificate: Certificate information
        dgii_environment: Current DGII environment
        certification_status: Certification workflow status
        parent_company_id: Parent company ID (for subsidiaries)
    """

    id: str
    name: str
    trade_name: str
    rnc: str
    email: str | None = None
    address: str
    branch: str | None = None
    municipality: str | None = None
    province: str | None = None
    phone: str | None = None
    website: str | None = None
    logo: str | None = None
    type: CompanyType = CompanyType.PRIMARY
    certificate: CertificatePublic | None = None
    dgii_environment: DGIIEnvironment = DGIIEnvironment.TEST
    certification_status: CertificationStatus = CertificationStatus.NOT_STARTED
    parent_company_id: str | None = None


class CertificateCreate(DGMaxBaseModel):
    """Model for creating/updating a certificate.

    Attributes:
        name: Certificate filename
        extension: File extension (e.g., "p12", "pfx")
        content: Base64-encoded certificate content
        password: Certificate password (stored securely, masked in repr)
    """

    name: str = Field(..., min_length=1, max_length=255)
    extension: str = Field(..., min_length=1, max_length=10)
    content: str = Field(..., min_length=1)
    password: SecretStr = Field(..., min_length=1, max_length=255)

    @field_serializer("password", when_used="always")
    @staticmethod
    def serialize_password(value: SecretStr) -> str:
        """Serialize password to plain string for API requests."""
        return value.get_secret_value()


class CompanyCreate(DGMaxBaseModel):
    """Model for creating a new company.

    Attributes:
        name: Legal name (razón social)
        trade_name: Commercial name (nombre comercial)
        rnc: Tax identification number
        email: Contact email
        address: Company address
        branch: Branch identifier
        municipality: Municipality
        province: Province
        phone: Contact phone
        website: Company website
        logo: Base64-encoded logo image
        type: Company type (optional, defaults based on context)
        certificate: Certificate for signing documents
    """

    name: str = Field(..., min_length=1, max_length=150)
    trade_name: str = Field(..., min_length=1, max_length=150)
    rnc: str = Field(..., min_length=1, max_length=40)
    email: EmailStr | None = None
    address: str = Field(..., min_length=1, max_length=100)
    branch: str | None = Field(default=None, max_length=20)
    municipality: str | None = Field(default=None, max_length=50)
    province: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=255)
    logo: str | None = None
    type: CompanyType | None = None
    certificate: CertificateCreate | None = None


class CompanyUpdate(DGMaxBaseModel):
    """Model for updating a company.

    All fields are optional. RNC cannot be changed.

    Attributes:
        name: Legal name (razón social)
        trade_name: Commercial name (nombre comercial)
        email: Contact email
        address: Company address
        branch: Branch identifier
        municipality: Municipality
        province: Province
        phone: Contact phone
        website: Company website
        logo: Base64-encoded logo image
        certificate: Certificate for signing documents
    """

    name: str | None = Field(default=None, min_length=1, max_length=150)
    trade_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=1, max_length=100)
    branch: str | None = Field(default=None, max_length=20)
    municipality: str | None = Field(default=None, max_length=50)
    province: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=255)
    logo: str | None = None
    certificate: CertificateCreate | None = None


class CompanyURLs(DGMaxBaseModel):
    """Company URLs for document reception and processing.

    Attributes:
        reception: URL for document reception
        approval: URL for document approval
        authentication: URL for authentication
    """

    reception: str
    approval: str
    authentication: str


class DGIIAuthorizationResponse(DGMaxBaseModel):
    """Response model for DGII certificate authorization validation.

    Attributes:
        authorized: Whether the company's certificate is authorized
        message: Description of the authorization status
        dgii_response: Raw DGII response (if available)
        status_code: HTTP status code from DGII (if available)
    """

    authorized: bool
    message: str
    dgii_response: str | None = None
    status_code: int | None = None
