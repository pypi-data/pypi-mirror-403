"""Tests for client factory functions"""

import pytest

from a2p.client import MemoryStorage, create_agent_client, create_user_client


class TestCreateAgentClient:
    """Test create_agent_client factory function"""

    def test_create_with_default_storage(self):
        """Test creating agent client with default storage"""
        client = create_agent_client(agent_did="did:a2p:agent:local:test")

        assert client is not None
        assert client.get_session_id() is not None

    def test_create_with_custom_storage(self):
        """Test creating agent client with custom storage"""
        storage = MemoryStorage()
        client = create_agent_client(agent_did="did:a2p:agent:local:test", storage=storage)

        assert client is not None
        assert client.get_session_id() is not None


class TestCreateUserClient:
    """Test create_user_client factory function"""

    def test_create_with_default_storage(self):
        """Test creating user client with default storage"""
        client = create_user_client()

        assert client is not None
        assert client.get_profile() is None

    def test_create_with_custom_storage(self):
        """Test creating user client with custom storage"""
        storage = MemoryStorage()
        client = create_user_client(storage=storage)

        assert client is not None
        assert client.get_profile() is None

    @pytest.mark.asyncio
    async def test_create_and_load_profile(self):
        """Test creating and loading profiles with factory client"""
        client = create_user_client()
        profile = await client.create_profile(display_name="Test User")

        assert profile.identity.display_name == "Test User"
        assert client.get_profile() is not None
