"""
Tests for the Client class
"""

import pytest
from scc_sdk import Client
from scc_sdk.exceptions import SCCError, AuthenticationError


def test_client_initialization():
    """Test client initialization."""
    client = Client(access_token="test_token")
    assert client.access_token == "test_token"
    assert client.base_url == "https://api.security.cisco.com/v1"
    assert hasattr(client, "organizations")
    assert hasattr(client, "subscriptions")
    assert hasattr(client, "groups")
    assert hasattr(client, "tokens")


def test_client_requires_access_token():
    """Test that client requires an access token."""
    with pytest.raises(ValueError):
        Client(access_token="")


def test_client_custom_base_url():
    """Test client with custom base URL."""
    client = Client(
        access_token="test_token",
        base_url="https://api.security.cisco.com",
        base_path="v2"
    )
    assert client.base_url == "https://api.security.cisco.com/v2"


def test_client_context_manager():
    """Test client as context manager."""
    with Client(access_token="test_token") as client:
        assert client.access_token == "test_token"
    # Session should be closed after exiting context


def test_client_custom_timeout():
    """Test client with custom timeout."""
    client = Client(access_token="test_token", timeout=60)
    assert client.timeout == 60
