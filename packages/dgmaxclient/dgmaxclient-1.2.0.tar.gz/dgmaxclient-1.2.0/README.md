# DGMaxClient

Python SDK for the DGMax API - Electronic fiscal document processing for the Dominican Republic.

## Installation

```bash
pip install dgmaxclient
```

## Quick Start

```python
from dgmaxclient import DGMaxClient

# Initialize the client
client = DGMaxClient(api_key="dgmax_xxx")

# List companies
companies = client.companies.list()
for company in companies.results:
    print(f"{company.name} ({company.rnc})")

# Create an invoice (E32)
invoice = client.invoices.create({
    "encabezado": {
        "id_doc": {
            "e_ncf": "E320000000001",
            "tipo_e_ncf": 32,
            # ... other fields
        },
        "emisor": {
            "rnc_emisor": "123456789",
            # ... other fields
        },
        "totales": {
            "monto_total": 1000.00,
            # ... other fields
        }
    },
    "detalles": {
        "item": [
            # ... line items
        ]
    }
})

print(f"Invoice created: {invoice.encf}")
print(f"Status: {invoice.status}")
```

## Architecture

DGMaxClient uses the **Facade Pattern** with **Composition** to provide a clean, namespaced API. The main client acts as a single entry point that composes multiple resource objects, each responsible for a specific API domain.

```
┌─────────────────┐
│   DGMaxClient   │ ◄── Facade (single entry point)
├─────────────────┤
│ .companies      │───► CompaniesResource
│ .invoices       │───► InvoicesResource
│ .purchases      │───► PurchasesResource
│ .credit_notes   │───► CreditNotesResource
│ ...             │───► (other resources)
└─────────────────┘
         │
         ▼
   HTTP/Auth layer (shared)
```

This pattern enables:
- **Clean API**: `client.companies.list()`, `client.invoices.create({...})`
- **Shared configuration**: All resources use the same authentication and settings
- **Separation of concerns**: Each resource handles its own domain logic
- **Discoverability**: IDE autocomplete works seamlessly

## Features

### Document Types (E31-E47)

The SDK supports all Dominican Republic electronic fiscal document types:

| Type | Resource | Description |
|------|----------|-------------|
| E31 | `client.fiscal_invoices` | Factura de Crédito Fiscal Electrónica |
| E32 | `client.invoices` | Factura de Consumo Electrónica |
| E33 | `client.debit_notes` | Nota de Débito Electrónica |
| E34 | `client.credit_notes` | Nota de Crédito Electrónica |
| E41 | `client.purchases` | Comprobante Electrónico de Compras |
| E43 | `client.minor_expenses` | Comprobante Electrónico para Gastos Menores |
| E44 | `client.special_regimes` | Comprobante Electrónico para Regímenes Especiales |
| E45 | `client.governmental` | Comprobante Electrónico Gubernamental |
| E46 | `client.exports` | Comprobante Electrónico para Exportaciones |
| E47 | `client.payments_abroad` | Comprobante Electrónico para Pagos al Exterior |

### Company Management

```python
from dgmaxclient import CompanyCreate, CertificateCreate

# List companies
companies = client.companies.list()

# Get a specific company
company = client.companies.get("company-uuid")

# Create a company with certificate
company = client.companies.create(CompanyCreate(
    name="Mi Empresa SRL",
    trade_name="Mi Empresa",
    rnc="123456789",
    address="Calle Principal #123",
    certificate=CertificateCreate(
        name="certificate",
        extension="p12",
        content="base64-encoded-certificate",
        password="certificate-password"
    )
))

# Update a company
company = client.companies.update("company-uuid", {
    "phone": "809-555-1234",
    "email": "info@miempresa.com"
})
```

### Document Operations

```python
from dgmaxclient import DocumentFilters, DocumentStatus, PaginationParams

# List documents with pagination
invoices = client.invoices.list(
    params=PaginationParams(limit=50, offset=0)
)

# List documents with filters
invoices = client.invoices.list(
    filters=DocumentFilters(
        status=DocumentStatus.COMPLETED,
        date_from="2024-01-01",
        date_to="2024-12-31",
        search="123456789"  # Search by RNC or eNCF
    )
)

# Get a specific document
invoice = client.invoices.get("document-uuid")

# Create a document
invoice = client.invoices.create({...})
```

### Received Documents (Receptor Module)

```python
# List received documents
received = client.received_documents.list()

# List with filters
received = client.received_documents.list(
    status_filter="PENDING",
    date_from="2024-01-01"
)

# Approve a received document
response = client.received_documents.approve("document-uuid")
if response.success:
    print(f"Document approved: {response.approval_id}")

# Reject a received document
response = client.received_documents.reject(
    "document-uuid",
    rejection_reason="Invoice amount does not match purchase order"
)

# List commercial approvals received
approvals = client.received_documents.list_commercial_approvals()
```

## Error Handling

The SDK provides a comprehensive exception hierarchy:

```python
from dgmaxclient import (
    DGMaxError,
    DGMaxAuthenticationError,
    DGMaxValidationError,
    DGMaxRequestError,
    DGMaxServerError,
    DGMaxTimeoutError,
    DGMaxConnectionError,
    DGMaxRateLimitError,
)

try:
    invoice = client.invoices.create({...})
except DGMaxAuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print(f"Status code: {e.status_code}")
except DGMaxValidationError as e:
    print(f"Validation error: {e.message}")
    if e.response:
        print(f"Details: {e.response}")
except DGMaxServerError as e:
    print(f"Server error (will retry): {e.message}")
except DGMaxTimeoutError:
    print("Request timed out")
except DGMaxConnectionError:
    print("Connection error - check your network")
except DGMaxRateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except DGMaxError as e:
    print(f"General error: {e.message}")
```

## Configuration

```python
# Custom base URL (for staging/testing)
client = DGMaxClient(
    api_key="dgmax_xxx",
    base_url="https://staging.dgmax.do"
)

# Custom timeout (default: 30 seconds)
client = DGMaxClient(
    api_key="dgmax_xxx",
    timeout=60
)
```

## Automatic Retries

The SDK automatically retries requests on:
- Server errors (5xx)
- Connection errors
- Timeout errors

Retries use exponential backoff with jitter (max 3 attempts).

## Type Safety

All responses are validated with Pydantic models:

```python
from dgmaxclient import ElectronicDocumentPublic, DocumentStatus

invoice: ElectronicDocumentPublic = client.invoices.get("uuid")

# Type-safe access
print(invoice.id)
print(invoice.encf)
print(invoice.status)  # DocumentStatus enum

if invoice.status == DocumentStatus.COMPLETED:
    print("Document processed successfully")
```

## Requirements

- Python 3.8+
- api-client >= 1.3.1
- pydantic >= 2.0
- tenacity >= 8.0
- requests >= 2.28.0

## License

MIT License - see LICENSE file for details.
