"""Comprehensive tests for proposal management - coverage improvement"""

from datetime import datetime, timedelta, timezone

from a2p.core.profile import add_memory, create_profile
from a2p.core.proposal import (
    add_proposal,
    approve_proposal,
    cleanup_resolved_proposals,
    create_proposal,
    expire_proposals,
    find_similar_memories,
    get_proposals_by_agent,
    reject_proposal,
    withdraw_proposal,
)


class TestCleanupResolvedProposals:
    """Test cleanup resolved proposals"""

    def test_cleanup_keeps_pending(self):
        """Test that pending proposals are kept"""
        profile = create_profile()
        proposal = create_proposal(agent_did="did:a2p:agent:test", content="Pending proposal")
        profile = add_proposal(profile, proposal)

        updated = cleanup_resolved_proposals(profile)

        # Function returns with pendingProposals (camelCase), but Pydantic allows both
        pending = (
            getattr(updated, "pendingProposals", None)
            or getattr(updated, "pending_proposals", None)
            or []
        )
        assert len(pending) == 1
        assert pending[0].status == "pending"

    def test_cleanup_keeps_recently_resolved(self):
        """Test that recently resolved proposals are kept"""
        profile = create_profile()
        proposal = create_proposal(agent_did="did:a2p:agent:test", content="Recent proposal")
        profile = add_proposal(profile, proposal)
        profile, _ = approve_proposal(profile, proposal.id)

        # After approval, proposal status is "approved" (not "pending")
        # But it has a resolution with resolved_at, so it should be kept if recent
        assert profile.pending_proposals is not None
        assert len(profile.pending_proposals) == 1
        assert profile.pending_proposals[0].status == "approved"
        assert profile.pending_proposals[0].resolution is not None

        updated = cleanup_resolved_proposals(profile, keep_days=30)

        # Should keep the recently resolved proposal
        pending = (
            getattr(updated, "pendingProposals", None)
            or getattr(updated, "pending_proposals", None)
            or []
        )
        assert len(pending) == 1

    def test_cleanup_removes_old_resolved(self):
        """Test that old resolved proposals are removed"""
        from a2p.types import ProposalAction, ProposalResolution

        profile = create_profile()
        proposal = create_proposal(agent_did="did:a2p:agent:test", content="Old proposal")
        profile = add_proposal(profile, proposal)
        proposal_id = profile.pending_proposals[0].id
        profile, _ = approve_proposal(profile, proposal_id)

        # Manually set old resolution date
        pending = list(profile.pending_proposals)
        if pending and pending[0].resolution:
            old_resolution = ProposalResolution(
                resolved_at=datetime.now(timezone.utc) - timedelta(days=35),
                action=ProposalAction.APPROVED,
                created_memory_id=pending[0].resolution.created_memory_id,
            )
            pending[0] = pending[0].model_copy(update={"resolution": old_resolution})
        profile = profile.model_copy(update={"pending_proposals": pending})

        updated = cleanup_resolved_proposals(profile, keep_days=30)

        pending = (
            getattr(updated, "pendingProposals", None)
            or getattr(updated, "pending_proposals", None)
            or []
        )
        assert len(pending) == 0

    def test_cleanup_default_keep_days(self):
        """Test cleanup with default keepDays"""
        profile = create_profile()
        proposal = create_proposal(agent_did="did:a2p:agent:test", content="Recent proposal")
        profile = add_proposal(profile, proposal)
        proposal_id = profile.pending_proposals[0].id
        profile, _ = approve_proposal(profile, proposal_id)

        updated = cleanup_resolved_proposals(profile)

        assert len(updated.pending_proposals) == 1

    def test_cleanup_keeps_proposals_without_resolution_date(self):
        """Test that proposals without resolution date are kept"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test", content="Proposal without resolution"
        )
        profile = add_proposal(profile, proposal)
        profile = reject_proposal(profile, proposal.id)

        # Remove resolution date by creating new proposal without resolution
        pending = list(profile.pending_proposals)
        if pending:
            # Create a copy without resolution
            pending[0] = pending[0].model_copy(update={"resolution": None}, deep=True)
        profile = profile.model_copy(update={"pendingProposals": pending})

        updated = cleanup_resolved_proposals(profile)

        assert len(updated.pending_proposals) == 1


class TestFindSimilarMemories:
    """Test find similar memories"""

    def test_find_similar_memories_word_overlap(self):
        """Test finding similar memories based on word overlap"""
        profile = create_profile()
        profile = add_memory(
            profile, content="User likes to play tennis on weekends", category="a2p:episodic"
        )
        profile = add_memory(
            profile, content="User prefers coffee over tea", category="a2p:episodic"
        )

        # Verify memories were added
        assert profile.memories is not None
        assert profile.memories.episodic is not None
        assert len(profile.memories.episodic) == 2

        # Algorithm: filters words > 3 chars, needs >50% similarity
        # Search "User likes to play tennis" -> words: ["user", "likes", "play", "tennis"]
        # (4 words, all > 3 chars)
        # Memory "User likes to play tennis on weekends" includes all 4 words
        # Similarity: 4/4 = 1.0 > 0.5 ✓
        similar = find_similar_memories(profile, "User likes to play tennis")

        assert len(similar) == 1
        assert "tennis" in similar[0].content.lower()

    def test_find_similar_memories_no_match(self):
        """Test when no similar memories found"""
        profile = create_profile()
        profile = add_memory(profile, content="User likes coffee", category="a2p:episodic")

        similar = find_similar_memories(profile, "User loves hiking mountains")

        assert len(similar) == 0

    def test_find_similar_memories_empty_profile(self):
        """Test with empty profile"""
        profile = create_profile()

        similar = find_similar_memories(profile, "Some content")

        assert len(similar) == 0

    def test_find_similar_memories_case_insensitive(self):
        """Test case insensitive matching"""
        profile = create_profile()
        profile = add_memory(profile, content="User LIKES TENNIS", category="a2p:episodic")

        # Verify memory was added (check via model_dump for alias)
        assert profile.memories is not None
        episodic_dump = profile.memories.model_dump(by_alias=True).get("a2p:episodic", [])
        assert len(episodic_dump) == 1

        # Search "user likes tennis" -> words: ["user", "likes", "tennis"] (3 words, all > 3 chars)
        # Memory "User LIKES TENNIS" includes all 3 words (case insensitive)
        # Similarity: 3/3 = 1.0 > 0.5 ✓
        similar = find_similar_memories(profile, "user likes tennis")

        assert len(similar) == 1

    def test_find_similar_memories_threshold(self):
        """Test similarity threshold"""
        profile = create_profile()
        profile = add_memory(
            profile, content="User likes tennis and swimming", category="a2p:episodic"
        )

        similar = find_similar_memories(profile, "User likes coffee and tea")

        # Should not match as similarity is below 0.5
        assert len(similar) == 0


class TestExpireProposals:
    """Test expire proposals"""

    def test_expire_old_proposals(self):
        """Test expiring old proposals"""
        profile = create_profile()
        old_proposal = create_proposal(agent_did="did:a2p:agent:test", content="Old proposal")
        # Create proposal with expired date
        old_proposal = old_proposal.model_copy(
            update={"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
        )

        new_proposal = create_proposal(agent_did="did:a2p:agent:test", content="New proposal")
        profile = add_proposal(profile, old_proposal)
        profile = add_proposal(profile, new_proposal)

        updated = expire_proposals(profile)

        pending = (
            getattr(updated, "pendingProposals", None)
            or getattr(updated, "pending_proposals", None)
            or []
        )
        assert len(pending) == 2

        expired = next((p for p in pending if p.id == old_proposal.id), None)
        assert expired is not None
        assert expired.status == "expired"

        still_pending = next((p for p in pending if p.id == new_proposal.id), None)
        assert still_pending is not None
        assert still_pending.status == "pending"


class TestGetProposalsByAgent:
    """Test get proposals by agent"""

    def test_get_proposals_by_agent(self):
        """Test getting proposals by agent DID"""
        profile = create_profile()
        proposal1 = create_proposal(agent_did="did:a2p:agent:test", content="Proposal 1")
        proposal2 = create_proposal(agent_did="did:a2p:agent:other", content="Proposal 2")
        profile = add_proposal(profile, proposal1)
        profile = add_proposal(profile, proposal2)

        # Verify proposals were added
        assert len(profile.pending_proposals) == 2

        found = get_proposals_by_agent(profile, "did:a2p:agent:test")

        assert len(found) == 1
        assert found[0].id == proposal1.id
        # Check that proposed_by has agentDid (it's a dict with agentDid key)
        assert isinstance(found[0].proposed_by, dict)
        assert found[0].proposed_by.get("agentDid") == "did:a2p:agent:test"


class TestWithdrawProposal:
    """Test withdraw proposal"""

    def test_withdraw_proposal(self):
        """Test withdrawing a proposal"""
        profile = create_profile()
        proposal = create_proposal(agent_did="did:a2p:agent:test", content="Test proposal")
        profile = add_proposal(profile, proposal)

        updated = withdraw_proposal(profile, proposal.id)

        pending = (
            getattr(updated, "pendingProposals", None)
            or getattr(updated, "pending_proposals", None)
            or []
        )
        assert len(pending) == 1
        assert pending[0].status == "withdrawn"
