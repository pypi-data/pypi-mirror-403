"""
DGMax client resources.

This module exports all resource classes for the DGMax SDK.
"""

from __future__ import annotations

from dgmaxclient.resources.base import BaseResource, DocumentResource
from dgmaxclient.resources.certification import CertificationResource
from dgmaxclient.resources.companies import CompaniesResource
from dgmaxclient.resources.credit_notes import CreditNotesResource
from dgmaxclient.resources.debit_notes import DebitNotesResource
from dgmaxclient.resources.exports import ExportsResource
from dgmaxclient.resources.fiscal_invoices import FiscalInvoicesResource
from dgmaxclient.resources.governmental import GovernmentalResource
from dgmaxclient.resources.invoices import InvoicesResource
from dgmaxclient.resources.minor_expenses import MinorExpensesResource
from dgmaxclient.resources.payments_abroad import PaymentsAbroadResource
from dgmaxclient.resources.purchases import PurchasesResource
from dgmaxclient.resources.received_documents import ReceivedDocumentsResource
from dgmaxclient.resources.special_regimes import SpecialRegimesResource

__all__ = [
    # Base classes
    "BaseResource",
    "DocumentResource",
    # Resource classes
    "CertificationResource",
    "CompaniesResource",
    "CreditNotesResource",
    "DebitNotesResource",
    "ExportsResource",
    "FiscalInvoicesResource",
    "GovernmentalResource",
    "InvoicesResource",
    "MinorExpensesResource",
    "PaymentsAbroadResource",
    "PurchasesResource",
    "ReceivedDocumentsResource",
    "SpecialRegimesResource",
]
