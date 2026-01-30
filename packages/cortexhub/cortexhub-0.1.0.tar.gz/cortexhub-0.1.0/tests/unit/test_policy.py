"""Unit tests for policy engine (loader, evaluator, models)."""

import pytest

from cortexhub.policy.effects import Decision, Effect
from cortexhub.policy.models import AuthorizationRequest


class TestAuthorizationRequest:
    """Test AuthorizationRequest model."""

    def test_create_request(self):
        """Test creating authorization request."""
        request = AuthorizationRequest.create(
            principal_id="agent.test",
            action_name="send_email",
            resource_id="send_email",
            args={"to": "user@example.com", "body": "Hello"},
            framework="test",
        )

        assert request.principal.id == "agent.test"
        assert request.action.name == "send_email"
        assert request.resource.id == "send_email"
        assert request.context["args"]["to"] == "user@example.com"
        assert request.context["runtime"]["framework"] == "test"
        assert "trace_id" in request.context["metadata"]

    def test_trace_id_property(self):
        """Test trace_id property extraction."""
        request = AuthorizationRequest.create(
            principal_id="agent.test",
            action_name="test_tool",
            resource_id="test_tool",
            args={},
            framework="test",
        )

        trace_id = request.trace_id
        assert trace_id != "unknown"
        assert len(trace_id) > 0


class TestDecision:
    """Test Decision model."""

    def test_allow_decision(self):
        """Test creating ALLOW decision."""
        decision = Decision.allow("Test allowed", policy_id="test-policy")

        assert decision.effect == Effect.ALLOW
        assert decision.is_allowed()
        assert not decision.is_denied()
        assert not decision.requires_approval()

    def test_deny_decision(self):
        """Test creating DENY decision."""
        decision = Decision.deny("Test denied", policy_id="test-policy")

        assert decision.effect == Effect.DENY
        assert decision.is_denied()
        assert not decision.is_allowed()
        assert not decision.requires_approval()

    def test_escalate_decision(self):
        """Test creating ESCALATE decision."""
        decision = Decision.escalate("Test escalated", policy_id="test-policy")

        assert decision.effect == Effect.ESCALATE
        assert decision.requires_approval()
        assert not decision.is_allowed()
        assert not decision.is_denied()
