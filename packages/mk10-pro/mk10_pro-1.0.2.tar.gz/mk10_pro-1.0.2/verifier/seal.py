# SPDX-License-Identifier: MIT
"""Standalone MTB sealing with integrity proof."""

from typing import Dict, Any

from verifier.utils.json import canonical_json_bytes
from verifier.utils.hash import compute_sha256


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
        from verifier.utils.hash import compute_hash
        computed_hash = compute_hash(canonical, algorithm)
    
    return computed_hash == expected_hash

