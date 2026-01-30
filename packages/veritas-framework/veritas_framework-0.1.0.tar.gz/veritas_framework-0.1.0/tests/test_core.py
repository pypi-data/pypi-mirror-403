"""
Tests for Veritas core functionality.
"""

import pytest
from datetime import datetime

from veritas.core.evidence import Evidence, EvidenceType, ArtifactReference
from veritas.core.behaviors import (
    AgentAction,
    VerificationBeforeClaim,
    LoudFailure,
    HonestUncertainty,
)
from veritas.core.context import TrustContext


class TestEvidence:
    """Tests for Evidence model."""

    def test_evidence_creation(self):
        """Test basic evidence creation."""
        evidence = Evidence(
            claim="Tests pass",
            evidence_type=EvidenceType.TEST_RESULTS,
            content="5 passed, 0 failed",
            agent_id="test-agent",
            verifiable_command="pytest",
        )

        assert evidence.claim == "Tests pass"
        assert evidence.evidence_type == EvidenceType.TEST_RESULTS
        assert evidence.is_verifiable()

    def test_evidence_not_verifiable_without_command(self):
        """Test that evidence without command is not verifiable."""
        evidence = Evidence(
            claim="Some claim",
            evidence_type=EvidenceType.LOG_ENTRY,
            content="log content",
            agent_id="test-agent",
        )

        assert not evidence.is_verifiable()

    def test_evidence_with_artifacts(self):
        """Test evidence with artifact references."""
        evidence = Evidence(
            claim="Screenshot captured",
            evidence_type=EvidenceType.SCREENSHOT,
            agent_id="test-agent",
            artifacts=[
                ArtifactReference(
                    path="/tmp/screenshot.png",
                    artifact_type="image",
                )
            ],
        )

        assert evidence.has_artifacts()
        assert len(evidence.artifacts) == 1


class TestBehaviors:
    """Tests for trust behaviors."""

    def test_verification_before_claim_passes(self):
        """Test that verified completion claims pass."""
        behavior = VerificationBeforeClaim()
        action = AgentAction(
            action_id="test-1",
            agent_id="test-agent",
            action_type="claim",
            description="Task complete",
            is_completion_claim=True,
            claimed_outcome="Tests pass",
            has_verification_evidence=True,
            evidence_ids=["ev-1"],
        )

        assert behavior.check(action)

    def test_verification_before_claim_fails_without_evidence(self):
        """Test that unverified completion claims fail."""
        behavior = VerificationBeforeClaim()
        action = AgentAction(
            action_id="test-1",
            agent_id="test-agent",
            action_type="claim",
            description="Task complete",
            is_completion_claim=True,
            claimed_outcome="Tests pass",
            has_verification_evidence=False,
            evidence_ids=[],
        )

        assert not behavior.check(action)

    def test_loud_failure_passes_when_logged(self):
        """Test that logged failures pass."""
        behavior = LoudFailure()
        action = AgentAction(
            action_id="test-1",
            agent_id="test-agent",
            action_type="execute",
            description="API call",
            is_failure=True,
            failure_reason="Connection timeout",
            is_silent_failure=False,
        )

        assert behavior.check(action)

    def test_loud_failure_fails_on_silent(self):
        """Test that silent failures are caught."""
        behavior = LoudFailure()
        action = AgentAction(
            action_id="test-1",
            agent_id="test-agent",
            action_type="execute",
            description="API call",
            is_failure=True,
            failure_reason="Connection timeout",
            is_silent_failure=True,
        )

        assert not behavior.check(action)

    def test_honest_uncertainty_fails_on_fabrication(self):
        """Test that fabricated data is caught."""
        behavior = HonestUncertainty()
        action = AgentAction(
            action_id="test-1",
            agent_id="test-agent",
            action_type="respond",
            description="Answering question",
            fabricated_data=True,
        )

        assert not behavior.check(action)


class TestTrustContext:
    """Tests for TrustContext."""

    def test_context_creation(self):
        """Test basic context creation."""
        ctx = TrustContext(agent_id="test-agent")

        assert ctx.agent_id == "test-agent"
        assert len(ctx.behaviors) > 0
        assert ctx.metrics.actions_total == 0

    def test_record_action(self):
        """Test recording an action."""
        ctx = TrustContext(agent_id="test-agent", strict_mode=False)

        action = ctx.record_action(
            action_type="execute",
            description="Running tests",
        )

        assert action.agent_id == "test-agent"
        assert ctx.metrics.actions_total == 1

    def test_add_evidence(self):
        """Test adding evidence to context."""
        ctx = TrustContext(agent_id="test-agent")

        evidence = ctx.add_evidence(
            claim="Tests pass",
            evidence_type="test_results",
            content="5 passed",
        )

        assert ctx.metrics.evidence_collected == 1
        assert len(ctx.evidence.evidence) == 1

    def test_audit_trail(self):
        """Test getting audit trail."""
        ctx = TrustContext(agent_id="test-agent", strict_mode=False)

        ctx.record_action(
            action_type="execute",
            description="Test action",
        )

        trail = ctx.get_audit_trail()

        assert trail["agent_id"] == "test-agent"
        assert len(trail["actions"]) == 1
