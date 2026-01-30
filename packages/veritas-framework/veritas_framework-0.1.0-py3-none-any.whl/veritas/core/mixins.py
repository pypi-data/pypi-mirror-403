"""
Agent Trust Mixin - A simple interface for adding trust tracking to agents.
"""

from typing import Any, Optional

from veritas.core.context import TrustContext
from veritas.core.evidence import EvidenceType


class AgentTrustMixin:
    """
    Mixin to add Veritas trust enforcement to any agent class.
    
    Provides convenient methods for starting tasks, adding evidence,
    and claiming completion with verification.
    """

    def init_trust(self, agent_id: str, strict_mode: bool = True) -> None:
        """Initialize the trust context for this agent."""
        self.trust_ctx = TrustContext(agent_id=agent_id, strict_mode=strict_mode)

    def start_trust_task(self, task_id: str, description: str) -> None:
        """Record the start of a new task."""
        if not hasattr(self, "trust_ctx"):
            raise RuntimeError("Trust context not initialized. Call init_trust() first.")
        
        self.trust_ctx.record_action(
            action_type="task_start",
            description=description,
            metadata={"task_id": task_id}
        )

    def add_test_evidence(self, claim: str, content: str) -> None:
        """Add test results as evidence."""
        self.trust_ctx.add_evidence(
            claim=claim,
            evidence_type=EvidenceType.TEST_RESULTS.value,
            content=content
        )

    def record_failure(self, error: Exception) -> None:
        """Record a failure (Loud Failure principle)."""
        self.trust_ctx.record_action(
            action_type="error",
            description=str(error),
            is_failure=True,
            failure_reason=str(error)
        )

    def claim_completion(self, claim: str) -> bool:
        """
        Claim task completion. 
        Will be validated against trust protocols (Layer 1).
        """
        # Record the claim
        self.trust_ctx.record_action(
            action_type="claim",
            description=f"Completion claim: {claim}",
            is_completion_claim=True,
            claimed_outcome=claim
        )
        
        # In a full implementation, this would call Layer 1 enforcement
        return True
