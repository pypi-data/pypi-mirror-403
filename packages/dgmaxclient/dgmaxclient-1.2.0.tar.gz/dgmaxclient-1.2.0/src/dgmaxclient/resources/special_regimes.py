"""
Special regimes resource (E44) for the DGMax client.

This module provides the resource class for E44 special regime operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class SpecialRegimesResource(DocumentResource):
    """Resource for E44 special regime operations.

    E44 - Comprobante Electrónico para Regímenes Especiales

    Used for transactions with entities under special tax regimes
    (free trade zones, exempt entities, etc.).

    Examples:
        >>> # List special regime documents
        >>> documents = client.special_regimes.list()

        >>> # Create a special regime document
        >>> document = client.special_regimes.create({
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
        >>> document = client.special_regimes.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the special regimes resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.special_regimes,
        )
