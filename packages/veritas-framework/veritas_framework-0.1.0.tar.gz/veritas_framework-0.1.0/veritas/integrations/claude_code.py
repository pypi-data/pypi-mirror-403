"""
Claude Code Integration - Trust enforcement for Claude Code agents.

This module provides hooks and wrappers that integrate Veritas trust
enforcement into Claude Code workflows.
"""

from datetime import datetime
from typing import Any, Callable, Optional

import structlog
from pydantic import BaseModel, Field

from veritas.core.behaviors import AgentAction, BehaviorViolation
from veritas.core.context import TrustContext, TrustViolationError
from veritas.core.evidence import Evidence, EvidenceType, EvidenceCollection
from veritas.layers.protocol import ProtocolEnforcer, ProtocolViolationError
from veritas.layers.gates import WorkflowGate, GateBlockedError
from veritas.layers.audit import TrustAuditor

logger = structlog.get_logger()


class ClaudeCodeHookConfig(BaseModel):
    """Configuration for Claude Code trust hooks."""

    # Enforcement settings
    enforce_verification: bool = Field(
        default=True,
        description="Require verification evidence before completion claims",
    )
    require_evidence_on_done: bool = Field(
        default=True,
        description="Block 'done' status without evidence",
    )
    audit_tool_calls: bool = Field(
        default=True,
        description="Audit tool calls for trust compliance",
    )

    # Strictness
    strict_mode: bool = Field(
        default=True,
        description="Raise exceptions on violations (vs logging)",
    )
    block_on_violation: bool = Field(
        default=True,
        description="Block actions that violate trust behaviors",
    )

    # Evidence requirements
    require_command_output: bool = Field(
        default=True,
        description="Require command output as evidence",
    )
    require_test_results: bool = Field(
        default=False,
        description="Require test results before completion",
    )

    # Audit settings
    spot_check_frequency: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Probability of spot-checking a claim",
    )


class ClaudeCodeTrustHook:
    """
    Trust enforcement hook for Claude Code.

    Integrates with Claude Code's hook system to enforce trust behaviors
    at critical points in the workflow.
    """

    def __init__(
        self,
        config: ClaudeCodeHookConfig | None = None,
        agent_id: str = "claude-code",
    ):
        self.config = config or ClaudeCodeHookConfig()
        self.context = TrustContext(
            agent_id=agent_id,
            strict_mode=self.config.strict_mode,
        )
        self.enforcer = ProtocolEnforcer(
            context=self.context,
            strict=self.config.strict_mode,
        )
        self.auditor = TrustAuditor(self.context)

        # Track current task for evidence collection
        self.current_task_id: Optional[str] = None
        self.current_evidence: EvidenceCollection = EvidenceCollection(
            claim="Current task evidence",
            agent_id=agent_id,
        )

    def on_task_start(self, task_id: str, task_description: str) -> None:
        """Called when a new task is started."""
        self.current_task_id = task_id
        self.current_evidence = EvidenceCollection(
            claim=f"Evidence for task: {task_description}",
            agent_id=self.context.agent_id,
        )

        logger.info(
            "task_started",
            task_id=task_id,
            description=task_description,
        )

    def on_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
    ) -> Evidence | None:
        """
        Called after a tool is executed.

        Captures tool output as evidence when appropriate.
        """
        # Skip non-evidentiary tools
        if tool_name in ["Read", "Glob", "Grep"]:
            return None

        # Capture Bash output as command evidence
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            output = str(tool_output)[:2000]  # Truncate

            evidence = Evidence(
                claim=f"Command executed: {command[:100]}",
                evidence_type=EvidenceType.COMMAND_OUTPUT,
                content=output,
                verifiable_command=command,
                agent_id=self.context.agent_id,
                context={"tool": tool_name, "task_id": self.current_task_id},
            )

            self.current_evidence.add(evidence)
            self.context.add_evidence(
                claim=evidence.claim,
                evidence_type=evidence.evidence_type.value,
                content=evidence.content,
                verifiable_command=evidence.verifiable_command,
            )

            logger.debug(
                "evidence_captured",
                tool=tool_name,
                command=command[:50],
            )

            return evidence

        return None

    def on_completion_claim(
        self,
        claim: str,
        evidence_ids: list[str] | None = None,
    ) -> bool:
        """
        Called when agent claims task completion.

        Returns True if claim is allowed, raises exception if blocked.
        """
        evidence_ids = evidence_ids or []

        # Check protocol rules
        action_data = {
            "is_completion_claim": True,
            "claimed_outcome": claim,
            "evidence_ids": evidence_ids or [
                str(e.timestamp.timestamp())
                for e in self.current_evidence.evidence
            ],
            "has_verification_evidence": len(self.current_evidence.evidence) > 0,
        }

        try:
            self.enforcer.check_action(action_data)
        except ProtocolViolationError as e:
            if self.config.block_on_violation:
                raise
            logger.warning(
                "completion_claim_violation",
                claim=claim,
                violations=[v.message for v in e.violations],
            )

        # Record the action
        self.context.record_action(
            action_type="claim",
            description=f"Completion claim: {claim}",
            is_completion_claim=True,
            claimed_outcome=claim,
            has_verification_evidence=len(evidence_ids) > 0,
            evidence_ids=evidence_ids,
        )

        # Spot check if configured
        import random
        if random.random() < self.config.spot_check_frequency:
            if self.current_evidence.evidence:
                # Audit the most recent evidence
                latest = self.current_evidence.evidence[-1]
                # Note: This would be async in practice
                logger.info(
                    "spot_check_triggered",
                    claim=claim,
                    evidence_claim=latest.claim,
                )

        return True

    def on_task_status_change(
        self,
        task_id: str,
        from_status: str,
        to_status: str,
    ) -> bool:
        """
        Called when task status is about to change.

        Enforces workflow gates for status transitions.
        """
        # Check if this transition requires evidence
        if to_status in ["review", "done"]:
            if self.config.require_evidence_on_done:
                if not self.current_evidence.evidence:
                    if self.config.block_on_violation:
                        raise GateBlockedError(
                            f"Cannot transition to '{to_status}' without evidence"
                        )
                    logger.warning(
                        "status_change_without_evidence",
                        task_id=task_id,
                        to_status=to_status,
                    )

        logger.info(
            "task_status_change",
            task_id=task_id,
            from_status=from_status,
            to_status=to_status,
            evidence_count=len(self.current_evidence.evidence),
        )

        return True

    def on_error(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> None:
        """
        Called when an error occurs.

        Ensures errors are logged (loud failure principle).
        """
        # Record as action with failure
        self.context.record_action(
            action_type="error",
            description=f"Error: {str(error)}",
            is_failure=True,
            failure_reason=str(error),
            is_silent_failure=False,  # We're logging it now
        )

        logger.error(
            "agent_error",
            error=str(error),
            context=context,
        )

    def get_trust_report(self) -> dict[str, Any]:
        """Get a trust report for the current session."""
        return {
            "agent_id": self.context.agent_id,
            "session_summary": self.context.summary(),
            "metrics": self.context.metrics.model_dump(),
            "violations": [v.model_dump() for v in self.context.violations],
            "evidence_count": len(self.current_evidence.evidence),
            "audit_trail": self.context.get_audit_trail(),
        }


class VeritasClaudeAgent:
    """
    A Claude Code agent wrapper with built-in Veritas trust enforcement.

    Wraps agent execution with automatic trust tracking, evidence collection,
    and behavior enforcement.
    """

    def __init__(
        self,
        agent_id: str,
        config: ClaudeCodeHookConfig | None = None,
    ):
        self.agent_id = agent_id
        self.hook = ClaudeCodeTrustHook(config=config, agent_id=agent_id)

    async def execute_task(
        self,
        task_id: str,
        task_description: str,
        executor: Callable[..., Any],
        **kwargs: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """
        Execute a task with trust enforcement.

        Returns (result, trust_report) tuple.
        """
        self.hook.on_task_start(task_id, task_description)

        try:
            result = await executor(**kwargs)

            # Attempt completion claim
            self.hook.on_completion_claim(
                claim=f"Task completed: {task_description}",
            )

            return result, self.hook.get_trust_report()

        except (ProtocolViolationError, TrustViolationError) as e:
            # Trust violation - log and re-raise
            self.hook.on_error(e, {"task_id": task_id})
            raise

        except Exception as e:
            # General error - ensure loud failure
            self.hook.on_error(e, {"task_id": task_id})
            raise

    def add_evidence(
        self,
        claim: str,
        evidence_type: EvidenceType,
        content: str,
        verifiable_command: Optional[str] = None,
    ) -> Evidence:
        """Manually add evidence to the current task."""
        evidence = Evidence(
            claim=claim,
            evidence_type=evidence_type,
            content=content,
            verifiable_command=verifiable_command,
            agent_id=self.agent_id,
        )

        self.hook.current_evidence.add(evidence)
        return evidence

    @property
    def trust_context(self) -> TrustContext:
        """Access the underlying trust context."""
        return self.hook.context
