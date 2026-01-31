"""Tests for edge cases in a2p clients"""

import pytest

from a2p.client import A2PClient, A2PUserClient, MemoryStorage
from a2p.core.profile import add_policy, create_profile


class TestA2PClientEdgeCases:
    """Test edge cases in A2PClient"""

    @pytest.mark.asyncio
    async def test_empty_scopes_array(self):
        """Test handling empty scopes array"""
        storage = MemoryStorage()
        profile = create_profile()
        profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["read_scoped"],
                "allow": ["a2p:*"],
            },
        )
        await storage.set(profile.id, profile)

        client = A2PClient(agent_did="did:a2p:agent:local:test", storage=storage)

        # Empty scopes should be denied
        with pytest.raises(Exception, match="Access denied"):
            await client.get_profile(user_did=profile.id, scopes=[])

    @pytest.mark.asyncio
    async def test_multiple_scopes_partial_access(self):
        """Test handling multiple scopes with partial access"""
        storage = MemoryStorage()
        profile = create_profile()
        profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["read_scoped"],
                "allow": ["a2p:preferences.communication"],
                "deny": ["a2p:preferences.sensitive"],
            },
        )
        await storage.set(profile.id, profile)

        client = A2PClient(agent_did="did:a2p:agent:local:test", storage=storage)

        response = await client.get_profile(
            user_did=profile.id,
            scopes=[
                "a2p:preferences.communication",
                "a2p:preferences.sensitive",
                "a2p:preferences.other",
            ],
        )

        assert response is not None
        # Should have filtered profile based on allowed scopes

    @pytest.mark.asyncio
    async def test_session_id_generation(self):
        """Test session ID generation"""
        client1 = A2PClient(agent_did="did:a2p:agent:local:test")
        client2 = A2PClient(agent_did="did:a2p:agent:local:test")

        session1 = client1.get_session_id()
        session2 = client2.get_session_id()

        assert session1 is not None
        assert session2 is not None
        assert session1 != session2

    @pytest.mark.asyncio
    async def test_new_session_creation(self):
        """Test creating new session"""
        client = A2PClient(agent_did="did:a2p:agent:local:test")
        session1 = client.get_session_id()

        session2 = client.new_session()

        assert session2 is not None
        assert session2 != session1
        assert client.get_session_id() == session2


class TestA2PUserClientEdgeCases:
    """Test edge cases in A2PUserClient"""

    @pytest.mark.asyncio
    async def test_create_profile_minimal(self):
        """Test creating profile with minimal options"""
        client = A2PUserClient()
        profile = await client.create_profile()

        assert profile.id is not None
        assert profile.version == "1.0"
        assert profile.profile_type == "human"

    @pytest.mark.asyncio
    async def test_create_profile_with_options(self):
        """Test creating profile with all options"""
        client = A2PUserClient()
        profile = await client.create_profile(display_name="Test User")

        assert profile.identity.display_name == "Test User"

    @pytest.mark.asyncio
    async def test_add_multiple_memories(self):
        """Test adding multiple memories"""
        client = A2PUserClient()
        await client.create_profile()

        await client.add_memory(content="Memory 1", category="a2p:preferences")
        await client.add_memory(content="Memory 2", category="a2p:preferences")

        profile = client.get_profile()
        episodic = profile.memories.get("a2p:episodic", [])
        assert len(episodic) == 2

    @pytest.mark.asyncio
    async def test_update_memory(self):
        """Test updating memory"""
        client = A2PUserClient()
        await client.create_profile()
        memory = await client.add_memory(content="Original content", category="a2p:preferences")

        updated = await client.update_memory(memory_id=memory.id, content="Updated content")

        assert updated.content == "Updated content"

    @pytest.mark.asyncio
    async def test_remove_memory(self):
        """Test removing memory"""
        client = A2PUserClient()
        await client.create_profile()
        memory = await client.add_memory(content="Test memory", category="a2p:preferences")

        await client.remove_memory(memory.id)

        profile = client.get_profile()
        episodic = profile.memories.get("a2p:episodic", [])
        assert len(episodic) == 0

    @pytest.mark.asyncio
    async def test_archive_memory(self):
        """Test archiving memory"""
        client = A2PUserClient()
        await client.create_profile()
        memory = await client.add_memory(content="Test memory", category="a2p:preferences")

        archived = await client.archive_memory(memory.id)

        assert archived.status == "archived"

    @pytest.mark.asyncio
    async def test_empty_pending_proposals(self):
        """Test getting empty pending proposals"""
        client = A2PUserClient()
        await client.create_profile()

        proposals = client.get_pending_proposals()
        assert proposals == []

    @pytest.mark.asyncio
    async def test_profile_with_no_memories(self):
        """Test profile with no memories"""
        client = A2PUserClient()
        await client.create_profile()

        profile = client.get_profile()
        assert profile.memories is not None
        episodic = profile.memories.get("a2p:episodic", [])
        assert len(episodic) == 0

    @pytest.mark.asyncio
    async def test_profile_with_no_policies(self):
        """Test profile with no policies"""
        client = A2PUserClient()
        await client.create_profile()

        profile = client.get_profile()
        assert profile.access_policies == []


class TestStorageEdgeCases:
    """Test edge cases in storage"""

    @pytest.mark.asyncio
    async def test_store_retrieve_same_profile_multiple_times(self):
        """Test storing and retrieving same profile multiple times"""
        storage = MemoryStorage()
        profile = create_profile()

        await storage.set(profile.id, profile)
        await storage.set(profile.id, profile)
        await storage.set(profile.id, profile)

        retrieved = await storage.get(profile.id)
        assert retrieved is not None
        assert retrieved.id == profile.id

    @pytest.mark.asyncio
    async def test_concurrent_storage_operations(self):
        """Test concurrent storage operations"""
        storage = MemoryStorage()
        profile1 = create_profile()
        profile2 = create_profile()

        import asyncio

        await asyncio.gather(
            storage.set(profile1.id, profile1),
            storage.set(profile2.id, profile2),
        )

        retrieved1, retrieved2 = await asyncio.gather(
            storage.get(profile1.id),
            storage.get(profile2.id),
        )

        assert retrieved1 is not None
        assert retrieved2 is not None
