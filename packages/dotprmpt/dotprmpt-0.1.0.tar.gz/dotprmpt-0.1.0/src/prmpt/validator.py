"""
.prmpt document validation.

Validates .prmpt documents against the normative requirements in the specification.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .exceptions import ParseError, ValidationError


def parse_string(content: str, source: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse a .prmpt document from a string (YAML or JSON).

    Args:
        content: Document content as string
        source: Optional source identifier for error messages

    Returns:
        Parsed document as dict

    Raises:
        ParseError: If parsing fails
    """
    content = content.strip()

    # Try JSON first if it looks like JSON
    if content.startswith('{'):
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ParseError(f"JSON parse error: {e}", source=source)

    # Try YAML
    try:
        result = yaml.safe_load(content)
        if result is None:
            raise ParseError("Empty document", source=source)
        if not isinstance(result, dict):
            raise ParseError("Document must be a mapping/object", source=source)
        return result
    except yaml.YAMLError as e:
        raise ParseError(f"YAML parse error: {e}", source=source)


def parse_file(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse a .prmpt document from a file.

    Args:
        filepath: Path to .prmpt file

    Returns:
        Parsed document as dict

    Raises:
        ParseError: If parsing fails
        FileNotFoundError: If file doesn't exist
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        raise ParseError(f"Error reading file: {e}", source=str(filepath))

    return parse_string(content, source=str(filepath))


def validate_semver(version: str) -> bool:
    """Check if a version string follows semantic versioning (MAJOR.MINOR.PATCH)."""
    return bool(re.match(r'^\d+\.\d+\.\d+$', version))


def validate_structure(doc: Dict[str, Any]) -> List[str]:
    """
    Validate a .prmpt document structure.

    Args:
        doc: Parsed document dict

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # §4: Check required top-level sections
    required_sections = [
        'Identity',
        'Scope',
        'Invariants',
        'Allowed Actions',
        'Forbidden Actions',
        'Inputs',
        'Outputs',
        'Validation',
        'Failure Modes'
    ]

    for section in required_sections:
        if section not in doc:
            errors.append(f"§4 Missing required section: {section}")

    if 'Identity' not in doc:
        return errors

    identity = doc['Identity']

    # §5.1: Identity validation
    if not isinstance(identity, dict):
        errors.append("§5.1 Identity must be an object")
    else:
        if 'name' not in identity:
            errors.append("§5.1 Identity.name is required")
        elif not isinstance(identity['name'], str):
            errors.append("§5.1 Identity.name must be a string")

        if 'version' not in identity:
            errors.append("§5.1 Identity.version is required")
        elif not isinstance(identity['version'], str):
            errors.append("§5.1 Identity.version must be a string")
        elif not validate_semver(identity['version']):
            errors.append("§5.1 Identity.version must be valid semver (MAJOR.MINOR.PATCH)")

    # §5.4: Allowed Actions
    if 'Allowed Actions' in doc:
        if not isinstance(doc['Allowed Actions'], list):
            errors.append("§5.4 Allowed Actions must be a list")

    # §5.5: Action conflicts
    if 'Allowed Actions' in doc and 'Forbidden Actions' in doc:
        if isinstance(doc['Allowed Actions'], list) and isinstance(doc['Forbidden Actions'], list):
            conflicts = set(doc['Allowed Actions']) & set(doc['Forbidden Actions'])
            if conflicts:
                errors.append(f"§5.5 Actions in both Allowed and Forbidden: {conflicts}")

    # §5.6: Inputs
    if 'Inputs' in doc and not isinstance(doc['Inputs'], dict):
        errors.append("§5.6 Inputs must be an object")

    # §5.7: Outputs
    if 'Outputs' in doc and not isinstance(doc['Outputs'], dict):
        errors.append("§5.7 Outputs must be an object")

    # §5.8: Validation section
    if 'Validation' in doc:
        validation = doc['Validation']
        if not isinstance(validation, dict):
            errors.append("§5.8 Validation must be an object")
        else:
            if 'mode' not in validation and 'checks' not in validation:
                errors.append("§5.8 Validation must have 'mode' or 'checks'")
            if 'mode' in validation and validation['mode'] not in ['none', 'schema', 'rules']:
                errors.append("§5.8 Validation.mode must be: none, schema, or rules")

    # §5.9: Failure Modes
    if 'Failure Modes' in doc:
        failure_modes = doc['Failure Modes']
        if not isinstance(failure_modes, list):
            errors.append("§5.9 Failure Modes must be a list")
        elif len(failure_modes) == 0:
            errors.append("§5.9 Failure Modes must not be empty")
        else:
            for i, mode in enumerate(failure_modes):
                if not isinstance(mode, dict):
                    errors.append(f"§5.9 Failure Modes[{i}] must be an object")
                else:
                    if 'id' not in mode:
                        errors.append(f"§5.9 Failure Modes[{i}] must have 'id'")
                    if 'action' not in mode:
                        errors.append(f"§5.9 Failure Modes[{i}] must have 'action'")

    return errors


def validate(
    source: Union[str, Path, Dict[str, Any]],
    *,
    strict: bool = False
) -> List[str]:
    """
    Validate a .prmpt document.

    Args:
        source: File path, content string, or parsed dict
        strict: If True, raise ValidationError on invalid document

    Returns:
        List of validation errors (empty if valid)

    Raises:
        ValidationError: If strict=True and document is invalid
        ParseError: If document cannot be parsed
    """
    # Parse if needed
    if isinstance(source, dict):
        doc = source
        source_name = None
    elif isinstance(source, Path) or (isinstance(source, str) and '\n' not in source and Path(source).exists()):
        source_name = str(source)
        doc = parse_file(source)
    else:
        source_name = None
        doc = parse_string(source)

    # Validate
    errors = validate_structure(doc)

    if strict and errors:
        raise ValidationError(errors, source=source_name)

    return errors
