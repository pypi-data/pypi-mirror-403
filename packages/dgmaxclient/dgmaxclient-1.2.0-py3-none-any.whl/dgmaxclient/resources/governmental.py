"""
Governmental resource (E45) for the DGMax client.

This module provides the resource class for E45 governmental document operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class GovernmentalResource(DocumentResource):
    """Resource for E45 governmental document operations.

    E45 - Comprobante Electrónico Gubernamental

    Used for transactions with government entities.

    Examples:
        >>> # List governmental documents
        >>> documents = client.governmental.list()

        >>> # Create a governmental document
        >>> document = client.governmental.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "comprador": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific document
        >>> document = client.governmental.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the governmental resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.governmental,
        )
