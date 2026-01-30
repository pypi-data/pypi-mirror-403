"""Unit tests for DGMax certification resources and models."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from dgmaxclient import DGMaxClient
from dgmaxclient.models import (
    CertificationCommercialApprovalBatchStatus,
    CertificationCommercialApprovalProgress,
    CertificationCommercialApprovalStatus,
    CertificationProviderInfoResponse,
    CertificationTestSuitePublic,
    DGIIAuthorizationResponse,
    EnvironmentSwitchResponse,
    TestItem,
    TestSuiteStatus,
    XMLSigningResponse,
)
from dgmaxclient.resources.certification import CertificationResource
from dgmaxclient.resources.companies import CompaniesResource


class TestCertificationResource:
    """Tests for CertificationResource methods."""

    def test_get_provider_info(
        self, client: DGMaxClient, sample_provider_info: dict
    ) -> None:
        """Test get_provider_info returns CertificationProviderInfoResponse."""
        with patch.object(client, "get", return_value=sample_provider_info):
            info = client.certification.get_provider_info()

        assert isinstance(info, CertificationProviderInfoResponse)
        assert info.software_type == "EXTERNO"
        assert info.software_name == "DGMax"
        assert info.provider.rnc == "123456789"
        assert info.provider.name == "Test Provider SRL"

    def test_get_provider_info_builds_correct_endpoint(
        self, client: DGMaxClient, sample_provider_info: dict
    ) -> None:
        """Test that get_provider_info calls the correct endpoint."""
        with patch.object(
            client, "get", return_value=sample_provider_info
        ) as mock_get:
            client.certification.get_provider_info()

        expected_endpoint = "https://api.dgmax.do/api/v1/certification/provider-info"
        mock_get.assert_called_once_with(expected_endpoint)

    def test_create_test_suite(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test create_test_suite returns CertificationTestSuitePublic."""
        with patch.object(client, "post", return_value=sample_test_suite):
            suite = client.certification.create_test_suite(
                company_id="123e4567-e89b-12d3-a456-426614174000",
                test_item=TestItem(
                    indicador_facturacion=1,
                    nombre_item="Producto de prueba",
                    precio_unitario_item=Decimal("1000.00"),
                ),
                start_sequence=1,
            )

        assert isinstance(suite, CertificationTestSuitePublic)
        assert suite.id == "suite-uuid-12345"
        assert suite.status == TestSuiteStatus.GENERATING

    def test_create_test_suite_with_dict(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test create_test_suite accepts dict item."""
        with patch.object(client, "post", return_value=sample_test_suite) as mock_post:
            client.certification.create_test_suite(
                company_id="123e4567-e89b-12d3-a456-426614174000",
                test_item={
                    "indicador_facturacion": 1,
                    "nombre_item": "Producto de prueba",
                    "precio_unitario_item": "1000.00",
                },
            )

        # Verify the payload was constructed correctly
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["company_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert payload["test_item"]["nombre_item"] == "Producto de prueba"
        assert payload["start_sequence"] == 1

    def test_create_test_suite_builds_correct_endpoint(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test that create_test_suite calls the correct endpoint."""
        with patch.object(
            client, "post", return_value=sample_test_suite
        ) as mock_post:
            client.certification.create_test_suite(
                company_id="123e4567-e89b-12d3-a456-426614174000",
                test_item={
                    "indicador_facturacion": 1,
                    "nombre_item": "Test",
                    "precio_unitario_item": "100.00",
                },
            )

        expected_endpoint = "https://api.dgmax.do/api/v1/certification/test-suites"
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_get_test_suite(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test get_test_suite returns CertificationTestSuitePublic."""
        suite_id = "suite-uuid-12345"

        with patch.object(client, "get", return_value=sample_test_suite):
            suite = client.certification.get_test_suite(suite_id)

        assert isinstance(suite, CertificationTestSuitePublic)
        assert suite.id == suite_id
        assert len(suite.test_cases) == 2

    def test_get_test_suite_builds_correct_endpoint(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test that get_test_suite calls the correct endpoint."""
        suite_id = "suite-uuid-12345"

        with patch.object(
            client, "get", return_value=sample_test_suite
        ) as mock_get:
            client.certification.get_test_suite(suite_id)

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/certification/test-suites/{suite_id}"
        )
        mock_get.assert_called_once_with(expected_endpoint)

    def test_get_provider_info_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that get_provider_info method has retry decorator applied."""
        method = CertificationResource.get_provider_info
        assert hasattr(method, "retry")

    def test_create_test_suite_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that create_test_suite method has retry decorator applied."""
        method = CertificationResource.create_test_suite
        assert hasattr(method, "retry")

    def test_get_test_suite_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that get_test_suite method has retry decorator applied."""
        method = CertificationResource.get_test_suite
        assert hasattr(method, "retry")


class TestCompanyCertificationMethods:
    """Tests for company certification-related methods."""

    def test_accept_postulation(
        self, client: DGMaxClient, sample_environment_switch_response: dict
    ) -> None:
        """Test accept_postulation returns EnvironmentSwitchResponse."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_environment_switch_response
        ):
            response = client.companies.accept_postulation(
                company_id=company_id,
                signed_xml="<xml>signed</xml>",
                security_code="ABC123",
            )

        assert isinstance(response, EnvironmentSwitchResponse)
        assert response.current_environment == "cert"
        assert response.previous_environment == "test"
        assert response.certification_status == "postulation_accepted"

    def test_accept_postulation_builds_correct_endpoint(
        self, client: DGMaxClient, sample_environment_switch_response: dict
    ) -> None:
        """Test that accept_postulation calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_environment_switch_response
        ) as mock_post:
            client.companies.accept_postulation(
                company_id=company_id,
                signed_xml="<xml>signed</xml>",
                security_code="ABC123",
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/companies/{company_id}/accept-postulation"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_accept_postulation_payload(
        self, client: DGMaxClient, sample_environment_switch_response: dict
    ) -> None:
        """Test that accept_postulation sends correct payload."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_environment_switch_response
        ) as mock_post:
            client.companies.accept_postulation(
                company_id=company_id,
                signed_xml="<xml>signed</xml>",
                security_code="ABC123",
            )

        payload = mock_post.call_args[1]["json"]
        assert payload["signed_xml"] == "<xml>signed</xml>"
        assert payload["security_code"] == "ABC123"

    def test_sign_postulation(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test sign_postulation returns XMLSigningResponse."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>postulation</xml>"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ):
            response = client.companies.sign_postulation(
                company_id=company_id,
                postulation_xml=xml_content,
            )

        assert isinstance(response, XMLSigningResponse)
        assert "storage.example.com" in response.signed_xml
        assert response.security_code == "ABC123"
        assert response.file_name == "202601163239770_signed.xml"

    def test_sign_postulation_builds_correct_endpoint(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test that sign_postulation calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>postulation</xml>"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ) as mock_post:
            client.companies.sign_postulation(
                company_id=company_id,
                postulation_xml=xml_content,
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/companies/{company_id}/sign-postulation"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_sign_postulation_multipart_upload(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test that sign_postulation sends multipart file upload."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>postulation</xml>"
        filename = "mi_postulacion.xml"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ) as mock_post:
            client.companies.sign_postulation(
                company_id=company_id,
                postulation_xml=xml_content,
                filename=filename,
            )

        files = mock_post.call_args[1]["files"]
        assert "postulation_xml" in files
        assert files["postulation_xml"][0] == filename
        assert files["postulation_xml"][1] == xml_content
        assert files["postulation_xml"][2] == "application/xml"

    def test_sign_declaration(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test sign_declaration returns XMLSigningResponse."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>declaration</xml>"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ):
            response = client.companies.sign_declaration(
                company_id=company_id,
                declaration_xml=xml_content,
            )

        assert isinstance(response, XMLSigningResponse)
        assert "storage.example.com" in response.signed_xml
        assert response.security_code == "ABC123"
        assert response.file_name == "202601163239770_signed.xml"

    def test_sign_declaration_builds_correct_endpoint(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test that sign_declaration calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>declaration</xml>"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ) as mock_post:
            client.companies.sign_declaration(
                company_id=company_id,
                declaration_xml=xml_content,
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/companies/{company_id}/sign-declaration"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_sign_declaration_multipart_upload(
        self, client: DGMaxClient, sample_xml_signing_response: dict
    ) -> None:
        """Test that sign_declaration sends multipart file upload."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xml_content = b"<xml>declaration</xml>"
        filename = "mi_declaracion.xml"

        with patch.object(
            client, "post", return_value=sample_xml_signing_response
        ) as mock_post:
            client.companies.sign_declaration(
                company_id=company_id,
                declaration_xml=xml_content,
                filename=filename,
            )

        files = mock_post.call_args[1]["files"]
        assert "declaration_xml" in files
        assert files["declaration_xml"][0] == filename
        assert files["declaration_xml"][1] == xml_content
        assert files["declaration_xml"][2] == "application/xml"

    def test_accept_declaration(
        self, client: DGMaxClient, sample_environment_switch_response: dict
    ) -> None:
        """Test accept_declaration returns EnvironmentSwitchResponse."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        # Modify response for PRD environment
        prd_response = {
            **sample_environment_switch_response,
            "previous_environment": "cert",
            "current_environment": "prd",
            "certification_status": "certified",
            "message": "Company is now in production",
        }

        with patch.object(client, "post", return_value=prd_response):
            response = client.companies.accept_declaration(
                company_id=company_id,
                signed_xml="<xml>signed</xml>",
                security_code="XYZ789",
            )

        assert isinstance(response, EnvironmentSwitchResponse)
        assert response.current_environment == "prd"
        assert response.previous_environment == "cert"
        assert response.certification_status == "certified"

    def test_accept_declaration_builds_correct_endpoint(
        self, client: DGMaxClient, sample_environment_switch_response: dict
    ) -> None:
        """Test that accept_declaration calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_environment_switch_response
        ) as mock_post:
            client.companies.accept_declaration(
                company_id=company_id,
                signed_xml="<xml>signed</xml>",
                security_code="XYZ789",
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/companies/{company_id}/accept-declaration"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_accept_postulation_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that accept_postulation method has retry decorator applied."""
        method = CompaniesResource.accept_postulation
        assert hasattr(method, "retry")

    def test_sign_postulation_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that sign_postulation method has retry decorator applied."""
        method = CompaniesResource.sign_postulation
        assert hasattr(method, "retry")

    def test_sign_declaration_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that sign_declaration method has retry decorator applied."""
        method = CompaniesResource.sign_declaration
        assert hasattr(method, "retry")

    def test_accept_declaration_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that accept_declaration method has retry decorator applied."""
        method = CompaniesResource.accept_declaration
        assert hasattr(method, "retry")

    def test_accept_postulation_invalid_company_id(
        self, client: DGMaxClient
    ) -> None:
        """Test accept_postulation with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.accept_postulation(
                company_id="invalid-id",
                signed_xml="<xml>signed</xml>",
                security_code="ABC123",
            )

    def test_sign_postulation_invalid_company_id(
        self, client: DGMaxClient
    ) -> None:
        """Test sign_postulation with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.sign_postulation(
                company_id="invalid-id",
                postulation_xml=b"<xml>postulation</xml>",
            )

    def test_sign_declaration_invalid_company_id(
        self, client: DGMaxClient
    ) -> None:
        """Test sign_declaration with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.sign_declaration(
                company_id="invalid-id",
                declaration_xml=b"<xml>declaration</xml>",
            )

    def test_accept_declaration_invalid_company_id(
        self, client: DGMaxClient
    ) -> None:
        """Test accept_declaration with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.accept_declaration(
                company_id="invalid-id",
                signed_xml="<xml>signed</xml>",
                security_code="XYZ789",
            )


class TestCertificationModels:
    """Tests for certification model validation."""

    def test_test_item_model(self) -> None:
        """Test TestItem model creation."""
        item = TestItem(
            indicador_facturacion=1,
            nombre_item="Test Product",
            precio_unitario_item=Decimal("1000.00"),
        )
        assert item.indicador_facturacion == 1
        assert item.nombre_item == "Test Product"
        assert item.precio_unitario_item == Decimal("1000.00")

    def test_test_item_defaults(self) -> None:
        """Test TestItem default values."""
        item = TestItem(
            indicador_facturacion=1,
            nombre_item="Test",
            precio_unitario_item=Decimal("100.00"),
        )
        assert item.indicador_bien_o_servicio == 1
        assert item.cantidad_item == "1"
        assert item.descripcion_item is None

    def test_test_suite_status_enum(self) -> None:
        """Test TestSuiteStatus enum values."""
        assert TestSuiteStatus.GENERATING == "generating"
        assert TestSuiteStatus.READY_FOR_UPLOAD == "ready_for_upload"
        assert TestSuiteStatus.APPROVED == "approved"
        assert TestSuiteStatus.REJECTED == "rejected"


class TestClientCertificationResource:
    """Tests for certification resource initialization in client."""

    def test_client_has_certification_resource(
        self, client: DGMaxClient
    ) -> None:
        """Test that client has certification resource initialized."""
        assert hasattr(client, "certification")
        assert isinstance(client.certification, CertificationResource)

    def test_certification_resource_has_client(
        self, client: DGMaxClient
    ) -> None:
        """Test that certification resource has reference to client."""
        assert client.certification.client is client


class TestCertificationXLSOperations:
    """Tests for XLS-based certification operations."""

    def test_create_test_suite_from_xls(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test create_test_suite_from_xls returns CertificationTestSuitePublic."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"

        with patch.object(client, "post", return_value=sample_test_suite):
            suite = client.certification.create_test_suite_from_xls(
                company_id=company_id,
                xls_file=xls_content,
            )

        assert isinstance(suite, CertificationTestSuitePublic)
        assert suite.id == "suite-uuid-12345"
        assert suite.status == TestSuiteStatus.GENERATING

    def test_create_test_suite_from_xls_builds_correct_endpoint(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test that create_test_suite_from_xls calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"

        with patch.object(
            client, "post", return_value=sample_test_suite
        ) as mock_post:
            client.certification.create_test_suite_from_xls(
                company_id=company_id,
                xls_file=xls_content,
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/certification/companies/{company_id}"
            "/test-suites/from-xls"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_create_test_suite_from_xls_multipart_upload(
        self, client: DGMaxClient, sample_test_suite: dict
    ) -> None:
        """Test that create_test_suite_from_xls sends multipart file upload."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"
        filename = "custom_pruebas.xlsx"

        with patch.object(
            client, "post", return_value=sample_test_suite
        ) as mock_post:
            client.certification.create_test_suite_from_xls(
                company_id=company_id,
                xls_file=xls_content,
                filename=filename,
            )

        files = mock_post.call_args[1]["files"]
        assert "xls_file" in files
        assert files["xls_file"][0] == filename
        assert files["xls_file"][1] == xls_content
        assert (
            files["xls_file"][2]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_create_commercial_approvals_from_xls(
        self, client: DGMaxClient, sample_commercial_approval_progress: dict
    ) -> None:
        """Test create_commercial_approvals_from_xls returns progress model."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"

        with patch.object(
            client, "post", return_value=sample_commercial_approval_progress
        ):
            progress = client.certification.create_commercial_approvals_from_xls(
                company_id=company_id,
                xls_file=xls_content,
            )

        assert isinstance(progress, CertificationCommercialApprovalProgress)
        assert progress.total == 3
        assert progress.sent == 2
        assert progress.failed == 1
        assert (
            progress.batch_status
            == CertificationCommercialApprovalBatchStatus.COMPLETED
        )

    def test_create_commercial_approvals_from_xls_builds_correct_endpoint(
        self, client: DGMaxClient, sample_commercial_approval_progress: dict
    ) -> None:
        """Test that create_commercial_approvals_from_xls calls correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"

        with patch.object(
            client, "post", return_value=sample_commercial_approval_progress
        ) as mock_post:
            client.certification.create_commercial_approvals_from_xls(
                company_id=company_id,
                xls_file=xls_content,
            )

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/certification/companies/{company_id}"
            "/commercial-approvals/from-xls"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_create_commercial_approvals_from_xls_multipart_upload(
        self, client: DGMaxClient, sample_commercial_approval_progress: dict
    ) -> None:
        """Test that create_commercial_approvals_from_xls sends multipart upload."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"
        xls_content = b"fake xls content"
        filename = "custom_aprobaciones.xlsx"

        with patch.object(
            client, "post", return_value=sample_commercial_approval_progress
        ) as mock_post:
            client.certification.create_commercial_approvals_from_xls(
                company_id=company_id,
                xls_file=xls_content,
                filename=filename,
            )

        files = mock_post.call_args[1]["files"]
        assert "xls_file" in files
        assert files["xls_file"][0] == filename
        assert files["xls_file"][1] == xls_content

    def test_get_commercial_approvals(
        self, client: DGMaxClient, sample_commercial_approval_progress: dict
    ) -> None:
        """Test get_commercial_approvals returns progress model."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "get", return_value=sample_commercial_approval_progress
        ):
            progress = client.certification.get_commercial_approvals(
                company_id=company_id
            )

        assert isinstance(progress, CertificationCommercialApprovalProgress)
        assert progress.total == 3
        assert len(progress.approvals) == 3

    def test_get_commercial_approvals_builds_correct_endpoint(
        self, client: DGMaxClient, sample_commercial_approval_progress: dict
    ) -> None:
        """Test that get_commercial_approvals calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "get", return_value=sample_commercial_approval_progress
        ) as mock_get:
            client.certification.get_commercial_approvals(company_id=company_id)

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/certification/companies/{company_id}"
            "/commercial-approvals"
        )
        mock_get.assert_called_once_with(expected_endpoint)

    def test_create_test_suite_from_xls_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that create_test_suite_from_xls has retry decorator applied."""
        method = CertificationResource.create_test_suite_from_xls
        assert hasattr(method, "retry")

    def test_create_commercial_approvals_from_xls_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that create_commercial_approvals_from_xls has retry decorator."""
        method = CertificationResource.create_commercial_approvals_from_xls
        assert hasattr(method, "retry")

    def test_get_commercial_approvals_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that get_commercial_approvals has retry decorator applied."""
        method = CertificationResource.get_commercial_approvals
        assert hasattr(method, "retry")


class TestCertificationCommercialApprovalModels:
    """Tests for certification commercial approval model validation."""

    def test_commercial_approval_status_enum(self) -> None:
        """Test CertificationCommercialApprovalStatus enum values."""
        assert CertificationCommercialApprovalStatus.PENDING == "pending"
        assert CertificationCommercialApprovalStatus.SENT == "sent"
        assert CertificationCommercialApprovalStatus.FAILED == "failed"

    def test_commercial_approval_batch_status_enum(self) -> None:
        """Test CertificationCommercialApprovalBatchStatus enum values."""
        assert CertificationCommercialApprovalBatchStatus.PENDING == "pending"
        assert CertificationCommercialApprovalBatchStatus.SUBMITTING == "submitting"
        assert CertificationCommercialApprovalBatchStatus.COMPLETED == "completed"
        assert CertificationCommercialApprovalBatchStatus.FAILED == "failed"

    def test_commercial_approval_progress_model(
        self, sample_commercial_approval_progress: dict
    ) -> None:
        """Test CertificationCommercialApprovalProgress model creation."""
        progress = CertificationCommercialApprovalProgress(
            **sample_commercial_approval_progress
        )
        assert progress.batch_id == "batch-uuid-12345"
        assert (
            progress.batch_status
            == CertificationCommercialApprovalBatchStatus.COMPLETED
        )
        assert progress.total == 3
        assert progress.pending == 0
        assert progress.sent == 2
        assert progress.failed == 1
        assert len(progress.approvals) == 3

    def test_commercial_approval_progress_approvals_parsed(
        self, sample_commercial_approval_progress: dict
    ) -> None:
        """Test that approvals are properly parsed in progress model."""
        progress = CertificationCommercialApprovalProgress(
            **sample_commercial_approval_progress
        )
        first_approval = progress.approvals[0]
        assert first_approval.id == "approval-uuid-1"
        assert first_approval.rnc_emisor == "987654321"
        assert first_approval.approve is True
        assert first_approval.status == CertificationCommercialApprovalStatus.SENT


class TestValidateDGIIAuthorization:
    """Tests for validate_dgii_authorization method."""

    def test_validate_dgii_authorization(
        self, client: DGMaxClient, sample_dgii_authorization_response: dict
    ) -> None:
        """Test validate_dgii_authorization returns DGIIAuthorizationResponse."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_dgii_authorization_response
        ):
            response = client.companies.validate_dgii_authorization(
                company_id=company_id
            )

        assert isinstance(response, DGIIAuthorizationResponse)
        assert response.authorized is True
        assert (
            response.message
            == "Certificate is authorized for electronic document operations"
        )
        assert response.dgii_response == "Autorizado"
        assert response.status_code == 200

    def test_validate_dgii_authorization_builds_correct_endpoint(
        self, client: DGMaxClient, sample_dgii_authorization_response: dict
    ) -> None:
        """Test that validate_dgii_authorization calls the correct endpoint."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_dgii_authorization_response
        ) as mock_post:
            client.companies.validate_dgii_authorization(company_id=company_id)

        expected_endpoint = (
            f"https://api.dgmax.do/api/v1/companies/{company_id}"
            "/validate-dgii-authorization"
        )
        assert mock_post.call_args[0][0] == expected_endpoint

    def test_validate_dgii_authorization_not_authorized(
        self, client: DGMaxClient, sample_dgii_authorization_not_authorized: dict
    ) -> None:
        """Test validate_dgii_authorization with not authorized response."""
        company_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch.object(
            client, "post", return_value=sample_dgii_authorization_not_authorized
        ):
            response = client.companies.validate_dgii_authorization(
                company_id=company_id
            )

        assert response.authorized is False
        assert response.message == "Certificate is not authorized"

    def test_validate_dgii_authorization_has_retry_decorator(
        self, client: DGMaxClient
    ) -> None:
        """Test that validate_dgii_authorization has retry decorator applied."""
        method = CompaniesResource.validate_dgii_authorization
        assert hasattr(method, "retry")

    def test_validate_dgii_authorization_invalid_company_id(
        self, client: DGMaxClient
    ) -> None:
        """Test validate_dgii_authorization with invalid company ID format."""
        with pytest.raises(ValueError, match="Invalid resource ID format"):
            client.companies.validate_dgii_authorization(company_id="invalid-id")
