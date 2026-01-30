"""
Verification - Protocols for verifying claims and evidence.

Verification is the act of confirming that a claim is true.
Without verification, claims are just assertions.
"""

from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, Field

from veritas.core.evidence import Evidence, EvidenceType

T = TypeVar("T")


class VerificationStatus(str, Enum):
    """Status of a verification attempt."""

    PENDING = "pending"  # Not yet verified
    PASSED = "passed"  # Verification succeeded
    FAILED = "failed"  # Verification failed
    SKIPPED = "skipped"  # Verification was skipped (with reason)
    ERROR = "error"  # Error during verification


class VerificationMethod(str, Enum):
    """How verification was performed."""

    COMMAND_EXECUTION = "command_execution"  # Ran a command
    API_CALL = "api_call"  # Made an API call
    FILE_CHECK = "file_check"  # Checked file existence/content
    ASSERTION = "assertion"  # Programmatic assertion
    HUMAN_REVIEW = "human_review"  # Human verified
    AUTOMATED_TEST = "automated_test"  # Test suite ran


class VerificationResult(BaseModel):
    """Result of a verification attempt."""

    verification_id: str = Field(
        default_factory=lambda: f"ver_{datetime.now().timestamp()}"
    )
    status: VerificationStatus
    method: VerificationMethod
    timestamp: datetime = Field(default_factory=datetime.now)

    # What was verified
    claim: str
    evidence_id: Optional[str] = None

    # Verification details
    command_run: Optional[str] = None
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None

    # Result details
    passed: bool = False
    failure_reason: Optional[str] = None
    error_message: Optional[str] = None

    # Verifier info
    verified_by: str  # Agent or human who verified
    verification_context: dict[str, Any] = Field(default_factory=dict)


class Verification(BaseModel):
    """
    A verification specification - what needs to be verified and how.

    Used to define verification requirements before execution.
    """

    claim: str = Field(description="The claim to verify")
    method: VerificationMethod = Field(description="How to verify")

    # Verification command (for command-based verification)
    command: Optional[str] = Field(
        default=None, description="Command to run for verification"
    )
    expected_output: Optional[str] = Field(
        default=None, description="Expected output (substring match)"
    )
    expected_exit_code: int = Field(default=0, description="Expected exit code")

    # API verification
    api_endpoint: Optional[str] = None
    expected_status_code: Optional[int] = None
    expected_response_contains: Optional[str] = None

    # File verification
    file_path: Optional[str] = None
    file_should_exist: bool = True
    file_should_contain: Optional[str] = None

    # Custom assertion
    assertion_func: Optional[Callable[..., bool]] = None

    async def execute(self, context: dict[str, Any] | None = None) -> VerificationResult:
        """Execute this verification and return result."""
        context = context or {}

        try:
            if self.method == VerificationMethod.COMMAND_EXECUTION:
                return await self._verify_command(context)
            elif self.method == VerificationMethod.FILE_CHECK:
                return await self._verify_file(context)
            elif self.method == VerificationMethod.ASSERTION:
                return await self._verify_assertion(context)
            else:
                return VerificationResult(
                    status=VerificationStatus.ERROR,
                    method=self.method,
                    claim=self.claim,
                    passed=False,
                    error_message=f"Verification method {self.method} not implemented",
                    verified_by="veritas",
                )
        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                method=self.method,
                claim=self.claim,
                passed=False,
                error_message=str(e),
                verified_by="veritas",
            )

    async def _verify_command(self, context: dict[str, Any]) -> VerificationResult:
        """Verify by running a command."""
        import asyncio

        if not self.command:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                method=self.method,
                claim=self.claim,
                passed=False,
                error_message="No command specified for command verification",
                verified_by="veritas",
            )

        proc = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() + stderr.decode()

        # Check exit code
        exit_code_ok = proc.returncode == self.expected_exit_code

        # Check output contains expected string
        output_ok = True
        if self.expected_output:
            output_ok = self.expected_output in output

        passed = exit_code_ok and output_ok

        return VerificationResult(
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            method=self.method,
            claim=self.claim,
            command_run=self.command,
            actual_output=output[:2000],  # Truncate long outputs
            expected_output=self.expected_output,
            passed=passed,
            failure_reason=None if passed else (
                f"Exit code: {proc.returncode} (expected {self.expected_exit_code})"
                if not exit_code_ok
                else f"Output did not contain: {self.expected_output}"
            ),
            verified_by="veritas",
            verification_context=context,
        )

    async def _verify_file(self, context: dict[str, Any]) -> VerificationResult:
        """Verify by checking a file."""
        from pathlib import Path

        if not self.file_path:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                method=self.method,
                claim=self.claim,
                passed=False,
                error_message="No file path specified for file verification",
                verified_by="veritas",
            )

        path = Path(self.file_path)
        exists = path.exists()

        if self.file_should_exist and not exists:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                method=self.method,
                claim=self.claim,
                passed=False,
                failure_reason=f"File does not exist: {self.file_path}",
                verified_by="veritas",
                verification_context=context,
            )

        if not self.file_should_exist and exists:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                method=self.method,
                claim=self.claim,
                passed=False,
                failure_reason=f"File should not exist but does: {self.file_path}",
                verified_by="veritas",
                verification_context=context,
            )

        # Check content if required
        if self.file_should_contain and exists:
            content = path.read_text()
            if self.file_should_contain not in content:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    method=self.method,
                    claim=self.claim,
                    passed=False,
                    failure_reason=f"File does not contain: {self.file_should_contain}",
                    verified_by="veritas",
                    verification_context=context,
                )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            method=self.method,
            claim=self.claim,
            passed=True,
            verified_by="veritas",
            verification_context=context,
        )

    async def _verify_assertion(self, context: dict[str, Any]) -> VerificationResult:
        """Verify using a custom assertion function."""
        if not self.assertion_func:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                method=self.method,
                claim=self.claim,
                passed=False,
                error_message="No assertion function specified",
                verified_by="veritas",
            )

        try:
            result = self.assertion_func(**context)
            return VerificationResult(
                status=VerificationStatus.PASSED if result else VerificationStatus.FAILED,
                method=self.method,
                claim=self.claim,
                passed=result,
                failure_reason=None if result else "Assertion returned False",
                verified_by="veritas",
                verification_context=context,
            )
        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.ERROR,
                method=self.method,
                claim=self.claim,
                passed=False,
                error_message=str(e),
                verified_by="veritas",
            )


class VerificationContext(BaseModel):
    """Context for tracking verification state across an operation."""

    context_id: str = Field(
        default_factory=lambda: f"vctx_{datetime.now().timestamp()}"
    )
    agent_id: str
    operation: str  # What operation is being verified
    started_at: datetime = Field(default_factory=datetime.now)

    # Verification tracking
    verifications_required: list[Verification] = Field(default_factory=list)
    verifications_completed: list[VerificationResult] = Field(default_factory=list)

    # Evidence collected
    evidence_collected: list[Evidence] = Field(default_factory=list)

    def add_requirement(self, verification: Verification) -> None:
        """Add a verification requirement."""
        self.verifications_required.append(verification)

    def record_result(self, result: VerificationResult) -> None:
        """Record a verification result."""
        self.verifications_completed.append(result)

    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to the context."""
        self.evidence_collected.append(evidence)

    def all_passed(self) -> bool:
        """Check if all verifications passed."""
        if len(self.verifications_completed) < len(self.verifications_required):
            return False
        return all(v.passed for v in self.verifications_completed)

    def pending_verifications(self) -> list[Verification]:
        """Get verifications that haven't been completed."""
        completed_claims = {v.claim for v in self.verifications_completed}
        return [v for v in self.verifications_required if v.claim not in completed_claims]


class VerificationRequired:
    """
    Decorator that enforces verification before a function can claim completion.

    Usage:
        @VerificationRequired(
            claim="Tests pass",
            method=VerificationMethod.COMMAND_EXECUTION,
            command="pytest",
            expected_exit_code=0
        )
        async def run_tests():
            ...
    """

    def __init__(
        self,
        claim: str,
        method: VerificationMethod,
        **kwargs: Any,
    ):
        self.verification = Verification(claim=claim, method=method, **kwargs)

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> tuple[T, VerificationResult]:
            # Execute the function
            result = await func(*args, **kwargs)

            # Execute verification
            verification_result = await self.verification.execute(
                context={"function_result": result, "args": args, "kwargs": kwargs}
            )

            if not verification_result.passed:
                raise VerificationFailedError(
                    f"Verification failed for claim: {self.verification.claim}. "
                    f"Reason: {verification_result.failure_reason}"
                )

            return result, verification_result

        return wrapper


class VerificationFailedError(Exception):
    """Raised when verification fails."""

    pass
