"""Tests for ID generation utilities"""

from a2p.utils.id import (
    generate_agent_did,
    generate_memory_id,
    generate_org_did,
    generate_policy_id,
    generate_proposal_id,
    generate_receipt_id,
    generate_request_id,
    generate_session_id,
    generate_user_did,
    get_namespace,
    is_local_did,
    is_valid_a2p_did,
    is_valid_agent_did,
    is_valid_did,
    is_valid_user_did,
    parse_did,
)


class TestIDGeneration:
    """Test ID generation functions"""

    def test_generate_memory_id(self):
        """Test memory ID generation"""
        mem_id = generate_memory_id()
        assert mem_id.startswith("mem_")
        assert len(mem_id) == 20  # "mem_" + 16 chars

    def test_generate_proposal_id(self):
        """Test proposal ID generation"""
        prop_id = generate_proposal_id()
        assert prop_id.startswith("prop_")
        assert len(prop_id) == 21  # "prop_" + 16 chars

    def test_generate_policy_id(self):
        """Test policy ID generation"""
        policy_id = generate_policy_id()
        assert policy_id.startswith("policy_")
        assert len(policy_id) == 19  # "policy_" + 12 chars

    def test_generate_receipt_id(self):
        """Test receipt ID generation"""
        receipt_id = generate_receipt_id()
        assert receipt_id.startswith("rcpt_")
        assert len(receipt_id) == 21  # "rcpt_" + 16 chars

    def test_generate_session_id(self):
        """Test session ID generation"""
        sess_id = generate_session_id()
        assert sess_id.startswith("sess_")
        assert len(sess_id) == 25  # "sess_" + 20 chars

    def test_generate_request_id(self):
        """Test request ID generation"""
        req_id = generate_request_id()
        assert req_id.startswith("req_")
        assert len(req_id) == 20  # "req_" + 16 chars

    def test_generate_user_did(self):
        """Test user DID generation"""
        did = generate_user_did()
        assert did.startswith("did:a2p:user:local:")
        assert len(did) > 20  # "did:a2p:user:local:" + identifier

    def test_generate_user_did_with_namespace(self):
        """Test user DID generation with namespace"""
        did = generate_user_did("gaugid", "alice")
        assert did == "did:a2p:user:gaugid:alice"

    def test_generate_user_did_with_identifier(self):
        """Test user DID generation with custom identifier"""
        did = generate_user_did("local", "alice")
        assert did == "did:a2p:user:local:alice"

    def test_generate_agent_did(self):
        """Test agent DID generation"""
        did = generate_agent_did("local", "My Agent")
        assert did.startswith("did:a2p:agent:local:")
        assert "my-agent" in did.lower()

    def test_generate_agent_did_special_chars(self):
        """Test agent DID generation with special characters"""
        did = generate_agent_did("local", "Agent@123!")
        assert did.startswith("did:a2p:agent:local:")
        assert "-" in did  # Special chars should be replaced

    def test_generate_org_did(self):
        """Test organization DID generation"""
        did = generate_org_did("local", "My Org")
        assert did.startswith("did:a2p:org:local:")
        assert "my-org" in did.lower()


class TestDIDValidation:
    """Test DID validation and parsing"""

    def test_is_valid_did_valid(self):
        """Test valid DID validation (generic)"""
        assert is_valid_did("did:a2p:user:gaugid:alice")
        assert is_valid_did("did:a2p:agent:local:my-agent")
        assert is_valid_did("did:example:123")
        assert is_valid_did("did:web:example.com")

    def test_is_valid_did_invalid(self):
        """Test invalid DID validation"""
        assert not is_valid_did("not-a-did")
        assert not is_valid_did("did:")
        assert not is_valid_did("did:a2p:")
        assert not is_valid_did("did:a2p:user:")
        assert not is_valid_did("DID:a2p:user:gaugid:alice")  # Uppercase

    def test_is_valid_a2p_did_valid(self):
        """Test valid a2p DID validation"""
        assert is_valid_a2p_did("did:a2p:user:gaugid:alice")
        assert is_valid_a2p_did("did:a2p:agent:local:my-agent")
        assert is_valid_a2p_did("did:a2p:org:gaugid:acme-corp")

    def test_is_valid_a2p_did_invalid(self):
        """Test invalid a2p DID validation (missing namespace)"""
        assert not is_valid_a2p_did("did:a2p:user:alice")  # missing namespace
        assert not is_valid_a2p_did("did:a2p:agent:my-agent")  # missing namespace
        assert not is_valid_a2p_did("did:other:test")

    def test_is_valid_agent_did(self):
        """Test agent DID validation"""
        assert is_valid_agent_did("did:a2p:agent:gaugid:my-assistant")
        assert is_valid_agent_did("did:a2p:agent:local:trusted-ai")
        assert not is_valid_agent_did("did:a2p:agent:my-assistant")  # missing namespace
        assert not is_valid_agent_did("did:a2p:user:gaugid:alice")

    def test_is_valid_user_did(self):
        """Test user DID validation"""
        assert is_valid_user_did("did:a2p:user:gaugid:alice")
        assert is_valid_user_did("did:a2p:user:local:alice")
        assert not is_valid_user_did("did:a2p:user:alice")  # missing namespace
        assert not is_valid_user_did("did:a2p:agent:gaugid:my-agent")

    def test_parse_did_valid(self):
        """Test a2p DID parsing"""
        result = parse_did("did:a2p:user:gaugid:alice")
        assert result is not None
        assert result["type"] == "user"
        assert result["namespace"] == "gaugid"
        assert result["identifier"] == "alice"

    def test_parse_did_local(self):
        """Test parsing local namespace DID"""
        result = parse_did("did:a2p:agent:local:my-agent")
        assert result is not None
        assert result["type"] == "agent"
        assert result["namespace"] == "local"
        assert result["identifier"] == "my-agent"

    def test_parse_did_invalid(self):
        """Test parsing invalid DID"""
        assert parse_did("not-a-did") is None
        assert parse_did("did:") is None
        assert parse_did("did:a2p:user:alice") is None  # missing namespace

    def test_get_namespace(self):
        """Test namespace extraction"""
        assert get_namespace("did:a2p:user:gaugid:alice") == "gaugid"
        assert get_namespace("did:a2p:agent:local:my-agent") == "local"
        assert get_namespace("did:a2p:user:alice") is None  # invalid

    def test_is_local_did(self):
        """Test local namespace detection"""
        assert is_local_did("did:a2p:user:local:alice")
        assert is_local_did("did:a2p:agent:local:my-agent")
        assert not is_local_did("did:a2p:user:gaugid:alice")
        assert not is_local_did("did:a2p:user:alice")  # invalid
