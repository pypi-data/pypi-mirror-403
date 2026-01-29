# SPDX-License-Identifier: MIT
"""File system utilities with content addressing."""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple


def content_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Compute content hash of a file.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm (sha256, sha512, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write(filepath: Path, content: bytes, mode: str = "wb") -> None:
    """
    Atomically write file content.
    
    Args:
        filepath: Target file path
        content: Content to write
        mode: Write mode
    """
    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
    with open(tmp_path, mode) as f:
        f.write(content)
    tmp_path.replace(filepath)


def get_file_info(filepath: Path) -> dict:
    """
    Get file metadata and content hash.
    
    Returns:
        Dictionary with size, mtime, and hash
    """
    stat = filepath.stat()
    return {
        "path": str(filepath),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "hash": content_hash(filepath),
    }


def content_address(path: Path, content: bytes, algorithm: str = "sha256") -> str:
    """
    Generate content address for bytes.
    
    Args:
        path: Original path (for extension)
        content: File content
        algorithm: Hash algorithm
        
    Returns:
        Content address string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(content)
    hash_hex = hash_obj.hexdigest()
    ext = path.suffix if path.suffix else ""
    return f"{hash_hex}{ext}"

