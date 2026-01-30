"""Tests for the main sign/verify API."""

import pytest
from unittest.mock import patch

from moss import sign, verify, SignResult, VerifyResult, enterprise_enabled


class TestSign:
    """Test the sign() function."""
    
    def test_sign_dict_output(self):
        """Sign a dictionary output."""
        result = sign(
            output={"action": "test", "value": 123},
            agent_id="test-agent",
        )
        
        assert isinstance(result, SignResult)
        assert result.envelope is not None
        assert result.signature is not None
        assert "test-agent" in result.agent_id
        assert result.timestamp > 0
    
    def test_sign_string_output(self):
        """Sign a string output."""
        result = sign(
            output="Hello, world!",
            agent_id="test-agent",
        )
        
        assert isinstance(result, SignResult)
        assert result.envelope is not None
        assert result.payload.get("output") == "Hello, world!"
    
    def test_sign_with_context(self):
        """Sign with context metadata."""
        result = sign(
            output={"action": "transfer"},
            agent_id="finance-agent",
            context={"user_id": "u123", "amount": 50000},
        )
        
        assert result.payload.get("_context") == {"user_id": "u123", "amount": 50000}
    
    def test_sign_with_action(self):
        """Sign with explicit action name."""
        result = sign(
            output={"data": "test"},
            agent_id="test-agent",
            action="custom_action",
        )
        
        assert isinstance(result, SignResult)
        # Action is used for enterprise policy, not stored in envelope
    
    def test_sign_normalizes_agent_id(self):
        """Agent ID is normalized to full subject format."""
        result = sign(
            output={"test": True},
            agent_id="my-agent",
        )
        
        assert result.agent_id == "moss:agent:my-agent"
    
    def test_sign_preserves_full_subject_id(self):
        """Full subject ID is preserved."""
        result = sign(
            output={"test": True},
            agent_id="moss:custom:my-agent",
        )
        
        assert result.agent_id == "moss:custom:my-agent"
    
    def test_sign_without_enterprise(self):
        """Sign without enterprise mode returns allowed=True."""
        with patch("moss.is_enterprise_mode", return_value=False):
            result = sign(
                output={"test": True},
                agent_id="test-agent",
            )
            
            assert result.allowed is True
            assert result.blocked is False
            assert result.evidence_id is None


class TestVerify:
    """Test the verify() function."""
    
    def test_verify_valid_envelope(self):
        """Verify a valid envelope."""
        # First sign something
        sign_result = sign(
            output={"action": "test"},
            agent_id="test-agent",
        )
        
        # Then verify it
        verify_result = verify(sign_result.envelope)
        
        assert isinstance(verify_result, VerifyResult)
        assert verify_result.valid is True
        assert verify_result.subject == sign_result.agent_id
    
    def test_verify_with_payload(self):
        """Verify envelope with original payload."""
        payload = {"action": "test", "value": 42}
        sign_result = sign(output=payload, agent_id="test-agent")
        
        # Verify with the original payload
        verify_result = verify(sign_result.envelope, payload=sign_result.payload)
        
        assert verify_result.valid is True
    
    def test_verify_envelope_dict(self):
        """Verify envelope from dict representation."""
        sign_result = sign(output={"test": True}, agent_id="test-agent")
        
        # Convert to dict and verify
        envelope_dict = sign_result.envelope.to_dict()
        verify_result = verify(envelope_dict)
        
        assert verify_result.valid is True
    
    def test_verify_invalid_envelope(self):
        """Verify returns invalid for malformed envelope."""
        verify_result = verify({"invalid": "envelope"})
        
        assert verify_result.valid is False
        assert verify_result.reason is not None


class TestSignResult:
    """Test SignResult dataclass."""
    
    def test_sign_result_properties(self):
        """SignResult exposes envelope properties."""
        result = sign(output={"test": True}, agent_id="test-agent")
        
        assert result.signature == result.envelope.signature
        assert result.agent_id == result.envelope.subject
        assert result.timestamp == result.envelope.issued_at
    
    def test_sign_result_to_dict(self):
        """SignResult can be serialized to dict."""
        result = sign(output={"test": True}, agent_id="test-agent")
        
        d = result.to_dict()
        
        assert "envelope" in d
        assert "payload" in d
        assert d["envelope"]["signature"] == result.signature


class TestEnterpriseEnabled:
    """Test enterprise_enabled() function."""
    
    def test_enterprise_enabled_function_exists(self):
        """enterprise_enabled() function is exported."""
        assert callable(enterprise_enabled)
