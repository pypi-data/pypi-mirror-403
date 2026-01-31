"""Tests for CrewAI adapter"""

import pytest
from a2p_crewai import A2PCrewMemory

from a2p import A2PUserClient, MemoryStorage, PermissionLevel, add_policy


class TestA2PCrewMemory:
    """Test CrewAI adapter"""

    @pytest.mark.asyncio
    async def test_load_user_context(self):
        """Test loading user context"""
        storage = MemoryStorage()
        user_client = A2PUserClient(storage)
        await user_client.create_profile(display_name="Alice")
        await user_client.add_memory(
            content="Senior ML Engineer",
            category="a2p:professional",
        )
        await user_client.add_memory(
            content="Prefers technical explanations",
            category="a2p:preferences.communication",
        )

        user_did = user_client.get_profile().id

        # Add policy
        profile = user_client.get_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*", "a2p:professional.*"],
        )
        await storage.set(user_did, profile)

        # Test adapter
        memory = A2PCrewMemory(
            agent_did="did:a2p:agent:crewai-test",
            default_scopes=["a2p:preferences", "a2p:professional"],
        )
        memory.client.storage = storage

        context = await memory.load_user_context(user_did)

        assert isinstance(context, str)
        assert "Senior ML Engineer" in context
        assert "technical" in context.lower()

    @pytest.mark.asyncio
    async def test_format_context(self):
        """Test context formatting"""
        memory = A2PCrewMemory(
            agent_did="did:a2p:agent:test",
            default_scopes=["a2p:preferences"],
        )

        profile_dict = {
            "common": {
                "preferences": {
                    "communication": {
                        "style": "technical",
                        "formality": "casual",
                    }
                }
            },
            "memories": {
                "a2p:professional": {
                    "occupation": "Engineer",
                }
            },
        }

        context = memory._format_context(profile_dict)
        assert "technical" in context
        assert "Engineer" in context
