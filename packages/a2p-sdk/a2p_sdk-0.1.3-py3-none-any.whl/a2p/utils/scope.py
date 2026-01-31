"""
Scope Utilities

Utilities for working with a2p scopes and access control.
"""

import re


def scope_matches(scope: str, pattern: str) -> bool:
    """
    Check if a scope matches a pattern (supports wildcards)

    Examples:
        scope_matches('a2p:preferences.communication', 'a2p:preferences.*') -> True
        scope_matches('a2p:health', 'a2p:*') -> True
        scope_matches('a2p:preferences', 'a2p:professional') -> False
    """
    # Exact match
    if scope == pattern:
        return True

    # Pattern with wildcard
    if pattern.endswith(".*"):
        prefix = pattern[:-2]
        return scope == prefix or scope.startswith(prefix + ".")

    # Pattern is just namespace:*
    if pattern.endswith(":*"):
        namespace = pattern[:-2]
        return scope.startswith(namespace + ":")

    return False


def any_scope_matches(scopes: list[str], pattern: str) -> bool:
    """Check if any scope in a list matches a pattern"""
    return any(scope_matches(scope, pattern) for scope in scopes)


def filter_scopes(
    requested_scopes: list[str],
    allow_patterns: list[str],
    deny_patterns: list[str] | None = None,
) -> list[str]:
    """Filter scopes based on allowed and denied patterns"""
    deny_patterns = deny_patterns or []

    result = []
    for scope in requested_scopes:
        # Check if explicitly denied
        if any(scope_matches(scope, pattern) for pattern in deny_patterns):
            continue
        # Check if allowed
        if any(scope_matches(scope, pattern) for pattern in allow_patterns):
            result.append(scope)

    return result


def parse_scope(scope: str) -> dict[str, str | list[str]] | None:
    """
    Parse a scope into its components

    Example:
        parse_scope('a2p:preferences.communication.style')
        -> {'namespace': 'a2p', 'category': 'preferences', 'path': ['communication', 'style']}
    """
    match = re.match(
        r"^(a2p|ext:[a-zA-Z0-9_]+):([a-zA-Z0-9_]+)((?:\.[a-zA-Z0-9_]+)*)$",
        scope,
    )
    if not match:
        return None

    namespace, category, path_str = match.groups()
    path = path_str[1:].split(".") if path_str else []

    return {
        "namespace": namespace,
        "category": category,
        "path": path,
    }


def build_scope(
    namespace: str,
    category: str,
    path: list[str] | None = None,
) -> str:
    """Build a scope string from components"""
    base = f"{namespace}:{category}"
    return f"{base}.{'.'.join(path)}" if path else base


def get_parent_scopes(scope: str) -> list[str]:
    """
    Get all parent scopes for a given scope

    Example:
        get_parent_scopes('a2p:preferences.communication.style')
        -> ['a2p:preferences.communication', 'a2p:preferences', 'a2p:*']
    """
    parsed = parse_scope(scope)
    if not parsed:
        return []

    parents: list[str] = []
    namespace = parsed["namespace"]
    category = parsed["category"]
    path = parsed["path"]

    # Add intermediate parents
    if isinstance(path, list):
        for i in range(len(path) - 1, -1, -1):
            parents.append(build_scope(str(namespace), str(category), path[:i] if i > 0 else None))

    # Add namespace wildcard
    parents.append(f"{namespace}:*")

    return parents


# Standard a2p scopes
class StandardScopes:
    """Standard a2p scopes"""

    # Identity
    IDENTITY = "a2p:identity"
    IDENTITY_NAME = "a2p:identity.name"
    IDENTITY_LOCATION = "a2p:identity.location"

    # Preferences
    PREFERENCES = "a2p:preferences"
    PREFERENCES_COMMUNICATION = "a2p:preferences.communication"
    PREFERENCES_CONTENT = "a2p:preferences.content"
    PREFERENCES_UI = "a2p:preferences.ui"

    # Professional
    PROFESSIONAL = "a2p:professional"
    PROFESSIONAL_SKILLS = "a2p:professional.skills"

    # Interests
    INTERESTS = "a2p:interests"
    INTERESTS_TOPICS = "a2p:interests.topics"
    INTERESTS_MUSIC = "a2p:interests.music"
    INTERESTS_READING = "a2p:interests.reading"

    # Context
    CONTEXT = "a2p:context"
    CONTEXT_PROJECTS = "a2p:context.currentProjects"
    CONTEXT_GOALS = "a2p:context.ongoingGoals"

    # Sensitive
    HEALTH = "a2p:health"
    RELATIONSHIPS = "a2p:relationships"
    FINANCIAL = "a2p:financial"

    # Episodic
    EPISODIC = "a2p:episodic"

    # Wildcards
    ALL = "a2p:*"
    ALL_PREFERENCES = "a2p:preferences.*"
    ALL_PROFESSIONAL = "a2p:professional.*"
    ALL_INTERESTS = "a2p:interests.*"


# Sensitivity levels for standard scopes
SCOPE_SENSITIVITY: dict[str, str] = {
    "a2p:preferences": "public",
    "a2p:preferences.communication": "public",
    "a2p:preferences.content": "public",
    "a2p:identity": "standard",
    "a2p:professional": "standard",
    "a2p:interests": "standard",
    "a2p:context": "standard",
    "a2p:health": "sensitive",
    "a2p:relationships": "sensitive",
    "a2p:financial": "restricted",
}


def get_scope_sensitivity(scope: str) -> str:
    """Get the sensitivity level for a scope"""
    # Check exact match
    if scope in SCOPE_SENSITIVITY:
        return SCOPE_SENSITIVITY[scope]

    # Check parent scopes
    parsed = parse_scope(scope)
    if not parsed:
        return "standard"

    category_scope = f"{parsed['namespace']}:{parsed['category']}"
    if category_scope in SCOPE_SENSITIVITY:
        return SCOPE_SENSITIVITY[category_scope]

    return "standard"
