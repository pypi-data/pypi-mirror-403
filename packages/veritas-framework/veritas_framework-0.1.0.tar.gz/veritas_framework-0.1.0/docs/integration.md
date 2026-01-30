# Integration Guide: Claude Code

Veritas provides first-class support for **Claude Code**, allowing you to enforce trust behaviors and capture evidence automatically during agent sessions.

## Quick Setup

The easiest way to integrate Veritas is using the `ClaudeCodeTrustHook`.

```python
from veritas.integrations.claude_code import ClaudeCodeTrustHook

# Initialize the hook
hook = ClaudeCodeTrustHook(
    enforce_verification=True,
    require_evidence_on_done=True,
    strict_mode=True
)

# Use in your execution loop
def my_executor(command):
    # Wrap your tool execution
    result = run_bash(command)
    hook.on_tool_call("Bash", {"command": command}, result)
    return result
```

## How It Works

### 1. Automatic Evidence Capture
The hook automatically recognizes certain tool calls (like `Bash`) and converts their outputs into Veritas `Evidence` objects.

### 2. Completion Claims
When an agent claims it has finished a task, the hook interceptor validates that required evidence (like test results or command outputs) has been recorded. If not, it blocks the completion claim.

### 3. Status Transitions
The hook monitors task status changes (e.g., `doing` → `review`). It ensures that workflow gates defined in your project are satisfied before allowing the transition.

## Manual Evidence Addition

You can also manually add evidence if the automatic capture misses something:

```python
hook.on_completion_claim(
    claim="Feature implementation is complete",
    evidence_ids=["ev_123", "ev_456"]
)
```

## Trust Reports

At the end of a session, you can generate a comprehensive trust report:

```python
report = hook.get_trust_report()
print(f"Agent ID: {report['agent_id']}")
print(f"Trust Metrics: {report['metrics']}")
```

## Advanced Configuration

Use `ClaudeCodeHookConfig` to fine-tune the strictness:

- `strict_mode`: Raise exceptions (True) or just log warnings (False).
- `spot_check_frequency`: Probability (0.0 to 1.0) that a claim will be audited.
- `block_on_violation`: Prevent actions that break trust behaviors.
