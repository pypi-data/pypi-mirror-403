"""
ID Generation Utilities

Utilities for generating unique identifiers for a2p entities.
"""

import re
import secrets
import string


def _random_alphanumeric(length: int) -> str:
    """Generate a random alphanumeric string"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_memory_id() -> str:
    """Generate a unique memory ID"""
    return f"mem_{_random_alphanumeric(16)}"


def generate_proposal_id() -> str:
    """Generate a unique proposal ID"""
    return f"prop_{_random_alphanumeric(16)}"


def generate_policy_id() -> str:
    """Generate a unique policy ID"""
    return f"policy_{_random_alphanumeric(12)}"


def generate_receipt_id() -> str:
    """Generate a unique consent receipt ID"""
    return f"rcpt_{_random_alphanumeric(16)}"


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"sess_{_random_alphanumeric(20)}"


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{_random_alphanumeric(16)}"


def generate_user_did(namespace: str = "local", identifier: str | None = None) -> str:
    """
    Generate a DID for a user.

    Args:
        namespace: Provider namespace (default: "local" for local profiles)
        identifier: Unique identifier within namespace (auto-generated if not provided)

    Returns:
        User DID string

    Examples:
        >>> generate_user_did("gaugid", "alice")
        'did:a2p:user:gaugid:alice'
        >>> generate_user_did()  # Uses "local" namespace
        'did:a2p:user:local:...'
    """
    id_part = identifier or _random_alphanumeric(12)
    return f"did:a2p:user:{namespace}:{id_part}"


def generate_agent_did(
    namespace: str = "local", name: str | None = None, identifier: str | None = None
) -> str:
    """
    Generate a DID for an agent.

    Args:
        namespace: Provider namespace (default: "local" for local agents)
        name: Agent name (will be sanitized if provided)
        identifier: Unique identifier within namespace (auto-generated if not provided)

    Returns:
        Agent DID string

    Examples:
        >>> generate_agent_did("gaugid", "my-assistant")
        'did:a2p:agent:gaugid:my-assistant'
        >>> generate_agent_did("local", identifier="agent-123")
        'did:a2p:agent:local:agent-123'
    """
    if identifier:
        id_part = identifier
    elif name:
        id_part = re.sub(r"[^a-z0-9]", "-", name.lower())
    else:
        id_part = _random_alphanumeric(12)
    return f"did:a2p:agent:{namespace}:{id_part}"


def generate_org_did(
    namespace: str = "local", name: str | None = None, identifier: str | None = None
) -> str:
    """
    Generate a DID for an organization.

    Args:
        namespace: Provider namespace (default: "local")
        name: Organization name (will be sanitized if provided)
        identifier: Unique identifier within namespace (auto-generated if not provided)

    Returns:
        Organization DID string
    """
    if identifier:
        id_part = identifier
    elif name:
        id_part = re.sub(r"[^a-z0-9]", "-", name.lower())
    else:
        id_part = _random_alphanumeric(12)
    return f"did:a2p:org:{namespace}:{id_part}"


def is_valid_did(did: str) -> bool:
    """Check if a string is a valid DID"""
    return bool(re.match(r"^did:[a-z0-9]+:[a-zA-Z0-9._-]+$", did))


# DID type patterns as per a2p protocol spec Section 4.4
# All patterns require namespace: did:a2p:<type>:<namespace>:<identifier>
DID_PATTERNS = {
    "user": re.compile(r"^did:a2p:user:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"),
    "agent": re.compile(r"^did:a2p:agent:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"),
    "org": re.compile(r"^did:a2p:org:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"),
    "entity": re.compile(r"^did:a2p:entity:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"),
    "service": re.compile(r"^did:a2p:service:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"),
}

# General a2p DID pattern (requires namespace)
A2P_DID_PATTERN = re.compile(
    r"^did:a2p:(user|agent|org|entity|service):[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$"
)

# Local namespace pattern (for self-hosted profiles)
LOCAL_DID_PATTERN = re.compile(r"^did:a2p:(user|agent|org|entity|service):local:[a-zA-Z0-9._-]+$")


def is_valid_a2p_did(did: str) -> bool:
    """
    Check if a string is a valid a2p protocol DID.

    Validates against the pattern defined in a2p protocol spec Section 4.4:
    ^did:a2p:(user|agent|org|entity|service):<namespace>:<identifier>

    All a2p DIDs MUST include a namespace component.

    Args:
        did: The DID string to validate

    Returns:
        True if valid a2p DID, False otherwise

    Examples:
        >>> is_valid_a2p_did("did:a2p:agent:gaugid:my-assistant")
        True
        >>> is_valid_a2p_did("did:a2p:user:local:alice")
        True
        >>> is_valid_a2p_did("did:a2p:agent:my-assistant")  # missing namespace
        False
        >>> is_valid_a2p_did("did:other:test")
        False
    """
    return bool(A2P_DID_PATTERN.match(did))


def is_valid_agent_did(did: str) -> bool:
    """
    Check if a string is a valid a2p agent DID.

    Validates against the pattern: ^did:a2p:agent:<namespace>:<identifier>$

    This is a protocol requirement (a2p spec Section 4.4.2).
    Invalid agent DIDs should return error code A2P010.

    Args:
        did: The DID string to validate

    Returns:
        True if valid agent DID, False otherwise

    Examples:
        >>> is_valid_agent_did("did:a2p:agent:gaugid:my-assistant")
        True
        >>> is_valid_agent_did("did:a2p:agent:local:trusted-ai")
        True
        >>> is_valid_agent_did("did:a2p:agent:my-assistant")  # missing namespace
        False
        >>> is_valid_agent_did("did:a2p:user:gaugid:alice")
        False
        >>> is_valid_agent_did("did:a2p:agent:gaugid:")
        False
    """
    return bool(DID_PATTERNS["agent"].match(did))


def is_valid_user_did(did: str) -> bool:
    """
    Check if a string is a valid a2p user DID.

    Validates against the pattern: ^did:a2p:user:<namespace>:<identifier>$

    Args:
        did: The DID string to validate

    Returns:
        True if valid user DID, False otherwise

    Examples:
        >>> is_valid_user_did("did:a2p:user:gaugid:alice")
        True
        >>> is_valid_user_did("did:a2p:user:local:alice")
        True
        >>> is_valid_user_did("did:a2p:user:alice")  # missing namespace
        False
    """
    return bool(DID_PATTERNS["user"].match(did))


def validate_agent_did(did: str) -> tuple[bool, dict[str, str] | None]:
    """
    Validate an agent DID and return structured error if invalid.

    This follows the a2p protocol spec error codes (Section 11.4).

    Args:
        did: The DID string to validate

    Returns:
        Tuple of (is_valid, error_dict or None)
        Error dict contains 'code' and 'message' keys.

    Examples:
        >>> validate_agent_did("did:a2p:agent:my-assistant")
        (True, None)
        >>> validate_agent_did("invalid-did")
        (False, {'code': 'A2P010', 'message': 'Invalid agent DID format'})
    """
    if is_valid_agent_did(did):
        return (True, None)

    return (
        False,
        {
            "code": "A2P010",
            "message": "Invalid agent DID format",
        },
    )


def parse_did(did: str) -> dict[str, str] | None:
    """
    Parse an a2p DID into its components: type, namespace, identifier.

    Args:
        did: The DID string to parse

    Returns:
        Dictionary with 'type', 'namespace', 'identifier' keys, or None if invalid

    Examples:
        >>> parse_did("did:a2p:agent:gaugid:my-assistant")
        {'type': 'agent', 'namespace': 'gaugid', 'identifier': 'my-assistant'}
        >>> parse_did("did:a2p:user:local:alice")
        {'type': 'user', 'namespace': 'local', 'identifier': 'alice'}
        >>> parse_did("did:a2p:agent:my-assistant")  # missing namespace
        None
    """
    match = re.match(
        r"^did:a2p:(user|agent|org|entity|service):([a-zA-Z0-9._-]+):([a-zA-Z0-9._-]+)$", did
    )
    if not match:
        return None
    return {
        "type": match.group(1),
        "namespace": match.group(2),
        "identifier": match.group(3),
    }


def get_namespace(did: str) -> str | None:
    """
    Extract namespace from an a2p DID.

    Args:
        did: The DID string

    Returns:
        Namespace string, or None if DID is invalid

    Examples:
        >>> get_namespace("did:a2p:agent:gaugid:my-assistant")
        'gaugid'
        >>> get_namespace("did:a2p:user:local:alice")
        'local'
    """
    parsed = parse_did(did)
    return parsed.get("namespace") if parsed else None


def is_local_did(did: str) -> bool:
    """
    Check if a DID uses the local namespace (for self-hosted profiles).

    Args:
        did: The DID string to check

    Returns:
        True if DID uses 'local' namespace, False otherwise

    Examples:
        >>> is_local_did("did:a2p:user:local:alice")
        True
        >>> is_local_did("did:a2p:agent:gaugid:my-assistant")
        False
    """
    return bool(LOCAL_DID_PATTERN.match(did))
