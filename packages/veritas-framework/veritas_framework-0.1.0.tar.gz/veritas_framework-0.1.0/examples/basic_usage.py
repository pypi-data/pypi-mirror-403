"""
Basic Usage Example - Veritas Framework

This example shows how to use Veritas to enforce trust in an agent workflow.
"""

import asyncio
from veritas import TrustContext, Evidence, EvidenceType
from veritas.layers import ProtocolEnforcer, WorkflowGate, GateRequirement
from veritas.layers.gates import TaskStatus


async def main():
    # 1. Create a trust context for your agent
    ctx = TrustContext(
        agent_id="example-agent",
        strict_mode=False,  # Set to True in production
    )

    print("=== Veritas Trust Framework Example ===\n")

    # 2. Record actions with verification
    print("Recording verified action...")
    action = ctx.record_action(
        action_type="execute",
        description="Running test suite",
        has_verification_evidence=False,
    )
    print(f"  Action recorded: {action.action_id}")

    # 3. Add evidence after execution
    print("\nAdding evidence...")
    evidence = ctx.add_evidence(
        claim="Tests executed successfully",
        evidence_type="test_results",
        content="10 passed, 0 failed, 0 skipped",
        verifiable_command="pytest tests/ -v",
    )
    print(f"  Evidence added: {evidence.claim}")

    # 4. Use protocol enforcer to validate completion claims
    print("\nValidating completion claim...")
    enforcer = ProtocolEnforcer(ctx, strict=False)

    completion_action = {
        "is_completion_claim": True,
        "claimed_outcome": "All tests pass",
        "evidence_ids": [str(evidence.timestamp.timestamp())],
        "has_verification_evidence": True,
    }

    passed, violations = enforcer.check_action(completion_action)
    print(f"  Passed: {passed}")
    if violations:
        print(f"  Violations: {[v.message for v in violations]}")

    # 5. Set up workflow gates
    print("\nSetting up workflow gate...")
    from veritas.core.evidence import EvidenceCollection

    gate = WorkflowGate(
        name="doing_to_review",
        from_status=TaskStatus.DOING,
        to_status=TaskStatus.REVIEW,
        requirements=[
            GateRequirement(
                name="test_results",
                evidence_type=EvidenceType.TEST_RESULTS,
                required=True,
            ),
        ],
    )

    # Create evidence collection
    evidence_collection = EvidenceCollection(
        claim="Task evidence",
        agent_id="example-agent",
    )
    evidence_collection.add(
        Evidence(
            claim="Tests pass",
            evidence_type=EvidenceType.TEST_RESULTS,
            content="10 passed, 0 failed",
            agent_id="example-agent",
        )
    )

    # Check gate
    gate_result = gate.check(evidence_collection)
    print(f"  Gate passed: {gate_result.passed}")
    print(f"  Requirements met: {gate_result.requirements_met}/{gate_result.requirements_total}")

    # 6. Get trust summary
    print("\n=== Trust Summary ===")
    print(ctx.summary())

    # 7. Get audit trail
    print("\n=== Audit Trail ===")
    trail = ctx.get_audit_trail()
    print(f"  Actions: {len(trail['actions'])}")
    print(f"  Evidence: {len(trail['evidence']['evidence'])}")
    print(f"  Violations: {len(trail['violations'])}")


if __name__ == "__main__":
    asyncio.run(main())
