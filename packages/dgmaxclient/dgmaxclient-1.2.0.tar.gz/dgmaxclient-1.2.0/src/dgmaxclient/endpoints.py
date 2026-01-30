"""
API endpoint definitions for the DGMax client.

This module provides endpoint URL definitions for all DGMax API routes
using the api-client's @endpoint decorator pattern.
"""

from __future__ import annotations

from apiclient import endpoint


def create_endpoints(base_url: str) -> type:
    """Create endpoint class with full URLs using api-client's @endpoint decorator.

    This factory function creates a class decorated with @endpoint that automatically
    prepends the base_url to all endpoint paths.

    Args:
        base_url: The base URL for the DGMax API (e.g., https://api.dgmax.do)

    Returns:
        Endpoint class with complete URLs as class attributes

    Examples:
        >>> Endpoints = create_endpoints("https://api.dgmax.do")
        >>> Endpoints.companies
        'https://api.dgmax.do/api/v1/companies'
    """
    # Remove trailing slash from base URL if present
    base_url = base_url.rstrip("/")

    @endpoint(base_url=base_url)
    class Endpoints:
        """DGMax API endpoint definitions with full URLs.

        All endpoints are automatically prefixed with the base URL
        using the api-client @endpoint decorator.

        Attributes:
            companies: Company management endpoints
            fiscal_invoices: E31 fiscal invoice endpoints
            invoices: E32 invoice endpoints
            debit_notes: E33 debit note endpoints
            credit_notes: E34 credit note endpoints
            purchases: E41 purchase endpoints
            minor_expenses: E43 minor expense endpoints
            special_regimes: E44 special regime endpoints
            governmental: E45 governmental endpoints
            exports: E46 export endpoints
            payments_abroad: E47 payments abroad endpoints
            received_documents: Received documents endpoints
        """

        # Company endpoints
        companies = "/api/v1/companies"

        # Document type endpoints (E31-E47)
        fiscal_invoices = "/api/v1/fiscal-invoices"  # E31
        invoices = "/api/v1/invoices"  # E32
        debit_notes = "/api/v1/debit-notes"  # E33
        credit_notes = "/api/v1/credit-notes"  # E34
        purchases = "/api/v1/purchases"  # E41
        minor_expenses = "/api/v1/minor-expenses"  # E43
        special_regimes = "/api/v1/special-regimes"  # E44
        governmental = "/api/v1/governmental"  # E45
        exports = "/api/v1/exports"  # E46
        payments_abroad = "/api/v1/payments-abroad"  # E47

        # Received documents (receptor module)
        received_documents = "/api/v1/received-documents"
        commercial_approvals = "/api/v1/received-documents/commercial-approvals"
        approve_document = "/api/v1/received-documents/{id}/approve"
        reject_document = "/api/v1/received-documents/{id}/reject"

        # Certification workflow endpoints
        certification_provider_info = "/api/v1/certification/provider-info"
        certification_test_suites = "/api/v1/certification/test-suites"
        certification_test_suites_from_xls = (
            "/api/v1/certification/companies/{company_id}/test-suites/from-xls"
        )
        certification_commercial_approvals_from_xls = (
            "/api/v1/certification/companies/{company_id}/commercial-approvals/from-xls"
        )
        certification_commercial_approvals = (
            "/api/v1/certification/companies/{company_id}/commercial-approvals"
        )

    return Endpoints
