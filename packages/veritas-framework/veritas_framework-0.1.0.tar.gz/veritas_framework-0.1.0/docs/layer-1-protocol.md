# Layer 1: Protocol-Embedded Enforcement

Layer 1 is the first line of defense in the Veritas Framework. It makes **lying structurally difficult** by embedding verification requirements directly into the agent's code execution path.

## Key Concept: Verification Before Claim

The core principle of Layer 1 is that an agent should never claim a task is "done" without evidence. We enforce this using Python decorators and protocol rules.

## Verification Decorators

### `@requires_verification`

This decorator ensures that a function cannot return a success status unless a verification step has been executed.

```python
from veritas.layers.protocol import requires_verification

@requires_verification(evidence_type="test_results")
def process_data(data):
    # Process logic...
    return "Success" # This will FAIL if no evidence was added to context
```

## Protocol Enforcer

The `ProtocolEnforcer` class checks actions against defined rules before allowing them to proceed.

### Validation Rules

- **CompletionClaimRule**: Ensures that any claim of completion is backed by at least one piece of verified evidence.
- **FailureHandlingRule**: Prevents silent fallbacks by requiring failures to be documented as "Loud Failures".
- **UncertaintyRule**: Flags "hallucination-prone" responses that don't acknowledge uncertainty.

## Example Usage

```python
from veritas.layers.protocol import ProtocolEnforcer
from veritas.core.context import TrustContext

ctx = TrustContext(agent_id="my-agent")
enforcer = ProtocolEnforcer(context=ctx)

# Attempting an action
action_data = {"is_completion_claim": True, "evidence_ids": []}
enforcer.check_action(action_data) # Raises ProtocolViolationError (missing evidence)
```

## Benefits

1. **Explicit Proof**: Forces the agent to think about what constitutes proof.
2. **Standardization**: Ensures all agents in a system follow the same "honesty protocol".
3. **Auditability**: Creates a record of verification attempts even if they fail.
