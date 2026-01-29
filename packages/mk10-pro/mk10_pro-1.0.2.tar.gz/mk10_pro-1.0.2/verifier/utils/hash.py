# SPDX-License-Identifier: MIT
"""Standalone cryptographic hashing utilities."""

import hashlib
from typing import Union
from pathlib import Path


def compute_hash(data: Union[bytes, str, Path], algorithm: str = "sha256") -> str:
    """
    Compute hash of data.
    
    Args:
        data: Bytes, string, or file path
        algorithm: Hash algorithm (sha256, sha512, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    
    if isinstance(data, Path):
        with open(data, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
    elif isinstance(data, str):
        hash_obj.update(data.encode("utf-8"))
    else:
        hash_obj.update(data)
    
    return hash_obj.hexdigest()


def compute_sha256(data: Union[bytes, str, Path]) -> str:
    """Compute SHA-256 hash."""
    return compute_hash(data, "sha256")

