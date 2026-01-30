"""
Layer 1: Protocol-Embedded Enforcement

Makes lying structurally difficult by embedding verification requirements
directly into the protocol/workflow definitions.

Key principle: The path of least resistance should be the honest path.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from veritas.core.evidence import Evidence, EvidenceType
from veritas.core.context import TrustContext


class RuleViolation(BaseModel):
    """A violation of a protocol rule."""

    rule_name: str
    violation_type: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    remediation: str


class ProtocolRule(ABC):
    """
    Base class for protocol rules that enforce trustworthy behavior.

    Protocol rules are checked BEFORE actions are allowed to proceed.
    They make violations structurally difficult, not just detectable.
    """

    name: str
    description: str

    @abstractmethod
    def check(self, context: TrustContext, action_data: dict[str, Any]) -> bool:
        """
        Check if the proposed action complies with this rule.

        Returns True if compliant, False if violation.
        """
        pass

    @abstractmethod
    def get_violation(
        self, context: TrustContext, action_data: dict[str, Any]
    ) -> RuleViolation:
        """Create a violation record when the rule is broken."""
        pass

    def get_remediation(self, action_data: dict[str, Any]) -> str:
        """Get remediation instructions for a violation."""
        return "Review the protocol rule and adjust the action accordingly."


class CompletionClaimRule(ProtocolRule):
    """
    Rule: Cannot claim completion without verification evidence.

    This rule makes it structurally impossible to say "done" without first
    running verification and attaching evidence.
    """

    name = "completion_claim_requires_verification"
    description = "Completion claims must be accompanied by verification evidence"

    def __init__(
        self,
        required_evidence_types: list[EvidenceType] | None = None,
        verification_command_required: bool = True,
    ):
        self.required_evidence_types = required_evidence_types or [EvidenceType.COMMAND_OUTPUT]
        self.verification_command_required = verification_command_required

    def check(self, context: TrustContext, action_data: dict[str, Any]) -> bool:
        """Check that completion claims have required evidence."""
        # Only applies to completion claims
        if not action_data.get("is_completion_claim", False):
            return True

        # Must have evidence
        evidence_ids = action_data.get("evidence_ids", [])
        if not evidence_ids:
            return False

        # Check evidence exists in context
        evidence_list = [
            e for e in context.evidence.evidence
            if any(str(e.timestamp.timestamp()) in eid for eid in evidence_ids)
        ]

        if not evidence_list:
            return False

        # Check required evidence types
        evidence_types = {e.evidence_type for e in evidence_list}
        for required_type in self.required_evidence_types:
            if required_type not in evidence_types:
                return False

        # Check verification command if required
        if self.verification_command_required:
            has_verifiable = any(e.is_verifiable() for e in evidence_list)
            if not has_verifiable:
                return False

        return True

    def get_violation(
        self, context: TrustContext, action_data: dict[str, Any]
    ) -> RuleViolation:
        missing = []
        evidence_ids = action_data.get("evidence_ids", [])

        if not evidence_ids:
            missing.append("any evidence")
        else:
            # Check what's missing
            evidence_list = context.evidence.evidence
            evidence_types = {e.evidence_type for e in evidence_list}
            for required_type in self.required_evidence_types:
                if required_type not in evidence_types:
                    missing.append(f"evidence type: {required_type}")

            if self.verification_command_required:
                has_verifiable = any(e.is_verifiable() for e in evidence_list)
                if not has_verifiable:
                    missing.append("verifiable command")

        return RuleViolation(
            rule_name=self.name,
            violation_type="missing_verification",
            message=f"Completion claim made without: {', '.join(missing)}",
            context=action_data,
            remediation=(
                "Before claiming completion:\n"
                "1. Run a verification command (e.g., pytest, curl health check)\n"
                "2. Capture the output as evidence\n"
                "3. Attach the evidence to your completion claim\n"
                "4. Include the verification command for reproducibility"
            ),
        )


class FailureHandlingRule(ProtocolRule):
    """
    Rule: Failures must be explicitly surfaced, never silent.

    This rule prevents silent fallbacks, swallowed exceptions, and
    "return None" on error patterns.
    """

    name = "failures_must_be_loud"
    description = "Failures must be explicitly surfaced with clear error information"

    # Keywords that suggest silent failure
    SILENT_FAILURE_PATTERNS = [
        "return None",
        "return {}",
        "return []",
        "pass  # ignore",
        "except: pass",
        "except Exception: pass",
        "# silently",
        "# ignore error",
    ]

    def check(self, context: TrustContext, action_data: dict[str, Any]) -> bool:
        """Check that failures are not being handled silently."""
        # Check if action involves error handling
        if not action_data.get("involves_error_handling", False):
            return True

        # Check for silent failure indicators
        has_error_logging = action_data.get("has_error_logging", False)
        has_error_notification = action_data.get("has_error_notification", False)
        uses_fallback = action_data.get("uses_fallback", False)
        fallback_announced = action_data.get("fallback_announced", False)

        # Errors must be logged
        if not has_error_logging:
            return False

        # If using fallback, it must be announced
        if uses_fallback and not fallback_announced:
            return False

        return True

    def get_violation(
        self, context: TrustContext, action_data: dict[str, Any]
    ) -> RuleViolation:
        issues = []

        if not action_data.get("has_error_logging", False):
            issues.append("Error not logged")

        if action_data.get("uses_fallback", False) and not action_data.get(
            "fallback_announced", False
        ):
            issues.append("Fallback used without announcement")

        return RuleViolation(
            rule_name=self.name,
            violation_type="silent_failure",
            message=f"Silent failure detected: {', '.join(issues)}",
            context=action_data,
            remediation=(
                "When handling errors:\n"
                "1. Always log the error with context\n"
                "2. Notify user/system of the failure\n"
                "3. If using fallback, announce it: 'Primary failed, using fallback: [reason]'\n"
                "4. Never return None/empty and continue silently"
            ),
        )


class UncertaintyRule(ProtocolRule):
    """
    Rule: Uncertainty must be acknowledged, not fabricated over.

    This rule prevents agents from making up data, presenting guesses
    as facts, or answering when "I don't know" is the honest answer.
    """

    name = "uncertainty_must_be_acknowledged"
    description = "When uncertain, agents must acknowledge it rather than fabricate"

    # Phrases that indicate honest uncertainty
    UNCERTAINTY_ACKNOWLEDGMENTS = [
        "I don't know",
        "I'm not sure",
        "I'm uncertain",
        "I cannot determine",
        "I would need to investigate",
        "This is a guess",
        "This may not be accurate",
        "I don't have enough information",
    ]

    def check(self, context: TrustContext, action_data: dict[str, Any]) -> bool:
        """Check that uncertainty is properly handled."""
        # Check if action involves information provision
        if action_data.get("action_type") not in ["respond", "generate", "claim"]:
            return True

        confidence = action_data.get("confidence", 1.0)
        has_uncertainty = confidence < 0.8
        acknowledged_uncertainty = action_data.get("uncertainty_acknowledged", False)

        # If uncertain, must acknowledge
        if has_uncertainty and not acknowledged_uncertainty:
            return False

        # Check for fabrication indicators
        if action_data.get("fabricated_data", False):
            return False

        return True

    def get_violation(
        self, context: TrustContext, action_data: dict[str, Any]
    ) -> RuleViolation:
        if action_data.get("fabricated_data", False):
            violation_type = "data_fabrication"
            message = "Data was fabricated to fill knowledge gaps"
        else:
            violation_type = "unacknowledged_uncertainty"
            message = "Uncertainty was not explicitly acknowledged"

        return RuleViolation(
            rule_name=self.name,
            violation_type=violation_type,
            message=message,
            context=action_data,
            remediation=(
                "When uncertain:\n"
                "1. Explicitly state 'I don't know' or 'I'm not sure'\n"
                "2. Offer to investigate further\n"
                "3. Never fabricate data to fill gaps\n"
                "4. If making an educated guess, clearly label it as such"
            ),
        )


class ProtocolEnforcer:
    """
    Enforces protocol rules on agent actions.

    The enforcer checks all actions against registered rules before
    allowing them to proceed. This makes violations structurally
    difficult rather than just detectable after the fact.
    """

    def __init__(
        self,
        context: TrustContext,
        rules: list[ProtocolRule] | None = None,
        strict: bool = True,
    ):
        self.context = context
        self.rules = rules or [
            CompletionClaimRule(),
            FailureHandlingRule(),
            UncertaintyRule(),
        ]
        self.strict = strict
        self.violations: list[RuleViolation] = []

    def add_rule(self, rule: ProtocolRule) -> None:
        """Add a protocol rule."""
        self.rules.append(rule)

    def check_action(self, action_data: dict[str, Any]) -> tuple[bool, list[RuleViolation]]:
        """
        Check an action against all protocol rules.

        Returns (passed, violations) tuple.
        In strict mode, raises ProtocolViolationError on failure.
        """
        violations = []

        for rule in self.rules:
            if not rule.check(self.context, action_data):
                violation = rule.get_violation(self.context, action_data)
                violations.append(violation)
                self.violations.append(violation)

        if violations and self.strict:
            raise ProtocolViolationError(violations)

        return len(violations) == 0, violations

    def enforce(self, action_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enforce protocol rules on an action.

        If rules pass, returns the action_data unchanged.
        If rules fail, raises ProtocolViolationError in strict mode,
        or adds violation info to action_data in non-strict mode.
        """
        passed, violations = self.check_action(action_data)

        if not passed and not self.strict:
            action_data["protocol_violations"] = [v.model_dump() for v in violations]

        return action_data

    def create_compliant_completion(
        self,
        claim: str,
        evidence: Evidence,
        verification_output: str,
    ) -> dict[str, Any]:
        """
        Helper to create a protocol-compliant completion claim.

        This makes the "right" way the easy way.
        """
        return {
            "is_completion_claim": True,
            "claimed_outcome": claim,
            "evidence_ids": [str(evidence.timestamp.timestamp())],
            "has_verification_evidence": True,
            "verification_output": verification_output,
        }


class ProtocolViolationError(Exception):
    """Raised when protocol rules are violated in strict mode."""

    def __init__(self, violations: list[RuleViolation]):
        self.violations = violations
        messages = [f"- {v.rule_name}: {v.message}" for v in violations]
        remediations = [f"\n{v.rule_name}:\n{v.remediation}" for v in violations]
        super().__init__(
            f"Protocol violations detected:\n"
            + "\n".join(messages)
            + "\n\nRemediation:"
            + "".join(remediations)
        )
