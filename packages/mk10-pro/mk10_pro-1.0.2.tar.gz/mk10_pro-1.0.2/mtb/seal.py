# SPDX-License-Identifier: MIT
"""MTB sealing with integrity proof."""

from typing import Dict, Any

from engine.util.json import canonical_json_bytes
from engine.evidence.hash import compute_sha256


def seal_mtb(mtb: Dict[str, Any]) -> Dict[str, Any]:
    """
    Seal MTB with integrity proof.
    
    Once sealed, MTB cannot be modified. Any change creates a new identity.
    
    Args:
        mtb: MTB dictionary (without integrity_proof)
        
    Returns:
        Sealed MTB with integrity_proof
    """
    # Create copy without integrity_proof if present
    mtb_copy = {k: v for k, v in mtb.items() if k != "integrity_proof"}
    
    # Compute canonical hash
    canonical = canonical_json_bytes(mtb_copy)
    hash_value = compute_sha256(canonical)
    
    # Add integrity proof
    sealed = mtb_copy.copy()
    sealed["integrity_proof"] = {
        "algorithm": "sha256",
        "hash": hash_value,
    }
    
    return sealed


def verify_seal(mtb: Dict[str, Any]) -> bool:
    """
    Verify MTB seal.
    
    Args:
        mtb: Sealed MTB dictionary
        
    Returns:
        True if seal is valid
    """
    if "integrity_proof" not in mtb:
        return False
    
    integrity_proof = mtb["integrity_proof"]
    expected_hash = integrity_proof.get("hash")
    algorithm = integrity_proof.get("algorithm", "sha256")
    
    if not expected_hash:
        return False
    
    # Recompute hash without integrity_proof
    mtb_without_proof = {k: v for k, v in mtb.items() if k != "integrity_proof"}
    canonical = canonical_json_bytes(mtb_without_proof)
    
    if algorithm == "sha256":
        computed_hash = compute_sha256(canonical)
    else:
        from engine.evidence.hash import compute_hash
        computed_hash = compute_hash(canonical, algorithm)
    
    return computed_hash == expected_hash

