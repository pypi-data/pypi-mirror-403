"""
Layer 2: Workflow Gates

Gates enforce that tasks cannot progress without required evidence.
This makes progress impossible without proof - not just inadvisable.

Key principle: No artifact, no transition.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, ConfigDict, Field

from veritas.core.evidence import Evidence, EvidenceCollection, EvidenceType


class TaskStatus(str, Enum):
    """Standard task statuses."""

    TODO = "todo"
    DOING = "doing"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class GateRequirement(BaseModel):
    """A requirement that must be satisfied to pass through a gate."""

    name: str = Field(description="Human-readable name for this requirement")
    evidence_type: EvidenceType = Field(description="Type of evidence required")
    required: bool = Field(default=True, description="Is this requirement mandatory?")

    # Validation
    validator: Optional[Callable[[Evidence], bool]] = Field(
        default=None,
        description="Custom validation function for the evidence",
    )
    validator_description: Optional[str] = Field(
        default=None,
        description="Human-readable description of what the validator checks",
    )

    # Constraints
    must_be_verified: bool = Field(
        default=False,
        description="Evidence must have been independently verified",
    )
    max_age_hours: Optional[float] = Field(
        default=None,
        description="Evidence must be newer than this many hours",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def check(self, evidence: Evidence) -> tuple[bool, str]:
        """
        Check if evidence satisfies this requirement.

        Returns (passed, reason) tuple.
        """
        # Type check
        if evidence.evidence_type != self.evidence_type:
            return False, f"Expected {self.evidence_type}, got {evidence.evidence_type}"

        # Verification check
        if self.must_be_verified and not evidence.is_verified:
            return False, "Evidence must be independently verified"

        # Age check
        if self.max_age_hours:
            age = (datetime.now() - evidence.timestamp).total_seconds() / 3600
            if age > self.max_age_hours:
                return False, f"Evidence is {age:.1f}h old, max allowed is {self.max_age_hours}h"

        # Custom validator
        if self.validator:
            try:
                if not self.validator(evidence):
                    reason = self.validator_description or "Custom validation failed"
                    return False, reason
            except Exception as e:
                return False, f"Validator error: {e}"

        return True, "Passed"


class GateResult(BaseModel):
    """Result of attempting to pass through a workflow gate."""

    gate_name: str
    passed: bool
    timestamp: datetime = Field(default_factory=datetime.now)

    # Transition details
    from_status: str
    to_status: str
    task_id: Optional[str] = None

    # Requirements check
    requirements_total: int = 0
    requirements_met: int = 0
    missing_requirements: list[str] = Field(default_factory=list)
    failed_requirements: list[dict[str, str]] = Field(default_factory=list)

    # Evidence used
    evidence_ids: list[str] = Field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary of the gate result."""
        if self.passed:
            return (
                f"Gate '{self.gate_name}' PASSED: {self.from_status} → {self.to_status} "
                f"({self.requirements_met}/{self.requirements_total} requirements met)"
            )
        else:
            missing = ", ".join(self.missing_requirements) if self.missing_requirements else "none"
            failed = ", ".join(f["name"] for f in self.failed_requirements) if self.failed_requirements else "none"
            return (
                f"Gate '{self.gate_name}' BLOCKED: Cannot transition {self.from_status} → {self.to_status}\n"
                f"  Missing: {missing}\n"
                f"  Failed: {failed}"
            )


class TaskTransition(BaseModel):
    """Represents a task status transition attempt."""

    task_id: str
    from_status: TaskStatus
    to_status: TaskStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str
    evidence: EvidenceCollection
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowGate(BaseModel):
    """
    A gate that controls task status transitions.

    Gates ensure tasks cannot progress without required evidence.
    This is Layer 2 enforcement: no proof, no progress.
    """

    name: str = Field(description="Gate name")
    from_status: TaskStatus = Field(description="Status transitioning from")
    to_status: TaskStatus = Field(description="Status transitioning to")
    requirements: list[GateRequirement] = Field(default_factory=list)

    # Configuration
    require_all: bool = Field(
        default=True,
        description="If True, all requirements must be met. If False, any one is sufficient.",
    )
    allow_override: bool = Field(
        default=False,
        description="If True, humans can override and force the transition.",
    )
    override_requires_reason: bool = Field(
        default=True,
        description="If override is allowed, require a documented reason.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def check(self, evidence: EvidenceCollection) -> GateResult:
        """
        Check if the provided evidence satisfies gate requirements.

        Returns a GateResult indicating pass/fail and details.
        """
        requirements_met = 0
        missing = []
        failed = []

        for req in self.requirements:
            # Find evidence of the required type
            matching_evidence = evidence.get_by_type(req.evidence_type)

            if not matching_evidence:
                if req.required:
                    missing.append(req.name)
                continue

            # Check each piece of matching evidence
            any_passed = False
            for e in matching_evidence:
                passed, reason = req.check(e)
                if passed:
                    any_passed = True
                    break
                else:
                    failed.append({"name": req.name, "reason": reason})

            if any_passed:
                requirements_met += 1
            elif req.required:
                if req.name not in missing:
                    missing.append(req.name)

        # Determine pass/fail
        if self.require_all:
            passed = len(missing) == 0 and len(failed) == 0
        else:
            passed = requirements_met > 0

        return GateResult(
            gate_name=self.name,
            passed=passed,
            from_status=self.from_status.value,
            to_status=self.to_status.value,
            requirements_total=len(self.requirements),
            requirements_met=requirements_met,
            missing_requirements=missing,
            failed_requirements=failed,
            evidence_ids=[str(e.timestamp.timestamp()) for e in evidence.evidence],
        )

    async def transition(
        self,
        task_id: str,
        evidence: EvidenceCollection,
        override: bool = False,
        override_reason: Optional[str] = None,
        agent_id: str = "unknown",
    ) -> GateResult:
        """
        Attempt to transition a task through this gate.

        If requirements are met, transition is allowed.
        If not met and override is requested (and allowed), transition with documentation.
        Otherwise, transition is blocked.
        """
        result = self.check(evidence)
        result.task_id = task_id

        if result.passed:
            return result

        # Handle override
        if override and self.allow_override:
            if self.override_requires_reason and not override_reason:
                raise GateOverrideError(
                    f"Gate '{self.name}' requires a reason for override"
                )

            # Log the override
            result.passed = True
            result.metadata = {
                "overridden": True,
                "override_reason": override_reason,
                "overridden_by": agent_id,
                "original_missing": result.missing_requirements,
            }
            return result

        # Blocked
        raise GateBlockedError(result)


class GateBlockedError(Exception):
    """Raised when a gate blocks a transition."""

    def __init__(self, result: GateResult):
        self.result = result
        super().__init__(result.summary())


class GateOverrideError(Exception):
    """Raised when an override is invalid."""

    pass


# Common gate configurations
def doing_to_review_gate(
    additional_requirements: list[GateRequirement] | None = None,
) -> WorkflowGate:
    """
    Standard gate for transitioning from 'doing' to 'review'.

    Requires test results and ensures work was actually verified.
    """
    requirements = [
        GateRequirement(
            name="test_results",
            evidence_type=EvidenceType.TEST_RESULTS,
            required=True,
            validator_description="Test results must be present",
        ),
        GateRequirement(
            name="verification_output",
            evidence_type=EvidenceType.COMMAND_OUTPUT,
            required=True,
            validator_description="Verification command must have been run",
        ),
    ]

    if additional_requirements:
        requirements.extend(additional_requirements)

    return WorkflowGate(
        name="doing_to_review",
        from_status=TaskStatus.DOING,
        to_status=TaskStatus.REVIEW,
        requirements=requirements,
    )


def review_to_done_gate(
    require_human_approval: bool = True,
) -> WorkflowGate:
    """
    Standard gate for transitioning from 'review' to 'done'.

    Optionally requires human approval evidence.
    """
    requirements = []

    if require_human_approval:
        requirements.append(
            GateRequirement(
                name="human_approval",
                evidence_type=EvidenceType.HUMAN_APPROVAL,
                required=True,
                validator_description="Human must approve the work",
            )
        )

    return WorkflowGate(
        name="review_to_done",
        from_status=TaskStatus.REVIEW,
        to_status=TaskStatus.DONE,
        requirements=requirements,
        allow_override=True,  # Humans can force-complete
        override_requires_reason=True,
    )
