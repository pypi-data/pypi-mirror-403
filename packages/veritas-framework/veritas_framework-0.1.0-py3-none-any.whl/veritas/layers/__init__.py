"""
Veritas Layers - The three trust enforcement layers.

Layer 1: Protocol-Embedded - Makes lying structurally difficult
Layer 2: Workflow Gates - Requires proof to proceed
Layer 3: Audit - Catches what slips through
"""

from veritas.layers.protocol import (
    ProtocolEnforcer,
    ProtocolRule,
    CompletionClaimRule,
    FailureHandlingRule,
    UncertaintyRule,
)
from veritas.layers.gates import (
    WorkflowGate,
    GateRequirement,
    GateResult,
    TaskTransition,
)
from veritas.layers.audit import (
    TrustAuditor,
    AuditResult,
    AuditFinding,
    AuditSeverity,
)

__all__ = [
    # Layer 1: Protocol
    "ProtocolEnforcer",
    "ProtocolRule",
    "CompletionClaimRule",
    "FailureHandlingRule",
    "UncertaintyRule",
    # Layer 2: Gates
    "WorkflowGate",
    "GateRequirement",
    "GateResult",
    "TaskTransition",
    # Layer 3: Audit
    "TrustAuditor",
    "AuditResult",
    "AuditFinding",
    "AuditSeverity",
]
