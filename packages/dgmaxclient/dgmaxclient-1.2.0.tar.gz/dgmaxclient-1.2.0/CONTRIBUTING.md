# Contributing to DGMaxClient

## Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dgmaxclient

# Type checking
mypy src/dgmaxclient

# Linting
ruff check src/dgmaxclient
```

## Load Testing

The integration tests include parallel invoice creation for load testing. You can run multiple instances with different configurations using environment variables:

- `DGMAX_COMPANY_ID`: Target company UUID
- `START_SEQ`: Starting sequence number for e-NCF generation

**Option 1: Two separate terminals**

```bash
# Terminal 1
DGMAX_COMPANY_ID=company-a-uuid START_SEQ=911000 pytest tests/integration/test_dgmaxclient.py::test_create_fiscal_invoices_parallel -s -m manual

# Terminal 2
DGMAX_COMPANY_ID=company-b-uuid START_SEQ=912000 pytest tests/integration/test_dgmaxclient.py::test_create_fiscal_invoices_parallel -s -m manual
```

**Option 2: Background processes (single command)**

```bash
DGMAX_COMPANY_ID=company-a-uuid START_SEQ=911000 pytest tests/integration/test_dgmaxclient.py::test_create_fiscal_invoices_parallel -s -m manual &
DGMAX_COMPANY_ID=company-b-uuid START_SEQ=912000 pytest tests/integration/test_dgmaxclient.py::test_create_fiscal_invoices_parallel -s -m manual &
wait
```
