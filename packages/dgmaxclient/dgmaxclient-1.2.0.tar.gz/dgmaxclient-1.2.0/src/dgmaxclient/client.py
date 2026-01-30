"""
Main client for the DGMax API.

This module provides the main DGMaxClient class for interacting
with the DGMax electronic fiscal document API.
"""

from __future__ import annotations

from typing import Any

from apiclient import APIClient, JsonResponseHandler

from dgmaxclient.authentication import ApiKeyAuthentication
from dgmaxclient.endpoints import create_endpoints
from dgmaxclient.error_handlers import DGMaxErrorHandler
from dgmaxclient.request_strategies import DGMaxRequestStrategy
from dgmaxclient.resources.certification import CertificationResource
from dgmaxclient.resources.companies import CompaniesResource
from dgmaxclient.resources.credit_notes import CreditNotesResource
from dgmaxclient.resources.debit_notes import DebitNotesResource
from dgmaxclient.resources.exports import ExportsResource
from dgmaxclient.resources.fiscal_invoices import FiscalInvoicesResource
from dgmaxclient.resources.governmental import GovernmentalResource
from dgmaxclient.resources.invoices import InvoicesResource
from dgmaxclient.resources.minor_expenses import MinorExpensesResource
from dgmaxclient.resources.payments_abroad import PaymentsAbroadResource
from dgmaxclient.resources.purchases import PurchasesResource
from dgmaxclient.resources.received_documents import ReceivedDocumentsResource
from dgmaxclient.resources.special_regimes import SpecialRegimesResource

DEFAULT_BASE_URL = "https://api.dgmax.do"
DEFAULT_TIMEOUT = 30


class DGMaxClient(APIClient):
    """Client for interacting with the DGMax API.

    This client provides typed access to all DGMax API endpoints for
    electronic fiscal document processing in the Dominican Republic.

    Attributes:
        companies: Company management resource
        certification: Certification workflow resource
        fiscal_invoices: E31 fiscal invoice resource
        invoices: E32 consumer invoice resource
        debit_notes: E33 debit note resource
        credit_notes: E34 credit note resource
        purchases: E41 purchase document resource
        minor_expenses: E43 minor expense resource
        special_regimes: E44 special regime resource
        governmental: E45 governmental document resource
        exports: E46 export document resource
        payments_abroad: E47 foreign payment resource
        received_documents: Received documents resource

    Examples:
        >>> from dgmaxclient import DGMaxClient
        >>>
        >>> # Initialize the client
        >>> client = DGMaxClient(api_key="dgmax_xxx")
        >>>
        >>> # List companies
        >>> companies = client.companies.list()
        >>> for company in companies.results:
        ...     print(f"{company.name} ({company.rnc})")
        >>>
        >>> # Create an invoice
        >>> invoice = client.invoices.create({
        ...     "encabezado": {...},
        ...     "detalles": {...}
        ... })
        >>> print(f"Invoice created: {invoice.encf}")
        >>>
        >>> # List received documents
        >>> received = client.received_documents.list()
        >>> for doc in received.results:
        ...     print(f"{doc.e_ncf} from {doc.rnc_emisor}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the DGMax client.

        Args:
            api_key: Your DGMax API key (format: dgmax_xxx)
            base_url: The base URL for the API (default: https://api.dgmax.do)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            DGMaxAuthenticationError: If the API key is invalid

        Examples:
            >>> # Basic usage
            >>> client = DGMaxClient(api_key="dgmax_xxx")
            >>>
            >>> # Custom base URL (for testing)
            >>> client = DGMaxClient(
            ...     api_key="dgmax_xxx",
            ...     base_url="https://staging.dgmax.do"
            ... )
            >>>
            >>> # Custom timeout
            >>> client = DGMaxClient(
            ...     api_key="dgmax_xxx",
            ...     timeout=60
            ... )
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

        # Initialize endpoints
        self.endpoints = create_endpoints(self._base_url)

        # Initialize the API client
        super().__init__(
            authentication_method=ApiKeyAuthentication(api_key=api_key),
            response_handler=JsonResponseHandler,
            error_handler=DGMaxErrorHandler,
            request_strategy=DGMaxRequestStrategy(),
        )

        # Set timeout
        self.set_timeout(timeout)

        # Initialize resources
        self._init_resources()

    def _init_resources(self) -> None:
        """Initialize API resources."""
        self.companies = CompaniesResource(self)
        self.certification = CertificationResource(self)
        self.fiscal_invoices = FiscalInvoicesResource(self)
        self.invoices = InvoicesResource(self)
        self.debit_notes = DebitNotesResource(self)
        self.credit_notes = CreditNotesResource(self)
        self.purchases = PurchasesResource(self)
        self.minor_expenses = MinorExpensesResource(self)
        self.special_regimes = SpecialRegimesResource(self)
        self.governmental = GovernmentalResource(self)
        self.exports = ExportsResource(self)
        self.payments_abroad = PaymentsAbroadResource(self)
        self.received_documents = ReceivedDocumentsResource(self)

    @property
    def base_url(self) -> str:
        """Get the base URL for the API."""
        return self._base_url

    @property
    def timeout(self) -> int:
        """Get the current timeout setting."""
        return self._timeout

    def set_timeout(self, timeout: int) -> None:
        """Set the request timeout.

        Args:
            timeout: Timeout in seconds
        """
        self._timeout = timeout

    def get_request_timeout(self) -> float:
        """Return the number of seconds before the request times out.

        Overrides the base APIClient method to use our configured timeout.

        Returns:
            Timeout in seconds
        """
        return float(self._timeout)

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request to the API.

        Args:
            endpoint: The API endpoint
            params: Query parameters

        Returns:
            The parsed JSON response
        """
        return super().get(endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make a POST request to the API.

        Args:
            endpoint: The API endpoint
            data: Form data
            json: JSON payload
            **kwargs: Additional arguments

        Returns:
            The parsed JSON response
        """
        return super().post(endpoint, data=data, json=json, **kwargs)

    def patch(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make a PATCH request to the API.

        Args:
            endpoint: The API endpoint
            data: Form data
            json: JSON payload
            **kwargs: Additional arguments

        Returns:
            The parsed JSON response
        """
        return super().patch(endpoint, data=data, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> Any:
        """Make a DELETE request to the API.

        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments

        Returns:
            The parsed JSON response (if any)
        """
        return super().delete(endpoint, **kwargs)

    def close(self) -> None:
        """Close the client and release resources.

        This closes the underlying HTTP session. After calling this method,
        the client should not be used for further requests.

        Examples:
            >>> client = DGMaxClient(api_key="dgmax_xxx")
            >>> try:
            ...     result = client.companies.list()
            ... finally:
            ...     client.close()
        """
        session = self.get_session()
        if session is not None:
            session.close()

    def __enter__(self) -> DGMaxClient:
        """Enter the context manager.

        Returns:
            The client instance
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager and close resources."""
        self.close()

    def __repr__(self) -> str:
        """Return a string representation of the client."""
        return "DGMaxClient()"
