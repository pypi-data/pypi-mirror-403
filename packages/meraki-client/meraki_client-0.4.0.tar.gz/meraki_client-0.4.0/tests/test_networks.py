"""Tests for network operations."""

import uuid

import pytest

from meraki_client import MerakiClient

pytestmark = pytest.mark.mutating


def test_network_lifecycle(client: MerakiClient, organization_id: str) -> None:
    """Test creating, updating, and deleting a network."""
    unique_suffix = uuid.uuid4().hex[:8]
    network_name = f"Test Network {unique_suffix}"
    product_types = ["switch"]
    tags = ["test"]
    notes = "Created by automated test"

    # Create network
    created = client.organizations.create_organization_network(
        organization_id=organization_id,
        name=network_name,
        product_types=product_types,
        tags=tags,
        notes=notes,
    )
    assert created is not None
    assert created.id is not None
    assert created.name == network_name
    assert created.product_types == product_types
    assert created.tags == tags
    assert created.notes == notes
    network_id = created.id

    updated_name = f"Updated Network {unique_suffix}"
    updated_notes = f"Updated by automated test {unique_suffix}"
    try:
        # Update network
        updated = client.networks.update_network(
            network_id,
            name=updated_name,
            notes=updated_notes,
        )
        assert updated is not None
        assert updated.name == updated_name
        assert updated.notes == updated_notes
    finally:
        # Delete network (cleanup)
        client.networks.delete_network(network_id)
