"""
Purchases resource (E41) for the DGMax client.

This module provides the resource class for E41 purchase document operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class PurchasesResource(DocumentResource):
    """Resource for E41 purchase document operations.

    E41 - Comprobante Electrónico de Compras

    Used for documenting purchases from informal suppliers
    who cannot issue fiscal documents.

    Examples:
        >>> # List purchase documents
        >>> purchases = client.purchases.list()

        >>> # Create a purchase document
        >>> purchase = client.purchases.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "proveedor_informal": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific purchase document
        >>> purchase = client.purchases.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the purchases resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.purchases,
        )
