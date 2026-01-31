"""Tests for profile management"""

from datetime import datetime, timezone

import pytest

from a2p.core.profile import (
    add_memory,
    add_policy,
    add_sub_profile,
    archive_memory,
    create_profile,
    export_profile,
    get_filtered_profile,
    import_profile,
    remove_memory,
    remove_policy,
    remove_sub_profile,
    update_identity,
    update_memory,
    update_policy,
    update_preferences,
    validate_profile,
)
from a2p.types import (
    CommonPreferences,
    MemorySource,
    MemoryStatus,
    ProfileType,
    SubProfile,
)


class TestCreateProfile:
    """Test profile creation"""

    def test_create_profile_default(self):
        """Test creating profile with defaults"""
        profile = create_profile()
        assert profile.id.startswith("did:a2p:user:")
        assert profile.version == "1.0"
        assert profile.profile_type == ProfileType.HUMAN
        assert profile.identity.did == profile.id
        assert profile.memories is not None
        assert profile.access_policies == []

    def test_create_profile_with_display_name(self):
        """Test creating profile with display name"""
        profile = create_profile(display_name="Alice")
        assert profile.identity.display_name == "Alice"

    def test_create_profile_with_preferences(self):
        """Test creating profile with preferences"""
        prefs = CommonPreferences(language="en", timezone="UTC")
        profile = create_profile(preferences=prefs)
        assert profile.common is not None
        assert profile.common.preferences.language == "en"


class TestUpdateProfile:
    """Test profile updates"""

    def test_update_identity(self):
        """Test updating profile identity"""
        profile = create_profile()
        updated = update_identity(profile, display_name="Bob")
        assert updated.identity.display_name == "Bob"
        assert updated.updated > profile.updated

    def test_update_preferences(self):
        """Test updating preferences"""
        profile = create_profile()
        updated = update_preferences(profile, language="es")
        assert updated.common is not None
        assert updated.common.preferences.language == "es"
        assert updated.updated > profile.updated


class TestMemoryManagement:
    """Test memory management"""

    def test_add_memory(self):
        """Test adding a memory"""
        profile = create_profile()
        updated = add_memory(
            profile,
            content="User likes Python",
            category="a2p:preferences",
        )
        assert len(updated.memories.episodic) == 1
        memory = updated.memories.episodic[0]
        assert memory.content == "User likes Python"
        assert memory.category == "a2p:preferences"
        assert memory.status == MemoryStatus.APPROVED

    def test_add_memory_with_source(self):
        """Test adding memory with source"""
        profile = create_profile()
        source = MemorySource(type="agent_proposal", timestamp=datetime.now(timezone.utc))
        updated = add_memory(profile, content="Test", source=source)
        memory = updated.memories.episodic[0]
        assert memory.source.type == "agent_proposal"

    def test_update_memory(self):
        """Test updating a memory"""
        profile = create_profile()
        profile = add_memory(profile, content="Original", category="a2p:preferences")
        memory_id = profile.memories.episodic[0].id

        updated = update_memory(profile, memory_id, content="Updated")
        assert updated.memories.episodic[0].content == "Updated"

    def test_remove_memory(self):
        """Test removing a memory"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:preferences")
        memory_id = profile.memories.episodic[0].id

        updated = remove_memory(profile, memory_id)
        assert len(updated.memories.episodic) == 0

    def test_archive_memory(self):
        """Test archiving a memory"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:preferences")
        memory_id = profile.memories.episodic[0].id

        updated = archive_memory(profile, memory_id)
        memory = updated.memories.episodic[0]
        assert memory.status == MemoryStatus.ARCHIVED


class TestSubProfileManagement:
    """Test sub-profile management"""

    def test_add_sub_profile(self):
        """Test adding a sub-profile"""
        profile = create_profile()
        sub_profile = SubProfile(
            id="did:a2p:sub:work",
            name="Work Profile",
            specialized={},
        )
        updated = add_sub_profile(profile, sub_profile)
        assert len(updated.sub_profiles) == 1
        assert updated.sub_profiles[0].id == "did:a2p:sub:work"

    def test_add_sub_profile_duplicate(self):
        """Test adding duplicate sub-profile fails"""
        profile = create_profile()
        sub_profile = SubProfile(id="did:a2p:sub:work", name="Work", specialized={})
        profile = add_sub_profile(profile, sub_profile)

        with pytest.raises(ValueError, match="already exists"):
            add_sub_profile(profile, sub_profile)

    def test_remove_sub_profile(self):
        """Test removing a sub-profile"""
        profile = create_profile()
        sub_profile = SubProfile(id="did:a2p:sub:work", name="Work", specialized={})
        profile = add_sub_profile(profile, sub_profile)

        updated = remove_sub_profile(profile, "did:a2p:sub:work")
        assert len(updated.sub_profiles) == 0


class TestPolicyManagement:
    """Test consent policy management"""

    def test_add_policy(self):
        """Test adding a policy"""
        profile = create_profile()
        updated = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=["read", "propose"],
            allow=["a2p:preferences.*"],
        )
        assert len(updated.access_policies) == 1
        policy = updated.access_policies[0]
        assert policy.agent_pattern == "did:a2p:agent:*"
        assert "read" in policy.permissions

    def test_update_policy(self):
        """Test updating a policy"""
        profile = create_profile()
        profile = add_policy(profile, agent_pattern="did:a2p:agent:*", permissions=["read"])
        policy_id = profile.access_policies[0].id

        updated = update_policy(profile, policy_id, enabled=False)
        assert updated.access_policies[0].enabled is False

    def test_remove_policy(self):
        """Test removing a policy"""
        profile = create_profile()
        profile = add_policy(profile, agent_pattern="did:a2p:agent:*", permissions=["read"])
        policy_id = profile.access_policies[0].id

        updated = remove_policy(profile, policy_id)
        assert len(updated.access_policies) == 0


class TestProfileFiltering:
    """Test profile filtering"""

    def test_get_filtered_profile_identity(self):
        """Test filtering profile with identity scope"""
        profile = create_profile(display_name="Alice")
        filtered = get_filtered_profile(profile, ["a2p:identity"])
        assert "identity" in filtered
        assert filtered["identity"]["displayName"] == "Alice"

    def test_get_filtered_profile_preferences(self):
        """Test filtering profile with preferences scope"""
        prefs = CommonPreferences(language="en")
        profile = create_profile(preferences=prefs)
        filtered = get_filtered_profile(profile, ["a2p:preferences"])
        assert "common" in filtered
        assert filtered["common"]["preferences"]["language"] == "en"

    def test_get_filtered_profile_memories(self):
        """Test filtering profile with memory scopes"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:preferences")
        filtered = get_filtered_profile(profile, ["a2p:preferences.*"])
        assert "memories" in filtered
        assert len(filtered["memories"]["a2p:episodic"]) == 1


class TestProfileValidation:
    """Test profile validation"""

    def test_validate_profile_valid(self):
        """Test validating valid profile"""
        profile = create_profile()
        profile_dict = profile.model_dump(by_alias=True)
        assert validate_profile(profile_dict) is True

    def test_validate_profile_invalid(self):
        """Test validating invalid profile"""
        assert validate_profile({}) is False
        assert validate_profile({"id": "invalid"}) is False
        assert validate_profile(None) is False


class TestProfileImportExport:
    """Test profile import/export"""

    def test_export_profile(self):
        """Test exporting profile to JSON"""
        profile = create_profile(display_name="Alice")
        json_str = export_profile(profile)
        assert isinstance(json_str, str)
        assert "Alice" in json_str
        assert "did:a2p:user:" in json_str

    def test_import_profile(self):
        """Test importing profile from JSON"""
        profile = create_profile(display_name="Alice")
        json_str = export_profile(profile)
        imported = import_profile(json_str)
        assert imported.identity.display_name == "Alice"
        assert imported.id == profile.id

    def test_import_profile_invalid(self):
        """Test importing invalid profile fails"""
        with pytest.raises(ValueError, match="Invalid profile"):
            import_profile('{"invalid": "data"}')
