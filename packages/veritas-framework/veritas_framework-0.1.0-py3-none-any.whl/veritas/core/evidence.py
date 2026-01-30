"""
Evidence - The atomic unit of trust in Veritas.

Every claim an agent makes must be backed by evidence. Evidence is:
- Verifiable: Can be independently confirmed
- Timestamped: When was this produced?
- Traceable: Who produced it? What command?
- Persistent: Stored for audit trail
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence an agent can produce."""

    # Execution evidence
    COMMAND_OUTPUT = "command_output"  # Output from a shell command
    API_RESPONSE = "api_response"  # Response from an API call
    TEST_RESULTS = "test_results"  # Test execution results
    LOG_ENTRY = "log_entry"  # Log file entry

    # Artifact evidence
    FILE_CREATED = "file_created"  # A file was created
    FILE_MODIFIED = "file_modified"  # A file was modified
    SCREENSHOT = "screenshot"  # Visual proof
    DIFF = "diff"  # Code diff

    # Verification evidence
    HEALTH_CHECK = "health_check"  # Service health verification
    ASSERTION = "assertion"  # Boolean assertion result
    METRIC = "metric"  # Numeric measurement

    # Human evidence
    HUMAN_APPROVAL = "human_approval"  # Human confirmed something
    HUMAN_INPUT = "human_input"  # Human provided input

    # Meta evidence
    COMPOSITE = "composite"  # Collection of other evidence


class ArtifactReference(BaseModel):
    """Reference to a stored artifact that serves as evidence."""

    path: str = Field(description="Path to the artifact file")
    artifact_type: str = Field(description="Type of artifact (log, screenshot, report, etc.)")
    size_bytes: Optional[int] = Field(default=None, description="Size of artifact")
    checksum: Optional[str] = Field(default=None, description="SHA256 checksum for integrity")
    created_at: datetime = Field(default_factory=datetime.now)

    def exists(self) -> bool:
        """Check if the artifact file exists."""
        return Path(self.path).exists()

    def verify_checksum(self) -> bool:
        """Verify artifact integrity via checksum."""
        if not self.checksum:
            return True  # No checksum to verify

        import hashlib

        try:
            with open(self.path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == self.checksum
        except FileNotFoundError:
            return False


class Evidence(BaseModel):
    """
    Evidence backing an agent's claim.

    Evidence is the foundation of trust. Without evidence, claims are assertions.
    With evidence, claims are verifiable facts.
    """

    # What is being claimed
    claim: str = Field(description="The claim this evidence supports")

    # Type and content
    evidence_type: EvidenceType = Field(description="Type of evidence")
    content: Optional[str] = Field(
        default=None, description="Direct content (for small evidence like command output)"
    )

    # Artifacts (for larger evidence)
    artifacts: list[ArtifactReference] = Field(
        default_factory=list, description="References to artifact files"
    )

    # Verification
    verifiable_command: Optional[str] = Field(
        default=None,
        description="Command that can be run to independently verify this evidence",
    )
    verification_instructions: Optional[str] = Field(
        default=None,
        description="Human-readable instructions for verification",
    )

    # Provenance
    agent_id: str = Field(description="ID of agent that produced this evidence")
    timestamp: datetime = Field(default_factory=datetime.now)
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context about how evidence was produced"
    )

    # Trust metadata
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this evidence (1.0 = certain)",
    )
    is_verified: bool = Field(
        default=False, description="Has this evidence been independently verified?"
    )
    verified_by: Optional[str] = Field(
        default=None, description="Who/what verified this evidence"
    )
    verified_at: Optional[datetime] = Field(default=None)

    def has_artifacts(self) -> bool:
        """Check if evidence has artifact references."""
        return len(self.artifacts) > 0

    def artifacts_exist(self) -> bool:
        """Verify all artifact files exist."""
        return all(artifact.exists() for artifact in self.artifacts)

    def is_verifiable(self) -> bool:
        """Check if this evidence can be independently verified."""
        return self.verifiable_command is not None or self.verification_instructions is not None

    def mark_verified(self, verified_by: str) -> None:
        """Mark this evidence as verified."""
        self.is_verified = True
        self.verified_by = verified_by
        self.verified_at = datetime.now()


class EvidenceCollection(BaseModel):
    """
    A collection of evidence supporting a larger claim or task completion.

    Used when multiple pieces of evidence together support a claim.
    """

    claim: str = Field(description="The overall claim this collection supports")
    evidence: list[Evidence] = Field(default_factory=list)
    agent_id: str = Field(description="ID of agent that assembled this collection")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Collection metadata
    is_complete: bool = Field(
        default=False, description="Has all required evidence been collected?"
    )
    missing_evidence: list[str] = Field(
        default_factory=list, description="Evidence types still needed"
    )

    def add(self, evidence: Evidence) -> None:
        """Add evidence to the collection."""
        self.evidence.append(evidence)

    def has_evidence_type(self, evidence_type: EvidenceType) -> bool:
        """Check if collection contains a specific evidence type."""
        return any(e.evidence_type == evidence_type for e in self.evidence)

    def get_by_type(self, evidence_type: EvidenceType) -> list[Evidence]:
        """Get all evidence of a specific type."""
        return [e for e in self.evidence if e.evidence_type == evidence_type]

    def all_verified(self) -> bool:
        """Check if all evidence in collection is verified."""
        return all(e.is_verified for e in self.evidence)

    def all_artifacts_exist(self) -> bool:
        """Verify all artifact files across all evidence exist."""
        return all(e.artifacts_exist() for e in self.evidence if e.has_artifacts())
