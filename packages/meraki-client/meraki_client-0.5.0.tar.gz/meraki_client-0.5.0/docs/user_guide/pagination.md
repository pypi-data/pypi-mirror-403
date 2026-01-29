# Using Pagination

Many Meraki API endpoints return paginated results. The client handles pagination automatically through the `PaginatedResponse` class.

## Basic Usage

Paginated endpoints return a lazy `PaginatedResponse` iterator. You can iterate directly over it or collect all results:

```python
from meraki_client import MerakiClient

client = MerakiClient()

# Iterate page by page (lazy - fetches pages as needed)
for device in client.organizations.get_organization_devices(
    organization_id=org_id
):
    print(device.name)

# Or collect all results at once
devices = client.organizations.get_organization_devices(
    organization_id=org_id
).collect()
```

## Controlling Pagination

### Limiting Pages

By default, all the pages are returned. Use `total_pages` to control how many pages to fetch:

```python
# Fetch all pages (default)
devices = client.organizations.get_organization_devices(
    organization_id=org_id,
    total_pages="all"
).collect()

# Fetch first 3 pages
devices = client.organizations.get_organization_devices(
    organization_id=org_id,
    total_pages=3
).collect()
```

### Pagination Direction

Some endpoints support bidirectional pagination. Use the `direction` parameter:

```python
# Paginate forward (default)
events = client.networks.get_network_events(
    network_id=network_id,
    direction="next"
)

# Paginate backward
events = client.networks.get_network_events(
    network_id=network_id,
    direction="prev"
)
```

## Async Pagination

The async client works similarly:

```python
from meraki_client.aio import AsyncMerakiClient

async with AsyncMerakiClient() as client:
    # Iterate asynchronously
    async for device in client.organizations.get_organization_devices(
        organization_id=org_id,
        total_pages="all"
    ):
        print(device.name)

    # Or collect all results
    devices = await client.organizations.get_organization_devices(
        organization_id=org_id,
        total_pages="all"
    ).collect()
```

## Per-Page Parameters

You can also use the API's native pagination parameters like `per_page`, `starting_after`, and `ending_before` for fine-grained control:

```python
# Get 100 items per page
devices = client.organizations.get_organization_devices(
    organization_id=org_id,
    per_page=100,
    total_pages="all"
).collect()
```
