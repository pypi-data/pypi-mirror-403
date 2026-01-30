"""
Agent Trust Profiles - Pre-defined trust configurations for common agent types.

These profiles define what evidence is required, what behaviors are enforced,
and what gates must be passed for different types of agents.
"""

from typing import Any

from pydantic import BaseModel, Field

from veritas.core.behaviors import (
    TrustBehavior,
    VerificationBeforeClaim,
    LoudFailure,
    HonestUncertainty,
    PaperTrail,
    DiligentExecution,
    STANDARD_BEHAVIORS,
)
from veritas.core.evidence import EvidenceType
from veritas.layers.protocol import (
    ProtocolRule,
    CompletionClaimRule,
    FailureHandlingRule,
    UncertaintyRule,
)
from veritas.layers.gates import (
    WorkflowGate,
    GateRequirement,
    TaskStatus,
)


class AgentTrustProfile(BaseModel):
    """
    A trust profile defining requirements for an agent type.

    Profiles specify:
    - What behaviors are enforced
    - What evidence is required
    - What gates must be passed
    - What protocol rules apply
    """

    name: str = Field(description="Profile name")
    description: str = Field(description="What this profile is for")

    # Behaviors to enforce
    behaviors: list[str] = Field(
        default_factory=lambda: [
            "verification_before_claim",
            "loud_failure",
            "honest_uncertainty",
            "paper_trail",
            "diligent_execution",
        ]
    )

    # Evidence requirements for completion
    required_evidence_types: list[str] = Field(
        default_factory=lambda: ["command_output"]
    )

    # Protocol rules
    protocol_rules: list[str] = Field(
        default_factory=lambda: [
            "completion_claim_requires_verification",
            "failures_must_be_loud",
            "uncertainty_must_be_acknowledged",
        ]
    )

    # Gate configurations
    gates: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # Strictness
    strict_mode: bool = Field(default=True)
    block_on_violation: bool = Field(default=True)

    class Config:
        arbitrary_types_allowed = True

    def get_behaviors(self) -> list[TrustBehavior]:
        """Get TrustBehavior instances for this profile."""
        behavior_map = {
            "verification_before_claim": VerificationBeforeClaim(),
            "loud_failure": LoudFailure(),
            "honest_uncertainty": HonestUncertainty(),
            "paper_trail": PaperTrail(),
            "diligent_execution": DiligentExecution(),
        }
        return [behavior_map[b] for b in self.behaviors if b in behavior_map]

    def get_protocol_rules(self) -> list[ProtocolRule]:
        """Get ProtocolRule instances for this profile."""
        rule_map = {
            "completion_claim_requires_verification": CompletionClaimRule(
                required_evidence_types=[
                    EvidenceType(t) for t in self.required_evidence_types
                ]
            ),
            "failures_must_be_loud": FailureHandlingRule(),
            "uncertainty_must_be_acknowledged": UncertaintyRule(),
        }
        return [rule_map[r] for r in self.protocol_rules if r in rule_map]


# Pre-defined profiles for common agent types


class QAAgentProfile(AgentTrustProfile):
    """Trust profile for QA/Testing agents like Helena and Victor."""

    name: str = "qa_agent"
    description: str = "Trust profile for QA and testing agents"

    required_evidence_types: list[str] = Field(
        default_factory=lambda: [
            "test_results",
            "command_output",
        ]
    )

    gates: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {
            "doing_to_review": {
                "requirements": [
                    {"name": "test_results", "evidence_type": "test_results", "required": True},
                    {"name": "test_output", "evidence_type": "command_output", "required": True},
                ]
            },
            "review_to_done": {
                "requirements": [
                    {"name": "all_tests_pass", "evidence_type": "assertion", "required": True},
                ]
            },
        }
    )

    def get_gates(self) -> list[WorkflowGate]:
        """Get WorkflowGate instances for QA workflow."""
        return [
            WorkflowGate(
                name="doing_to_review",
                from_status=TaskStatus.DOING,
                to_status=TaskStatus.REVIEW,
                requirements=[
                    GateRequirement(
                        name="test_results",
                        evidence_type=EvidenceType.TEST_RESULTS,
                        required=True,
                    ),
                    GateRequirement(
                        name="test_output",
                        evidence_type=EvidenceType.COMMAND_OUTPUT,
                        required=True,
                    ),
                ],
            ),
            WorkflowGate(
                name="review_to_done",
                from_status=TaskStatus.REVIEW,
                to_status=TaskStatus.DONE,
                requirements=[
                    GateRequirement(
                        name="all_tests_pass",
                        evidence_type=EvidenceType.ASSERTION,
                        required=True,
                    ),
                ],
                allow_override=True,
                override_requires_reason=True,
            ),
        ]


class DeveloperAgentProfile(AgentTrustProfile):
    """Trust profile for developer agents."""

    name: str = "developer_agent"
    description: str = "Trust profile for coding and development agents"

    required_evidence_types: list[str] = Field(
        default_factory=lambda: [
            "command_output",
            "diff",
        ]
    )

    gates: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {
            "doing_to_review": {
                "requirements": [
                    {"name": "code_compiles", "evidence_type": "command_output", "required": True},
                    {"name": "tests_pass", "evidence_type": "test_results", "required": True},
                    {"name": "code_diff", "evidence_type": "diff", "required": False},
                ]
            },
        }
    )

    def get_gates(self) -> list[WorkflowGate]:
        """Get WorkflowGate instances for developer workflow."""
        return [
            WorkflowGate(
                name="doing_to_review",
                from_status=TaskStatus.DOING,
                to_status=TaskStatus.REVIEW,
                requirements=[
                    GateRequirement(
                        name="code_compiles",
                        evidence_type=EvidenceType.COMMAND_OUTPUT,
                        required=True,
                        validator_description="Code must compile without errors",
                    ),
                    GateRequirement(
                        name="tests_pass",
                        evidence_type=EvidenceType.TEST_RESULTS,
                        required=True,
                    ),
                    GateRequirement(
                        name="code_diff",
                        evidence_type=EvidenceType.DIFF,
                        required=False,
                    ),
                ],
            ),
        ]


class PMAgentProfile(AgentTrustProfile):
    """Trust profile for project management agents like Gage."""

    name: str = "pm_agent"
    description: str = "Trust profile for project management agents"

    required_evidence_types: list[str] = Field(
        default_factory=lambda: [
            "log_entry",
        ]
    )

    # PM agents have relaxed evidence requirements but strict paper trail
    behaviors: list[str] = Field(
        default_factory=lambda: [
            "loud_failure",
            "honest_uncertainty",
            "paper_trail",  # Critical for PM
        ]
    )

    protocol_rules: list[str] = Field(
        default_factory=lambda: [
            "failures_must_be_loud",
            "uncertainty_must_be_acknowledged",
        ]
    )

    def get_gates(self) -> list[WorkflowGate]:
        """Get WorkflowGate instances for PM workflow."""
        return [
            WorkflowGate(
                name="task_creation",
                from_status=TaskStatus.TODO,
                to_status=TaskStatus.DOING,
                requirements=[
                    GateRequirement(
                        name="task_documented",
                        evidence_type=EvidenceType.LOG_ENTRY,
                        required=True,
                    ),
                ],
            ),
        ]
