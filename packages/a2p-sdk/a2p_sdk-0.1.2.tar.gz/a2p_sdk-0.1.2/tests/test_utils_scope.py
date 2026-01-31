"""Tests for scope utilities"""

from a2p.utils.scope import (
    any_scope_matches,
    build_scope,
    filter_scopes,
    get_parent_scopes,
    get_scope_sensitivity,
    parse_scope,
    scope_matches,
)


class TestScopeMatching:
    """Test scope matching functions"""

    def test_scope_matches_exact(self):
        """Test exact scope matching"""
        assert scope_matches("a2p:preferences", "a2p:preferences")
        assert scope_matches("a2p:professional", "a2p:professional")
        assert not scope_matches("a2p:preferences", "a2p:professional")

    def test_scope_matches_wildcard_suffix(self):
        """Test wildcard suffix matching"""
        assert scope_matches("a2p:preferences.communication", "a2p:preferences.*")
        assert scope_matches("a2p:preferences.ui", "a2p:preferences.*")
        assert not scope_matches("a2p:professional", "a2p:preferences.*")

    def test_scope_matches_namespace_wildcard(self):
        """Test namespace wildcard matching"""
        assert scope_matches("a2p:preferences", "a2p:*")
        assert scope_matches("a2p:professional.skills", "a2p:*")
        assert not scope_matches("ext:custom", "a2p:*")

    def test_any_scope_matches(self):
        """Test any scope matching"""
        scopes = ["a2p:preferences", "a2p:professional", "a2p:interests"]
        assert any_scope_matches(scopes, "a2p:preferences.*")
        assert any_scope_matches(scopes, "a2p:*")
        assert not any_scope_matches(scopes, "a2p:health")


class TestScopeFiltering:
    """Test scope filtering"""

    def test_filter_scopes_allow(self):
        """Test scope filtering with allow patterns"""
        requested = ["a2p:preferences", "a2p:professional", "a2p:health"]
        allowed = ["a2p:preferences.*", "a2p:professional"]
        result = filter_scopes(requested, allowed)
        assert "a2p:preferences" in result
        assert "a2p:professional" in result
        assert "a2p:health" not in result

    def test_filter_scopes_deny(self):
        """Test scope filtering with deny patterns"""
        requested = ["a2p:preferences", "a2p:health", "a2p:financial"]
        allowed = ["a2p:*"]
        denied = ["a2p:health", "a2p:financial"]
        result = filter_scopes(requested, allowed, denied)
        assert "a2p:preferences" in result
        assert "a2p:health" not in result
        assert "a2p:financial" not in result

    def test_filter_scopes_wildcard(self):
        """Test scope filtering with wildcard"""
        requested = ["a2p:preferences", "a2p:professional", "a2p:interests"]
        allowed = ["a2p:*"]
        result = filter_scopes(requested, allowed)
        assert len(result) == 3


class TestScopeParsing:
    """Test scope parsing and building"""

    def test_parse_scope_simple(self):
        """Test parsing simple scope"""
        result = parse_scope("a2p:preferences")
        assert result is not None
        assert result["namespace"] == "a2p"
        assert result["category"] == "preferences"
        assert result["path"] == []

    def test_parse_scope_nested(self):
        """Test parsing nested scope"""
        result = parse_scope("a2p:preferences.communication.style")
        assert result is not None
        assert result["namespace"] == "a2p"
        assert result["category"] == "preferences"
        assert result["path"] == ["communication", "style"]

    def test_parse_scope_ext_namespace(self):
        """Test parsing external namespace scope"""
        result = parse_scope("ext:custom:category.path")
        assert result is not None
        assert result["namespace"] == "ext:custom"
        assert result["category"] == "category"
        assert result["path"] == ["path"]

    def test_parse_scope_invalid(self):
        """Test parsing invalid scope"""
        assert parse_scope("invalid") is None
        assert parse_scope("a2p") is None

    def test_build_scope_simple(self):
        """Test building simple scope"""
        scope = build_scope("a2p", "preferences")
        assert scope == "a2p:preferences"

    def test_build_scope_with_path(self):
        """Test building scope with path"""
        scope = build_scope("a2p", "preferences", ["communication", "style"])
        assert scope == "a2p:preferences.communication.style"

    def test_get_parent_scopes(self):
        """Test getting parent scopes"""
        parents = get_parent_scopes("a2p:preferences.communication.style")
        assert "a2p:preferences.communication" in parents
        assert "a2p:preferences" in parents
        assert "a2p:*" in parents


class TestScopeSensitivity:
    """Test scope sensitivity levels"""

    def test_get_scope_sensitivity_exact(self):
        """Test getting sensitivity for exact scope"""
        assert get_scope_sensitivity("a2p:preferences") == "public"
        assert get_scope_sensitivity("a2p:health") == "sensitive"
        assert get_scope_sensitivity("a2p:financial") == "restricted"

    def test_get_scope_sensitivity_nested(self):
        """Test getting sensitivity for nested scope"""
        # Should inherit from parent
        assert get_scope_sensitivity("a2p:preferences.communication") == "public"
        assert get_scope_sensitivity("a2p:health.conditions") == "sensitive"

    def test_get_scope_sensitivity_default(self):
        """Test default sensitivity for unknown scope"""
        assert get_scope_sensitivity("a2p:unknown") == "standard"
        assert get_scope_sensitivity("ext:custom") == "standard"
