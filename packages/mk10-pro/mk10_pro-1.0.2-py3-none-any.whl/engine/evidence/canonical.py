# SPDX-License-Identifier: MIT
"""Canonical representation for evidence."""

from typing import Any, Dict
from engine.util.json import canonical_json_bytes
from engine.evidence.hash import compute_sha256


def canonicalize_evidence(evidence: Dict[str, Any]) -> bytes:
    """
    Convert evidence to canonical bytes.
    
    Canonical means deterministic, reproducible representation.
    
    Args:
        evidence: Evidence dictionary
        
    Returns:
        Canonical bytes
    """
    return canonical_json_bytes(evidence)


def hash_evidence(evidence: Dict[str, Any]) -> str:
    """
    Compute hash of canonical evidence.
    
    Args:
        evidence: Evidence dictionary
        
    Returns:
        SHA-256 hash
    """
    canonical = canonicalize_evidence(evidence)
    return compute_sha256(canonical)


def seal_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Seal evidence with integrity proof.
    
    Adds canonical hash to evidence.
    
    Args:
        evidence: Evidence dictionary
        
    Returns:
        Sealed evidence with integrity_proof
    """
    sealed = evidence.copy()
    sealed["integrity_proof"] = {
        "algorithm": "sha256",
        "hash": hash_evidence(evidence),
    }
    return sealed

