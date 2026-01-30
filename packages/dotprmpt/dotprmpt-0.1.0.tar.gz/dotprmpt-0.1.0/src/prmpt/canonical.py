"""
Canonical JSON serialization for .prmpt documents.

Provides deterministic JSON serialization to ensure that
the same logical document always produces identical byte output.

Canonicalization rules:
- UTF-8 encoding
- Sorted keys at all levels (recursive)
- 2-space indentation
- No trailing whitespace
- Newline at end of file
"""

import json
from typing import Any


def canonical_dumps(obj: Any) -> str:
    """
    Serialize an object to canonical JSON format.

    Ensures deterministic output by:
    - Sorting all object keys recursively
    - Using consistent indentation (2 spaces)
    - Ensuring newline at end of file

    Args:
        obj: Python object to serialize (dict, list, etc.)

    Returns:
        Canonical JSON string with trailing newline
    """
    json_str = json.dumps(
        obj,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        separators=(',', ': ')
    )

    if not json_str.endswith('\n'):
        json_str += '\n'

    return json_str


def canonical_dumps_bytes(obj: Any) -> bytes:
    """
    Serialize an object to canonical JSON format as UTF-8 bytes.

    Args:
        obj: Python object to serialize

    Returns:
        Canonical JSON as UTF-8 encoded bytes
    """
    return canonical_dumps(obj).encode('utf-8')
