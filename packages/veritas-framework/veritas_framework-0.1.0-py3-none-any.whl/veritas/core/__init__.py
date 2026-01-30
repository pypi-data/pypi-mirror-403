"""
Veritas Core - Fundamental types and behaviors for trust-based agents.
"""

from veritas.core.behaviors import (
    TrustBehavior,
    BehaviorViolation,
    VerificationBeforeClaim,
    LoudFailure,
    HonestUncertainty,
    PaperTrail,
    DiligentExecution,
)
from veritas.core.evidence import (
    Evidence,
    EvidenceType,
    EvidenceCollection,
    ArtifactReference,
)
from veritas.core.verification import (
    Verification,
    VerificationResult,
    VerificationRequired,
    VerificationContext,
)
from veritas.core.context import TrustContext

__all__ = [
    "TrustBehavior",
    "BehaviorViolation",
    "VerificationBeforeClaim",
    "LoudFailure",
    "HonestUncertainty",
    "PaperTrail",
    "DiligentExecution",
    "Evidence",
    "EvidenceType",
    "EvidenceCollection",
    "ArtifactReference",
    "Verification",
    "VerificationResult",
    "VerificationRequired",
    "VerificationContext",
    "TrustContext",
]
