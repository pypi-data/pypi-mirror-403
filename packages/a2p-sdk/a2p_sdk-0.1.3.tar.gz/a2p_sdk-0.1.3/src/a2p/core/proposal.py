"""
Proposal Management

Functionality for creating, reviewing, and managing memory proposals.
"""

from datetime import datetime, timedelta, timezone

from a2p.types import (
    Memory,
    MemoryMetadata,
    MemorySource,
    MemoryStatus,
    Profile,
    Proposal,
    ProposalAction,
    ProposalResolution,
    ProposalStatus,
    ProposedMemory,
    SensitivityLevel,
)
from a2p.utils.id import generate_memory_id, generate_proposal_id
from a2p.utils.scope import get_scope_sensitivity


def create_proposal(
    agent_did: str,
    content: str,
    agent_name: str | None = None,
    session_id: str | None = None,
    category: str | None = None,
    confidence: float = 0.7,
    context: str | None = None,
    suggested_sensitivity: SensitivityLevel | None = None,
    suggested_scope: list[str] | None = None,
    suggested_tags: list[str] | None = None,
    expires_in_days: int = 7,
    priority: str = "normal",
) -> Proposal:
    """Create a new memory proposal"""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expires_in_days)

    return Proposal(
        id=generate_proposal_id(),
        proposedBy={
            "agentDid": agent_did,
            "agentName": agent_name,
            "sessionId": session_id,
        },
        proposedAt=now,
        memory=ProposedMemory(
            content=content,
            category=category,
            confidence=confidence,
            suggestedSensitivity=suggested_sensitivity,
            suggestedScope=suggested_scope,
            suggestedTags=suggested_tags,
        ),
        context=context,
        status=ProposalStatus.PENDING,
        expiresAt=expires_at,
        priority=priority,
    )


def add_proposal(profile: Profile, proposal: Proposal) -> Profile:
    """Add a proposal to a profile"""
    existing = list(profile.pending_proposals or [])

    if any(p.id == proposal.id for p in existing):
        raise ValueError(f"Proposal already exists: {proposal.id}")

    existing.append(proposal)

    return profile.model_copy(
        update={
            "pending_proposals": existing,
            "updated": datetime.now(timezone.utc),
        }
    )


def approve_proposal(
    profile: Profile,
    proposal_id: str,
    edited_content: str | None = None,
    edited_category: str | None = None,
    edited_sensitivity: SensitivityLevel | None = None,
    edited_scope: list[str] | None = None,
    edited_tags: list[str] | None = None,
) -> tuple[Profile, Memory]:
    """Approve a proposal and create a memory"""
    proposals = list(profile.pending_proposals or [])
    proposal_index = next((i for i, p in enumerate(proposals) if p.id == proposal_id), None)

    if proposal_index is None:
        raise ValueError(f"Proposal not found: {proposal_id}")

    proposal = proposals[proposal_index]

    if proposal.status != ProposalStatus.PENDING:
        raise ValueError(f"Proposal is not pending: {proposal.status}")

    now = datetime.now(timezone.utc)
    memory_id = generate_memory_id()

    is_edited = bool(
        edited_content or edited_category or edited_sensitivity or edited_scope or edited_tags
    )

    # Determine sensitivity
    final_category = edited_category or proposal.memory.category
    final_sensitivity = (
        edited_sensitivity
        or proposal.memory.suggested_sensitivity
        or SensitivityLevel(get_scope_sensitivity(final_category or "a2p:episodic"))
    )

    # Create the memory
    memory = Memory(
        id=memory_id,
        content=edited_content or proposal.memory.content,
        category=final_category,
        source=MemorySource(
            type="agent_proposal",
            agentDid=proposal.proposed_by.get("agentDid"),
            agentName=proposal.proposed_by.get("agentName"),
            sessionId=proposal.proposed_by.get("sessionId"),
            timestamp=proposal.proposed_at,
            context=proposal.context,
        ),
        confidence=proposal.memory.confidence or 0.7,
        status=MemoryStatus.APPROVED,
        sensitivity=final_sensitivity,
        scope=edited_scope or proposal.memory.suggested_scope,
        tags=edited_tags or proposal.memory.suggested_tags,
        metadata=MemoryMetadata(
            approvedAt=now,
            useCount=0,
            initialConfidence=proposal.memory.confidence,
        ),
    )

    # Update the proposal
    updated_proposal = proposal.model_copy(
        update={
            "status": ProposalStatus.APPROVED,
            "resolution": ProposalResolution(
                resolvedAt=now,
                action=ProposalAction.APPROVED_WITH_EDITS if is_edited else ProposalAction.APPROVED,
                editedContent=edited_content,
                editedCategory=edited_category,
                createdMemoryId=memory_id,
            ),
        }
    )

    proposals[proposal_index] = updated_proposal

    # Update memories
    memories = profile.memories
    episodic = list(memories.episodic or []) if memories else []
    episodic.append(memory)

    new_memories = (memories or profile.memories).model_copy(update={"a2p:episodic": episodic})

    updated_profile = profile.model_copy(
        update={
            "pending_proposals": proposals,
            "memories": new_memories,
            "updated": now,
        }
    )

    return updated_profile, memory


def reject_proposal(
    profile: Profile,
    proposal_id: str,
    reason: str | None = None,
) -> Profile:
    """Reject a proposal"""
    proposals = list(profile.pending_proposals or [])
    proposal_index = next((i for i, p in enumerate(proposals) if p.id == proposal_id), None)

    if proposal_index is None:
        raise ValueError(f"Proposal not found: {proposal_id}")

    proposal = proposals[proposal_index]

    if proposal.status != ProposalStatus.PENDING:
        raise ValueError(f"Proposal is not pending: {proposal.status}")

    now = datetime.now(timezone.utc)

    updated_proposal = proposal.model_copy(
        update={
            "status": ProposalStatus.REJECTED,
            "resolution": ProposalResolution(
                resolvedAt=now,
                action=ProposalAction.REJECTED,
                reason=reason,
            ),
        }
    )

    proposals[proposal_index] = updated_proposal

    return profile.model_copy(
        update={
            "pending_proposals": proposals,
            "updated": now,
        }
    )


def withdraw_proposal(profile: Profile, proposal_id: str) -> Profile:
    """Withdraw a proposal (agent-initiated)"""
    proposals = list(profile.pending_proposals or [])
    proposal_index = next((i for i, p in enumerate(proposals) if p.id == proposal_id), None)

    if proposal_index is None:
        raise ValueError(f"Proposal not found: {proposal_id}")

    proposal = proposals[proposal_index]

    if proposal.status != ProposalStatus.PENDING:
        raise ValueError(f"Proposal is not pending: {proposal.status}")

    now = datetime.now(timezone.utc)

    updated_proposal = proposal.model_copy(
        update={
            "status": ProposalStatus.WITHDRAWN,
            "resolution": ProposalResolution(
                resolvedAt=now,
                action=ProposalAction.WITHDRAWN,
            ),
        }
    )

    proposals[proposal_index] = updated_proposal

    return profile.model_copy(
        update={
            "pending_proposals": proposals,
            "updated": now,
        }
    )


def get_pending_proposals(profile: Profile) -> list[Proposal]:
    """Get pending proposals"""
    return [p for p in (profile.pending_proposals or []) if p.status == ProposalStatus.PENDING]


def get_proposals_by_agent(profile: Profile, agent_did: str) -> list[Proposal]:
    """Get proposals by agent"""
    return [
        p for p in (profile.pending_proposals or []) if p.proposed_by.get("agentDid") == agent_did
    ]


def expire_proposals(profile: Profile) -> Profile:
    """Expire old proposals"""
    now = datetime.now(timezone.utc)
    proposals = list(profile.pending_proposals or [])
    has_expired = False

    for i, proposal in enumerate(proposals):
        if (
            proposal.status == ProposalStatus.PENDING
            and proposal.expires_at
            and proposal.expires_at < now
        ):
            has_expired = True
            proposals[i] = proposal.model_copy(
                update={
                    "status": ProposalStatus.EXPIRED,
                    "resolution": ProposalResolution(
                        resolvedAt=now,
                        action=ProposalAction.EXPIRED,
                    ),
                }
            )

    if not has_expired:
        return profile

    return profile.model_copy(
        update={
            "pending_proposals": proposals,
            "updated": now,
        }
    )


def cleanup_resolved_proposals(
    profile: Profile,
    keep_days: int = 30,
) -> Profile:
    """Clean up resolved proposals"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    proposals = profile.pending_proposals or []

    filtered = [
        p
        for p in proposals
        if p.status == ProposalStatus.PENDING
        or not p.resolution
        or not p.resolution.resolved_at
        or p.resolution.resolved_at > cutoff
    ]

    if len(filtered) == len(proposals):
        return profile

    return profile.model_copy(
        update={
            "pending_proposals": filtered,
            "updated": datetime.now(timezone.utc),
        }
    )


def find_similar_memories(
    profile: Profile,
    content: str,
    threshold: float = 0.5,
) -> list[Memory]:
    """Find similar existing memories"""
    memories = profile.memories
    if not memories:
        return []

    # Access episodic memories - Pydantic stores alias data separately
    # Try direct attribute first, then model_dump for alias
    episodic = getattr(memories, "episodic", None)
    if episodic is None:
        # Try accessing via model_dump to get alias value
        try:
            memories_dict = memories.model_dump(by_alias=True)
            episodic = memories_dict.get("a2p:episodic", [])
        except Exception:
            episodic = []

    if not episodic:
        return []

    content_lower = content.lower()
    words = [w for w in content_lower.split() if len(w) > 3]

    similar = []
    for memory in episodic:
        # Memory might be a dict (from model_dump) or Memory object
        if isinstance(memory, dict):
            memory_content = memory.get("content", "")
        else:
            memory_content = memory.content
        memory_lower = memory_content.lower()
        matching_words = [w for w in words if w in memory_lower]
        if words:
            similarity = len(matching_words) / len(words)
            if similarity > threshold:
                # Convert dict back to Memory object if needed
                if isinstance(memory, dict):
                    from a2p.types import Memory

                    similar.append(Memory(**memory))
                else:
                    similar.append(memory)

    return similar
