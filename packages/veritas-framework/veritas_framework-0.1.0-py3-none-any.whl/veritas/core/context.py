"""
TrustContext - The central context for trust-based agent operations.

A TrustContext tracks:
- Agent identity
- Trust behaviors being enforced
- Evidence collected
- Violations detected
- Audit trail
"""

from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

import structlog
from pydantic import BaseModel, ConfigDict, Field

from veritas.core.behaviors import (
    AgentAction,
    BehaviorViolation,
    TrustBehavior,
    STANDARD_BEHAVIORS,
)
from veritas.core.evidence import Evidence, EvidenceCollection
from veritas.core.verification import (
    Verification,
    VerificationContext,
    VerificationResult,
)

logger = structlog.get_logger()
T = TypeVar("T")


class TrustMetrics(BaseModel):
    """Metrics tracking trust-related statistics."""

    actions_total: int = 0
    actions_verified: int = 0
    violations_total: int = 0
    violations_by_type: dict[str, int] = Field(default_factory=dict)
    evidence_collected: int = 0
    verifications_passed: int = 0
    verifications_failed: int = 0

    def record_action(self, verified: bool = False) -> None:
        self.actions_total += 1
        if verified:
            self.actions_verified += 1

    def record_violation(self, behavior_type: str) -> None:
        self.violations_total += 1
        self.violations_by_type[behavior_type] = (
            self.violations_by_type.get(behavior_type, 0) + 1
        )

    def record_evidence(self) -> None:
        self.evidence_collected += 1

    def record_verification(self, passed: bool) -> None:
        if passed:
            self.verifications_passed += 1
        else:
            self.verifications_failed += 1

    @property
    def verification_rate(self) -> float:
        """Percentage of actions that were verified."""
        if self.actions_total == 0:
            return 0.0
        return self.actions_verified / self.actions_total

    @property
    def violation_rate(self) -> float:
        """Violations per action."""
        if self.actions_total == 0:
            return 0.0
        return self.violations_total / self.actions_total


class TrustContext(BaseModel):
    """
    Central context for trust-based agent operations.

    Usage:
        ctx = TrustContext(agent_id="helena-qa")

        # Record an action
        action = ctx.record_action(
            action_type="execute",
            description="Running test suite",
            is_completion_claim=False
        )

        # Add evidence
        evidence = ctx.add_evidence(
            claim="Tests executed",
            evidence_type=EvidenceType.TEST_RESULTS,
            content="5 passed, 0 failed",
            verifiable_command="pytest -v"
        )

        # Check behaviors
        violations = ctx.check_behaviors(action)
    """

    # Identity
    agent_id: str
    context_id: str = Field(
        default_factory=lambda: f"ctx_{datetime.now().timestamp()}"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Configuration
    behaviors: list[TrustBehavior] = Field(default_factory=lambda: STANDARD_BEHAVIORS.copy())
    strict_mode: bool = Field(
        default=True,
        description="If True, violations raise exceptions. If False, violations are logged.",
    )

    # State
    actions: list[AgentAction] = Field(default_factory=list)
    evidence: EvidenceCollection = Field(default=None)
    violations: list[BehaviorViolation] = Field(default_factory=list)
    verification_contexts: list[VerificationContext] = Field(default_factory=list)

    # Metrics
    metrics: TrustMetrics = Field(default_factory=TrustMetrics)

    # Callbacks
    on_violation: Optional[Callable[[BehaviorViolation], None]] = None
    on_evidence: Optional[Callable[[Evidence], None]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.evidence is None:
            self.evidence = EvidenceCollection(
                claim=f"Evidence for {self.agent_id}",
                agent_id=self.agent_id,
            )

    def record_action(
        self,
        action_type: str,
        description: str,
        is_completion_claim: bool = False,
        claimed_outcome: Optional[str] = None,
        has_verification_evidence: bool = False,
        evidence_ids: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> AgentAction:
        """Record an action taken by the agent."""
        action = AgentAction(
            action_id=f"act_{len(self.actions)}_{datetime.now().timestamp()}",
            agent_id=self.agent_id,
            action_type=action_type,
            description=description,
            is_completion_claim=is_completion_claim,
            claimed_outcome=claimed_outcome,
            has_verification_evidence=has_verification_evidence,
            evidence_ids=evidence_ids or [],
            **kwargs,
        )

        self.actions.append(action)
        self.metrics.record_action(verified=has_verification_evidence)

        # Log the action
        logger.info(
            "action_recorded",
            agent_id=self.agent_id,
            action_id=action.action_id,
            action_type=action_type,
            description=description,
        )

        # Check behaviors
        self._check_behaviors(action)

        return action

    def add_evidence(
        self,
        claim: str,
        evidence_type: str,
        content: Optional[str] = None,
        artifacts: Optional[list[dict[str, Any]]] = None,
        verifiable_command: Optional[str] = None,
        **kwargs: Any,
    ) -> Evidence:
        """Add evidence to the context."""
        from veritas.core.evidence import ArtifactReference, EvidenceType as ET

        artifact_refs = []
        if artifacts:
            for art in artifacts:
                artifact_refs.append(ArtifactReference(**art))

        evidence = Evidence(
            claim=claim,
            evidence_type=ET(evidence_type) if isinstance(evidence_type, str) else evidence_type,
            content=content,
            artifacts=artifact_refs,
            verifiable_command=verifiable_command,
            agent_id=self.agent_id,
            **kwargs,
        )

        self.evidence.add(evidence)
        self.metrics.record_evidence()

        # Log the evidence
        logger.info(
            "evidence_added",
            agent_id=self.agent_id,
            claim=claim,
            evidence_type=str(evidence_type),
            has_artifacts=len(artifact_refs) > 0,
        )

        # Callback
        if self.on_evidence:
            self.on_evidence(evidence)

        return evidence

    def _check_behaviors(self, action: AgentAction) -> list[BehaviorViolation]:
        """Check action against all behaviors and record violations."""
        violations = []

        for behavior in self.behaviors:
            if not behavior.applies_to(action):
                continue

            if not behavior.check(action):
                violation = behavior.on_violation(action)
                violations.append(violation)
                self.violations.append(violation)
                self.metrics.record_violation(str(violation.behavior))

                # Log violation
                logger.warning(
                    "behavior_violation",
                    agent_id=self.agent_id,
                    behavior=str(violation.behavior),
                    severity=violation.severity,
                    description=violation.violation_description,
                )

                # Callback
                if self.on_violation:
                    self.on_violation(violation)

                # Strict mode raises exception
                if self.strict_mode and violation.severity in ["high", "critical"]:
                    raise TrustViolationError(violation)

        return violations

    def start_verification(self, operation: str) -> VerificationContext:
        """Start a new verification context for an operation."""
        ctx = VerificationContext(
            agent_id=self.agent_id,
            operation=operation,
        )
        self.verification_contexts.append(ctx)
        return ctx

    async def verify(self, verification: Verification) -> VerificationResult:
        """Execute a verification and record the result."""
        result = await verification.execute()
        self.metrics.record_verification(result.passed)

        logger.info(
            "verification_executed",
            agent_id=self.agent_id,
            claim=verification.claim,
            method=str(verification.method),
            passed=result.passed,
        )

        return result

    def get_audit_trail(self) -> dict[str, Any]:
        """Get the complete audit trail for this context."""
        return {
            "context_id": self.context_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "actions": [a.model_dump() for a in self.actions],
            "evidence": self.evidence.model_dump(),
            "violations": [v.model_dump() for v in self.violations],
            "metrics": self.metrics.model_dump(),
        }

    def summary(self) -> str:
        """Get a human-readable summary of the trust context."""
        return (
            f"TrustContext({self.agent_id})\n"
            f"  Actions: {self.metrics.actions_total} "
            f"({self.metrics.verification_rate:.0%} verified)\n"
            f"  Evidence: {self.metrics.evidence_collected} pieces\n"
            f"  Violations: {self.metrics.violations_total}\n"
            f"  Verifications: {self.metrics.verifications_passed} passed, "
            f"{self.metrics.verifications_failed} failed"
        )


class TrustViolationError(Exception):
    """Raised when a trust behavior is violated in strict mode."""

    def __init__(self, violation: BehaviorViolation):
        self.violation = violation
        super().__init__(
            f"Trust violation ({violation.behavior}): {violation.violation_description}\n"
            f"Remediation: {violation.remediation}"
        )
