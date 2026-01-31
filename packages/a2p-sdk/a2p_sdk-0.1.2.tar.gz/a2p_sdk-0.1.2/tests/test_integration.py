"""Integration tests for a2p SDK

These tests verify end-to-end workflows combining multiple components
"""

import pytest

from a2p.client import (
    MemoryStorage,
    create_agent_client,
    create_user_client,
)
from a2p.core.profile import add_policy, create_profile


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""

    @pytest.mark.asyncio
    async def test_full_workflow_create_policy_access_propose(self):
        """Test complete workflow: create profile, add policy, request access, propose memory"""
        storage = MemoryStorage()

        # 1. User creates profile
        user_client = create_user_client(storage=storage)
        profile = await user_client.create_profile(display_name="Alice")

        # 2. User adds policy for agent
        updated_profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["read_scoped", "propose"],
                "allow": ["a2p:preferences.*"],
            },
        )
        await storage.set(profile.id, updated_profile)
        await user_client.load_profile(profile.id)

        # 3. Agent requests access
        agent_client = create_agent_client(
            agent_did="did:a2p:agent:local:assistant", storage=storage
        )
        access_response = await agent_client.get_profile(
            user_did=profile.id, scopes=["a2p:preferences.communication"]
        )

        assert access_response is not None

        # 4. Agent proposes memory
        proposal_response = await agent_client.propose_memory(
            user_did=profile.id,
            content="User prefers email communication",
            category="a2p:preferences.communication",
        )

        assert proposal_response is not None
        assert "proposal_id" in proposal_response or "id" in proposal_response

        # 5. User approves proposal
        await user_client.load_profile(profile.id)
        pending = user_client.get_pending_proposals()
        assert len(pending) > 0

        proposal_id = proposal_response.get("proposal_id") or proposal_response.get("id")
        memory = await user_client.approve_proposal(proposal_id)
        assert memory.content == "User prefers email communication"
        assert memory.status == "approved"

    @pytest.mark.asyncio
    async def test_multiple_agents_access_same_profile(self):
        """Test multiple agents accessing the same profile"""
        storage = MemoryStorage()

        # User creates profile with policy for all agents
        user_client = create_user_client(storage=storage)
        profile = await user_client.create_profile(display_name="Bob")

        updated_profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["read_scoped"],
                "allow": ["a2p:preferences.*"],
            },
        )
        await storage.set(profile.id, updated_profile)

        # Multiple agents request access
        agent1 = create_agent_client(agent_did="did:a2p:agent:local:agent1", storage=storage)
        agent2 = create_agent_client(agent_did="did:a2p:agent:local:agent2", storage=storage)

        response1 = await agent1.get_profile(user_did=profile.id, scopes=["a2p:preferences"])
        response2 = await agent2.get_profile(user_did=profile.id, scopes=["a2p:preferences"])

        assert response1 is not None
        assert response2 is not None

    @pytest.mark.asyncio
    async def test_profile_export_import_workflow(self):
        """Test profile export and import workflow"""
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()

        # Create profile in first storage
        client1 = create_user_client(storage=storage1)
        await client1.create_profile(display_name="Charlie")
        await client1.add_memory(content="Likes Python programming", category="a2p:preferences")

        # Export profile
        json_str = client1.export_profile()
        assert len(json_str) > 0

        # Import into second storage
        client2 = create_user_client(storage=storage2)
        imported = await client2.import_profile(json_str)

        assert imported.identity.display_name == "Charlie"
        episodic = imported.memories.get("a2p:episodic", [])
        assert len(episodic) == 1
        assert episodic[0].content == "Likes Python programming"

    @pytest.mark.asyncio
    async def test_proposal_rejection_workflow(self):
        """Test proposal rejection workflow"""
        storage = MemoryStorage()

        # User creates profile
        user_client = create_user_client(storage=storage)
        profile = await user_client.create_profile()

        # Add policy
        updated_profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["propose"],
                "allow": ["a2p:preferences.*"],
            },
        )
        await storage.set(profile.id, updated_profile)

        # Agent proposes memory
        agent_client = create_agent_client(agent_did="did:a2p:agent:local:test", storage=storage)
        proposal_response = await agent_client.propose_memory(
            user_did=profile.id, content="Incorrect information", category="a2p:preferences"
        )

        # User rejects proposal
        await user_client.load_profile(profile.id)
        proposal_id = proposal_response.get("proposal_id") or proposal_response.get("id")
        await user_client.reject_proposal(proposal_id, reason="Not accurate")

        # Verify proposal is rejected
        final_profile = user_client.get_profile()
        pending = final_profile.pending_proposals or []
        rejected = next((p for p in pending if p.id == proposal_id), None)
        assert rejected is not None
        assert rejected.status == "rejected"


class TestConcurrentOperations:
    """Test concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_profile_access(self):
        """Test concurrent profile access by multiple agents"""
        storage = MemoryStorage()
        profile = create_profile()
        await storage.set(profile.id, profile)

        agent1 = create_agent_client(agent_did="did:a2p:agent:local:a1", storage=storage)
        agent2 = create_agent_client(agent_did="did:a2p:agent:local:a2", storage=storage)

        # Add policy for both agents
        updated_profile = add_policy(
            profile,
            {
                "agent_pattern": "did:a2p:agent:*",
                "permissions": ["read_scoped"],
                "allow": ["a2p:preferences.*"],
            },
        )
        await storage.set(profile.id, updated_profile)

        # Concurrent access requests
        import asyncio

        response1, response2 = await asyncio.gather(
            agent1.get_profile(user_did=profile.id, scopes=["a2p:preferences"]),
            agent2.get_profile(user_did=profile.id, scopes=["a2p:preferences"]),
        )

        assert response1 is not None
        assert response2 is not None
