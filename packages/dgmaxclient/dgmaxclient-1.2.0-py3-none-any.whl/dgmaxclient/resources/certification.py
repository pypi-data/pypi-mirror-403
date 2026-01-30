"""
Certification resource for the DGMax client.

This module provides the resource class for certification workflow operations,
including test suite management and provider info retrieval.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dgmaxclient.models.certification import (
    CertificationCommercialApprovalProgress,
    CertificationProviderInfoResponse,
    CertificationTestSuitePublic,
    TestItem,
)
from dgmaxclient.retrying import retry_request

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class CertificationResource:
    """Resource for certification workflow operations.

    Provides methods for managing the DGII certification process,
    including test suite creation and provider info retrieval.

    Examples:
        >>> # Get provider info for DGII portal registration
        >>> info = client.certification.get_provider_info()
        >>> print(f"Software: {info.software_name} v{info.software_version}")

        >>> # Create a test suite for certification (single item generates 20 docs)
        >>> from decimal import Decimal
        >>> suite = client.certification.create_test_suite(
        ...     company_id="company-uuid",
        ...     test_item=TestItem(
        ...         indicador_facturacion=1,
        ...         nombre_item="Producto de prueba",
        ...         precio_unitario_item=Decimal("1000.00"),
        ...     ),
        ...     start_sequence=1
        ... )
        >>> print(f"Test suite created: {suite.id}")

        >>> # Get test suite status
        >>> suite = client.certification.get_test_suite("suite-uuid")
        >>> print(f"Status: {suite.status}")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the certification resource.

        Args:
            client: The DGMax client instance
        """
        self.client = client

    @retry_request
    def get_provider_info(self) -> CertificationProviderInfoResponse:
        """Get provider information for DGII portal registration.

        Returns provider details needed when registering with the DGII
        portal for the certification process.

        Returns:
            CertificationProviderInfoResponse with provider details

        Examples:
            >>> info = client.certification.get_provider_info()
            >>> print(f"RNC: {info.provider.rnc}")
            >>> print(f"Name: {info.provider.name}")
        """
        endpoint = self.client.endpoints.certification_provider_info
        response = self.client.get(endpoint)
        return CertificationProviderInfoResponse(**response)

    @retry_request
    def create_test_suite(
        self,
        company_id: str,
        test_item: dict[str, Any] | TestItem,
        start_sequence: int = 1,
    ) -> CertificationTestSuitePublic:
        """Create a certification test suite.

        Creates a test suite with a single test item that generates
        all 20 certification documents (10 main + 10 resúmenes).

        Args:
            company_id: The company to create the test suite for
            test_item: Test item with product details for document generation
            start_sequence: Starting sequence number for documents

        Returns:
            CertificationTestSuitePublic with the created test suite

        Examples:
            >>> # Using TestItem model
            >>> from decimal import Decimal
            >>> suite = client.certification.create_test_suite(
            ...     company_id="company-uuid",
            ...     test_item=TestItem(
            ...         indicador_facturacion=1,
            ...         nombre_item="Producto de prueba",
            ...         precio_unitario_item=Decimal("1000.00"),
            ...     ),
            ...     start_sequence=100
            ... )

            >>> # Using dict
            >>> suite = client.certification.create_test_suite(
            ...     company_id="company-uuid",
            ...     test_item={
            ...         "indicador_facturacion": 1,
            ...         "nombre_item": "Producto de prueba",
            ...         "precio_unitario_item": "1000.00",
            ...     }
            ... )
        """
        endpoint = self.client.endpoints.certification_test_suites

        # Convert TestItem model to dict if needed
        if hasattr(test_item, "model_dump"):
            item_data = test_item.model_dump()
        else:
            item_data = test_item

        payload = {
            "company_id": company_id,
            "test_item": item_data,
            "start_sequence": start_sequence,
        }

        response = self.client.post(endpoint, json=payload)
        return CertificationTestSuitePublic(**response)

    @retry_request
    def get_test_suite(self, suite_id: str) -> CertificationTestSuitePublic:
        """Get a certification test suite by ID.

        Args:
            suite_id: The test suite identifier

        Returns:
            CertificationTestSuitePublic with the test suite details

        Examples:
            >>> suite = client.certification.get_test_suite("suite-uuid")
            >>> print(f"Status: {suite.status}")
            >>> print(f"Test cases: {len(suite.test_cases)}")
        """
        endpoint = f"{self.client.endpoints.certification_test_suites}/{suite_id}"
        response = self.client.get(endpoint)
        return CertificationTestSuitePublic(**response)

    @retry_request
    def create_test_suite_from_xls(
        self,
        company_id: str,
        xls_file: bytes,
        filename: str = "pruebas.xlsx",
    ) -> CertificationTestSuitePublic:
        """Create test suite from DGII XLS file (Paso 2: Pruebas de Datos).

        Parses the DGII-provided Excel file containing test cases and
        creates a test suite with all required documents.

        Args:
            company_id: The company to create the test suite for
            xls_file: The XLS file content as bytes
            filename: Filename for the uploaded XLS (default: pruebas.xlsx)

        Returns:
            CertificationTestSuitePublic with the created test suite

        Examples:
            >>> with open("pruebas.xlsx", "rb") as f:
            ...     xls_content = f.read()
            >>> suite = client.certification.create_test_suite_from_xls(
            ...     company_id="company-uuid",
            ...     xls_file=xls_content
            ... )
            >>> print(f"Test suite created: {suite.id}")
        """
        endpoint = self.client.endpoints.certification_test_suites_from_xls.format(
            company_id=company_id
        )
        files = {
            "xls_file": (
                filename,
                xls_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        response = self.client.post(endpoint, files=files)
        return CertificationTestSuitePublic(**response)

    @retry_request
    def create_commercial_approvals_from_xls(
        self,
        company_id: str,
        xls_file: bytes,
        filename: str = "aprobaciones.xlsx",
    ) -> CertificationCommercialApprovalProgress:
        """Create commercial approvals from DGII XLS file (Paso 3).

        Parses the DGII-provided Excel file containing commercial approval
        test cases and creates approvals for all documents.

        Args:
            company_id: The company to create approvals for
            xls_file: The XLS file content as bytes
            filename: Filename for the uploaded XLS (default: aprobaciones.xlsx)

        Returns:
            CertificationCommercialApprovalProgress with created approvals

        Examples:
            >>> with open("aprobaciones.xlsx", "rb") as f:
            ...     xls_content = f.read()
            >>> progress = client.certification.create_commercial_approvals_from_xls(
            ...     company_id="company-uuid",
            ...     xls_file=xls_content
            ... )
            >>> print(f"Created {progress.total} approvals")
        """
        endpoint = (
            self.client.endpoints.certification_commercial_approvals_from_xls.format(
                company_id=company_id
            )
        )
        files = {
            "xls_file": (
                filename,
                xls_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        response = self.client.post(endpoint, files=files)
        return CertificationCommercialApprovalProgress(**response)

    @retry_request
    def get_commercial_approvals(
        self,
        company_id: str,
    ) -> CertificationCommercialApprovalProgress:
        """Get commercial approvals progress (Paso 3).

        Retrieves the current status and progress of commercial approvals
        for a company during the certification process.

        Args:
            company_id: The company identifier

        Returns:
            CertificationCommercialApprovalProgress with current status

        Examples:
            >>> progress = client.certification.get_commercial_approvals(
            ...     company_id="company-uuid"
            ... )
            >>> print(f"Sent: {progress.sent}/{progress.total}")
            >>> print(f"Failed: {progress.failed}")
        """
        endpoint = self.client.endpoints.certification_commercial_approvals.format(
            company_id=company_id
        )
        response = self.client.get(endpoint)
        return CertificationCommercialApprovalProgress(**response)
