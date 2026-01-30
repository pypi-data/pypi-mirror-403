# Core Concepts

This document explains the fundamental concepts behind the Veritas Framework.

## Philosophy: Trust as Character

Traditional agent frameworks treat trust as a permission system:
```
if trust_score >= threshold:
    grant_autonomy()
```

Veritas treats trust as **character** - consistent behaviors that make an agent reliable:

```
agent_demonstrates_integrity() → humans_rely_on_agent() →
errors_are_debuggable() → trust_deepens()
```

**Key insight**: Errors are acceptable. Lies are not.

## The Five Trust Behaviors

Every trustworthy agent embodies these behaviors:

### 1. Verification Before Claim

**Principle**: Never say "done" without proof.

```python
# BAD - Claiming without verification
def complete_task():
    run_tests()
    return "All tests pass"  # How do we know?

# GOOD - Verification before claim
def complete_task():
    result = run_tests()
    assert result.exit_code == 0, "Tests failed"
    return Evidence(
        claim="All tests pass",
        proof=result.output,
        verifiable_command="pytest"
    )
```

### 2. Loud Failure

**Principle**: Failures must be surfaced, never hidden.

```python
# BAD - Silent fallback
def get_data():
    try:
        return fetch_from_primary()
    except:
        return fetch_from_fallback()  # Silent switch!

# GOOD - Announced fallback
def get_data():
    try:
        return fetch_from_primary()
    except Exception as e:
        logger.warning(f"Primary failed: {e}, using fallback")
        return fetch_from_fallback()
```

### 3. Honest Uncertainty

**Principle**: "I don't know" is valid; fabrication is not.

```python
# BAD - Fabricating to fill gaps
def answer_question(q):
    if not sure:
        return "The answer is probably X"  # Hallucination

# GOOD - Acknowledging uncertainty
def answer_question(q):
    if not sure:
        return "I don't know. Should I investigate?"
```

### 4. Paper Trail

**Principle**: Every action must be logged and traceable.

```python
# BAD - No audit trail
def modify_database():
    db.update(data)

# GOOD - Full audit trail
def modify_database():
    logger.info(f"Modifying database: {data}")
    result = db.update(data)
    logger.info(f"Result: {result}")
    return AuditedAction(action="db_update", data=data, result=result)
```

### 5. Diligent Execution

**Principle**: Complete all steps, even tedious ones.

```python
# BAD - Skipping "unimportant" steps
def deploy():
    build()
    # skip tests, they're slow
    push_to_production()

# GOOD - Complete execution
def deploy():
    build()
    run_tests()  # Even if slow
    run_security_scan()  # Even if tedious
    push_to_production()
```

## Evidence

Evidence is the atomic unit of trust. Every claim must be backed by evidence.

### Evidence Types

| Type | Use Case |
|------|----------|
| `COMMAND_OUTPUT` | Shell command results |
| `TEST_RESULTS` | Test execution output |
| `API_RESPONSE` | API call responses |
| `SCREENSHOT` | Visual proof |
| `LOG_ENTRY` | Log file entries |
| `HUMAN_APPROVAL` | Human confirmation |

### Evidence Properties

```python
evidence = Evidence(
    claim="API returns 200",           # What is being claimed
    evidence_type=EvidenceType.API_RESPONSE,
    content="{'status': 'ok'}",        # The proof
    verifiable_command="curl /health", # How to verify
    agent_id="victor-qa",              # Who produced it
    timestamp=datetime.now(),          # When
    confidence=1.0,                    # Agent's confidence
)
```

### Evidence Collection

Multiple pieces of evidence can be collected to support a larger claim:

```python
collection = EvidenceCollection(
    claim="Feature is production-ready",
    evidence=[
        Evidence(claim="Tests pass", ...),
        Evidence(claim="Security scan clean", ...),
        Evidence(claim="Performance acceptable", ...),
    ]
)
```

## Trust Context

The TrustContext is the central tracking object for an agent session.

```python
ctx = TrustContext(agent_id="helena-qa")

# Records actions
ctx.record_action(
    action_type="execute",
    description="Running tests"
)

# Collects evidence
ctx.add_evidence(
    claim="Tests pass",
    evidence_type="test_results",
    content="5 passed, 0 failed"
)

# Tracks violations
# (automatically when behaviors are broken)

# Provides audit trail
trail = ctx.get_audit_trail()
```

## The Three Layers

Veritas enforces trust through three defense layers:

### Layer 1: Protocol-Embedded

Makes lying structurally difficult by requiring verification in the workflow.

### Layer 2: Workflow Gates

Makes progress impossible without proof. Tasks cannot transition without evidence.

### Layer 3: Audit

Catches what slips through by reviewing completed work.

See the layer-specific documentation for details:
- [Layer 1: Protocol-Embedded](layer-1-protocol.md)
- [Layer 2: Workflow Gates](layer-2-gates.md)
- [Layer 3: Trust Audit](layer-3-audit.md)
