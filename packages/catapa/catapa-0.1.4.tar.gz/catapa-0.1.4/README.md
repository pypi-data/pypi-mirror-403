# CATAPA Python SDK

A comprehensive Python client library for the CATAPA API with ergonomic wrapper and automatic OAuth2 authentication handling.

## Features

- 🔐 **Automatic OAuth2 Authentication** - Client credentials flow with automatic token refresh
- 🚀 **Ergonomic API** - Simple, intuitive interface for all CATAPA APIs
- 📝 **Full Type Support** - Complete type hints with generated models
- 📦 **Direct Imports** - `from catapa import EmployeeApi`
- 🎯 **Auto-Refresh Tokens** - Tokens are automatically refreshed on every API call

## Installation

```bash
# Install from local directory
pip install -e /path/to/catapa-python
```

When installed, two packages are available:

- `catapa`: The main package with wrapper and authentication logic
- `openapi_client`: The raw generated OpenAPI client code

## Quick Start

```python
from catapa import Catapa, EmployeeApi

# 1. Initialize the client
client = Catapa(
    tenant='your-tenant',
    client_id='your-client-id',
    client_secret='your-client-secret'
)

# 2. Create API instances and use them
employee_api = EmployeeApi(client)
employees = employee_api.list_all_employees(page=0, size=10)

print(f"Found {len(employees.content)} employees")
```

## Usage Examples

### Using Multiple APIs

You can import and use multiple API classes:

```python
from catapa import Catapa, OrganizationApi, MasterDataApi, TaxApi

client = Catapa(
    tenant='your-tenant',
    client_id='your-client-id',
    client_secret='your-client-secret'
)

# Use different APIs with the same client
org_api = OrganizationApi(client)
company = org_api.get_companies()

master_data_api = MasterDataApi(client)
countries = master_data_api.get_countries()

tax_api = TaxApi(client)
tax_rates = tax_api.get_tax_rates()
```

### Long-Running Services

The SDK is perfect for long-running services - tokens are automatically refreshed on every API call:

```python
from catapa import Catapa, EmployeeApi
import time

client = Catapa(tenant='your-tenant', client_id='your-id', client_secret='your-secret')
employee_api = EmployeeApi(client)

# Make an API call
employees = employee_api.list_all_employees(page=0, size=10)

# Wait an hour (token would normally expire)
time.sleep(3600)

# This call will automatically refresh the token if needed
employees = employee_api.list_all_employees(page=0, size=10)  # ✅ Works!
```

### Error Handling

```python
from catapa import Catapa, EmployeeApi
from openapi_client.exceptions import ApiException

client = Catapa(tenant='your-tenant', client_id='your-id', client_secret='your-secret')
employee_api = EmployeeApi(client)

try:
    employees = employee_api.list_all_employees(page=0, size=10)
except ApiException as e:
    print(f"API Error: {e.status} - {e.reason}")
```

## Available APIs

All CATAPA APIs are available through the `catapa` package:

```python
from catapa import (
    Catapa,
    EmployeeApi,
    OrganizationApi,
    MasterDataApi,
    TaxApi,
    SalaryPaymentApi,
    PayrollProcessSnapshotApi,
    # ... and 40+ more APIs
)
```

## Authentication

The client automatically handles OAuth2 authentication using client credentials flow. You don't need to manage tokens manually:

- **Automatic Token Refresh**: Tokens are refreshed on every API call (5-minute buffer before expiration)
- **No Manual Management**: No need to check token expiration or refresh manually

## Requirements

- Python 3.11+
