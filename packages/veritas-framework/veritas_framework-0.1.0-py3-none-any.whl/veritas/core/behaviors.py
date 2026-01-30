"""
Trust Behaviors - The five character traits that define trustworthy agents.

These behaviors are not rules to follow, but character to embody:
1. Verification Before Claim - Never say "done" without proof
2. Loud Failure - No silent fallbacks; errors are surfaced
3. Honest Uncertainty - "I don't know" is valid; never fabricate
4. Paper Trail - Every action logged, every decision documented
5. Diligent Execution - No shortcuts, even when tedious
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class BehaviorType(str, Enum):
    """The five core trust behaviors."""

    VERIFICATION_BEFORE_CLAIM = "verification_before_claim"
    LOUD_FAILURE = "loud_failure"
    HONEST_UNCERTAINTY = "honest_uncertainty"
    PAPER_TRAIL = "paper_trail"
    DILIGENT_EXECUTION = "diligent_execution"


class AgentAction(BaseModel):
    """Represents an action taken by an agent that can be evaluated for trust."""

    action_id: str
    agent_id: str
    action_type: str  # e.g., "claim", "execute", "respond", "fail"
    timestamp: datetime = Field(default_factory=datetime.now)

    # Action details
    description: str
    target: Optional[str] = None  # What the action affects
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)

    # Claim metadata (for completion claims)
    is_completion_claim: bool = False
    claimed_outcome: Optional[str] = None
    has_verification_evidence: bool = False
    evidence_ids: list[str] = Field(default_factory=list)

    # Failure metadata
    is_failure: bool = False
    failure_reason: Optional[str] = None
    is_silent_failure: bool = False  # Did it fail without notifying?
    has_fallback: bool = False
    fallback_was_silent: bool = False

    # Uncertainty metadata
    expresses_uncertainty: bool = False
    uncertainty_acknowledged: bool = False
    fabricated_data: bool = False

    # Execution metadata
    steps_required: int = 0
    steps_completed: int = 0
    shortcuts_taken: list[str] = Field(default_factory=list)


class BehaviorViolation(BaseModel):
    """A violation of a trust behavior."""

    violation_id: str = Field(default_factory=lambda: f"viol_{datetime.now().timestamp()}")
    behavior: BehaviorType
    agent_id: str
    action: AgentAction
    timestamp: datetime = Field(default_factory=datetime.now)

    # Violation details
    violation_description: str
    severity: str = "medium"  # low, medium, high, critical
    remediation: str  # What should be done to fix this

    # Context
    context: dict[str, Any] = Field(default_factory=dict)

    # Resolution
    is_resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


class TrustBehavior(ABC):
    """
    Base class for trust behaviors.

    A trust behavior defines:
    - What actions to check
    - How to determine if the behavior is violated
    - What to do when violated
    """

    behavior_type: BehaviorType

    @abstractmethod
    def check(self, action: AgentAction) -> bool:
        """
        Check if an action complies with this behavior.

        Returns True if compliant, False if violated.
        """
        pass

    @abstractmethod
    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        """
        Create a violation record when the behavior is not followed.
        """
        pass

    def applies_to(self, action: AgentAction) -> bool:
        """
        Check if this behavior applies to the given action.
        Override in subclasses for selective application.
        """
        return True


class VerificationBeforeClaim(TrustBehavior):
    """
    Behavior: Never claim completion without verification evidence.

    Violations:
    - Saying "done" without running verification
    - Claiming success without proof artifacts
    - Asserting outcomes without testing
    """

    behavior_type = BehaviorType.VERIFICATION_BEFORE_CLAIM

    def applies_to(self, action: AgentAction) -> bool:
        """Only applies to completion claims."""
        return action.is_completion_claim

    def check(self, action: AgentAction) -> bool:
        """Check that completion claims have verification evidence."""
        if not action.is_completion_claim:
            return True
        return action.has_verification_evidence and len(action.evidence_ids) > 0

    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        return BehaviorViolation(
            behavior=self.behavior_type,
            agent_id=action.agent_id,
            action=action,
            violation_description=(
                f"Agent claimed '{action.claimed_outcome}' without verification evidence. "
                "Completion claims must be backed by proof."
            ),
            severity="high",
            remediation=(
                "Run verification command and attach output as evidence. "
                "Do not claim completion until verification passes."
            ),
        )


class LoudFailure(TrustBehavior):
    """
    Behavior: Failures must be surfaced, not hidden.

    Violations:
    - Silent fallbacks (service fails, agent continues with alternative)
    - Swallowed exceptions (catch and ignore)
    - Return None/empty when error occurred
    - Continue as if nothing happened
    """

    behavior_type = BehaviorType.LOUD_FAILURE

    def applies_to(self, action: AgentAction) -> bool:
        """Applies to actions that involve failure handling."""
        return action.is_failure or action.has_fallback

    def check(self, action: AgentAction) -> bool:
        """Check that failures are not silent."""
        if action.is_failure:
            return not action.is_silent_failure
        if action.has_fallback:
            return not action.fallback_was_silent
        return True

    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        if action.is_silent_failure:
            description = (
                f"Agent failed silently: {action.failure_reason}. "
                "Failures must be explicitly reported, not hidden."
            )
        else:
            description = (
                "Agent used a silent fallback without notifying. "
                "Fallbacks are acceptable but must be announced."
            )

        return BehaviorViolation(
            behavior=self.behavior_type,
            agent_id=action.agent_id,
            action=action,
            violation_description=description,
            severity="critical",
            remediation=(
                "When failures occur: 1) Log the error explicitly, "
                "2) Notify the user/system, 3) Do not continue silently. "
                "If using fallback, announce: 'Primary failed, using fallback: [reason]'"
            ),
        )


class HonestUncertainty(TrustBehavior):
    """
    Behavior: Acknowledge uncertainty rather than fabricating.

    Violations:
    - Making up data to fill gaps
    - Presenting guesses as facts
    - Hallucinating information
    - Answering when "I don't know" is the honest answer
    """

    behavior_type = BehaviorType.HONEST_UNCERTAINTY

    def applies_to(self, action: AgentAction) -> bool:
        """Applies to actions involving information provision."""
        return action.action_type in ["respond", "generate", "claim"]

    def check(self, action: AgentAction) -> bool:
        """Check that uncertainty is acknowledged, not fabricated."""
        if action.fabricated_data:
            return False
        if action.expresses_uncertainty and not action.uncertainty_acknowledged:
            return False
        return True

    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        if action.fabricated_data:
            description = (
                "Agent fabricated data rather than acknowledging uncertainty. "
                "This is a fundamental trust violation."
            )
            severity = "critical"
        else:
            description = (
                "Agent expressed uncertainty but did not explicitly acknowledge it. "
                "Uncertainty must be clearly communicated."
            )
            severity = "high"

        return BehaviorViolation(
            behavior=self.behavior_type,
            agent_id=action.agent_id,
            action=action,
            violation_description=description,
            severity=severity,
            remediation=(
                "When uncertain: 1) Say 'I don't know' explicitly, "
                "2) Offer to investigate, 3) Never fabricate. "
                "Honest uncertainty builds trust; fabrication destroys it."
            ),
        )


class PaperTrail(TrustBehavior):
    """
    Behavior: Every action must be logged and traceable.

    Violations:
    - Actions without logging
    - Decisions without documented reasoning
    - Untraceable modifications
    - Missing audit trail
    """

    behavior_type = BehaviorType.PAPER_TRAIL

    def check(self, action: AgentAction) -> bool:
        """Check that action has proper logging and traceability."""
        # Actions must have basic identification
        if not action.action_id or not action.agent_id:
            return False
        # Non-trivial actions must have description
        if action.action_type in ["execute", "modify", "delete"] and not action.description:
            return False
        return True

    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        return BehaviorViolation(
            behavior=self.behavior_type,
            agent_id=action.agent_id,
            action=action,
            violation_description=(
                "Action lacks proper documentation for audit trail. "
                "All actions must be traceable."
            ),
            severity="medium",
            remediation=(
                "Ensure all actions have: 1) Unique action_id, "
                "2) Clear description, 3) Timestamp, 4) Agent identification. "
                "When errors occur later, we need to trace back."
            ),
        )


class DiligentExecution(TrustBehavior):
    """
    Behavior: Complete all steps without shortcuts.

    Violations:
    - Skipping "unimportant" steps
    - Taking shortcuts on tedious tasks
    - Partial completion presented as full
    - Quality degradation on boring work
    """

    behavior_type = BehaviorType.DILIGENT_EXECUTION

    def applies_to(self, action: AgentAction) -> bool:
        """Applies to execution actions with multiple steps."""
        return action.action_type == "execute" and action.steps_required > 0

    def check(self, action: AgentAction) -> bool:
        """Check that all required steps were completed."""
        if action.steps_required > 0:
            if action.steps_completed < action.steps_required:
                return False
        if len(action.shortcuts_taken) > 0:
            return False
        return True

    def on_violation(self, action: AgentAction) -> BehaviorViolation:
        if action.steps_completed < action.steps_required:
            description = (
                f"Agent completed {action.steps_completed}/{action.steps_required} steps. "
                "All required steps must be completed."
            )
        else:
            description = (
                f"Agent took shortcuts: {', '.join(action.shortcuts_taken)}. "
                "Shortcuts compromise reliability."
            )

        return BehaviorViolation(
            behavior=self.behavior_type,
            agent_id=action.agent_id,
            action=action,
            violation_description=description,
            severity="high",
            remediation=(
                "Complete all required steps, even tedious ones. "
                "Quality must not degrade based on task interest level. "
                "If steps can be legitimately skipped, document why."
            ),
        )


# Convenience: All standard behaviors
STANDARD_BEHAVIORS: list[TrustBehavior] = [
    VerificationBeforeClaim(),
    LoudFailure(),
    HonestUncertainty(),
    PaperTrail(),
    DiligentExecution(),
]
