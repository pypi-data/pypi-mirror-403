"""
.prmpt Contract class.

The main interface for working with .prmpt contracts.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml

from .validator import parse_file, parse_string, validate_structure
from .resolver import resolve
from .canonical import canonical_dumps
from .exceptions import (
    ValidationError,
    InputViolation,
    OutputViolation,
    HandoffRequired,
    ActionForbidden,
)


class Contract:
    """
    A .prmpt contract defining LLM interaction constraints.

    The Contract class provides a high-level interface for:
    - Loading and validating .prmpt documents
    - Generating system prompts for LLMs
    - Validating inputs and outputs
    - Checking actions and handoff conditions

    Example:
        >>> contract = Contract.load("my-bot.prmpt")
        >>> print(contract.name)
        "my-bot"
        >>> errors = contract.validate_input({"query": "hello"})
        >>> system_prompt = contract.to_system_prompt()
    """

    def __init__(self, effective: Dict[str, Any], source: Optional[str] = None):
        """
        Initialize a Contract from an effective prompt dict.

        Use Contract.load() or Contract.loads() for normal usage.

        Args:
            effective: Resolved effective prompt dict
            source: Optional source path for error messages
        """
        self._effective = effective
        self._source = source

        # Identity
        identity = effective.get('identity', {})
        self.name: str = identity.get('name', '')
        self.version: str = identity.get('version', '')
        self.spec_version: Optional[str] = identity.get('spec_version')
        self.description: Optional[str] = identity.get('description')
        self.target_model: Optional[str] = identity.get('target_model')
        self.parameters: Dict[str, Any] = identity.get('parameters', {})
        self.maintainers: List[str] = identity.get('maintainers', [])

        # Scope
        self.scope: Dict[str, Any] = effective.get('scope', {})

        # Constraints
        self.invariants: List[str] = effective.get('invariants', [])
        self.allowed_actions: Set[str] = set(effective.get('allowed_actions', []))
        self.forbidden_actions: Set[str] = set(effective.get('forbidden_actions', []))

        # I/O
        self.inputs: Dict[str, Any] = effective.get('inputs', {})
        self.outputs: Dict[str, Any] = effective.get('outputs', {})
        self.validation: Dict[str, Any] = effective.get('validation', {})

        # Failure modes
        self._failure_modes_list = effective.get('failure_modes', [])
        self.failure_modes: Dict[str, Dict[str, Any]] = {
            fm['id']: fm for fm in self._failure_modes_list
        }

        # Handoff rules (optional)
        self.handoff_rules: Optional[Dict[str, Any]] = effective.get('handoff_rules')

    @classmethod
    def load(cls, path: Union[str, Path]) -> "Contract":
        """
        Load a contract from a .prmpt file.

        Args:
            path: Path to .prmpt file

        Returns:
            Contract instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ParseError: If file cannot be parsed
            ValidationError: If contract is invalid
        """
        path = Path(path)
        effective = resolve(path)
        return cls(effective, source=str(path))

    @classmethod
    def loads(cls, content: str, source: Optional[str] = None) -> "Contract":
        """
        Load a contract from a YAML or JSON string.

        Args:
            content: Contract content as string
            source: Optional source identifier for errors

        Returns:
            Contract instance

        Raises:
            ParseError: If content cannot be parsed
            ValidationError: If contract is invalid
        """
        effective = resolve(content)
        return cls(effective, source=source)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contract":
        """
        Create a contract from a dict (already parsed).

        Args:
            data: Contract as dict (with original key casing)

        Returns:
            Contract instance

        Raises:
            ValidationError: If contract is invalid
        """
        effective = resolve(data)
        return cls(effective)

    def to_dict(self) -> Dict[str, Any]:
        """Export the effective contract as a dict."""
        return self._effective.copy()

    def to_json(self) -> str:
        """Export the contract as canonical JSON."""
        return canonical_dumps(self._effective)

    def to_yaml(self) -> str:
        """Export the contract as YAML."""
        return yaml.dump(self._effective, default_flow_style=False, sort_keys=True)

    def to_system_prompt(self) -> str:
        """
        Generate a system prompt from the contract.

        Creates natural language instructions for the LLM based on
        the contract's scope, invariants, allowed/forbidden actions,
        and output requirements.

        Returns:
            System prompt string
        """
        parts = []

        # Scope
        if 'description' in self.scope:
            parts.append(f"You are: {self.scope['description']}")

        if 'boundaries' in self.scope:
            parts.append("\nScope boundaries:")
            for boundary in self.scope['boundaries']:
                parts.append(f"- {boundary}")

        # Invariants
        if self.invariants:
            parts.append("\nRules you must ALWAYS follow:")
            for invariant in self.invariants:
                parts.append(f"- {invariant}")

        # Allowed actions
        if self.allowed_actions:
            parts.append("\nYou are allowed to:")
            for action in sorted(self.allowed_actions):
                parts.append(f"- {action}")

        # Forbidden actions
        if self.forbidden_actions:
            parts.append("\nYou are FORBIDDEN from:")
            for action in sorted(self.forbidden_actions):
                parts.append(f"- {action}")

        # Output format
        output_format = self.outputs.get('format')
        if output_format in ['structured', 'json']:
            parts.append("\nYou must respond in valid JSON format only.")
            if 'schema' in self.outputs:
                parts.append(f"JSON schema: {json.dumps(self.outputs['schema'])}")

        # Handoff conditions
        if self.handoff_rules and 'conditions' in self.handoff_rules:
            parts.append("\nHandoff to human when:")
            for condition in self.handoff_rules['conditions']:
                parts.append(f"- {condition}")

        return "\n".join(parts)

    def validate_input(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate input data against the contract's input schema.

        Args:
            data: Input data dict

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if 'parameters' not in self.inputs:
            return errors

        expected_params = self.inputs['parameters']

        for param_name, param_spec in expected_params.items():
            # Check required
            if param_spec.get('required', False) and param_name not in data:
                errors.append(f"Missing required parameter: {param_name}")
                continue

            # Type check
            if param_name in data:
                value = data[param_name]
                expected_type = param_spec.get('type', 'string')

                type_checks = {
                    'string': str,
                    'number': (int, float),
                    'boolean': bool,
                    'object': dict,
                    'array': list,
                }

                if expected_type in type_checks:
                    if not isinstance(value, type_checks[expected_type]):
                        errors.append(
                            f"Parameter '{param_name}' must be {expected_type}, "
                            f"got {type(value).__name__}"
                        )

        return errors

    def validate_output(self, output: str) -> List[str]:
        """
        Validate LLM output against the contract's output schema.

        Args:
            output: LLM output string

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        output_format = self.outputs.get('format', 'text')

        if output_format in ['structured', 'json']:
            try:
                parsed = json.loads(output)

                # Basic schema validation
                if 'schema' in self.outputs:
                    schema = self.outputs['schema']
                    errors.extend(self._validate_schema(parsed, schema, ''))

            except json.JSONDecodeError as e:
                errors.append(f"Output must be valid JSON: {e}")

        return errors

    def _validate_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        path: str
    ) -> List[str]:
        """Basic JSON schema validation."""
        errors = []

        if 'type' in schema:
            expected_type = schema['type']
            type_map = {
                'object': dict,
                'array': list,
                'string': str,
                'number': (int, float),
                'boolean': bool,
            }

            if expected_type in type_map:
                if not isinstance(data, type_map[expected_type]):
                    prefix = f"{path}." if path else ""
                    errors.append(
                        f"{prefix}Expected type {expected_type}, got {type(data).__name__}"
                    )

        if schema.get('type') == 'object' and 'properties' in schema:
            if isinstance(data, dict):
                for prop_name, prop_schema in schema['properties'].items():
                    if prop_name in data:
                        prop_path = f"{path}.{prop_name}" if path else prop_name
                        errors.extend(
                            self._validate_schema(data[prop_name], prop_schema, prop_path)
                        )

        return errors

    def check_action(self, action: str) -> bool:
        """
        Check if an action is allowed by the contract.

        Args:
            action: Action name to check

        Returns:
            True if allowed, False if forbidden
        """
        # Forbidden overrides allowed
        if action in self.forbidden_actions:
            return False

        # If no allowed actions, check not forbidden
        if not self.allowed_actions:
            return action not in self.forbidden_actions

        # Check explicitly allowed
        return action in self.allowed_actions

    def require_action(self, action: str) -> None:
        """
        Require that an action is allowed, raising if not.

        Args:
            action: Action name to check

        Raises:
            ActionForbidden: If action is not allowed
        """
        if not self.check_action(action):
            raise ActionForbidden(action)

    def should_handoff(self, data: Dict[str, Any]) -> bool:
        """
        Check if input should trigger a handoff to human.

        Args:
            data: Input data dict

        Returns:
            True if handoff is required
        """
        if not self.handoff_rules or 'conditions' not in self.handoff_rules:
            return False

        # Simple keyword matching for handoff conditions
        query = str(data.get('user_query', data.get('query', ''))).lower()

        for condition in self.handoff_rules['conditions']:
            condition_lower = condition.lower()
            # Check for keywords in condition
            if 'human' in condition_lower and 'human' in query:
                return True
            if 'billing' in condition_lower and 'billing' in query:
                return True
            if 'refund' in condition_lower and 'refund' in query:
                return True

        return False

    def require_no_handoff(self, data: Dict[str, Any]) -> None:
        """
        Require that input doesn't trigger handoff, raising if it does.

        Args:
            data: Input data dict

        Raises:
            HandoffRequired: If handoff condition is met
        """
        if self.should_handoff(data):
            raise HandoffRequired("Handoff condition met", context=data)

    def handle_failure(self, failure_mode_id: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the failure response for a given failure mode.

        Args:
            failure_mode_id: ID of the failure mode
            context: Optional context about the failure

        Returns:
            Failure response dict
        """
        if failure_mode_id not in self.failure_modes:
            return {
                'error': True,
                'failure_mode': 'unknown',
                'action': 'abort',
                'message': f"Unknown failure mode: {failure_mode_id}",
                'context': context,
            }

        fm = self.failure_modes[failure_mode_id]
        return {
            'error': True,
            'failure_mode': failure_mode_id,
            'action': fm['action'],
            'message': f"Contract violation: {failure_mode_id}",
            'context': context,
        }

    def check_spec_compatibility(self) -> Optional[str]:
        """
        Check if this contract's spec_version is compatible with the library.

        Returns:
            Warning message if incompatible, None if compatible or no spec_version set
        """
        if not self.spec_version:
            return None

        from . import __spec_version__

        if self.spec_version != __spec_version__:
            return (
                f"Contract targets spec v{self.spec_version}, "
                f"but library implements v{__spec_version__}"
            )
        return None

    def __repr__(self) -> str:
        return f"Contract(name={self.name!r}, version={self.version!r})"

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
