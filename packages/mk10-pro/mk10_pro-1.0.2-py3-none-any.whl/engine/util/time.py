# SPDX-License-Identifier: MIT
"""Time utilities for deterministic timestamps."""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat()


def from_iso8601(iso_str: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def deterministic_timestamp(base: Optional[datetime] = None) -> str:
    """
    Generate deterministic timestamp.
    
    If base is provided, uses that. Otherwise uses current UTC.
    """
    dt = base if base is not None else utc_now()
    return to_iso8601(dt)

