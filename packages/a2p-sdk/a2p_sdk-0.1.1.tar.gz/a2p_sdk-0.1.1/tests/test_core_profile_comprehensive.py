"""Comprehensive tests for profile management - coverage improvement"""

import json

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
    update_sub_profile,
    validate_profile,
)
from a2p.types import MemoryStatus, PermissionLevel


class TestProfileIdentity:
    """Test profile identity operations"""

    def test_update_identity_display_name(self):
        """Test updating display name"""
        profile = create_profile()
        profile = update_identity(profile, displayName="John Doe")

        # Pydantic allows both snake_case and camelCase
        assert (
            profile.identity.display_name == "John Doe"
            or profile.identity.displayName == "John Doe"
        )
        assert profile.updated is not None

    def test_update_identity_pronouns(self):
        """Test updating pronouns"""
        profile = create_profile()
        profile = update_identity(profile, pronouns="they/them")

        assert profile.identity.pronouns == "they/them"

    def test_update_identity_multiple_fields(self):
        """Test updating multiple identity fields"""
        profile = create_profile()
        profile = update_identity(profile, displayName="Jane Smith", pronouns="she/her")

        # Pydantic allows both snake_case and camelCase
        assert (
            profile.identity.display_name == "Jane Smith"
            or profile.identity.displayName == "Jane Smith"
        )
        assert profile.identity.pronouns == "she/her"


class TestProfilePreferences:
    """Test profile preferences operations"""

    def test_update_preferences_language(self):
        """Test updating language preference"""
        profile = create_profile()
        from a2p.types import ContentPreferences

        prefs = ContentPreferences(language="en")
        profile = update_preferences(profile, content=prefs)

        assert profile.common is not None
        assert profile.common.preferences is not None
        assert profile.common.preferences.content.language == "en"

    def test_update_preferences_communication(self):
        """Test updating communication preference"""
        profile = create_profile()
        from a2p.types import CommunicationPreferences

        comm_prefs = CommunicationPreferences(preferredChannels=["email", "sms"])
        profile = update_preferences(profile, communication=comm_prefs)

        assert profile.common is not None
        assert profile.common.preferences is not None
        # Pydantic allows both snake_case and camelCase
        channels = (
            profile.common.preferences.communication.preferred_channels
            or profile.common.preferences.communication.preferredChannels
        )
        assert channels == ["email", "sms"]


class TestMemoryOperations:
    """Test memory operations"""

    def test_update_memory_content(self):
        """Test updating memory content"""
        profile = create_profile()
        profile = add_memory(profile, content="Original content", category="a2p:episodic")
        # Access episodic via model_dump for alias
        episodic_dump = (
            profile.memories.model_dump(by_alias=True).get("a2p:episodic", [])
            if profile.memories
            else []
        )
        memory_id = (
            episodic_dump[0].id
            if episodic_dump and hasattr(episodic_dump[0], "id")
            else (
                episodic_dump[0].get("id")
                if episodic_dump and isinstance(episodic_dump[0], dict)
                else None
            )
        )
        assert memory_id is not None

        profile = update_memory(profile, memory_id, content="Updated content")

        # Access via model_dump for alias
        updated_dump = (
            profile.memories.model_dump(by_alias=True).get("a2p:episodic", [])
            if profile.memories
            else []
        )
        assert len(updated_dump) == 1
        content = (
            updated_dump[0].content
            if hasattr(updated_dump[0], "content")
            else updated_dump[0].get("content")
        )
        assert content == "Updated content"

    def test_update_memory_category(self):
        """Test updating memory category"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")
        episodic = profile.memories.episodic if profile.memories else []
        memory_id = episodic[0].id if episodic else None
        assert memory_id is not None

        profile = update_memory(profile, memory_id, category="a2p:semantic")

        updated_episodic = profile.memories.episodic if profile.memories else []
        updated_semantic = profile.memories.semantic if profile.memories else []
        # Memory should be moved from episodic to semantic
        assert len(updated_episodic) == 0
        assert len(updated_semantic) == 1

    def test_remove_memory(self):
        """Test removing a memory"""
        profile = create_profile()
        profile = add_memory(profile, content="To be removed", category="a2p:episodic")
        episodic = profile.memories.episodic if profile.memories else []
        memory_id = episodic[0].id if episodic else None
        assert memory_id is not None

        profile = remove_memory(profile, memory_id)

        updated_episodic = profile.memories.episodic if profile.memories else []
        assert len(updated_episodic) == 0

    def test_archive_memory(self):
        """Test archiving a memory"""
        profile = create_profile()
        profile = add_memory(profile, content="To be archived", category="a2p:episodic")
        episodic = profile.memories.episodic if profile.memories else []
        memory_id = episodic[0].id if episodic else None
        assert memory_id is not None

        profile = archive_memory(profile, memory_id)

        updated_episodic = profile.memories.episodic if profile.memories else []
        assert len(updated_episodic) == 1
        assert updated_episodic[0].status == MemoryStatus.ARCHIVED
        assert updated_episodic[0].metadata.archived_at is not None


class TestSubProfileOperations:
    """Test sub-profile operations"""

    def test_add_sub_profile(self):
        """Test adding a sub-profile"""
        from a2p.types import SubProfile

        profile = create_profile()
        sub_profile = SubProfile(id="sub_work", name="Work Profile", context="work")
        profile = add_sub_profile(profile, sub_profile)

        assert len(profile.sub_profiles) == 1
        assert profile.sub_profiles[0].name == "Work Profile"
        assert profile.sub_profiles[0].context == "work"

    def test_update_sub_profile(self):
        """Test updating a sub-profile"""
        profile = create_profile()
        profile = add_sub_profile(profile, name="Original", context="work")
        sub_profile_id = profile.sub_profiles[0].id

        profile = update_sub_profile(profile, sub_profile_id, name="Updated")

        assert profile.sub_profiles[0].name == "Updated"

    def test_remove_sub_profile(self):
        """Test removing a sub-profile"""
        from a2p.types import SubProfile

        profile = create_profile()
        sub_profile = SubProfile(id="sub_work", name="To remove", context="work")
        profile = add_sub_profile(profile, sub_profile)
        sub_profile_id = profile.sub_profiles[0].id

        profile = remove_sub_profile(profile, sub_profile_id)

        assert len(profile.sub_profiles) == 0


class TestPolicyOperations:
    """Test policy operations"""

    def test_update_policy(self):
        """Test updating a policy"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        policy_id = profile.access_policies[0].id

        profile = update_policy(profile, policy_id, name="Updated Policy")

        assert profile.access_policies[0].name == "Updated Policy"

    def test_remove_policy(self):
        """Test removing a policy"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        policy_id = profile.access_policies[0].id

        profile = remove_policy(profile, policy_id)

        assert len(profile.access_policies) == 0


class TestProfileFiltering:
    """Test profile filtering"""

    def test_get_filtered_profile_with_scopes(self):
        """Test filtering profile by scopes"""
        profile = create_profile()
        profile = add_memory(
            profile,
            content="Public memory",
            category="a2p:episodic",
            scope=["a2p:preferences.communication"],
        )
        profile = add_memory(
            profile, content="Private memory", category="a2p:episodic", scope=["a2p:health.*"]
        )

        filtered = get_filtered_profile(profile, allowed_scopes=["a2p:preferences.*"])

        # get_filtered_profile returns a dict
        assert isinstance(filtered, dict)
        assert "memories" in filtered
        memories_dict = filtered["memories"]
        episodic = memories_dict.get("a2p:episodic", []) if isinstance(memories_dict, dict) else []
        assert len(episodic) == 1
        content = (
            episodic[0].get("content") if isinstance(episodic[0], dict) else episodic[0].content
        )
        assert content == "Public memory"

    def test_get_filtered_profile_no_scopes(self):
        """Test filtering profile with no allowed scopes"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")

        filtered = get_filtered_profile(profile, allowed_scopes=[])

        # get_filtered_profile returns a dict
        assert isinstance(filtered, dict)
        # Should return empty or no memories
        if "memories" in filtered:
            memories_dict = filtered["memories"]
            episodic = (
                memories_dict.get("a2p:episodic", []) if isinstance(memories_dict, dict) else []
            )
            assert len(episodic) == 0


class TestProfileValidation:
    """Test profile validation"""

    def test_validate_profile_valid(self):
        """Test validating a valid profile"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")

        # validate_profile expects a dict, not a Profile object
        profile_dict = profile.model_dump(by_alias=True)
        result = validate_profile(profile_dict)

        # validate_profile returns bool
        assert result is True

    def test_validate_profile_invalid_did(self):
        """Test validating profile with invalid DID"""
        profile = create_profile()
        profile = profile.model_copy(update={"id": "invalid-did"})

        result = validate_profile(profile)

        # validate_profile returns bool
        assert result is False


class TestProfileExportImport:
    """Test profile export and import"""

    def test_export_profile(self):
        """Test exporting a profile"""
        profile = create_profile()
        profile = add_memory(profile, content="Test memory", category="a2p:episodic")
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )

        exported_str = export_profile(profile)
        exported = json.loads(exported_str)

        assert exported["id"] == profile.id
        assert exported["version"] == profile.version
        assert "memories" in exported
        assert "accessPolicies" in exported or "access_policies" in exported

    def test_import_profile(self):
        """Test importing a profile"""
        profile = create_profile()
        profile = add_memory(profile, content="Test", category="a2p:episodic")
        exported_str = export_profile(profile)

        imported = import_profile(exported_str)

        assert imported.id == profile.id
        episodic = (
            imported.memories.model_dump(by_alias=True).get("a2p:episodic", [])
            if imported.memories
            else []
        )
        assert len(episodic) == 1
        content = (
            episodic[0].content if hasattr(episodic[0], "content") else episodic[0].get("content")
        )
        assert content == "Test"

    def test_import_profile_invalid(self):
        """Test importing an invalid profile"""
        import json

        invalid_data = json.dumps({"id": "invalid", "version": "1.0"})

        with pytest.raises((ValueError, Exception)):
            import_profile(invalid_data)
