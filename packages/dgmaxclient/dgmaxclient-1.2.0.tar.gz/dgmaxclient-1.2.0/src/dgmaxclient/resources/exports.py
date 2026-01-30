"""
Exports resource (E46) for the DGMax client.

This module provides the resource class for E46 export document operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class ExportsResource(DocumentResource):
    """Resource for E46 export document operations.

    E46 - Comprobante Electrónico para Exportaciones

    Used for documenting export transactions.

    Examples:
        >>> # List export documents
        >>> exports = client.exports.list()

        >>> # Create an export document
        >>> export = client.exports.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "comprador": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...},
        ...     "destino": {...}
        ... })

        >>> # Get a specific export document
        >>> export = client.exports.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the exports resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.exports,
        )
