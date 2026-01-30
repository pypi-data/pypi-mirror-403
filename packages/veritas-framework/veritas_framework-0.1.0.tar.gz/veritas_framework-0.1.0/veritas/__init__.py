"""
Veritas Framework - Trust-Based Agent Architecture for Reliable AI Systems

Trust is character, not permission. Veritas enforces trustworthy agent behavior
through three defense layers:

1. Protocol-Embedded: Makes lying structurally difficult
2. Workflow Gates: Requires proof to proceed
3. Audit: Catches what slips through

Usage:
    from veritas import TrustContext, Evidence, TrustBehavior
    from veritas.layers import ProtocolEnforcer, WorkflowGate, TrustAuditor
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
from veritas.core.mixins import AgentTrustMixin

__version__ = "0.1.0"

__all__ = [
    # Core
    "TrustContext",
    "AgentTrustMixin",
    # Behaviors
    "TrustBehavior",
    "BehaviorViolation",
    "VerificationBeforeClaim",
    "LoudFailure",
    "HonestUncertainty",
    "PaperTrail",
    "DiligentExecution",
    # Evidence
    "Evidence",
    "EvidenceType",
    "EvidenceCollection",
    "ArtifactReference",
    # Verification
    "Verification",
    "VerificationResult",
    "VerificationRequired",
    "VerificationContext",
]
