"""Tests for error handling in a2p clients"""

import pytest

from a2p.client import A2PClient, A2PUserClient, MemoryStorage
from a2p.core.profile import create_profile


class TestA2PClientErrorHandling:
    """Test error handling in A2PClient"""

    @pytest.mark.asyncio
    async def test_request_access_profile_not_found(self):
        """Test requesting access to non-existent profile"""
        client = A2PClient(agent_did="did:a2p:agent:local:test", storage=MemoryStorage())

        with pytest.raises(Exception, match="Profile not found"):
            await client.get_profile(
                user_did="did:a2p:user:local:nonexistent", scopes=["a2p:preferences"]
            )

    @pytest.mark.asyncio
    async def test_request_access_denied(self):
        """Test requesting access when denied"""
        storage = MemoryStorage()
        profile = create_profile()
        await storage.set(profile.id, profile)

        client = A2PClient(agent_did="did:a2p:agent:local:test", storage=storage)

        with pytest.raises(Exception, match="Access denied"):
            await client.get_profile(user_did=profile.id, scopes=["a2p:preferences"])

    @pytest.mark.asyncio
    async def test_propose_memory_profile_not_found(self):
        """Test proposing memory to non-existent profile"""
        client = A2PClient(agent_did="did:a2p:agent:local:test", storage=MemoryStorage())

        with pytest.raises(Exception, match="Profile not found"):
            await client.propose_memory(
                user_did="did:a2p:user:local:nonexistent", content="Test proposal"
            )


class TestA2PUserClientErrorHandling:
    """Test error handling in A2PUserClient"""

    @pytest.mark.asyncio
    async def test_load_profile_not_found(self):
        """Test loading non-existent profile"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="Profile not found"):
            await client.load_profile("did:a2p:user:local:nonexistent")

    @pytest.mark.asyncio
    async def test_approve_proposal_not_found(self):
        """Test approving non-existent proposal"""
        client = A2PUserClient()
        await client.create_profile()

        with pytest.raises(Exception, match="Proposal not found"):
            await client.approve_proposal("non-existent-proposal-id")

    @pytest.mark.asyncio
    async def test_reject_proposal_not_found(self):
        """Test rejecting non-existent proposal"""
        client = A2PUserClient()
        await client.create_profile()

        with pytest.raises(Exception, match="Proposal not found"):
            await client.reject_proposal("non-existent-proposal-id")

    @pytest.mark.asyncio
    async def test_add_memory_without_profile(self):
        """Test adding memory without profile"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="No profile loaded"):
            await client.add_memory(content="Test memory", category="a2p:preferences")

    @pytest.mark.asyncio
    async def test_update_memory_without_profile(self):
        """Test updating memory without profile"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="No profile loaded"):
            await client.update_memory(memory_id="mem_123", content="Updated content")

    @pytest.mark.asyncio
    async def test_remove_memory_without_profile(self):
        """Test removing memory without profile"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="No profile loaded"):
            await client.remove_memory("mem_123")

    @pytest.mark.asyncio
    async def test_export_profile_without_profile(self):
        """Test exporting profile without profile"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="No profile loaded"):
            client.export_profile()

    @pytest.mark.asyncio
    async def test_import_profile_invalid_json(self):
        """Test importing invalid JSON"""
        client = A2PUserClient()

        with pytest.raises(Exception):
            await client.import_profile("invalid json")

    @pytest.mark.asyncio
    async def test_import_profile_invalid_structure(self):
        """Test importing invalid profile structure"""
        client = A2PUserClient()

        with pytest.raises(Exception, match="Invalid profile"):
            await client.import_profile('{"invalid": "structure"}')
