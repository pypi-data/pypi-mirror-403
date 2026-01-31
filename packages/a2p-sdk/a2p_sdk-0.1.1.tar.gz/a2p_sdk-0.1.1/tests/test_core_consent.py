"""Tests for consent management"""

from a2p.core.consent import (
    agent_matches_pattern,
    create_consent_receipt,
    evaluate_access,
    evaluate_conditions,
    has_permission,
)
from a2p.core.profile import add_policy, create_profile
from a2p.types import PermissionLevel


class TestAgentPatternMatching:
    """Test agent pattern matching"""

    def test_agent_matches_pattern_wildcard(self):
        """Test matching with wildcard"""
        assert agent_matches_pattern("did:a2p:agent:test", "*")
        assert agent_matches_pattern("did:a2p:agent:anything", "*")

    def test_agent_matches_pattern_exact(self):
        """Test exact matching"""
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:test")
        assert not agent_matches_pattern("did:a2p:agent:other", "did:a2p:agent:test")

    def test_agent_matches_pattern_prefix(self):
        """Test prefix matching"""
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:*")
        assert agent_matches_pattern("did:a2p:agent:my-agent", "did:a2p:agent:*")
        assert not agent_matches_pattern("did:a2p:user:test", "did:a2p:agent:*")


class TestConditionEvaluation:
    """Test condition evaluation"""

    def test_evaluate_conditions_no_conditions(self):
        """Test evaluating with no conditions"""
        assert evaluate_conditions(None, None) is True
        assert evaluate_conditions({}, None) is True

    def test_evaluate_conditions_no_agent_profile(self):
        """Test evaluating with no agent profile"""
        conditions = {"require_verified_operator": True}
        assert evaluate_conditions(conditions, None) is True


class TestAccessEvaluation:
    """Test access evaluation"""

    def test_evaluate_access_no_policies(self):
        """Test access evaluation with no policies"""
        profile = create_profile()
        result = evaluate_access(
            profile,
            "did:a2p:agent:test",
            ["a2p:preferences"],
        )

        assert result["granted"] is False
        assert len(result["allowed_scopes"]) == 0

    def test_evaluate_access_granted(self):
        """Test access evaluation with matching policy"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )

        result = evaluate_access(
            profile,
            "did:a2p:agent:test",
            ["a2p:preferences.communication"],
        )

        assert result["granted"] is True
        assert "a2p:preferences.communication" in result["allowed_scopes"]

    def test_evaluate_access_denied_scope(self):
        """Test access evaluation with denied scope"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
            deny=["a2p:preferences.private"],
        )

        result = evaluate_access(
            profile,
            "did:a2p:agent:test",
            ["a2p:preferences.communication", "a2p:preferences.private"],
        )

        assert result["granted"] is True
        assert "a2p:preferences.communication" in result["allowed_scopes"]
        assert "a2p:preferences.private" in result["denied_scopes"]

    def test_evaluate_access_pattern_mismatch(self):
        """Test access evaluation with pattern mismatch"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:specific",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )

        result = evaluate_access(
            profile,
            "did:a2p:agent:other",
            ["a2p:preferences"],
        )

        assert result["granted"] is False

    def test_evaluate_access_priority(self):
        """Test access evaluation with policy priority"""
        profile = create_profile()
        # Lower priority policy (denies)
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
            deny=["a2p:preferences.private"],
            priority=100,
        )
        # Higher priority policy (allows)
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
            priority=50,  # Higher priority
        )

        result = evaluate_access(
            profile,
            "did:a2p:agent:test",
            ["a2p:preferences.private"],
        )

        # Higher priority policy should win
        assert result["granted"] is True


class TestPermissionChecking:
    """Test permission checking"""

    def test_has_permission(self):
        """Test checking if permission exists"""
        permissions = [PermissionLevel.READ_SCOPED, PermissionLevel.PROPOSE]
        assert has_permission(permissions, PermissionLevel.READ_SCOPED) is True
        assert has_permission(permissions, PermissionLevel.PROPOSE) is True
        assert has_permission(permissions, PermissionLevel.WRITE) is False

    def test_has_permission_none(self):
        """Test checking permission with NONE"""
        permissions = [PermissionLevel.NONE]
        assert has_permission(permissions, PermissionLevel.READ_SCOPED) is False


class TestConsentReceipt:
    """Test consent receipt creation"""

    def test_create_consent_receipt(self):
        """Test creating consent receipt"""
        receipt = create_consent_receipt(
            user_did="did:a2p:user:alice",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences"],
            permissions=[PermissionLevel.READ_SCOPED],
        )

        assert receipt["userDid"] == "did:a2p:user:alice"
        assert receipt["agentDid"] == "did:a2p:agent:test"
        assert receipt["granted"] is True
        assert "a2p:preferences" in receipt["grantedScopes"]
        assert receipt["id"].startswith("rcpt_")

    def test_create_consent_receipt_with_denied(self):
        """Test creating consent receipt with denied scopes"""
        receipt = create_consent_receipt(
            user_did="did:a2p:user:alice",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences"],
            denied_scopes=["a2p:health"],
            permissions=[PermissionLevel.READ_SCOPED],
        )

        assert "a2p:preferences" in receipt["grantedScopes"]
        assert "a2p:health" in receipt["deniedScopes"]
