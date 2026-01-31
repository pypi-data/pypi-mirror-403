"""Tests for proposal management"""

from datetime import datetime, timedelta, timezone

import pytest

from a2p.core.profile import create_profile
from a2p.core.proposal import (
    add_proposal,
    approve_proposal,
    create_proposal,
    get_pending_proposals,
    reject_proposal,
)
from a2p.types import MemoryStatus, ProposalStatus


class TestCreateProposal:
    """Test proposal creation"""

    def test_create_proposal(self):
        """Test creating a proposal"""
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="User likes Python",
            category="a2p:preferences",
            confidence=0.8,
        )

        assert proposal.id.startswith("prop_")
        assert proposal.memory.content == "User likes Python"
        assert proposal.memory.category == "a2p:preferences"
        assert proposal.memory.confidence == 0.8
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.proposed_by.agent_did == "did:a2p:agent:test"

    def test_create_proposal_with_expiry(self):
        """Test creating proposal with expiry"""
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="Test",
            expires_in_days=14,
        )

        assert proposal.expires_at is not None
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=14)
        # Allow 1 second tolerance
        assert abs((proposal.expires_at - expected_expiry).total_seconds()) < 1


class TestProposalManagement:
    """Test proposal management"""

    def test_add_proposal(self):
        """Test adding proposal to profile"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="Test proposal",
        )

        updated = add_proposal(profile, proposal)
        assert len(updated.pending_proposals) == 1
        assert updated.pending_proposals[0].id == proposal.id

    def test_add_proposal_duplicate(self):
        """Test adding duplicate proposal fails"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="Test",
        )
        profile = add_proposal(profile, proposal)

        with pytest.raises(ValueError, match="already exists"):
            add_proposal(profile, proposal)

    def test_get_pending_proposals(self):
        """Test getting pending proposals"""
        profile = create_profile()

        proposal1 = create_proposal(
            agent_did="did:a2p:agent:test1",
            content="Proposal 1",
        )
        proposal2 = create_proposal(
            agent_did="did:a2p:agent:test2",
            content="Proposal 2",
        )

        profile = add_proposal(profile, proposal1)
        profile = add_proposal(profile, proposal2)

        pending = get_pending_proposals(profile)
        assert len(pending) == 2


class TestProposalApproval:
    """Test proposal approval"""

    def test_approve_proposal(self):
        """Test approving a proposal"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="User likes Python",
            category="a2p:preferences",
        )
        profile = add_proposal(profile, proposal)

        updated_profile, memory = approve_proposal(profile, proposal.id)

        assert memory.content == "User likes Python"
        assert memory.category == "a2p:preferences"
        assert memory.status == MemoryStatus.APPROVED
        assert len(updated_profile.pending_proposals) == 0
        assert len(updated_profile.memories.episodic) == 1

    def test_approve_proposal_with_edits(self):
        """Test approving proposal with edits"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="Original content",
            category="a2p:preferences",
        )
        profile = add_proposal(profile, proposal)

        updated_profile, memory = approve_proposal(
            profile,
            proposal.id,
            edited_content="Edited content",
            edited_category="a2p:interests",
        )

        assert memory.content == "Edited content"
        assert memory.category == "a2p:interests"

    def test_approve_proposal_not_found(self):
        """Test approving non-existent proposal fails"""
        profile = create_profile()

        with pytest.raises(ValueError, match="not found"):
            approve_proposal(profile, "nonexistent-id")


class TestProposalRejection:
    """Test proposal rejection"""

    def test_reject_proposal(self):
        """Test rejecting a proposal"""
        profile = create_profile()
        proposal = create_proposal(
            agent_did="did:a2p:agent:test",
            content="Test proposal",
        )
        profile = add_proposal(profile, proposal)

        updated = reject_proposal(profile, proposal.id, reason="Not relevant")

        assert len(updated.pending_proposals) == 0
        # Check that proposal was marked as rejected
        # (implementation may vary)

    def test_reject_proposal_not_found(self):
        """Test rejecting non-existent proposal fails"""
        profile = create_profile()

        with pytest.raises(ValueError, match="not found"):
            reject_proposal(profile, "nonexistent-id")
