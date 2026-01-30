"""
Credit notes resource (E34) for the DGMax client.

This module provides the resource class for E34 credit note operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class CreditNotesResource(DocumentResource):
    """Resource for E34 credit note operations.

    E34 - Nota de Crédito Electrónica

    Used to reduce the amount of a previously issued invoice (E31/E32),
    typically for returns, discounts, or corrections.

    Examples:
        >>> # List credit notes
        >>> notes = client.credit_notes.list()

        >>> # Create a credit note referencing an existing invoice
        >>> note = client.credit_notes.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "comprador": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...},
        ...     "informacion_referencia": {
        ...         "ncf_modificado": "E310000000001",
        ...         ...
        ...     }
        ... })

        >>> # Get a specific credit note
        >>> note = client.credit_notes.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the credit notes resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.credit_notes,
        )
