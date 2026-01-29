# Using Batch Endpoints

The Meraki API supports [action batches](https://developer.cisco.com/meraki/api-v1/action-batches-overview/) which allow you to submit multiple configuration changes in a single request. This is useful for bulk operations and ensures changes are applied atomically.

## How Action Batches Work

1. Build a list of actions using `client.batch.<scope>.<operation>()`
2. Submit the batch via `client.organizations.create_organization_action_batch()`
3. The API executes all actions in sequence

## Building Batch Actions

The `client.batch` object mirrors the regular API structure but returns action definitions instead of making requests:

```python
from meraki_client import MerakiClient

client = MerakiClient()

# Build individual actions
action1 = client.batch.networks.update_network(
    network_id="N_123",
    name="Updated Network Name"
)

action2 = client.batch.networks.update_network(
    network_id="N_456", 
    name="Another Network"
)

action3 = client.batch.devices.update_device(
    serial="QXXX-XXXX-XXXX",
    name="Updated Device Name"
)
```

## Submitting a Batch

Submit the actions using `create_organization_action_batch`:

```python
# Submit the batch
result = client.organizations.create_organization_action_batch(
    organization_id=org_id,
    actions=[action1, action2, action3],
    confirmed=True,  # Execute immediately
    synchronous=True  # Wait for completion
)

print(f"Batch ID: {result.id}")
print(f"Status: {result.status.completed}")
```

## Batch Options

### Confirmed vs Unconfirmed

- `confirmed=True`: Actions execute immediately
- `confirmed=False`: Creates a draft that must be confirmed later

```python
# Create unconfirmed batch
batch = client.organizations.create_organization_action_batch(
    organization_id=org_id,
    actions=[action1, action2],
    confirmed=False
)

# Later, confirm it
client.organizations.update_organization_action_batch(
    organization_id=org_id,
    action_batch_id=batch.id,
    confirmed=True
)
```

### Synchronous vs Asynchronous

- `synchronous=True`: Request blocks until batch completes
- `synchronous=False`: Request returns immediately, check status later

```python
# Async batch (returns immediately)
batch = client.organizations.create_organization_action_batch(
    organization_id=org_id,
    actions=actions,
    confirmed=True,
    synchronous=False
)

# Check status later
status = client.organizations.get_organization_action_batch(
    organization_id=org_id,
    action_batch_id=batch.id
)
```
