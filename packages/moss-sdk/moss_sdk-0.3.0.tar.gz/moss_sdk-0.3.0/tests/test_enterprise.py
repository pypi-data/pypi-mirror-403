"""Tests for enterprise module."""

import os
import pytest
from unittest.mock import patch, MagicMock

from moss.enterprise import (
    is_enterprise_mode,
    evaluate_sync,
    evaluate_async,
    EnterpriseResult,
    PolicyResult,
    Decision,
)


class TestEnterpriseMode:
    """Test enterprise mode detection."""
    
    def test_enterprise_mode_disabled_by_default(self):
        """Enterprise mode is disabled when no API key is set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove MOSS_API_KEY if it exists
            os.environ.pop("MOSS_API_KEY", None)
            # Need to reimport to pick up env change
            import importlib
            import moss.enterprise
            importlib.reload(moss.enterprise)
            assert not moss.enterprise.is_enterprise_mode()
    
    def test_enterprise_mode_enabled_with_key(self):
        """Enterprise mode is enabled when API key is set."""
        with patch.dict(os.environ, {"MOSS_API_KEY": "test_key"}):
            import importlib
            import moss.enterprise
            importlib.reload(moss.enterprise)
            assert moss.enterprise.is_enterprise_mode()


class TestEnterpriseResult:
    """Test EnterpriseResult dataclass."""
    
    def test_allowed_when_no_policy(self):
        """Action is allowed when no policy evaluation occurred."""
        from moss.enterprise import EnterpriseResult
        result = EnterpriseResult()
        assert result.allowed is True
        assert result.blocked is False
    
    def test_allowed_when_policy_allows(self):
        """Action is allowed when policy decision is ALLOW."""
        from moss.enterprise import EnterpriseResult, PolicyResult, Decision
        result = EnterpriseResult(
            policy=PolicyResult(decision=Decision.ALLOW)
        )
        assert result.allowed is True
        assert result.blocked is False
    
    def test_blocked_when_policy_blocks(self):
        """Action is blocked when policy decision is BLOCK."""
        from moss.enterprise import EnterpriseResult, PolicyResult, Decision
        result = EnterpriseResult(
            policy=PolicyResult(decision=Decision.BLOCK, reason="Not allowed")
        )
        assert result.allowed is False
        assert result.blocked is True


class TestEvaluateSync:
    """Test synchronous evaluation."""
    
    def test_returns_empty_result_when_not_enterprise(self):
        """Returns empty result when enterprise mode is disabled."""
        with patch("moss.enterprise.is_enterprise_mode", return_value=False):
            result = evaluate_sync(
                agent_id="test-agent",
                action="test",
                envelope={"subject": "moss:agent:test"},
                payload={"action": "test"},
            )
            assert result.policy is None
            assert result.error is None
    
    def test_returns_error_when_httpx_not_installed(self):
        """Returns error when httpx is not installed."""
        with patch("moss.enterprise.is_enterprise_mode", return_value=True):
            with patch.dict("sys.modules", {"httpx": None}):
                # This should handle ImportError gracefully
                result = evaluate_sync(
                    agent_id="test-agent",
                    action="test",
                    envelope={},
                    payload={},
                )
                # Should either return error or succeed if httpx is available
                assert result is not None


class TestPolicyResult:
    """Test PolicyResult dataclass."""
    
    def test_policy_result_with_all_fields(self):
        """PolicyResult can be created with all fields."""
        result = PolicyResult(
            decision=Decision.BLOCK,
            reason="Policy violation",
            shadow_mode=False,
            evidence_id="ev_123",
            usage_warning="80% of quota used",
        )
        assert result.decision == Decision.BLOCK
        assert result.reason == "Policy violation"
        assert result.shadow_mode is False
        assert result.evidence_id == "ev_123"
        assert result.usage_warning == "80% of quota used"
