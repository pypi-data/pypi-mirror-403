"""Pytest configuration and shared fixtures for all tests."""

import os

import pytest

from meraki_client import MerakiClient


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "mutating: marks tests that create/update/delete resources (deselect with '-m \"not mutating\"')",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip mutating tests unless explicitly requested."""
    # If -m option was provided, let pytest handle it normally
    if config.getoption("-m"):
        return

    skip_mutating = pytest.mark.skip(
        reason="Mutating tests skipped by default. Use -m mutating to run."
    )
    for item in items:
        if "mutating" in item.keywords:
            item.add_marker(skip_mutating)


@pytest.fixture(scope="module")
def client() -> MerakiClient:
    """Create a Meraki client for testing."""
    api_key = os.environ.get("MERAKI_DASHBOARD_API_KEY_TESTS")
    if not api_key:
        pytest.skip("MERAKI_DASHBOARD_API_KEY_TESTS environment variable not set")
    return MerakiClient(api_key=api_key)


@pytest.fixture(scope="module")
def organization_id(client: MerakiClient) -> str:
    """Get the first organization ID for testing."""
    org_id = os.environ.get("ORGANIZATION_ID_TESTS")
    if org_id:
        return org_id
    orgs = client.organizations.get_organizations().collect()
    if not orgs:
        pytest.skip("No organizations available for testing")
    org = orgs[0]
    if not org.id:
        pytest.skip("No organization ID available for testing")
    return org.id


@pytest.fixture(scope="module")
def network_id(client: MerakiClient, organization_id: str) -> str:
    """Get the first network ID for testing."""
    env_network_id = os.environ.get("NETWORK_ID_TESTS")
    if env_network_id:
        return env_network_id
    networks = client.organizations.get_organization_networks(organization_id).collect()
    if not networks:
        pytest.skip("No networks available for testing")
    network = networks[0]
    if not network.id:
        pytest.skip("No network ID available for testing")
    return network.id


@pytest.fixture(scope="module")
def device_serial(client: MerakiClient, organization_id: str) -> str:
    """Get the first device serial for testing."""
    env_device_id = os.environ.get("DEVICE_ID_TESTS")
    if env_device_id:
        return env_device_id
    devices = client.organizations.get_organization_devices(organization_id).collect()
    if not devices:
        pytest.skip("No devices available for testing")
    device = devices[0]
    if not device.serial:
        pytest.skip("No device serial available for testing")
    return device.serial
