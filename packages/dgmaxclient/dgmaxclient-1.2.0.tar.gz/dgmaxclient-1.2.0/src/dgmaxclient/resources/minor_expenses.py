"""
Minor expenses resource (E43) for the DGMax client.

This module provides the resource class for E43 minor expense operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dgmaxclient.resources.base import DocumentResource

if TYPE_CHECKING:
    from dgmaxclient.client import DGMaxClient


class MinorExpensesResource(DocumentResource):
    """Resource for E43 minor expense operations.

    E43 - Comprobante Electrónico para Gastos Menores

    Used for small purchases and expenses that don't require
    formal invoices (petty cash, tips, parking, etc.).

    Examples:
        >>> # List minor expenses
        >>> expenses = client.minor_expenses.list()

        >>> # Create a minor expense
        >>> expense = client.minor_expenses.create({
        ...     "encabezado": {
        ...         "version": "1.0",
        ...         "id_doc": {...},
        ...         "emisor": {...},
        ...         "totales": {...}
        ...     },
        ...     "detalles": {...}
        ... })

        >>> # Get a specific minor expense
        >>> expense = client.minor_expenses.get("document-uuid")
    """

    def __init__(self, client: DGMaxClient) -> None:
        """Initialize the minor expenses resource.

        Args:
            client: The DGMax client instance
        """
        super().__init__(
            client=client,
            endpoint=client.endpoints.minor_expenses,
        )
