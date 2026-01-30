"""
Fiscal invoices resource (E31) for the DGMax client.

This module provides the resource class for E31 fiscal invoice operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class FiscalInvoicesResource(DocumentResource):
    """Resource for E31 fiscal invoice operations.

    E31 - Factura de Crédito Fiscal Electrónica

    Used for B2B transactions where the buyer needs tax credit.

    Examples:
        >>> # List fiscal invoices
        >>> invoices = client.fiscal_invoices.list()

        >>> # Create a fiscal invoice
        >>> invoice = client.fiscal_invoices.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "comprador": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific invoice
        >>> invoice = client.fiscal_invoices.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the fiscal invoices resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.fiscal_invoices,
        )
