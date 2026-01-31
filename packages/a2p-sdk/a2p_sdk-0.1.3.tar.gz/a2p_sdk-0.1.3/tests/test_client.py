"""Tests for a2p clients"""

import pytest

from a2p.client import (
    A2PClient,
    A2PUserClient,
    MemoryStorage,
    create_agent_client,
    create_user_client,
)
from a2p.core.profile import add_policy, create_profile
from a2p.types import (
    MemoryStatus,
    PermissionLevel,
)


class TestMemoryStorage:
    """Test memory storage implementation"""

    @pytest.mark.asyncio
    async def test_storage_get_set(self):
        """Test getting and setting profiles"""
        storage = MemoryStorage()
        profile = create_profile()

        await storage.set(profile.id, profile)
        retrieved = await storage.get(profile.id)

        assert retrieved is not None
        assert retrieved.id == profile.id

    @pytest.mark.asyncio
    async def test_storage_delete(self):
        """Test deleting profiles"""
        storage = MemoryStorage()
        profile = create_profile()

        await storage.set(profile.id, profile)
        await storage.delete(profile.id)

        retrieved = await storage.get(profile.id)
        assert retrieved is None


class TestA2PUserClient:
    """Test user client"""

    @pytest.mark.asyncio
    async def test_create_profile(self):
        """Test creating a profile"""
        client = A2PUserClient()
        profile = await client.create_profile(display_name="Alice")

        assert profile.identity.display_name == "Alice"
        assert profile.id.startswith("did:a2p:user:")

    @pytest.mark.asyncio
    async def test_load_profile(self):
        """Test loading a profile"""
        client = A2PUserClient()
        profile = await client.create_profile(display_name="Alice")
        profile_id = profile.id

        loaded = await client.load_profile(profile_id)
        assert loaded is not None
        assert loaded.identity.display_name == "Alice"

    @pytest.mark.asyncio
    async def test_add_memory(self):
        """Test adding a memory"""
        client = A2PUserClient()
        await client.create_profile()

        memory = await client.add_memory(
            content="User likes Python",
            category="a2p:preferences",
        )

        assert memory.content == "User likes Python"
        assert memory.status == MemoryStatus.APPROVED

    @pytest.mark.asyncio
    async def test_get_pending_proposals(self):
        """Test getting pending proposals"""
        client = A2PUserClient()
        await client.create_profile()

        # Create a proposal via agent client
        agent_client = A2PClient("did:a2p:agent:test", storage=client.storage)
        user_did = client.get_profile().id

        # Add policy to allow proposals
        profile = client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.PROPOSE],
            allow=["a2p:preferences.*"],
        )
        await client.storage.set(user_did, profile)
        await client.load_profile(user_did)

        await agent_client.propose_memory(
            user_did=user_did,
            content="Test proposal",
            category="a2p:preferences",
        )

        proposals = client.get_pending_proposals()
        assert len(proposals) == 1
        assert proposals[0].memory.content == "Test proposal"

    @pytest.mark.asyncio
    async def test_approve_proposal(self):
        """Test approving a proposal"""
        client = A2PUserClient()
        await client.create_profile()
        user_did = client.get_profile().id

        # Setup policy
        profile = client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.PROPOSE],
            allow=["a2p:preferences.*"],
        )
        await client.storage.set(user_did, profile)
        await client.load_profile(user_did)

        # Create proposal
        agent_client = A2PClient("did:a2p:agent:test", storage=client.storage)
        result = await agent_client.propose_memory(
            user_did=user_did,
            content="Test proposal",
            category="a2p:preferences",
        )

        # Approve it
        memory = await client.approve_proposal(result["proposal_id"])
        assert memory.content == "Test proposal"
        assert memory.status == MemoryStatus.APPROVED

    @pytest.mark.asyncio
    async def test_reject_proposal(self):
        """Test rejecting a proposal"""
        client = A2PUserClient()
        await client.create_profile()
        user_did = client.get_profile().id

        # Setup policy
        profile = client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.PROPOSE],
            allow=["a2p:preferences.*"],
        )
        await client.storage.set(user_did, profile)
        await client.load_profile(user_did)

        # Create proposal
        agent_client = A2PClient("did:a2p:agent:test", storage=client.storage)
        result = await agent_client.propose_memory(
            user_did=user_did,
            content="Test proposal",
            category="a2p:preferences",
        )

        # Reject it
        await client.reject_proposal(result["proposal_id"], reason="Not relevant")

        proposals = client.get_pending_proposals()
        assert len(proposals) == 0

    @pytest.mark.asyncio
    async def test_export_import_profile(self):
        """Test exporting and importing profile"""
        client = A2PUserClient()
        await client.create_profile(display_name="Alice")
        await client.add_memory(content="Test memory", category="a2p:preferences")

        json_str = client.export_profile()
        assert isinstance(json_str, str)

        # Create new client and import
        new_client = A2PUserClient()
        imported = await new_client.import_profile(json_str)
        assert imported.identity.display_name == "Alice"
        assert len(imported.memories.episodic) == 1


class TestA2PClient:
    """Test agent client"""

    @pytest.mark.asyncio
    async def test_request_access_granted(self):
        """Test requesting access with granted policy"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        # Add policy
        profile = user_client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        await storage.set(user_did, profile)

        # Request access
        agent_client = A2PClient("did:a2p:agent:test", storage=storage)
        response = await agent_client.request_access(
            user_did=user_did,
            scopes=["a2p:preferences.communication"],
        )

        assert "profile" in response
        assert "consent" in response
        assert response["consent"]["granted"]

    @pytest.mark.asyncio
    async def test_request_access_denied(self):
        """Test requesting access without policy"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        agent_client = A2PClient("did:a2p:agent:test", storage=storage)

        with pytest.raises(PermissionError, match="Access denied"):
            await agent_client.request_access(
                user_did=user_did,
                scopes=["a2p:preferences"],
            )

    @pytest.mark.asyncio
    async def test_get_profile(self):
        """Test getting profile (convenience method)"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        # Add policy
        profile = user_client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        await storage.set(user_did, profile)

        agent_client = A2PClient("did:a2p:agent:test", storage=storage)
        profile_data = await agent_client.get_profile(
            user_did=user_did,
            scopes=["a2p:preferences"],
        )

        assert "id" in profile_data
        assert "common" in profile_data

    @pytest.mark.asyncio
    async def test_propose_memory(self):
        """Test proposing a memory"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        # Add policy
        profile = user_client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.PROPOSE],
            allow=["a2p:preferences.*"],
        )
        await storage.set(user_did, profile)

        agent_client = A2PClient("did:a2p:agent:test", storage=storage)
        result = await agent_client.propose_memory(
            user_did=user_did,
            content="Agent learned this",
            category="a2p:preferences",
            confidence=0.8,
        )

        assert "proposal_id" in result
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_propose_memory_no_permission(self):
        """Test proposing memory without permission"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        agent_client = A2PClient("did:a2p:agent:test", storage=storage)

        with pytest.raises(PermissionError, match="does not have propose permission"):
            await agent_client.propose_memory(
                user_did=user_did,
                content="Test",
                category="a2p:preferences",
            )

    @pytest.mark.asyncio
    async def test_check_permission(self):
        """Test checking permission"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile()
        user_did = user_client.get_profile().id

        # Add policy
        profile = user_client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        await storage.set(user_did, profile)

        agent_client = A2PClient("did:a2p:agent:test", storage=storage)
        has_read = await agent_client.check_permission(
            user_did=user_did,
            permission=PermissionLevel.READ_SCOPED,
            scope="a2p:preferences",
        )
        assert has_read is True

        has_propose = await agent_client.check_permission(
            user_did=user_did,
            permission=PermissionLevel.PROPOSE,
            scope="a2p:preferences",
        )
        assert has_propose is False

    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test session ID management"""
        client = A2PClient("did:a2p:agent:test")
        session_id = client.get_session_id()

        assert session_id.startswith("sess_")

        new_session_id = client.new_session()
        assert new_session_id != session_id
        assert client.get_session_id() == new_session_id


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_agent_client(self):
        """Test creating agent client"""
        client = create_agent_client("did:a2p:agent:test")
        assert isinstance(client, A2PClient)
        assert client.agent_did == "did:a2p:agent:test"

    def test_create_user_client(self):
        """Test creating user client"""
        client = create_user_client()
        assert isinstance(client, A2PUserClient)
