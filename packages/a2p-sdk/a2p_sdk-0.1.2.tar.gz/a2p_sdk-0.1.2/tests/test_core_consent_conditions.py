"""Tests for consent condition evaluation - comprehensive coverage"""

from a2p.core.consent import evaluate_access, evaluate_conditions
from a2p.core.profile import add_policy, create_profile
from a2p.types import (
    AgentA2PSupport,
    AgentIdentity,
    AgentOperator,
    AgentProfile,
    AgentTrustMetrics,
    PolicyConditions,
)


def create_agent_profile(**kwargs):
    """Helper to create AgentProfile with required fields"""
    agent_id = kwargs.get("did", kwargs.get("id", "did:a2p:agent:test"))
    # Extract operator if provided, otherwise create default
    operator = (
        kwargs.pop("operator", None)
        if "operator" in kwargs
        else AgentOperator(did="did:a2p:org:test", name="Test Org", verified=False)
    )

    defaults = {
        "id": agent_id,
        "identity": AgentIdentity(name=kwargs.get("name", "Test Agent")),
        "a2pSupport": AgentA2PSupport(protocol_version="1.0"),
        "operator": operator,
    }
    # Update with any remaining kwargs (like trust_metrics)
    defaults.update(kwargs)
    return AgentProfile(**defaults)


class TestConditionEvaluation:
    """Test condition evaluation comprehensively"""

    def test_require_verified_operator_met(self):
        """Test requireVerifiedOperator when met"""
        conditions = PolicyConditions(require_verified_operator=True)
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", verified=True)
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_require_verified_operator_not_met(self):
        """Test requireVerifiedOperator when not met"""
        conditions = PolicyConditions(require_verified_operator=True)
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", verified=False)
        )
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_require_verified_operator_missing_operator(self):
        """Test requireVerifiedOperator when operator missing"""
        conditions = PolicyConditions(require_verified_operator=True)
        agent_profile = create_agent_profile()
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_min_trust_score_met(self):
        """Test minTrustScore when met"""
        conditions = PolicyConditions(min_trust_score=0.7)
        agent_profile = create_agent_profile(trust_metrics=AgentTrustMetrics(community_score=0.8))
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_min_trust_score_not_met(self):
        """Test minTrustScore when not met"""
        conditions = PolicyConditions(min_trust_score=0.7)
        agent_profile = create_agent_profile(trust_metrics=AgentTrustMetrics(community_score=0.5))
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_min_trust_score_missing_metrics(self):
        """Test minTrustScore when trust metrics missing"""
        conditions = PolicyConditions(min_trust_score=0.7)
        agent_profile = create_agent_profile()
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_require_audit_met(self):
        """Test requireAudit when met"""
        conditions = PolicyConditions(require_audit=True)
        agent_profile = create_agent_profile(
            trust_metrics=AgentTrustMetrics(
                security_audit={"status": "passed"}, community_score=0.5
            )
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_require_audit_not_met(self):
        """Test requireAudit when not met"""
        conditions = PolicyConditions(require_audit=True)
        agent_profile = create_agent_profile(
            trust_metrics=AgentTrustMetrics(security_audit=None, community_score=0.5)
        )
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_require_audit_missing_metrics(self):
        """Test requireAudit when trust metrics missing"""
        conditions = PolicyConditions(require_audit=True)
        agent_profile = create_agent_profile()
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_allowed_jurisdictions_met(self):
        """Test allowedJurisdictions when met"""
        conditions = PolicyConditions(allowed_jurisdictions=["US", "EU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", jurisdiction="US")
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_allowed_jurisdictions_not_met(self):
        """Test allowedJurisdictions when not met"""
        conditions = PolicyConditions(allowed_jurisdictions=["US", "EU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", jurisdiction="CN")
        )
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_allowed_jurisdictions_missing_jurisdiction(self):
        """Test allowedJurisdictions when jurisdiction missing"""
        conditions = PolicyConditions(allowed_jurisdictions=["US", "EU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A")
        )
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_blocked_jurisdictions_blocked(self):
        """Test blockedJurisdictions when blocked"""
        conditions = PolicyConditions(blocked_jurisdictions=["CN", "RU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", jurisdiction="CN")
        )
        assert evaluate_conditions(conditions, agent_profile) is False

    def test_blocked_jurisdictions_not_blocked(self):
        """Test blockedJurisdictions when not blocked"""
        conditions = PolicyConditions(blocked_jurisdictions=["CN", "RU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", jurisdiction="US")
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_blocked_jurisdictions_missing_jurisdiction(self):
        """Test blockedJurisdictions when jurisdiction missing"""
        conditions = PolicyConditions(blocked_jurisdictions=["CN", "RU"])
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A")
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_combined_conditions_all_met(self):
        """Test combined conditions when all met"""
        conditions = PolicyConditions(
            require_verified_operator=True,
            min_trust_score=0.7,
            require_audit=True,
            allowed_jurisdictions=["US", "EU"],
        )
        agent_profile = create_agent_profile(
            operator=AgentOperator(
                did="did:a2p:org:company-a", name="Company A", verified=True, jurisdiction="US"
            ),
            trust_metrics=AgentTrustMetrics(
                community_score=0.8, security_audit={"status": "passed"}, transparency_score=0.8
            ),
        )
        assert evaluate_conditions(conditions, agent_profile) is True

    def test_combined_conditions_one_fails(self):
        """Test combined conditions when one fails"""
        conditions = PolicyConditions(
            require_verified_operator=True,
            min_trust_score=0.7,
        )
        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", verified=True),
            trust_metrics=AgentTrustMetrics(community_score=0.5),  # Below threshold
        )
        assert evaluate_conditions(conditions, agent_profile) is False


class TestConditionEvaluationInAccess:
    """Test condition evaluation in access evaluation"""

    def test_evaluate_access_with_conditions(self):
        """Test evaluateAccess with conditions"""
        from a2p.types import PermissionLevel

        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=[PermissionLevel.READ_SCOPED],
            allow=["a2p:preferences.*"],
            conditions=PolicyConditions(require_verified_operator=True, min_trust_score=0.7),
        )

        agent_profile = create_agent_profile(
            operator=AgentOperator(did="did:a2p:org:company-a", name="Company A", verified=True),
            trust_metrics=AgentTrustMetrics(
                community_score=0.8, security_audit={"status": "passed"}
            ),
        )

        result = evaluate_access(
            profile, "did:a2p:agent:test", ["a2p:preferences.communication"], agent_profile
        )

        assert result["granted"] is True

    def test_evaluate_access_with_conditions_fails(self):
        """Test evaluateAccess with conditions that fail"""
        profile = create_profile()
        profile = add_policy(
            profile,
            agent_pattern="did:a2p:agent:*",
            permissions=["read_scoped"],
            allow=["a2p:preferences.*"],
            conditions=PolicyConditions(
                require_verified_operator=True,
            ),
        )

        agent_profile = create_agent_profile(
            operator=AgentOperator(
                did="did:a2p:org:company-a",
                name="Company A",
                verified=False,  # Not verified
            )
        )

        result = evaluate_access(
            profile, "did:a2p:agent:test", ["a2p:preferences.communication"], agent_profile
        )

        assert result["granted"] is False
