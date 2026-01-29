# SPDX-License-Identifier: MIT
"""Standalone JSON utilities with canonical formatting."""

import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON string.
    
    Canonical means:
    - No whitespace
    - Sorted keys
    - Consistent formatting
    
    Args:
        obj: Object to serialize
        
    Returns:
        Canonical JSON string
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize to canonical JSON bytes."""
    return canonical_json(obj).encode("utf-8")

