"""
prmpt - System-enforced LLM contracts.

A specification and library for defining, validating, and enforcing
behavioral constraints on AI/LLM interactions.

Basic usage:
    >>> import prmpt
    >>> contract = prmpt.load("my-bot.prmpt")
    >>> print(contract.name)
    "my-bot"
    >>> errors = contract.validate_input({"query": "hello"})
    >>> system_prompt = contract.to_system_prompt()

Validation:
    >>> errors = prmpt.validate("contract.prmpt")
    >>> prmpt.validate("contract.prmpt", strict=True)  # Raises on error

Resolution:
    >>> effective = prmpt.resolve("contract.prmpt")
    >>> json_str = prmpt.resolve_to_json("contract.prmpt")
"""

from .contract import Contract
from .validator import validate, parse_file, parse_string
from .resolver import resolve, resolve_to_json
from .canonical import canonical_dumps
from .exceptions import (
    PrmptError,
    ParseError,
    ValidationError,
    ContractViolation,
    InputViolation,
    OutputViolation,
    HandoffRequired,
    ActionForbidden,
)

__version__ = "0.1.0"        # Library/package version
__spec_version__ = "0.1.0"   # .prmpt specification version this library implements

__all__ = [
    # Version
    "__version__",
    "__spec_version__",
    # Main class
    "Contract",
    # Top-level functions
    "load",
    "loads",
    "validate",
    "resolve",
    "resolve_to_json",
    # Parsing
    "parse_file",
    "parse_string",
    # Serialization
    "canonical_dumps",
    # Exceptions
    "PrmptError",
    "ParseError",
    "ValidationError",
    "ContractViolation",
    "InputViolation",
    "OutputViolation",
    "HandoffRequired",
    "ActionForbidden",
]


def load(path) -> Contract:
    """
    Load a .prmpt contract from a file.

    This is the main entry point for loading contracts.

    Args:
        path: Path to .prmpt file (str or Path)

    Returns:
        Contract instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ParseError: If file cannot be parsed
        ValidationError: If contract is invalid

    Example:
        >>> contract = prmpt.load("my-bot.prmpt")
        >>> print(contract.name)
        "my-bot"
    """
    return Contract.load(path)


def loads(content: str, source: str = None) -> Contract:
    """
    Load a .prmpt contract from a string.

    Args:
        content: Contract content as YAML or JSON string
        source: Optional source identifier for error messages

    Returns:
        Contract instance

    Raises:
        ParseError: If content cannot be parsed
        ValidationError: If contract is invalid

    Example:
        >>> contract = prmpt.loads('''
        ... Identity:
        ...   name: test
        ...   version: 1.0.0
        ... ...
        ... ''')
    """
    return Contract.loads(content, source=source)
