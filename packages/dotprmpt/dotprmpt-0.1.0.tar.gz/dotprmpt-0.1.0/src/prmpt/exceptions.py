"""
prmpt exceptions.

All exceptions raised by the prmpt library.
"""

from typing import List, Optional


class PrmptError(Exception):
    """Base exception for all prmpt errors."""
    pass


class ParseError(PrmptError):
    """Failed to parse .prmpt document (invalid YAML/JSON)."""

    def __init__(self, message: str, source: Optional[str] = None):
        self.source = source
        super().__init__(message)


class ValidationError(PrmptError):
    """Contract structure is invalid (missing sections, bad types, etc.)."""

    def __init__(self, errors: List[str], source: Optional[str] = None):
        self.errors = errors
        self.source = source
        message = f"Invalid .prmpt contract: {'; '.join(errors)}"
        super().__init__(message)


class ContractViolation(PrmptError):
    """Runtime violation of contract constraints."""

    def __init__(
        self,
        violation_type: str,
        message: str,
        violations: Optional[List[str]] = None,
        failure_mode: Optional[str] = None
    ):
        self.violation_type = violation_type
        self.violations = violations or []
        self.failure_mode = failure_mode
        super().__init__(f"{violation_type}: {message}")


class InputViolation(ContractViolation):
    """Input validation failed."""

    def __init__(self, violations: List[str]):
        super().__init__(
            violation_type="input_violation",
            message="Input validation failed",
            violations=violations,
            failure_mode="invalid_input"
        )


class OutputViolation(ContractViolation):
    """Output validation failed."""

    def __init__(self, violations: List[str], output: Optional[str] = None):
        self.output = output
        super().__init__(
            violation_type="output_violation",
            message="Output validation failed",
            violations=violations,
            failure_mode="invalid_output"
        )


class HandoffRequired(ContractViolation):
    """Handoff to human or another agent is required."""

    def __init__(self, reason: str, context: Optional[dict] = None):
        self.reason = reason
        self.context = context or {}
        super().__init__(
            violation_type="handoff_required",
            message=reason,
            failure_mode="out_of_scope"
        )


class ActionForbidden(ContractViolation):
    """Attempted action is forbidden by contract."""

    def __init__(self, action: str):
        self.action = action
        super().__init__(
            violation_type="forbidden_action",
            message=f"Action '{action}' is forbidden",
            violations=[f"Forbidden action: {action}"],
            failure_mode="forbidden_action"
        )
