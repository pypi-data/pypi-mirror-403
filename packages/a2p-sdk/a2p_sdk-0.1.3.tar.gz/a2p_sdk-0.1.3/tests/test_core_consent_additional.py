"""Additional tests for consent management - coverage improvement"""

from datetime import datetime, timedelta, timezone

from a2p.core.consent import (
    agent_matches_pattern,
    create_category_policy,
    create_consent_receipt,
    create_default_policy,
    get_matching_policies,
    is_consent_valid,
    merge_permissions,
    revoke_consent,
)
from a2p.core.profile import add_policy, create_profile
from a2p.types import PermissionLevel


class TestConsentReceipt:
    """Test consent receipt creation and validation"""

    def test_create_consent_receipt_with_expiry(self):
        """Test creating consent receipt with expiry"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        receipt = create_consent_receipt(
            user_did="did:a2p:user:test",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences.*"],
            permissions=[PermissionLevel.READ_SCOPED],
            expires_at=expires_at,
        )

        # create_consent_receipt returns a ConsentReceipt object
        assert receipt.user_did == "did:a2p:user:test" or receipt.userDid == "did:a2p:user:test"
        assert receipt.agent_did == "did:a2p:agent:test" or receipt.agentDid == "did:a2p:agent:test"
        assert receipt.expires_at is not None or receipt.expiresAt is not None

    def test_is_consent_valid_with_expiry(self):
        """Test consent validity with expiry"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        receipt = create_consent_receipt(
            user_did="did:a2p:user:test",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences.*"],
            permissions=[PermissionLevel.READ_SCOPED],
            expires_at=expires_at,
        )

        assert is_consent_valid(receipt) is True

    def test_is_consent_valid_expired(self):
        """Test expired consent is invalid"""
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        receipt = create_consent_receipt(
            user_did="did:a2p:user:test",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences.*"],
            permissions=[PermissionLevel.READ_SCOPED],
            expires_at=expires_at,
        )

        assert is_consent_valid(receipt) is False

    def test_revoke_consent_with_reason(self):
        """Test revoking consent with reason"""
        receipt = create_consent_receipt(
            user_did="did:a2p:user:test",
            agent_did="did:a2p:agent:test",
            granted_scopes=["a2p:preferences.*"],
            permissions=[PermissionLevel.READ_SCOPED],
        )

        revoked = revoke_consent(receipt, "User requested")

        # revoke_consent returns a ConsentReceipt object
        assert revoked.revoked_at is not None or revoked.revokedAt is not None
        assert (
            revoked.revoked_reason == "User requested" or revoked.revokedReason == "User requested"
        )
        assert is_consent_valid(revoked) is False


class TestPolicyCreation:
    """Test policy creation functions"""

    def test_create_default_policy(self):
        """Test creating default policy"""
        policy = create_default_policy("did:a2p:agent:test")

        assert policy.agent_pattern == "did:a2p:agent:test"
        assert policy.enabled is True
        assert PermissionLevel.READ_SCOPED in policy.permissions
        assert "a2p:preferences.*" in policy.allow

    def test_create_default_policy_with_options(self):
        """Test creating default policy with custom options"""
        policy = create_default_policy(
            "did:a2p:agent:test",
            name="Custom Policy",
            scopes=["a2p:identity.*"],
            permissions=[PermissionLevel.READ_FULL],
        )

        assert policy.name == "Custom Policy"
        assert policy.allow == ["a2p:identity.*"]
        assert PermissionLevel.READ_FULL in policy.permissions

    def test_create_category_policy(self):
        """Test creating category policy"""
        policy = create_category_policy(
            "did:a2p:agent:*",
            name="All Agents Policy",
            allow=["a2p:preferences.*"],
            deny=["a2p:health.*"],
            permissions=[PermissionLevel.READ_SCOPED],
        )

        assert policy.agent_pattern == "did:a2p:agent:*"
        assert policy.name == "All Agents Policy"
        assert policy.allow == ["a2p:preferences.*"]
        assert policy.deny == ["a2p:health.*"]
        assert policy.priority == 50


class TestPolicyMatching:
    """Test policy matching functions"""

    def test_get_matching_policies(self):
        """Test getting matching policies"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:other",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )

        matching = get_matching_policies(profile, "did:a2p:agent:test")

        assert len(matching) == 1
        assert matching[0].agent_pattern == "did:a2p:agent:*"

    def test_get_matching_policies_no_match(self):
        """Test getting matching policies when none match"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:other",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )

        matching = get_matching_policies(profile, "did:a2p:agent:test")

        assert len(matching) == 0

    def test_merge_permissions(self):
        """Test merging permissions from multiple policies"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
        )
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.PROPOSE],
            allow=["a2p:preferences.*"],
        )

        matching = get_matching_policies(profile, "did:a2p:agent:test")
        assert len(matching) == 2  # Should match both policies
        merged = merge_permissions(matching)

        assert PermissionLevel.READ_SCOPED in merged
        assert PermissionLevel.PROPOSE in merged


class TestAgentPatternMatching:
    """Test agent pattern matching"""

    def test_agent_matches_pattern_wildcard(self):
        """Test matching with wildcard"""
        assert agent_matches_pattern("did:a2p:agent:test", "*") is True
        assert agent_matches_pattern("did:a2p:agent:anything", "*") is True

    def test_agent_matches_pattern_exact(self):
        """Test exact matching"""
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:test") is True
        assert agent_matches_pattern("did:a2p:agent:other", "did:a2p:agent:test") is False

    def test_agent_matches_pattern_prefix(self):
        """Test prefix matching"""
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:*") is True
        assert agent_matches_pattern("did:a2p:agent:my-agent", "did:a2p:agent:*") is True
        assert agent_matches_pattern("did:a2p:user:test", "did:a2p:agent:*") is False

    def test_agent_matches_pattern_with_question_mark(self):
        """Test matching with question mark wildcard"""
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:te?t") is True
        assert agent_matches_pattern("did:a2p:agent:test", "did:a2p:agent:t??t") is True
