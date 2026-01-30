# Layer 2: Workflow Gates

Layer 2 focuses on **process integrity**. While Layer 1 ensures individual actions are verified, Layer 2 ensures that the overall workflow cannot progress until specific requirements are met.

## Key Principle: No Proof, No Progress

Workflow Gates are checkpoints between task statuses (e.g., `DOING` → `REVIEW`). If the required evidence is missing or invalid, the transition is physically blocked.

## WorkflowGate Class

A `WorkflowGate` defines the requirements for moving from one state to another.

### Configuration

```python
from veritas.layers.gates import WorkflowGate, GateRequirement
from veritas.core.evidence import EvidenceType

# Create a gate for the Dev-to-Review transition
gate = WorkflowGate(
    name="dev_to_review",
    from_status="doing",
    to_status="review",
    requirements=[
        GateRequirement(
            name="unit_tests",
            evidence_type=EvidenceType.TEST_RESULTS,
            required=True
        ),
        GateRequirement(
            name="static_analysis",
            evidence_type=EvidenceType.COMMAND_OUTPUT,
            required=True
        )
    ]
)
```

## Gate Requirements

Each requirement can specify:
- **Evidence Type**: What kind of proof is needed.
- **Must Be Verified**: Whether the evidence needs independent verification.
- **Max Age**: How "fresh" the evidence must be.
- **Custom Validator**: A function to inspect the evidence content.

## Implementation Flow

1. **Define the Gate**: Create the `WorkflowGate` instance with requirements.
2. **Collect Evidence**: As the agent works, it adds evidence to its `TrustContext`.
3. **Attempt Transition**: Call `gate.transition()` with the collected evidence.
4. **Enforce**: If requirements aren't met, a `GateBlockedError` is raised.

## Benefits

- **Preventing Corner Cutting**: Agents cannot skip "tedious" validation steps.
- **Reliable Transitions**: Humans or other agents can trust that a "Ready for Review" task actually meets the bar.
- **Structured YAML**: Gates can be defined in YAML files for easy configuration and audit.
