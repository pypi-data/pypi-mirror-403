# SPDX-License-Identifier: MIT
"""JSON utilities with canonical formatting."""

import json
from typing import Any, Dict, List


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


def load_json(filepath: str) -> Any:
    """Load JSON from file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, obj: Any, canonical: bool = False) -> None:
    """
    Save object as JSON.
    
    Args:
        filepath: Target file path
        obj: Object to serialize
        canonical: Use canonical formatting
    """
    if canonical:
        content = canonical_json(obj)
    else:
        content = json.dumps(obj, indent=2, ensure_ascii=False)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

