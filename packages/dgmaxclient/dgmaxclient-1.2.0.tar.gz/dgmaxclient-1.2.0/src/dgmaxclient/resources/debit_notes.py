"""
Debit notes resource (E33) for the DGMax client.

This module provides the resource class for E33 debit note operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class DebitNotesResource(DocumentResource):
    """Resource for E33 debit note operations.

    E33 - Nota de Débito Electrónica

    Used to increase the amount of a previously issued invoice (E31/E32).

    Examples:
        >>> # List debit notes
        >>> notes = client.debit_notes.list()

        >>> # Create a debit note referencing an existing invoice
        >>> note = client.debit_notes.create({
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

        >>> # Get a specific debit note
        >>> note = client.debit_notes.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the debit notes resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.debit_notes,
        )
