# Getting Started

## Installation

Install the package from PyPI:

```shell
pip install meraki-client
```

Or with [uv](https://docs.astral.sh/uv/):

```shell
uv add meraki-client
```

## API Key Setup

1. Enable API access in your Meraki dashboard organization
2. [Obtain an API key](https://documentation.meraki.com/Platform_Management/Dashboard_Administration/Operate_and_Maintain/How-Tos/Cisco_Meraki_Dashboard_API)

Pass the API key to the client directly:

```python
from meraki_client import MerakiClient

client = MerakiClient(api_key="YOUR_KEY_HERE")
```

Or set it as an environment variable:

```shell
export MERAKI_DASHBOARD_API_KEY=YOUR_KEY_HERE
```

## Basic Usage

### Synchronous Client

```python
from meraki_client import MerakiClient

client = MerakiClient()

# Get all organizations
orgs = client.organizations.get_organizations().collect()

# Get a specific organization
org = client.organizations.get_organization(organization_id="123456")

# Get networks in an organization
networks = client.organizations.get_organization_networks(
    organization_id="123456"
).collect()
```

### Asynchronous Client

```python
from meraki_client.aio import AsyncMerakiClient

async with AsyncMerakiClient() as client:
    orgs = await client.organizations.get_organizations().collect()
    
    org = await client.organizations.get_organization(
        organization_id="123456"
    )
```
