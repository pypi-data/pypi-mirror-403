"""
a2p Client

Main client for interacting with the a2p protocol.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from a2p.core.consent import (
    create_consent_receipt,
    evaluate_access,
    has_permission,
)
from a2p.core.profile import (
    add_memory,
    create_profile,
    export_profile,
    get_filtered_profile,
    import_profile,
)
from a2p.core.proposal import (
    add_proposal,
    approve_proposal,
    create_proposal,
    get_pending_proposals,
    reject_proposal,
)
from a2p.types import (
    AgentProfile,
    Memory,
    MemorySource,
    MemoryStatus,
    PermissionLevel,
    Profile,
    Proposal,
    SensitivityLevel,
)
from a2p.utils.id import generate_session_id


class ProfileStorage(ABC):
    """Abstract base class for profile storage"""

    @abstractmethod
    async def get(self, did: str) -> Profile | None:
        """Get a profile by DID"""
        ...

    @abstractmethod
    async def set(self, did: str, profile: Profile) -> None:
        """Store a profile"""
        ...

    @abstractmethod
    async def delete(self, did: str) -> None:
        """Delete a profile"""
        ...


# MemoryStorage moved to a2p.storage.memory
# Import here for backward compatibility
try:
    from a2p.storage.memory import MemoryStorage
except ImportError:
    # Fallback for backward compatibility if storage module not available
    class MemoryStorage(ProfileStorage):  # type: ignore[no-redef]
        """In-memory storage implementation"""

        def __init__(self) -> None:
            self._profiles: dict[str, Profile] = {}

        async def get(self, did: str) -> Profile | None:
            return self._profiles.get(did)

        async def set(self, did: str, profile: Profile) -> None:
            self._profiles[did] = profile

        async def delete(self, did: str) -> None:
            self._profiles.pop(did, None)


class A2PClient:
    """
    a2p Client for agents

    This client is used by AI agents to interact with user profiles.
    """

    def __init__(
        self,
        agent_did: str,
        private_key: str | None = None,
        storage: ProfileStorage | None = None,
    ) -> None:
        self.agent_did = agent_did
        self.private_key = private_key
        self.storage = storage or MemoryStorage()
        self.session_id = generate_session_id()
        self.agent_profile: AgentProfile | None = None

    def set_agent_profile(self, profile: AgentProfile) -> None:
        """Set the agent profile for trust evaluation"""
        self.agent_profile = profile

    async def request_access(
        self,
        user_did: str,
        scopes: list[str],
        sub_profile: str | None = None,
        purpose: str | None = None,
    ) -> dict[str, Any]:
        """Request access to a user's profile"""
        profile = await self.storage.get(user_did)

        if not profile:
            raise ValueError(f"Profile not found: {user_did}")

        # Evaluate access based on policies
        access_result = evaluate_access(
            profile,
            self.agent_did,
            scopes,
            self.agent_profile,
        )

        if not access_result["granted"]:
            raise PermissionError("Access denied: No matching policy grants access")

        # Create consent receipt
        consent = create_consent_receipt(
            user_did=user_did,
            agent_did=self.agent_did,
            operator_did=(
                self.agent_profile.operator.did
                if self.agent_profile and self.agent_profile.operator
                else None
            ),
            policy_id=(
                access_result["matched_policy"].id if access_result["matched_policy"] else None
            ),
            granted_scopes=access_result["allowed_scopes"],
            denied_scopes=access_result["denied_scopes"],
            permissions=access_result["permissions"],
            sub_profile=sub_profile,
            purpose=purpose,
        )

        # Get filtered profile
        filtered_profile = get_filtered_profile(
            profile,
            access_result["allowed_scopes"],
            sub_profile,
        )

        return {
            "profile": filtered_profile,
            "consent": consent,
            "filtered_scopes": access_result["allowed_scopes"],
        }

    async def get_profile(
        self,
        user_did: str,
        scopes: list[str],
        sub_profile: str | None = None,
    ) -> dict[str, Any]:
        """Get a user's profile (convenience method)"""
        response = await self.request_access(user_did, scopes, sub_profile)
        return response["profile"]

    async def propose_memory(
        self,
        user_did: str,
        content: str,
        category: str | None = None,
        memory_type: str = "episodic",
        confidence: float = 0.7,
        context: str | None = None,
        suggested_sensitivity: SensitivityLevel | None = None,
    ) -> dict[str, Any]:
        """Propose a new memory to a user's profile"""
        # Validate memory_type
        if memory_type not in ("episodic", "semantic", "procedural"):
            raise ValueError(
                f"Invalid memory_type: {memory_type}. "
                f"Must be one of: episodic, semantic, procedural"
            )

        # Check if storage has a propose_memory method (e.g., CloudStorage)
        if hasattr(self.storage, "propose_memory"):
            # Use storage's protocol endpoint for proposing memories
            return await self.storage.propose_memory(  # type: ignore
                user_did=user_did,
                content=content,
                category=category,
                memory_type=memory_type,
                confidence=confidence,
                context=context,
            )

        # Fallback to local implementation for MemoryStorage
        profile = await self.storage.get(user_did)

        if not profile:
            raise ValueError(f"Profile not found: {user_did}")

        # Check if agent has propose permission
        access_result = evaluate_access(
            profile,
            self.agent_did,
            [category or "a2p:episodic"],
            self.agent_profile,
        )

        if not has_permission(access_result["permissions"], PermissionLevel.PROPOSE):
            raise PermissionError("Access denied: Agent does not have propose permission")

        # Create proposal
        proposal = create_proposal(
            agent_did=self.agent_did,
            agent_name=(self.agent_profile.identity.name if self.agent_profile else None),
            session_id=self.session_id,
            content=content,
            category=category,
            confidence=confidence,
            context=context,
            suggested_sensitivity=suggested_sensitivity,
        )

        # Add proposal to profile
        updated_profile = add_proposal(profile, proposal)
        await self.storage.set(user_did, updated_profile)

        return {
            "proposal_id": proposal.id,
            "status": proposal.status.value,
        }

    async def check_permission(
        self,
        user_did: str,
        permission: PermissionLevel,
        scope: str | None = None,
    ) -> bool:
        """Check if agent has a specific permission for a user"""
        profile = await self.storage.get(user_did)

        if not profile:
            return False

        scopes = [scope] if scope else ["a2p:*"]
        access_result = evaluate_access(
            profile,
            self.agent_did,
            scopes,
            self.agent_profile,
        )

        return has_permission(access_result["permissions"], permission)

    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id

    def new_session(self) -> str:
        """Start a new session"""
        self.session_id = generate_session_id()
        return self.session_id


class A2PUserClient:
    """
    a2p User Client

    This client is used by users to manage their own profiles.
    """

    def __init__(self, storage: ProfileStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()
        self.profile: Profile | None = None

    async def create_profile(
        self,
        display_name: str | None = None,
    ) -> Profile:
        """Create a new profile"""
        self.profile = create_profile(display_name=display_name)
        await self.storage.set(self.profile.id, self.profile)
        return self.profile

    async def load_profile(self, did: str) -> Profile | None:
        """Load an existing profile"""
        self.profile = await self.storage.get(did)
        return self.profile

    def get_profile(self) -> Profile | None:
        """Get the current profile"""
        return self.profile

    async def save_profile(self) -> None:
        """Save the current profile"""
        if not self.profile:
            raise ValueError("No profile loaded")
        await self.storage.set(self.profile.id, self.profile)

    async def add_memory(
        self,
        content: str,
        category: str | None = None,
        sensitivity: SensitivityLevel | None = None,
        scope: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> Memory:
        """Add a memory manually"""
        if not self.profile:
            raise ValueError("No profile loaded")

        self.profile = add_memory(
            self.profile,
            content=content,
            category=category,
            sensitivity=sensitivity,
            scope=scope,
            tags=tags,
            source=MemorySource(
                type="user_manual",
                timestamp=datetime.now(timezone.utc),
            ),
            status=MemoryStatus.APPROVED,
            confidence=1.0,
        )
        await self.save_profile()

        episodic = self.profile.memories.episodic if self.profile.memories else []
        return episodic[-1] if episodic else None

    def get_pending_proposals(self) -> list[Proposal]:
        """Get pending proposals"""
        if not self.profile:
            return []
        return get_pending_proposals(self.profile)

    async def approve_proposal(
        self,
        proposal_id: str,
        edited_content: str | None = None,
        edited_category: str | None = None,
    ) -> Memory:
        """Approve a proposal"""
        if not self.profile:
            raise ValueError("No profile loaded")

        self.profile, memory = approve_proposal(
            self.profile,
            proposal_id,
            edited_content=edited_content,
            edited_category=edited_category,
        )
        await self.save_profile()
        return memory

    async def reject_proposal(
        self,
        proposal_id: str,
        reason: str | None = None,
    ) -> None:
        """Reject a proposal"""
        if not self.profile:
            raise ValueError("No profile loaded")

        self.profile = reject_proposal(self.profile, proposal_id, reason)
        await self.save_profile()

    def export_profile(self) -> str:
        """Export profile to JSON"""
        if not self.profile:
            raise ValueError("No profile loaded")
        return export_profile(self.profile)

    async def import_profile(self, json_str: str) -> Profile:
        """Import profile from JSON"""
        self.profile = import_profile(json_str)
        await self.save_profile()
        return self.profile


def create_agent_client(
    agent_did: str,
    private_key: str | None = None,
    storage: ProfileStorage | None = None,
) -> A2PClient:
    """Create an agent client"""
    return A2PClient(agent_did, private_key, storage)


def create_user_client(storage: ProfileStorage | None = None) -> A2PUserClient:
    """Create a user client"""
    return A2PUserClient(storage)
