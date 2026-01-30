"""
Test fixtures for DGMaxClient tests.

This module provides pytest fixtures for unit and integration testing.
"""

from __future__ import annotations

import pytest

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from dgmaxclient import DGMaxClient

    DGMAXCLIENT_AVAILABLE = True
except ImportError:
    DGMaxClient = None  # type: ignore
    DGMAXCLIENT_AVAILABLE = False


@pytest.fixture
def api_key() -> str:
    """Return a test API key."""
    return "dgmax_test_key_12345"


@pytest.fixture
def base_url() -> str:
    """Return the test base URL."""
    return "https://api.dgmax.do"


@pytest.fixture
def client(api_key: str, base_url: str) -> DGMaxClient:
    """Create a DGMax client for testing."""
    return DGMaxClient(api_key=api_key, base_url=base_url)


@pytest.fixture
def sample_company() -> dict:
    """Return sample company data."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Company SRL",
        "trade_name": "Test Company",
        "rnc": "123456789",
        "email": "test@example.com",
        "address": "Calle Test #123",
        "branch": None,
        "municipality": "Santo Domingo",
        "province": "Distrito Nacional",
        "phone": "809-555-1234",
        "website": "https://testcompany.com",
        "logo": None,
        "type": "primary",
        "certificate": None,
        "dgii_environment": "test",
        "certification_status": "not_started",
        "parent_company_id": None,
    }


@pytest.fixture
def sample_document() -> dict:
    """Return sample electronic document data."""
    return {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "status": "COMPLETED",
        "rnc": "123456789",
        "encf": "E310000000001",
        "document_stamp_url": "https://dgii.gov.do/stamp/...",
        "security_code": "ABC123",
        "signature_date": "2024-01-15T10:30:00",
        "signed_xml": "documents/signed/E310000000001.xml",
        "resume_xml": None,
        "pdf": "documents/pdf/E310000000001.pdf",
        "queued_at": None,
        "referenced_document_id": None,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "external_status": {
            "codigo": "1",
            "estado": "Aceptado",
            "rnc": "123456789",
            "encf": "E310000000001",
            "secuencia_utilizada": True,
            "fecha_recepcion": "2024-01-15T10:35:00",
            "mensajes": [],
        },
    }


@pytest.fixture
def sample_received_document() -> dict:
    """Return sample received document data."""
    return {
        "id": "789e0123-e89b-12d3-a456-426614174000",
        "company_id": "123e4567-e89b-12d3-a456-426614174000",
        "rnc_emisor": "987654321",
        "rnc_comprador": "123456789",
        "e_ncf": "E310000000099",
        "status": "PENDING",
        "received_at": "2024-01-15T10:30:00Z",
        "xml_url": "https://storage.example.com/signed-url",
        "arecf_xml_url": None,
    }


@pytest.fixture
def sample_commercial_approval() -> dict:
    """Return sample commercial approval data."""
    return {
        "id": "abc12345-e89b-12d3-a456-426614174000",
        "company_id": "123e4567-e89b-12d3-a456-426614174000",
        "direction": "SENT",
        "rnc_emisor": "987654321",
        "rnc_comprador": "123456789",
        "e_ncf": "E310000000099",
        "fecha_emision": "2024-01-15",
        "monto_total": "1000.00",
        "approval_action": "APPROVED",
        "rejection_reason": None,
        "fecha_hora_aprobacion_comercial": "2024-01-15T10:30:00",
        "submission_status": "COMPLETED",
        "dgii_track_id": "track-123",
        "created_at": "2024-01-15T10:30:00Z",
        "received_document_id": "789e0123-e89b-12d3-a456-426614174000",
        "electronic_document_id": None,
        "acecf_xml_url": "https://storage.example.com/acecf-signed-url",
    }


@pytest.fixture
def paginated_response(sample_document: dict) -> dict:
    """Return a sample paginated response."""
    return {
        "count": 1,
        "results": [sample_document],
    }


@pytest.fixture
def paginated_companies_response(sample_company: dict) -> dict:
    """Return a sample paginated companies response."""
    return {
        "count": 1,
        "results": [sample_company],
    }


@pytest.fixture
def sample_provider_info() -> dict:
    """Return sample provider info data."""
    return {
        "software_type": "EXTERNO",
        "software_name": "DGMax",
        "software_version": "1.0.0",
        "provider": {
            "rnc": "123456789",
            "name": "Test Provider SRL",
            "trade_name": "Test Provider",
        },
    }


@pytest.fixture
def sample_test_suite() -> dict:
    """Return sample certification test suite data."""
    return {
        "id": "suite-uuid-12345",
        "company_id": "123e4567-e89b-12d3-a456-426614174000",
        "test_item": {
            "indicador_facturacion": 1,
            "nombre_item": "Producto de prueba",
            "descripcion_item": None,
            "indicador_bien_o_servicio": 1,
            "cantidad_item": "1",
            "precio_unitario_item": "1000.00",
        },
        "start_sequence": 1,
        "status": "generating",
        "certification_mode": "EXTERNO",
        "postulation_xml_signed": None,
        "postulation_signed_at": None,
        "declaracion_jurada_xml_signed": None,
        "declaracion_signed_at": None,
        "main_documents_zip": None,
        "resumenes_zip": None,
        "created_at": "2024-01-15T10:30:00Z",
        "completed_at": None,
        "test_cases": [
            {
                "id": "test-case-1",
                "test_type": "e31",
                "test_number": 1,
                "notes": None,
                "created_at": "2024-01-15T10:30:00Z",
                "electronic_document_id": None,
                "document_status": None,
            },
            {
                "id": "test-case-2",
                "test_type": "e32_consumo",
                "test_number": 2,
                "notes": None,
                "created_at": "2024-01-15T10:30:00Z",
                "electronic_document_id": None,
                "document_status": None,
            },
        ],
    }


@pytest.fixture
def sample_xml_signing_response() -> dict:
    """Return sample XML signing response data."""
    return {
        "signed_xml": "https://storage.example.com/signed.xml?token=abc",
        "security_code": "ABC123",
        "signature_date": "16-01-2026 08:36:04",
        "file_name": "202601163239770_signed.xml",
        "signed_xml_key": "company/uuid/assets/signed_xml/doc.xml",
    }


@pytest.fixture
def sample_environment_switch_response() -> dict:
    """Return sample environment switch response data."""
    return {
        "message": "Successfully switched to certification environment",
        "company_id": "123e4567-e89b-12d3-a456-426614174000",
        "previous_environment": "test",
        "current_environment": "cert",
        "certification_status": "postulation_accepted",
        "switched_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_commercial_approval_progress() -> dict:
    """Return sample certification commercial approval progress data."""
    return {
        "batch_id": "batch-uuid-12345",
        "batch_status": "completed",
        "total": 3,
        "pending": 0,
        "sent": 2,
        "failed": 1,
        "approvals": [
            {
                "id": "approval-uuid-1",
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "batch-uuid-12345",
                "rnc_emisor": "987654321",
                "e_ncf": "E310000000001",
                "fecha_emision": "2024-01-15",
                "monto_total": "1000.00",
                "approve": True,
                "rejection_reason": None,
                "status": "sent",
                "acecf_xml": "<xml>acecf</xml>",
                "dgii_response": "Aceptado",
                "error_detail": None,
                "created_at": "2024-01-15T10:30:00Z",
                "submitted_at": "2024-01-15T10:35:00Z",
            },
            {
                "id": "approval-uuid-2",
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "batch-uuid-12345",
                "rnc_emisor": "987654322",
                "e_ncf": "E310000000002",
                "fecha_emision": "2024-01-15",
                "monto_total": "2000.00",
                "approve": False,
                "rejection_reason": "1",
                "status": "sent",
                "acecf_xml": "<xml>acecf</xml>",
                "dgii_response": "Aceptado",
                "error_detail": None,
                "created_at": "2024-01-15T10:30:00Z",
                "submitted_at": "2024-01-15T10:35:00Z",
            },
            {
                "id": "approval-uuid-3",
                "company_id": "123e4567-e89b-12d3-a456-426614174000",
                "batch_id": "batch-uuid-12345",
                "rnc_emisor": "987654323",
                "e_ncf": "E310000000003",
                "fecha_emision": "2024-01-15",
                "monto_total": "3000.00",
                "approve": True,
                "rejection_reason": None,
                "status": "failed",
                "acecf_xml": None,
                "dgii_response": None,
                "error_detail": {"error": "Connection timeout"},
                "created_at": "2024-01-15T10:30:00Z",
                "submitted_at": None,
            },
        ],
    }


@pytest.fixture
def sample_dgii_authorization_response() -> dict:
    """Return sample DGII authorization response data."""
    return {
        "authorized": True,
        "message": "Certificate is authorized for electronic document operations",
        "dgii_response": "Autorizado",
        "status_code": 200,
    }


@pytest.fixture
def sample_dgii_authorization_not_authorized() -> dict:
    """Return sample DGII authorization response for not authorized case."""
    return {
        "authorized": False,
        "message": "Certificate is not authorized",
        "dgii_response": "No autorizado",
        "status_code": 403,
    }
