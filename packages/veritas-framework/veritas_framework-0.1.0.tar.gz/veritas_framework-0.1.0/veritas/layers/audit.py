"""
Layer 3: Trust Audit

The audit layer catches what slips through Layers 1 and 2.
It reviews completed work to verify claims match reality.

Key principle: Trust but verify - after the fact.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

import structlog
from pydantic import BaseModel, Field

from veritas.core.context import TrustContext
from veritas.core.evidence import Evidence, EvidenceCollection
from veritas.core.verification import Verification, VerificationMethod, VerificationResult

logger = structlog.get_logger()


class AuditSeverity(str, Enum):
    """Severity levels for audit findings."""

    INFO = "info"  # Informational, not a problem
    LOW = "low"  # Minor issue, should be noted
    MEDIUM = "medium"  # Should be addressed
    HIGH = "high"  # Serious issue, requires attention
    CRITICAL = "critical"  # Trust-breaking, immediate action required


class AuditFindingType(str, Enum):
    """Types of audit findings."""

    # Evidence issues
    MISSING_EVIDENCE = "missing_evidence"
    STALE_EVIDENCE = "stale_evidence"
    UNVERIFIED_EVIDENCE = "unverified_evidence"
    INVALID_EVIDENCE = "invalid_evidence"

    # Claim issues
    UNSUBSTANTIATED_CLAIM = "unsubstantiated_claim"
    CLAIM_EVIDENCE_MISMATCH = "claim_evidence_mismatch"
    FABRICATED_CONTENT = "fabricated_content"

    # Behavioral issues
    SILENT_FAILURE_DETECTED = "silent_failure_detected"
    SHORTCUT_TAKEN = "shortcut_taken"
    INCOMPLETE_WORK = "incomplete_work"

    # Pattern issues
    REPEATED_VIOLATIONS = "repeated_violations"
    DECLINING_QUALITY = "declining_quality"
    TRUST_EROSION = "trust_erosion"


class AuditFinding(BaseModel):
    """A finding from a trust audit."""

    finding_id: str = Field(
        default_factory=lambda: f"find_{datetime.now().timestamp()}"
    )
    finding_type: AuditFindingType
    severity: AuditSeverity
    timestamp: datetime = Field(default_factory=datetime.now)

    # What was found
    title: str
    description: str
    evidence_refs: list[str] = Field(default_factory=list)

    # Context
    agent_id: str
    action_id: Optional[str] = None
    task_id: Optional[str] = None

    # Remediation
    remediation: str
    requires_immediate_action: bool = False

    # Resolution
    is_resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class AuditResult(BaseModel):
    """Result of a trust audit."""

    audit_id: str = Field(
        default_factory=lambda: f"audit_{datetime.now().timestamp()}"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: str

    # Scope
    audit_type: str  # "spot_check", "full_review", "pattern_analysis"
    scope_description: str

    # Findings
    findings: list[AuditFinding] = Field(default_factory=list)
    findings_by_severity: dict[str, int] = Field(default_factory=dict)

    # Summary
    passed: bool = True
    trust_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall trust score (1.0 = fully trusted)",
    )
    summary: str = ""

    # Verification results
    verifications_run: int = 0
    verifications_passed: int = 0
    verifications_failed: int = 0

    def add_finding(self, finding: AuditFinding) -> None:
        """Add a finding to the audit result."""
        self.findings.append(finding)
        self.findings_by_severity[finding.severity.value] = (
            self.findings_by_severity.get(finding.severity.value, 0) + 1
        )

        # Update pass status based on severity
        if finding.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            self.passed = False

    def calculate_trust_score(self) -> float:
        """Calculate trust score based on findings."""
        if not self.findings:
            return 1.0

        # Weight findings by severity
        weights = {
            AuditSeverity.INFO: 0.0,
            AuditSeverity.LOW: 0.05,
            AuditSeverity.MEDIUM: 0.15,
            AuditSeverity.HIGH: 0.3,
            AuditSeverity.CRITICAL: 0.5,
        }

        total_deduction = sum(
            weights.get(f.severity, 0) for f in self.findings
        )

        self.trust_score = max(0.0, 1.0 - total_deduction)
        return self.trust_score


class TrustAuditor:
    """
    Audits agent work for trust violations.

    The auditor performs three types of checks:
    1. Spot checks: Random verification of specific claims
    2. Full reviews: Comprehensive review of all work
    3. Pattern analysis: Looking for systematic issues
    """

    def __init__(self, context: TrustContext):
        self.context = context
        self.audit_history: list[AuditResult] = []

    async def spot_check(
        self,
        claim: str,
        evidence: Evidence,
    ) -> AuditResult:
        """
        Perform a spot check on a specific claim and evidence.

        Verifies that the claim is actually supported by the evidence.
        """
        result = AuditResult(
            agent_id=self.context.agent_id,
            audit_type="spot_check",
            scope_description=f"Spot check of claim: {claim}",
        )

        # Check 1: Evidence exists and has content
        if not evidence.content and not evidence.has_artifacts():
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.MISSING_EVIDENCE,
                    severity=AuditSeverity.HIGH,
                    title="Evidence has no content",
                    description=f"Claim '{claim}' has evidence with no content or artifacts",
                    agent_id=self.context.agent_id,
                    remediation="Re-run the verification and capture actual output",
                )
            )

        # Check 2: Evidence is verifiable
        if evidence.is_verifiable() and evidence.verifiable_command:
            verification = Verification(
                claim=claim,
                method=VerificationMethod.COMMAND_EXECUTION,
                command=evidence.verifiable_command,
            )
            ver_result = await verification.execute()
            result.verifications_run += 1

            if ver_result.passed:
                result.verifications_passed += 1
            else:
                result.verifications_failed += 1
                result.add_finding(
                    AuditFinding(
                        finding_type=AuditFindingType.CLAIM_EVIDENCE_MISMATCH,
                        severity=AuditSeverity.CRITICAL,
                        title="Verification failed on re-run",
                        description=(
                            f"Running '{evidence.verifiable_command}' failed.\n"
                            f"Reason: {ver_result.failure_reason}"
                        ),
                        agent_id=self.context.agent_id,
                        remediation="Investigate why verification no longer passes",
                        requires_immediate_action=True,
                    )
                )

        # Check 3: Artifacts exist (if claimed)
        if evidence.has_artifacts() and not evidence.artifacts_exist():
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.INVALID_EVIDENCE,
                    severity=AuditSeverity.HIGH,
                    title="Artifact files missing",
                    description="Evidence references artifact files that do not exist",
                    agent_id=self.context.agent_id,
                    evidence_refs=[a.path for a in evidence.artifacts],
                    remediation="Locate or regenerate missing artifact files",
                )
            )

        # Check 4: Evidence age
        age_hours = (datetime.now() - evidence.timestamp).total_seconds() / 3600
        if age_hours > 24:
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.STALE_EVIDENCE,
                    severity=AuditSeverity.MEDIUM,
                    title="Evidence is stale",
                    description=f"Evidence is {age_hours:.1f} hours old",
                    agent_id=self.context.agent_id,
                    remediation="Consider re-verifying with fresh evidence",
                )
            )

        result.calculate_trust_score()
        result.summary = self._generate_summary(result)
        self.audit_history.append(result)

        logger.info(
            "spot_check_completed",
            agent_id=self.context.agent_id,
            claim=claim,
            passed=result.passed,
            trust_score=result.trust_score,
            findings_count=len(result.findings),
        )

        return result

    async def full_review(
        self,
        evidence_collection: EvidenceCollection,
    ) -> AuditResult:
        """
        Perform a full review of all evidence in a collection.
        """
        result = AuditResult(
            agent_id=self.context.agent_id,
            audit_type="full_review",
            scope_description=f"Full review of {len(evidence_collection.evidence)} evidence items",
        )

        for evidence in evidence_collection.evidence:
            # Run spot check on each piece
            spot_result = await self.spot_check(evidence.claim, evidence)

            # Aggregate findings
            for finding in spot_result.findings:
                result.add_finding(finding)

            result.verifications_run += spot_result.verifications_run
            result.verifications_passed += spot_result.verifications_passed
            result.verifications_failed += spot_result.verifications_failed

        # Pattern analysis on the collection
        await self._analyze_patterns(result, evidence_collection)

        result.calculate_trust_score()
        result.summary = self._generate_summary(result)
        self.audit_history.append(result)

        return result

    async def analyze_agent_history(self) -> AuditResult:
        """
        Analyze the agent's historical behavior for patterns.
        """
        result = AuditResult(
            agent_id=self.context.agent_id,
            audit_type="pattern_analysis",
            scope_description="Analysis of agent behavioral patterns",
        )

        # Analyze violations
        violations = self.context.violations
        if violations:
            violation_types = {}
            for v in violations:
                vtype = str(v.behavior)
                violation_types[vtype] = violation_types.get(vtype, 0) + 1

            # Check for repeated violations
            for vtype, count in violation_types.items():
                if count >= 3:
                    result.add_finding(
                        AuditFinding(
                            finding_type=AuditFindingType.REPEATED_VIOLATIONS,
                            severity=AuditSeverity.HIGH,
                            title=f"Repeated {vtype} violations",
                            description=f"Agent has {count} violations of type {vtype}",
                            agent_id=self.context.agent_id,
                            remediation=f"Review and address the root cause of {vtype} violations",
                        )
                    )

        # Analyze metrics for declining quality
        metrics = self.context.metrics
        if metrics.verification_rate < 0.5:
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.DECLINING_QUALITY,
                    severity=AuditSeverity.MEDIUM,
                    title="Low verification rate",
                    description=f"Only {metrics.verification_rate:.0%} of actions were verified",
                    agent_id=self.context.agent_id,
                    remediation="Increase verification of actions before claiming completion",
                )
            )

        if metrics.violation_rate > 0.1:
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.TRUST_EROSION,
                    severity=AuditSeverity.HIGH,
                    title="High violation rate",
                    description=f"{metrics.violation_rate:.0%} of actions resulted in violations",
                    agent_id=self.context.agent_id,
                    remediation="Review agent protocols and improve compliance",
                )
            )

        result.calculate_trust_score()
        result.summary = self._generate_summary(result)
        self.audit_history.append(result)

        return result

    async def _analyze_patterns(
        self,
        result: AuditResult,
        evidence_collection: EvidenceCollection,
    ) -> None:
        """Analyze evidence collection for patterns."""
        # Check for missing evidence types
        if evidence_collection.missing_evidence:
            for missing in evidence_collection.missing_evidence:
                result.add_finding(
                    AuditFinding(
                        finding_type=AuditFindingType.MISSING_EVIDENCE,
                        severity=AuditSeverity.MEDIUM,
                        title=f"Missing {missing} evidence",
                        description=f"Expected evidence type '{missing}' was not provided",
                        agent_id=self.context.agent_id,
                        remediation=f"Provide {missing} evidence to complete the collection",
                    )
                )

        # Check completion status
        if not evidence_collection.is_complete:
            result.add_finding(
                AuditFinding(
                    finding_type=AuditFindingType.INCOMPLETE_WORK,
                    severity=AuditSeverity.MEDIUM,
                    title="Evidence collection incomplete",
                    description="Not all required evidence has been collected",
                    agent_id=self.context.agent_id,
                    remediation="Complete evidence collection before claiming done",
                )
            )

    def _generate_summary(self, result: AuditResult) -> str:
        """Generate a human-readable summary of audit results."""
        if result.passed:
            return (
                f"Audit PASSED with trust score {result.trust_score:.0%}. "
                f"{result.verifications_passed}/{result.verifications_run} verifications passed. "
                f"{len(result.findings)} findings ({result.findings_by_severity})."
            )
        else:
            critical = result.findings_by_severity.get("critical", 0)
            high = result.findings_by_severity.get("high", 0)
            return (
                f"Audit FAILED with trust score {result.trust_score:.0%}. "
                f"{critical} critical, {high} high severity findings. "
                f"Immediate attention required."
            )

    def get_trust_trend(self) -> list[dict[str, Any]]:
        """Get trust score trend over audit history."""
        return [
            {
                "audit_id": a.audit_id,
                "timestamp": a.timestamp.isoformat(),
                "trust_score": a.trust_score,
                "findings_count": len(a.findings),
            }
            for a in self.audit_history
        ]
