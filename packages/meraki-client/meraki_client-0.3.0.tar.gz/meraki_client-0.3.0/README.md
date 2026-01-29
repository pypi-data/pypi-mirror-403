<p align="center"><strong>Meraki Client</strong> <em>- Python client for Meraki Dashboard API.</em></p>

<p align="center">
<a href="https://pypi.org/project/meraki-client/">
  <img src="https://img.shields.io/pypi/v/meraki-client" alt="pypi">
</a>
<a href="https://github.com/ollipa/meraki-client-python/actions/workflows/ci.yml">
  <img src="https://github.com/ollipa/meraki-client-python/actions/workflows/ci.yml/badge.svg" alt="ci">
</a>
<a href="https://meraki-client.readthedocs.io/">
  <img src="https://img.shields.io/readthedocs/meraki-client" alt="documentation">
</a>
<a href="https://github.com/ollipa/meraki-client-python/blob/main/LICENSE">
  <img src="https://img.shields.io/pypi/l/meraki-client" alt="license">
</a>
</p>

<hr>

<p align="center">
<a href="https://meraki-client.readthedocs.io/">
  <b>Documentation</b>
</a>
</p>

<hr>

Python client for the [Meraki Dashboard API](https://developer.cisco.com/meraki/api-v1/). Auto-generated from the OpenAPI spec to stay current with the latest releases.

**Installation:**

```shell
pip install meraki-client
```

## Features

- Modern Python 3.11+ with full type annotations
- Sync and async clients built on httpx
- Pydantic models for requests and responses
- Automatic retries and pagination
- Full API coverage ([auto-generated from OpenAPI](https://github.com/meraki/openapi))

## Setup

1. Enable API access in your Meraki dashboard organization and [obtain an API key](https://documentation.meraki.com/Platform_Management/Dashboard_Administration/Operate_and_Maintain/How-Tos/Cisco_Meraki_Dashboard_API)

2. Pass the API key to the client, or set it as an environment variable:

   ```python
   client = MerakiClient(api_key="YOUR_KEY_HERE")
   ```

   ```shell
   export MERAKI_DASHBOARD_API_KEY=YOUR_KEY_HERE
   ```

### Application identification

Cisco Meraki recommends that ecosystem partners and application developers identify their application with API requests. See [User agents guide](https://developer.cisco.com/meraki/api-v1/user-agents-overview/#user-agents) for formatting details.

```python
client = MerakiClient(caller="ApplicationName/1.0 VendorName")
```

Or via environment variable:

```shell
export MERAKI_PYTHON_SDK_CALLER="ApplicationName/1.0 VendorName"
```

## Usage

API calls follow the pattern `client.<scope>.<operation>()`, where scope maps to the OpenAPI tags (e.g., `organizations`, `networks`, `devices`).

### Synchronous

```python
from meraki_client import MerakiClient

client = MerakiClient()
org = client.organizations.get_organization(org_id)
```

### Asynchronous

```python
from meraki_client.aio import AsyncMerakiClient

async with AsyncMerakiClient() as client:
    orgs = await client.organizations.get_organization(org_id)
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](https://github.com/ollipa/meraki-client-python/blob/main/CONTRIBUTING.md) for development setup, testing, and code generation instructions.

## Disclaimer

This is an unofficial community project, not affiliated with or endorsed by Cisco. For the official Meraki Python SDK, see [meraki/dashboard-api-python](https://github.com/meraki/dashboard-api-python). This project was forked from the official Meraki Python SDK.
