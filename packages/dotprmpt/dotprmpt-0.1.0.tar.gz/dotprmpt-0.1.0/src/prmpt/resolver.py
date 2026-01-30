"""
.prmpt document resolution.

Implements the resolution algorithm from the specification §6:
1. Parse the document
2. Validate structure
3. Resolve defaults
4. Produce the effective prompt
5. Lock all constraints prior to invocation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .validator import parse_file, parse_string, validate_structure
from .canonical import canonical_dumps
from .exceptions import ParseError, ValidationError


def _resolve_defaults(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve defaults for optional fields.

    Tool-specific defaults:
    - If Identity.parameters is missing, set to {}
    """
    resolved = doc.copy()

    if 'Identity' in resolved and isinstance(resolved['Identity'], dict):
        if 'parameters' not in resolved['Identity']:
            resolved['Identity']['parameters'] = {}

    return resolved


def _normalize_keys(obj: Any) -> Any:
    """
    Normalize keys from Title Case to snake_case.

    Converts "Allowed Actions" -> "allowed_actions", etc.
    """
    if isinstance(obj, dict):
        normalized = {}
        for key, value in obj.items():
            snake_key = key.replace(' ', '_').lower()
            normalized[snake_key] = _normalize_keys(value)
        return normalized
    elif isinstance(obj, list):
        return [_normalize_keys(item) for item in obj]
    else:
        return obj


def _produce_effective(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce the effective prompt object from a validated document.

    The effective prompt is the fully resolved representation used
    by host systems to construct LLM interactions.
    """
    effective = _normalize_keys(doc)

    # Sort actions for determinism (they represent sets)
    if 'allowed_actions' in effective and isinstance(effective['allowed_actions'], list):
        effective['allowed_actions'] = sorted(effective['allowed_actions'])

    if 'forbidden_actions' in effective and isinstance(effective['forbidden_actions'], list):
        effective['forbidden_actions'] = sorted(effective['forbidden_actions'])

    return effective


def resolve(
    source: Union[str, Path, Dict[str, Any]],
    *,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Resolve a .prmpt document to its effective prompt representation.

    Implements the §6 resolution algorithm:
    1. Parse the document
    2. Validate structure
    3. Resolve defaults
    4. Produce the effective prompt
    5. Lock constraints (returned as immutable-treated dict)

    Args:
        source: File path, content string, or parsed dict
        validate: If True (default), validate before resolving

    Returns:
        Effective prompt dict with snake_case keys

    Raises:
        ParseError: If document cannot be parsed
        ValidationError: If document is invalid and validate=True
    """
    # Step 1: Parse if needed
    if isinstance(source, dict):
        doc = source
    elif isinstance(source, Path):
        doc = parse_file(source)
    elif '\n' not in source and Path(source).exists():
        doc = parse_file(source)
    else:
        doc = parse_string(source)

    # Step 2: Validate
    if validate:
        errors = validate_structure(doc)
        if errors:
            raise ValidationError(errors)

    # Step 3: Resolve defaults
    doc = _resolve_defaults(doc)

    # Step 4: Produce effective prompt
    effective = _produce_effective(doc)

    # Step 5: Lock constraints (treat as immutable)
    return effective


def resolve_to_json(source: Union[str, Path, Dict[str, Any]]) -> str:
    """
    Resolve a .prmpt document to canonical JSON string.

    Args:
        source: File path, content string, or parsed dict

    Returns:
        Canonical JSON string
    """
    effective = resolve(source)
    return canonical_dumps(effective)
