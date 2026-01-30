"""
Invoices resource (E32) for the DGMax client.

This module provides the resource class for E32 consumer invoice operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class InvoicesResource(DocumentResource):
    """Resource for E32 consumer invoice operations.

    E32 - Factura de Consumo Electrónica

    Used for B2C transactions (sales to final consumers).

    Note: Invoices below the RFCE threshold are processed synchronously
    and may return immediately with COMPLETED or FAILED status.

    Examples:
        >>> # List invoices
        >>> invoices = client.invoices.list()

        >>> # Create an invoice
        >>> invoice = client.invoices.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific invoice
        >>> invoice = client.invoices.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the invoices resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.invoices,
        )
