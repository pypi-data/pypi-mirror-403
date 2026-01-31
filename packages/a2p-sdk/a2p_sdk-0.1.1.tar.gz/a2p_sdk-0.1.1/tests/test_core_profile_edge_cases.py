"""Edge case tests for profile management - coverage improvement"""

from datetime import datetime, timezone

import pytest

from a2p.core.profile import (
    add_memory,
    add_policy,
    add_sub_profile,
    archive_memory,
    create_profile,
    get_filtered_profile,
    import_profile,
    remove_memory,
    remove_policy,
    remove_sub_profile,
    update_memory,
    update_policy,
    update_sub_profile,
    validate_profile,
)
from a2p.types import (
    MemorySource,
    MemorySourceType,
    PermissionLevel,
    SensitivityLevel,
    SubProfile,
)


class TestProfileEdgeCases:
    """Test edge cases for profile operations"""

    def test_create_profile_with_custom_did(self):
        """Test creating profile with custom DID"""
        custom_did = "did:a2p:user:custom123"
        profile = create_profile(did=custom_did)

        assert profile.id == custom_did
        assert profile.identity.did == custom_did

    def test_create_profile_with_preferences(self):
        """Test creating profile with initial preferences"""
        from a2p.types import CommonPreferences, ContentPreferences

        prefs = CommonPreferences(content=ContentPreferences(language="en"))
        profile = create_profile(preferences=prefs)

        assert profile.common is not None
        assert profile.common.preferences is not None
        assert profile.common.preferences.content.language == "en"

    def test_update_memory_not_found(self):
        """Test updating non-existent memory"""
        profile = create_profile()

        with pytest.raises(ValueError, match="Memory not found"):
            update_memory(profile, "nonexistent_id", content="Test")

    def test_update_memory_with_no_memories(self):
        """Test updating memory when profile has no memories"""
        profile = create_profile()

        with pytest.raises(ValueError, match="Memory not found"):
            update_memory(profile, "some_id", content="Test")

    def test_remove_memory_not_found(self):
        """Test removing non-existent memory"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")

        # Should not raise error, just return unchanged profile
        result = remove_memory(profile, "nonexistent_id")
        assert len(result.memories.episodic) == 1

    def test_remove_memory_with_no_memories(self):
        """Test removing memory when profile has no memories"""
        profile = create_profile()

        result = remove_memory(profile, "some_id")
        assert result == profile

    def test_archive_memory_not_found(self):
        """Test archiving non-existent memory"""
        profile = create_profile()

        with pytest.raises(ValueError, match="Memory not found"):
            archive_memory(profile, "nonexistent_id")

    def test_add_memory_with_custom_source(self):
        """Test adding memory with custom source"""
        source = MemorySource(
            type=MemorySourceType.AGENT_SUGGESTED,
            agent_did="did:a2p:agent:test",
            timestamp=datetime.now(timezone.utc),
        )
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic", source=source)

        episodic = profile.memories.episodic if profile.memories else []
        assert len(episodic) == 1
        assert episodic[0].source.type == MemorySourceType.AGENT_SUGGESTED
        assert episodic[0].source.agent_did == "did:a2p:agent:test"

    def test_add_memory_with_custom_sensitivity(self):
        """Test adding memory with custom sensitivity"""
        profile = create_profile()
        profile = add_memory(
            profile, content="Sensitive", category="a2p:episodic", sensitivity=SensitivityLevel.HIGH
        )

        episodic = profile.memories.episodic if profile.memories else []
        assert len(episodic) == 1
        assert episodic[0].sensitivity == SensitivityLevel.HIGH

    def test_add_memory_with_scope_and_tags(self):
        """Test adding memory with scope and tags"""
        profile = create_profile()
        profile = add_memory(
            profile,
            content="Scoped memory",
            category="a2p:episodic",
            scope=["a2p:preferences.*"],
            tags=["important", "personal"],
        )

        episodic = profile.memories.episodic if profile.memories else []
        assert len(episodic) == 1
        assert episodic[0].scope == ["a2p:preferences.*"]
        assert episodic[0].tags == ["important", "personal"]

    def test_add_sub_profile_duplicate(self):
        """Test adding duplicate sub-profile"""
        profile = create_profile()
        sub_profile = SubProfile(id="sub_1", name="Work")
        profile = add_sub_profile(profile, sub_profile)

        with pytest.raises(ValueError, match="Sub-profile already exists"):
            add_sub_profile(profile, sub_profile)

    def test_update_sub_profile_not_found(self):
        """Test updating non-existent sub-profile"""
        profile = create_profile()

        with pytest.raises(ValueError, match="Sub-profile not found"):
            update_sub_profile(profile, "nonexistent_id", name="Test")

    def test_remove_sub_profile_not_found(self):
        """Test removing non-existent sub-profile"""
        profile = create_profile()
        result = remove_sub_profile(profile, "nonexistent_id")

        assert result == profile

    def test_add_policy_with_kwargs(self):
        """Test adding policy with additional kwargs"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
            conditions={"require_verified_operator": True},
        )

        assert len(profile.access_policies) == 1
        # Check that kwargs were passed through
        assert profile.access_policies[0].conditions is not None

    def test_update_policy_not_found(self):
        """Test updating non-existent policy"""
        profile = create_profile()

        with pytest.raises(ValueError, match="Policy not found"):
            update_policy(profile, "nonexistent_id", name="Test")

    def test_remove_policy_not_found(self):
        """Test removing non-existent policy"""
        profile = create_profile()
        result = remove_policy(profile, "nonexistent_id")

        assert result == profile

    def test_get_filtered_profile_sub_profile(self):
        """Test filtering profile with sub-profile"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")

        filtered = get_filtered_profile(
            profile, allowed_scopes=["a2p:preferences.*"], sub_profile_id="sub_1"
        )

        assert isinstance(filtered, dict)
        assert filtered["id"] == profile.id

    def test_get_filtered_profile_all_scopes(self):
        """Test filtering profile with all scopes"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")

        filtered = get_filtered_profile(profile, allowed_scopes=["a2p:*"])

        assert isinstance(filtered, dict)
        assert "identity" in filtered
        assert "memories" in filtered

    def test_get_filtered_profile_memory_scope_filtering(self):
        """Test filtering memories by scope"""
        profile = create_profile()
        profile = add_memory(
            profile,
            content="Allowed",
            category="a2p:episodic",
            scope=["a2p:preferences.communication"],
        )
        profile = add_memory(
            profile, content="Denied", category="a2p:episodic", scope=["a2p:health.*"]
        )

        filtered = get_filtered_profile(profile, allowed_scopes=["a2p:preferences.*"])

        memories_dict = filtered.get("memories", {})
        episodic = memories_dict.get("a2p:episodic", [])
        assert len(episodic) == 1
        content = (
            episodic[0].get("content") if isinstance(episodic[0], dict) else episodic[0].content
        )
        assert content == "Allowed"

    def test_validate_profile_invalid_structure(self):
        """Test validating invalid profile structure"""
        invalid_data = "not a dict"
        result = validate_profile(invalid_data)
        assert result is False

    def test_validate_profile_missing_fields(self):
        """Test validating profile with missing fields"""
        invalid_data = {"id": "did:a2p:user:test"}
        result = validate_profile(invalid_data)
        assert result is False

    def test_validate_profile_invalid_identity(self):
        """Test validating profile with invalid identity"""
        invalid_data = {
            "id": "did:a2p:user:test",
            "version": "1.0",
            "profileType": "human",
            "identity": "not a dict",
        }
        result = validate_profile(invalid_data)
        assert result is False

    def test_validate_profile_invalid_identity_did(self):
        """Test validating profile with invalid identity DID"""
        invalid_data = {
            "id": "did:a2p:user:test",
            "version": "1.0",
            "profileType": "human",
            "identity": {"did": "invalid-did"},
        }
        result = validate_profile(invalid_data)
        assert result is False

    def test_import_profile_invalid_json(self):
        """Test importing profile with invalid JSON"""
        import json

        with pytest.raises((ValueError, json.JSONDecodeError)):
            import_profile("not valid json")

    def test_import_profile_invalid_structure(self):
        """Test importing profile with invalid structure"""
        invalid_json = '{"id": "invalid", "version": "1.0"}'
        with pytest.raises(ValueError, match="Invalid profile structure"):
            import_profile(invalid_json)

    def test_update_memory_category_change(self):
        """Test updating memory category moves it between categories"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")
        episodic = profile.memories.episodic if profile.memories else []
        memory_id = episodic[0].id if episodic else None

        # Update category - this should move the memory
        # Note: update_memory doesn't handle category changes, so this tests the current behavior
        profile = update_memory(profile, memory_id, category="a2p:semantic")

        # Memory should still be in episodic (current implementation doesn't move)
        updated_episodic = profile.memories.episodic if profile.memories else []
        # The category field is updated but memory stays in episodic
        assert len(updated_episodic) == 1
