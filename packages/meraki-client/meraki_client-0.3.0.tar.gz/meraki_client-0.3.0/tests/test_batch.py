"""Tests for action batch operations."""

import uuid

import pytest

from meraki_client import MerakiClient

pytestmark = pytest.mark.mutating


def test_network_batch_with_multiple_actions(client: MerakiClient, organization_id: str) -> None:
    """Test action batch with multiple update_network actions."""
    unique_suffix = uuid.uuid4().hex[:8]
    network_name = f"Test Network Batch {unique_suffix}"
    product_types = ["switch"]

    # Create network using regular API
    created = client.organizations.create_organization_network(
        organization_id=organization_id,
        name=network_name,
        product_types=product_types,
    )
    assert created is not None
    assert created.id is not None
    network_id = created.id

    updated_name = f"Updated Network {unique_suffix}"
    updated_notes = f"Updated notes {unique_suffix}"
    updated_tags = ["batch-test"]
    try:
        # Build batch with three update actions
        update_name = client.batch.networks.update_network(network_id, name=updated_name)
        update_notes = client.batch.networks.update_network(network_id, notes=updated_notes)
        update_tags = client.batch.networks.update_network(network_id, tags=updated_tags)

        # Execute batch with all actions
        batch = client.organizations.create_organization_action_batch(
            organization_id=organization_id,
            actions=[update_name, update_notes, update_tags],
            confirmed=True,
            synchronous=True,
        )
        assert batch is not None
        assert batch.status is not None
        assert batch.status.completed is True
        assert batch.status.failed is False

        # Verify the updates
        updated = client.networks.get_network(network_id)
        assert updated is not None
        assert updated.name == updated_name
        assert updated.notes == updated_notes
        assert updated.tags == updated_tags
    finally:
        # Delete network using regular API (cleanup)
        client.networks.delete_network(network_id)
