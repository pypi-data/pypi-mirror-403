"""
Profile Management

Core functionality for creating, reading, and updating a2p profiles.
"""

import json
from datetime import datetime, timezone
from typing import Any

from a2p.types import (
    Common,
    CommonPreferences,
    ConsentPolicy,
    Identity,
    Memories,
    Memory,
    MemoryMetadata,
    MemorySource,
    MemoryStatus,
    Profile,
    ProfileSettings,
    ProfileType,
    SensitivityLevel,
    SubProfile,
)
from a2p.utils.id import generate_memory_id, generate_policy_id, generate_user_did, is_valid_did
from a2p.utils.scope import get_scope_sensitivity


def create_profile(
    did: str | None = None,
    display_name: str | None = None,
    profile_type: ProfileType = ProfileType.HUMAN,
    preferences: CommonPreferences | None = None,
) -> Profile:
    """Create a new empty profile"""
    profile_did = did or generate_user_did()
    now = datetime.now(timezone.utc)

    return Profile(
        id=profile_did,
        version="0.1.0-alpha",
        profileType=profile_type,
        created=now,
        updated=now,
        identity=Identity(did=profile_did, displayName=display_name),
        common=Common(preferences=preferences) if preferences else None,
        memories=Memories(),
        subProfiles=[],
        pendingProposals=[],
        accessPolicies=[],
        settings=ProfileSettings(),
    )


def update_identity(profile: Profile, **kwargs: Any) -> Profile:
    """Update profile identity"""
    identity_dict = profile.identity.model_dump(by_alias=True)
    identity_dict.update(kwargs)

    return profile.model_copy(
        update={
            "identity": Identity(**identity_dict),
            "updated": datetime.now(timezone.utc),
        }
    )


def update_preferences(profile: Profile, **kwargs: Any) -> Profile:
    """Update profile preferences"""
    current_prefs = profile.common.preferences if profile.common else None
    prefs_dict = current_prefs.model_dump(by_alias=True) if current_prefs else {}
    prefs_dict.update(kwargs)

    return profile.model_copy(
        update={
            "common": Common(preferences=CommonPreferences(**prefs_dict)),
            "updated": datetime.now(timezone.utc),
        }
    )


def add_memory(
    profile: Profile,
    content: str,
    category: str | None = None,
    source: MemorySource | None = None,
    confidence: float = 0.8,
    status: MemoryStatus = MemoryStatus.APPROVED,
    sensitivity: SensitivityLevel | None = None,
    scope: list[str] | None = None,
    tags: list[str] | None = None,
    memory_id: str | None = None,
) -> Profile:
    """Add a memory to the profile"""
    mem_id = memory_id or generate_memory_id()
    now = datetime.now(timezone.utc)

    if source is None:
        source = MemorySource(type="user_manual", timestamp=now)

    if sensitivity is None:
        sens_str = get_scope_sensitivity(category or "a2p:episodic")
        sensitivity = SensitivityLevel(sens_str)

    memory = Memory(
        id=mem_id,
        content=content,
        category=category,
        source=source,
        confidence=confidence,
        status=status,
        sensitivity=sensitivity,
        scope=scope,
        tags=tags,
        metadata=MemoryMetadata(
            approvedAt=now if status == MemoryStatus.APPROVED else None,
            useCount=0,
        ),
    )

    memories = profile.memories or Memories()
    episodic = list(memories.episodic or [])
    episodic.append(memory)

    new_memories = memories.model_copy(update={"a2p:episodic": episodic})

    return profile.model_copy(
        update={
            "memories": new_memories,
            "updated": now,
        }
    )


def update_memory(
    profile: Profile,
    memory_id: str,
    **kwargs: Any,
) -> Profile:
    """Update a memory in the profile"""
    memories = profile.memories
    if not memories:
        raise ValueError(f"Memory not found: {memory_id}")

    # Access episodic via model_dump for alias, then convert back to Memory objects
    memories_dict = memories.model_dump(by_alias=True)
    episodic_data = memories_dict.get("a2p:episodic", [])

    if not episodic_data:
        raise ValueError(f"Memory not found: {memory_id}")

    # Find memory index and convert dicts to Memory objects
    episodic = []
    memory_index = None
    for i, m_data in enumerate(episodic_data):
        if isinstance(m_data, dict):
            # Convert dict to Memory object
            memory = Memory(**m_data)
        else:
            memory = m_data
        episodic.append(memory)

        if memory.id == memory_id:
            memory_index = i

    if memory_index is None:
        raise ValueError(f"Memory not found: {memory_id}")

    # Update the memory
    memory = episodic[memory_index]
    updated_memory = memory.model_copy(update=kwargs)
    episodic[memory_index] = updated_memory

    new_memories = memories.model_copy(update={"a2p:episodic": episodic})

    return profile.model_copy(
        update={
            "memories": new_memories,
            "updated": datetime.now(timezone.utc),
        }
    )


def remove_memory(profile: Profile, memory_id: str) -> Profile:
    """Remove a memory from the profile"""
    memories = profile.memories
    if not memories:
        return profile

    # Access episodic via model_dump for alias
    memories_dict = memories.model_dump(by_alias=True)
    episodic_data = memories_dict.get("a2p:episodic", [])

    if not episodic_data:
        return profile

    # Filter out the memory to remove
    filtered_episodic = []
    for m in episodic_data:
        mem_id = m.id if hasattr(m, "id") else m.get("id")
        if mem_id != memory_id:
            filtered_episodic.append(m)

    new_memories = memories.model_copy(update={"a2p:episodic": filtered_episodic})

    return profile.model_copy(
        update={
            "memories": new_memories,
            "updated": datetime.now(timezone.utc),
        }
    )


def archive_memory(profile: Profile, memory_id: str) -> Profile:
    """Archive a memory (soft delete)"""
    return update_memory(
        profile,
        memory_id,
        status=MemoryStatus.ARCHIVED,
        metadata=MemoryMetadata(archivedAt=datetime.now(timezone.utc)),
    )


def add_sub_profile(profile: Profile, sub_profile: SubProfile) -> Profile:
    """Add a sub-profile"""
    existing = list(profile.sub_profiles or [])

    if any(sp.id == sub_profile.id for sp in existing):
        raise ValueError(f"Sub-profile already exists: {sub_profile.id}")

    existing.append(sub_profile)

    return profile.model_copy(
        update={
            "sub_profiles": existing,
            "updated": datetime.now(timezone.utc),
        }
    )


def update_sub_profile(
    profile: Profile,
    sub_profile_id: str,
    **kwargs: Any,
) -> Profile:
    """Update a sub-profile"""
    sub_profiles = list(profile.sub_profiles or [])
    index = next((i for i, sp in enumerate(sub_profiles) if sp.id == sub_profile_id), None)

    if index is None:
        raise ValueError(f"Sub-profile not found: {sub_profile_id}")

    sub_profiles[index] = sub_profiles[index].model_copy(update=kwargs)

    return profile.model_copy(
        update={
            "sub_profiles": sub_profiles,
            "updated": datetime.now(timezone.utc),
        }
    )


def remove_sub_profile(profile: Profile, sub_profile_id: str) -> Profile:
    """Remove a sub-profile"""
    sub_profiles = [sp for sp in (profile.sub_profiles or []) if sp.id != sub_profile_id]

    return profile.model_copy(
        update={
            "sub_profiles": sub_profiles,
            "updated": datetime.now(timezone.utc),
        }
    )


def add_policy(
    profile: Profile,
    agent_pattern: str,
    permissions: list[str],
    policy_id: str | None = None,
    name: str | None = None,
    allow: list[str] | None = None,
    deny: list[str] | None = None,
    **kwargs: Any,
) -> Profile:
    """Add a consent policy"""
    pol_id = policy_id or generate_policy_id()
    now = datetime.now(timezone.utc)

    policy = ConsentPolicy(
        id=pol_id,
        name=name,
        agentPattern=agent_pattern,
        permissions=permissions,
        allow=allow,
        deny=deny,
        enabled=True,
        priority=100,
        created=now,
        updated=now,
        **kwargs,
    )

    policies = list(profile.access_policies or [])
    policies.append(policy)

    return profile.model_copy(
        update={
            "access_policies": policies,
            "updated": now,
        }
    )


def update_policy(
    profile: Profile,
    policy_id: str,
    **kwargs: Any,
) -> Profile:
    """Update a consent policy"""
    policies = list(profile.access_policies or [])
    index = next((i for i, p in enumerate(policies) if p.id == policy_id), None)

    if index is None:
        raise ValueError(f"Policy not found: {policy_id}")

    kwargs["updated"] = datetime.now(timezone.utc)
    policies[index] = policies[index].model_copy(update=kwargs)

    return profile.model_copy(
        update={
            "access_policies": policies,
            "updated": datetime.now(timezone.utc),
        }
    )


def remove_policy(profile: Profile, policy_id: str) -> Profile:
    """Remove a consent policy"""
    policies = [p for p in (profile.access_policies or []) if p.id != policy_id]

    return profile.model_copy(
        update={
            "access_policies": policies,
            "updated": datetime.now(timezone.utc),
        }
    )


def get_filtered_profile(
    profile: Profile,
    allowed_scopes: list[str],
    sub_profile_id: str | None = None,
) -> dict[str, Any]:
    """Get filtered profile based on allowed scopes"""
    filtered: dict[str, Any] = {
        "id": profile.id,
        "version": profile.version,
        "profileType": profile.profile_type.value,
    }

    # Check scope permissions
    def scope_allowed(scope: str) -> bool:
        for allowed in allowed_scopes:
            if allowed == "a2p:*" or scope.startswith(allowed.replace(".*", "")):
                return True
        return False

    if scope_allowed("a2p:identity"):
        filtered["identity"] = profile.identity.model_dump(by_alias=True)

    if scope_allowed("a2p:preferences") and profile.common:
        filtered["common"] = profile.common.model_dump(by_alias=True)

    if profile.memories:
        filtered_memories: dict[str, Any] = {}
        memories_dict = profile.memories.model_dump(by_alias=True)

        for key, value in memories_dict.items():
            if value is not None and scope_allowed(key):
                if key == "a2p:episodic":
                    # Filter episodic memories by scope
                    filtered_memories[key] = [
                        m
                        for m in value
                        if not m.get("scope")
                        or any(s in allowed_scopes for s in m.get("scope", []))
                    ]
                else:
                    filtered_memories[key] = value

        filtered["memories"] = filtered_memories

    return filtered


def validate_profile(data: Any) -> bool:
    """Validate a profile structure"""
    if not isinstance(data, dict):
        return False

    if "id" not in data or not is_valid_did(data["id"]):
        return False

    if "version" not in data:
        return False

    if "profileType" not in data:
        return False

    if "identity" not in data or not isinstance(data["identity"], dict):
        return False

    if "did" not in data["identity"] or not is_valid_did(data["identity"]["did"]):
        return False

    return True


def export_profile(profile: Profile) -> str:
    """Export profile to JSON"""
    return profile.model_dump_json(by_alias=True, indent=2)


def import_profile(json_str: str) -> Profile:
    """Import profile from JSON"""
    data = json.loads(json_str)

    if not validate_profile(data):
        raise ValueError("Invalid profile structure")

    return Profile.model_validate(data)
