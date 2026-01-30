"""
Claude Code Integration Example

Shows how to use Veritas with Claude Code agents.
"""

import asyncio
from veritas.integrations.claude_code import (
    ClaudeCodeTrustHook,
    ClaudeCodeHookConfig,
    VeritasClaudeAgent,
)
from veritas.core.evidence import EvidenceType


async def example_with_hook():
    """Example using the trust hook directly."""
    print("=== Claude Code Trust Hook Example ===\n")

    # Configure the hook
    config = ClaudeCodeHookConfig(
        enforce_verification=True,
        require_evidence_on_done=True,
        strict_mode=False,  # Don't raise exceptions
        spot_check_frequency=0.5,  # Check 50% of claims
    )

    # Create the hook
    hook = ClaudeCodeTrustHook(
        config=config,
        agent_id="helena-qa",
    )

    # Simulate task workflow
    print("1. Starting task...")
    hook.on_task_start("task-123", "Run frontend tests")

    # Simulate tool calls
    print("2. Simulating Bash tool call...")
    evidence = hook.on_tool_call(
        tool_name="Bash",
        tool_input={"command": "npm test"},
        tool_output="PASS src/App.test.tsx\n  ✓ renders learn react link (39 ms)",
    )
    if evidence:
        print(f"   Evidence captured: {evidence.claim[:50]}...")

    # Try completion claim
    print("3. Attempting completion claim...")
    try:
        hook.on_completion_claim("All frontend tests pass")
        print("   Completion claim accepted")
    except Exception as e:
        print(f"   Completion claim rejected: {e}")

    # Get trust report
    print("\n4. Trust Report:")
    report = hook.get_trust_report()
    print(f"   Agent: {report['agent_id']}")
    print(f"   Evidence count: {report['evidence_count']}")
    print(f"   Violations: {len(report['violations'])}")


async def example_with_agent_wrapper():
    """Example using the agent wrapper."""
    print("\n=== Veritas Claude Agent Wrapper Example ===\n")

    # Create wrapped agent
    agent = VeritasClaudeAgent(
        agent_id="victor-qa",
        config=ClaudeCodeHookConfig(
            strict_mode=False,
            require_test_results=True,
        ),
    )

    # Define a task executor
    async def run_api_tests():
        """Simulated API test execution."""
        # In reality, this would run actual tests
        return {
            "passed": 15,
            "failed": 0,
            "duration": "2.5s",
        }

    # Execute with trust enforcement
    print("Executing task with trust enforcement...")

    # Add evidence before claiming completion
    agent.add_evidence(
        claim="API tests executed",
        evidence_type=EvidenceType.TEST_RESULTS,
        content="15 passed, 0 failed",
        verifiable_command="pytest tests/api/ -v",
    )

    result, trust_report = await agent.execute_task(
        task_id="api-test-001",
        task_description="Run API integration tests",
        executor=run_api_tests,
    )

    print(f"\nTask result: {result}")
    print(f"Trust score: {trust_report['metrics']['actions_total']} actions tracked")


async def main():
    await example_with_hook()
    await example_with_agent_wrapper()


if __name__ == "__main__":
    asyncio.run(main())
