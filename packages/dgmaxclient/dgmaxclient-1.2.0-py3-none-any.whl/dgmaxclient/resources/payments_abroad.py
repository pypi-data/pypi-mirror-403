"""
Payments abroad resource (E47) for the DGMax client.

This module provides the resource class for E47 foreign payment operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class PaymentsAbroadResource(DocumentResource):
    """Resource for E47 foreign payment operations.

    E47 - Comprobante Electrónico para Pagos al Exterior

    Used for documenting payments made to foreign entities
    (services, royalties, etc.).

    Examples:
        >>> # List foreign payment documents
        >>> payments = client.payments_abroad.list()

        >>> # Create a foreign payment document
        >>> payment = client.payments_abroad.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "beneficiario_exterior": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific foreign payment document
        >>> payment = client.payments_abroad.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the payments abroad resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.payments_abroad,
        )
