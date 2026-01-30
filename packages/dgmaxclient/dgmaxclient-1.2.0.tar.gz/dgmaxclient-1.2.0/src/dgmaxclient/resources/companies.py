"""
Companies resource for the DGMax client.

This module provides the resource class for company operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dgmaxclient.models.certification import (
    EnvironmentSwitchResponse,
    XMLSigningResponse,
)
from dgmaxclient.models.companies import (
    CompanyCreate,
    CompanyPublic,
    CompanyUpdate,
    CompanyURLs,
    DGIIAuthorizationResponse,
)
from dgmaxclient.models.pagination import PaginatedResponse, PaginationParams
from dgmaxclient.resources.base import BaseResource
from dgmaxclient.retrying import retry_request

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class CompaniesResource(BaseResource[CompanyPublic]):
    """Resource for company management operations.

    Provides CRUD operations for companies including certificate
    management and configuration.

    Examples:
        >>> # List all companies
        >>> companies = client.companies.list()
        >>> for company in companies.results:
        ...     print(f"{company.name} ({company.rnc})")

        >>> # Get a specific company
        >>> company = client.companies.get("company-uuid")

        >>> # Create a new company
        >>> company = client.companies.create({
        ...     "name": "Mi Empresa SRL",
        ...     "trade_name": "Mi Empresa",
        ...     "rnc": "123456789",
        ...     "address": "Calle Principal #123"
        ... })

        >>> # Update a company
        >>> company = client.companies.update("company-uuid", {
        ...     "phone": "809-555-1234"
        ... })
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the companies resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.companies,
            model_class=CompanyPublic,
        )

    def list(
        self,
        params: PaginationParams | None = None,
        **kwargs: Any,
    ) -> PaginatedResponse[CompanyPublic]:
        """List all companies.

        Args:
            params: Pagination parameters
            **kwargs: Additional query parameters

        Returns:
            Paginated response with companies
        """
        return super().list(params=params, **kwargs)

    def create(
        self,
        data: dict[str, Any] | CompanyCreate,
    ) -> CompanyPublic:
        """Create a new company.

        Args:
            data: Company creation data

        Returns:
            The created company

        Examples:
            >>> company = client.companies.create(CompanyCreate(
            ...     name="Mi Empresa SRL",
            ...     trade_name="Mi Empresa",
            ...     rnc="123456789",
            ...     address="Calle Principal #123",
            ...     certificate=CertificateCreate(
            ...         name="certificate",
            ...         extension="p12",
            ...         content="base64-encoded-content",
            ...         password="certificate-password"
            ...     )
            ... ))
        """
        return super().create(data)

    def update(
        self,
        company_id: str,
        data: dict[str, Any] | CompanyUpdate,
    ) -> CompanyPublic:
        """Update an existing company.

        Note: RNC cannot be changed after creation.

        Args:
            company_id: The company identifier
            data: Update data (only non-None fields will be updated)

        Returns:
            The updated company

        Examples:
            >>> company = client.companies.update(
            ...     "company-uuid",
            ...     CompanyUpdate(
            ...         phone="809-555-1234",
            ...         email="info@miempresa.com"
            ...     )
            ... )
        """
        return super().update(company_id, data)

    @retry_request
    def get_urls(self, company_id: str) -> CompanyURLs:
        """Get URLs for a company.

        Args:
            company_id: The company identifier

        Returns:
            CompanyURLs with reception, approval, and authentication URLs
        """
        endpoint = f"{self._get_endpoint(company_id)}/urls"
        response = self.client.get(endpoint)
        return CompanyURLs(**response)

    @retry_request
    def accept_postulation(
        self,
        company_id: str,
        signed_xml: str,
        security_code: str,
    ) -> EnvironmentSwitchResponse:
        """Accept postulation to switch from TEST to CERT environment.

        After completing the test suite in the TEST environment,
        use this method to accept the postulation and transition
        the company to the CERT environment.

        Args:
            company_id: The company identifier
            signed_xml: The signed postulation XML from DGII portal
            security_code: Security code from DGII portal

        Returns:
            EnvironmentSwitchResponse with the new environment status

        Examples:
            >>> response = client.companies.accept_postulation(
            ...     company_id="company-uuid",
            ...     signed_xml="<xml>...</xml>",
            ...     security_code="ABC123"
            ... )
            >>> print(f"New environment: {response.new_environment}")
        """
        endpoint = f"{self._get_endpoint(company_id)}/accept-postulation"
        payload = {
            "signed_xml": signed_xml,
            "security_code": security_code,
        }
        response = self.client.post(endpoint, json=payload)
        return EnvironmentSwitchResponse(**response)

    @retry_request
    def sign_postulation(
        self,
        company_id: str,
        postulation_xml: bytes,
        filename: str = "postulacion.xml",
    ) -> XMLSigningResponse:
        """Sign a postulation XML using the company's certificate.

        Signs the postulation XML file for the first certification
        step (TEST -> CERT). This is a multipart file upload.

        Args:
            company_id: The company identifier
            postulation_xml: The postulation XML content as bytes
            filename: Filename for the uploaded XML (default: postulacion.xml)

        Returns:
            XMLSigningResponse with the signed XML content

        Examples:
            >>> with open("postulacion.xml", "rb") as f:
            ...     xml_content = f.read()
            >>> response = client.companies.sign_postulation(
            ...     company_id="company-uuid",
            ...     postulation_xml=xml_content
            ... )
            >>> print(f"Signed XML: {response.signed_xml[:100]}...")
        """
        endpoint = f"{self._get_endpoint(company_id)}/sign-postulation"
        files = {"postulation_xml": (filename, postulation_xml, "application/xml")}
        response = self.client.post(endpoint, files=files)
        return XMLSigningResponse(**response)

    @retry_request
    def sign_declaration(
        self,
        company_id: str,
        declaration_xml: bytes,
        filename: str = "declaracion.xml",
    ) -> XMLSigningResponse:
        """Sign a declaration XML using the company's certificate.

        Signs the declaration XML file for the final certification
        step (CERT -> PRD). This is a multipart file upload.

        Args:
            company_id: The company identifier
            declaration_xml: The declaration XML content as bytes
            filename: Filename for the uploaded XML (default: declaracion.xml)

        Returns:
            XMLSigningResponse with the signed XML content

        Examples:
            >>> with open("declaracion.xml", "rb") as f:
            ...     xml_content = f.read()
            >>> response = client.companies.sign_declaration(
            ...     company_id="company-uuid",
            ...     declaration_xml=xml_content
            ... )
            >>> print(f"Signed XML: {response.signed_xml[:100]}...")
        """
        endpoint = f"{self._get_endpoint(company_id)}/sign-declaration"
        files = {"declaration_xml": (filename, declaration_xml, "application/xml")}
        response = self.client.post(endpoint, files=files)
        return XMLSigningResponse(**response)

    @retry_request
    def accept_declaration(
        self,
        company_id: str,
        signed_xml: str,
        security_code: str,
    ) -> EnvironmentSwitchResponse:
        """Accept declaration to switch from CERT to PRD environment.

        After completing certification in the CERT environment,
        use this method to accept the declaration and transition
        the company to the production (PRD) environment.

        Args:
            company_id: The company identifier
            signed_xml: The signed declaration XML from DGII portal
            security_code: Security code from DGII portal

        Returns:
            EnvironmentSwitchResponse with the new environment status

        Examples:
            >>> response = client.companies.accept_declaration(
            ...     company_id="company-uuid",
            ...     signed_xml="<xml>...</xml>",
            ...     security_code="XYZ789"
            ... )
            >>> print(f"Company is now in: {response.new_environment}")
        """
        endpoint = f"{self._get_endpoint(company_id)}/accept-declaration"
        payload = {
            "signed_xml": signed_xml,
            "security_code": security_code,
        }
        response = self.client.post(endpoint, json=payload)
        return EnvironmentSwitchResponse(**response)

    @retry_request
    def validate_dgii_authorization(
        self,
        company_id: str,
    ) -> DGIIAuthorizationResponse:
        """Validate company's DGII certificate authorization.

        Checks with DGII whether the company's certificate is authorized
        for electronic document operations.

        Args:
            company_id: The company identifier

        Returns:
            DGIIAuthorizationResponse with authorization status

        Examples:
            >>> auth = client.companies.validate_dgii_authorization(
            ...     company_id="company-uuid"
            ... )
            >>> if auth.authorized:
            ...     print("Certificate is authorized")
            ... else:
            ...     print(f"Not authorized: {auth.message}")
        """
        endpoint = f"{self._get_endpoint(company_id)}/validate-dgii-authorization"
        response = self.client.post(endpoint)
        return DGIIAuthorizationResponse(**response)
