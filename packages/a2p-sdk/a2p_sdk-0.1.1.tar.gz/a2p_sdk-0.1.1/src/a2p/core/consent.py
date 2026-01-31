"""
Consent Management

Functionality for managing consent policies and access control.
"""

import re
from datetime import datetime, timezone
from typing import Any

from a2p.types import (
    AgentProfile,
    ConsentPolicy,
    ConsentReceipt,
    PermissionLevel,
    Profile,
)
from a2p.utils.id import generate_policy_id, generate_receipt_id
from a2p.utils.scope import filter_scopes


def agent_matches_pattern(agent_did: str, pattern: str) -> bool:
    """Check if an agent DID matches a pattern"""
    if pattern == "*":
        return True

    regex_pattern = pattern.replace("*", ".*").replace("?", ".")
    return bool(re.match(f"^{regex_pattern}$", agent_did))


def evaluate_conditions(
    conditions: Any,
    agent_profile: AgentProfile | None,
) -> bool:
    """Evaluate policy conditions against agent profile"""
    if not conditions or not agent_profile:
        return True

    if getattr(conditions, "require_verified_operator", False):
        if not agent_profile.operator or not agent_profile.operator.verified:
            return False

    min_score = getattr(conditions, "min_trust_score", None)
    if min_score is not None:
        score = agent_profile.trust_metrics.community_score if agent_profile.trust_metrics else 0
        if (score or 0) < min_score:
            return False

    if getattr(conditions, "require_audit", False):
        if not agent_profile.trust_metrics or not agent_profile.trust_metrics.security_audit:
            return False

    allowed = getattr(conditions, "allowed_jurisdictions", None)
    if allowed:
        jurisdiction = agent_profile.operator.jurisdiction if agent_profile.operator else None
        if not jurisdiction or jurisdiction not in allowed:
            return False

    blocked = getattr(conditions, "blocked_jurisdictions", None)
    if blocked:
        jurisdiction = agent_profile.operator.jurisdiction if agent_profile.operator else None
        if jurisdiction and jurisdiction in blocked:
            return False

    return True


def evaluate_access(
    profile: Profile,
    agent_did: str,
    requested_scopes: list[str],
    agent_profile: AgentProfile | None = None,
) -> dict[str, Any]:
    """Evaluate if an agent has access based on policies"""
    policies = sorted(
        [p for p in (profile.access_policies or []) if p.enabled],
        key=lambda p: p.priority,
    )

    if not policies:
        return {
            "granted": False,
            "allowed_scopes": [],
            "denied_scopes": requested_scopes,
            "permissions": [PermissionLevel.NONE],
            "matched_policy": None,
        }

    # Find matching policy
    matched_policy = None
    for policy in policies:
        # Check agent pattern
        if policy.agent_pattern and not agent_matches_pattern(agent_did, policy.agent_pattern):
            continue

        # Check specific agent DIDs
        if policy.agent_dids and agent_did not in policy.agent_dids:
            continue

        # Check operator DIDs
        if policy.operator_dids and agent_profile:
            op_did = agent_profile.operator.did if agent_profile.operator else None
            if not op_did or op_did not in policy.operator_dids:
                continue

        # Check conditions
        if policy.conditions and not evaluate_conditions(policy.conditions, agent_profile):
            continue

        # Check expiry
        if policy.expiry and policy.expiry < datetime.now(timezone.utc):
            continue

        matched_policy = policy
        break

    if not matched_policy:
        return {
            "granted": False,
            "allowed_scopes": [],
            "denied_scopes": requested_scopes,
            "permissions": [PermissionLevel.NONE],
            "matched_policy": None,
        }

    # Filter scopes
    allow_patterns = matched_policy.allow or []
    deny_patterns = matched_policy.deny or []

    allowed_scopes = filter_scopes(requested_scopes, allow_patterns, deny_patterns)
    denied_scopes = [s for s in requested_scopes if s not in allowed_scopes]

    return {
        "granted": len(allowed_scopes) > 0,
        "allowed_scopes": allowed_scopes,
        "denied_scopes": denied_scopes,
        "permissions": matched_policy.permissions,
        "matched_policy": matched_policy,
    }


def create_consent_receipt(
    user_did: str,
    agent_did: str,
    granted_scopes: list[str],
    permissions: list[PermissionLevel],
    operator_did: str | None = None,
    policy_id: str | None = None,
    denied_scopes: list[str] | None = None,
    sub_profile: str | None = None,
    expires_at: datetime | None = None,
    purpose: str | None = None,
    legal_basis: str | None = None,
) -> ConsentReceipt:
    """Create a consent receipt"""
    now = datetime.now(timezone.utc)

    return ConsentReceipt(
        receiptId=generate_receipt_id(),
        userDid=user_did,
        agentDid=agent_did,
        operatorDid=operator_did,
        policyId=policy_id,
        grantedScopes=granted_scopes,
        deniedScopes=denied_scopes,
        permissions=permissions,
        subProfile=sub_profile,
        grantedAt=now,
        expiresAt=expires_at,
        consentMethod="policy_match" if policy_id else "explicit_grant",
        purpose=purpose,
        legalBasis=legal_basis or "consent",
    )


def is_consent_valid(receipt: ConsentReceipt) -> bool:
    """Check if a consent receipt is still valid"""
    if receipt.revoked_at:
        return False

    if receipt.expires_at and receipt.expires_at < datetime.now(timezone.utc):
        return False

    return True


def revoke_consent(receipt: ConsentReceipt, reason: str | None = None) -> ConsentReceipt:
    """Revoke a consent receipt"""
    return receipt.model_copy(
        update={
            "revokedAt": datetime.now(timezone.utc),
            "revokedReason": reason,
        }
    )


def create_default_policy(
    agent_did: str,
    name: str | None = None,
    scopes: list[str] | None = None,
    permissions: list[PermissionLevel] | None = None,
) -> ConsentPolicy:
    """Create a default policy for an agent"""
    now = datetime.now(timezone.utc)

    return ConsentPolicy(
        id=generate_policy_id(),
        name=name or f"Policy for {agent_did}",
        agentPattern=agent_did,
        allow=scopes or ["a2p:preferences.*"],
        deny=["a2p:health.*", "a2p:financial.*"],
        permissions=permissions or [PermissionLevel.READ_SCOPED, PermissionLevel.PROPOSE],
        enabled=True,
        priority=100,
        created=now,
        updated=now,
    )


def create_category_policy(
    agent_pattern: str,
    name: str,
    allow: list[str],
    permissions: list[PermissionLevel],
    deny: list[str] | None = None,
    conditions: Any | None = None,
) -> ConsentPolicy:
    """Create a policy for a category of agents"""
    now = datetime.now(timezone.utc)

    return ConsentPolicy(
        id=generate_policy_id(),
        name=name,
        agentPattern=agent_pattern,
        allow=allow,
        deny=deny or [],
        permissions=permissions,
        conditions=conditions,
        enabled=True,
        priority=50,
        created=now,
        updated=now,
    )


def get_matching_policies(profile: Profile, agent_did: str) -> list[ConsentPolicy]:
    """Get all active policies for an agent"""
    return sorted(
        [
            p
            for p in (profile.access_policies or [])
            if p.enabled and agent_matches_pattern(agent_did, p.agent_pattern)
        ],
        key=lambda p: p.priority,
    )


def has_permission(
    permissions: list[PermissionLevel],
    required: PermissionLevel,
) -> bool:
    """Check if a specific permission is granted"""
    hierarchy = [
        PermissionLevel.NONE,
        PermissionLevel.READ_PUBLIC,
        PermissionLevel.READ_SCOPED,
        PermissionLevel.READ_FULL,
        PermissionLevel.PROPOSE,
        PermissionLevel.WRITE,
    ]

    required_index = hierarchy.index(required)
    return any(hierarchy.index(p) >= required_index for p in permissions)


def merge_permissions(policies: list[ConsentPolicy]) -> list[PermissionLevel]:
    """Merge permissions from multiple policies"""
    all_permissions: set[PermissionLevel] = set()

    for policy in policies:
        for permission in policy.permissions:
            all_permissions.add(permission)

    return list(all_permissions)
