# SPDX-License-Identifier: MIT
"""
Content Integrity Verifier Node

A pure, deterministic node that verifies content integrity and extracts
deterministic metadata from content-addressed inputs.

AXIOM COMPLIANCE:
- Pure function: No side effects
- Content-addressed I/O: All inputs/outputs content-addressed
- Deterministic: Same input = same output
- No filesystem state: Works with content bytes only
- No environment: No env vars, no system calls
- No clock: No time dependencies
- No randomness: Pure computation only
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import hashlib
import struct

from engine.core.node import Node, NodeInput, NodeOutput
from engine.core.context import ExecutionContext
from engine.core.errors import ExecutionError, ValidationError


@dataclass(frozen=True)
class ContentVerifierConfig:
    """Immutable configuration for ContentVerifier node."""
    hash_algorithm: str = "sha256"
    verify_integrity: bool = True
    extract_metadata: bool = True


class ContentVerifierNode(Node):
    """
    Content Integrity Verifier Node.
    
    Verifies that content matches its content address and extracts
    deterministic metadata from the content.
    
    This is a pure function with no side effects.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, "content_verifier", config)
        
        # Parse and validate config
        try:
            self.verifier_config = ContentVerifierConfig(
                hash_algorithm=config.get("hash_algorithm", "sha256"),
                verify_integrity=config.get("verify_integrity", True),
                extract_metadata=config.get("extract_metadata", True),
            )
        except Exception as e:
            raise ExecutionError(f"Invalid ContentVerifier config: {e}")
        
        # Validate hash algorithm
        try:
            hashlib.new(self.verifier_config.hash_algorithm)
        except ValueError:
            raise ExecutionError(
                f"Unsupported hash algorithm: {self.verifier_config.hash_algorithm}"
            )
    
    def validate_inputs(self, inputs: List[NodeInput]) -> bool:
        """
        Validate inputs before execution.
        
        Contract:
        - Exactly 1 input required
        - Input must have content_address
        - Input metadata must contain 'content_bytes' for verification
        """
        if len(inputs) != 1:
            return False
        
        inp = inputs[0]
        if not inp.content_address:
            return False
        
        # Content bytes should be in metadata for pure operation
        # (In real implementation, content would be retrieved via content address)
        if self.verifier_config.verify_integrity:
            if "content_bytes" not in inp.metadata:
                # Content bytes not provided - cannot verify
                # This is acceptable if content is retrieved elsewhere
                pass
        
        return True
    
    def execute(
        self,
        inputs: List[NodeInput],
        context: ExecutionContext,
    ) -> NodeOutput:
        """
        Execute content verification.
        
        Formal Contract:
        
        INPUT CONTRACT:
        - inputs: List[NodeInput] with exactly 1 element
        - input.content_address: str (format: "{hash}{extension}")
        - input.metadata: Dict containing:
          - "content_bytes": bytes (content to verify)
          - Optional: "size": int, "mime_type": str
        
        OUTPUT CONTRACT:
        - output.content_address: str (same as input if valid, or error)
        - output.metadata: Dict containing:
          - "verified": bool
          - "hash_algorithm": str
          - "computed_hash": str
          - "expected_hash": str
          - "size": int
          - "metadata_extracted": Dict (if extract_metadata=True)
        - output.evidence: Dict with execution evidence
        
        DETERMINISM:
        - Same input.content_address + input.metadata = same output
        - Hash computation is deterministic
        - Metadata extraction is deterministic (no time, no randomness)
        
        FAILURE MODES:
        - InputValidationError: Invalid input structure
        - IntegrityMismatchError: Content hash doesn't match address
        - MetadataExtractionError: Failed to extract metadata
        """
        # Validate inputs
        if not self.validate_inputs(inputs):
            raise ExecutionError(
                f"ContentVerifier {self.node_id}: Invalid inputs. "
                f"Expected 1 input, got {len(inputs)}"
            )
        
        inp = inputs[0]
        content_bytes = inp.metadata.get("content_bytes")
        
        if content_bytes is None:
            raise ExecutionError(
                f"ContentVerifier {self.node_id}: content_bytes not provided in metadata"
            )
        
        # Extract hash from content address
        # Format: "{hash}{extension}" where hash is hex string
        content_addr = inp.content_address
        hash_hex, extension = self._parse_content_address(content_addr)
        
        # Compute hash of content
        computed_hash = self._compute_hash(content_bytes)
        
        # Verify integrity if required
        verified = True
        if self.verifier_config.verify_integrity:
            verified = computed_hash == hash_hex
            if not verified:
                raise ValidationError(
                    f"ContentVerifier {self.node_id}: Integrity mismatch. "
                    f"Expected hash: {hash_hex}, computed: {computed_hash}"
                )
        
        # Extract deterministic metadata
        extracted_metadata = {}
        if self.verifier_config.extract_metadata:
            extracted_metadata = self._extract_metadata(content_bytes, extension)
        
        # Build output metadata
        output_metadata = {
            "verified": verified,
            "hash_algorithm": self.verifier_config.hash_algorithm,
            "computed_hash": computed_hash,
            "expected_hash": hash_hex,
            "size": len(content_bytes),
            "metadata_extracted": extracted_metadata,
        }
        
        # Output has same content address if verified
        # (Content unchanged, just verified)
        output_content_address = inp.content_address if verified else f"invalid_{computed_hash}{extension}"
        
        # Generate evidence
        evidence = self.get_evidence(inputs, NodeOutput(
            content_address=output_content_address,
            path=inp.path,  # Path is metadata, not used for computation
            metadata=output_metadata,
            evidence={},
        ))
        
        # Add verification-specific evidence
        evidence["verification"] = {
            "algorithm": self.verifier_config.hash_algorithm,
            "computed_hash": computed_hash,
            "expected_hash": hash_hex,
            "verified": verified,
            "content_size": len(content_bytes),
        }
        
        return NodeOutput(
            content_address=output_content_address,
            path=inp.path,  # Path preserved as metadata
            metadata=output_metadata,
            evidence=evidence,
        )
    
    def _parse_content_address(self, content_address: str) -> Tuple[str, str]:
        """
        Parse content address into hash and extension.
        
        Format: "{hash}{extension}"
        Hash is hex string (length depends on algorithm).
        Extension starts with '.' or is empty.
        
        Returns:
            (hash_hex, extension) tuple
        """
        # Find extension (starts with '.')
        if '.' in content_address:
            # Find last dot (for extensions like .tar.gz)
            last_dot = content_address.rfind('.')
            hash_hex = content_address[:last_dot]
            extension = content_address[last_dot:]
        else:
            hash_hex = content_address
            extension = ""
        
        return (hash_hex, extension)
    
    def _compute_hash(self, content: bytes) -> str:
        """
        Compute hash of content.
        
        Pure function: Deterministic for same input.
        """
        hash_obj = hashlib.new(self.verifier_config.hash_algorithm)
        hash_obj.update(content)
        return hash_obj.hexdigest()
    
    def _extract_metadata(self, content: bytes, extension: str) -> Dict[str, Any]:
        """
        Extract deterministic metadata from content.
        
        Pure function: No time, no randomness, no environment.
        Only deterministic analysis of content bytes.
        
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "size": len(content),
            "extension": extension,
        }
        
        # Detect file type from magic bytes (deterministic)
        if len(content) >= 4:
            magic = content[:4]
            
            # Common magic bytes (deterministic detection)
            if magic.startswith(b'\x89PNG'):
                metadata["detected_type"] = "image/png"
            elif magic.startswith(b'\xff\xd8\xff'):
                metadata["detected_type"] = "image/jpeg"
            elif magic.startswith(b'GIF8'):
                metadata["detected_type"] = "image/gif"
            elif magic.startswith(b'RIFF') and b'WEBP' in content[:12]:
                metadata["detected_type"] = "image/webp"
            elif magic.startswith(b'\x00\x00\x00') and len(content) > 8:
                # Possible video/audio container
                # Check for common formats
                if b'ftyp' in content[:32]:
                    metadata["detected_type"] = "video/container"
            elif content.startswith(b'<?xml'):
                metadata["detected_type"] = "application/xml"
            elif content.startswith(b'{') or content.startswith(b'['):
                metadata["detected_type"] = "application/json"
            else:
                metadata["detected_type"] = "application/octet-stream"
        else:
            metadata["detected_type"] = "application/octet-stream"
        
        # Extract size-based metadata (deterministic)
        if len(content) > 0:
            metadata["non_empty"] = True
            metadata["byte_range"] = {
                "min": int(min(content)),
                "max": int(max(content)),
            }
        else:
            metadata["non_empty"] = False
        
        return metadata


# ============================================================================
# FORMAL SPECIFICATION
# ============================================================================

"""
FORMAL INPUT CONTRACT:

Input: List[NodeInput] where:
  - len(inputs) == 1
  - inputs[0].content_address: str
    Format: "{hash_hex}{extension}"
    Example: "a1b2c3d4e5f6.mxf"
  - inputs[0].metadata: Dict[str, Any]
    Required: "content_bytes": bytes
    Optional: "size": int, "mime_type": str

FORMAL OUTPUT CONTRACT:

Output: NodeOutput where:
  - output.content_address: str
    If verified: same as input.content_address
    If invalid: "invalid_{computed_hash}{extension}"
  - output.metadata: Dict[str, Any]
    Required fields:
      - "verified": bool
      - "hash_algorithm": str
      - "computed_hash": str
      - "expected_hash": str
      - "size": int
      - "metadata_extracted": Dict
  - output.evidence: Dict[str, Any]
    Contains execution evidence with verification details

DETERMINISM PROOF SKETCH:

1. Hash Computation:
   - hash(content_bytes) is deterministic (cryptographic hash function)
   - Same content_bytes → same hash
   - No randomness, no time, no environment

2. Metadata Extraction:
   - Based on content bytes only (magic bytes, size)
   - No time dependencies
   - No environment variables
   - No randomness
   - Same content → same metadata

3. Verification:
   - Comparison: computed_hash == expected_hash
   - Pure boolean operation
   - Deterministic

4. Output Construction:
   - All outputs derived from inputs and config
   - No external state
   - Same inputs + same config → same outputs

Therefore: f(inputs, config) is deterministic.

EVIDENCE EMITTED:

{
  "node_id": str,
  "node_type": "content_verifier",
  "inputs": [{
    "content_address": str,
    "metadata": Dict
  }],
  "output": {
    "content_address": str,
    "metadata": Dict
  },
  "config": Dict,
  "verification": {
    "algorithm": str,
    "computed_hash": str,
    "expected_hash": str,
    "verified": bool,
    "content_size": int
  }
}

FAILURE MODES (Typed, Explicit):

1. ExecutionError (Input Validation):
   - "Invalid inputs. Expected 1 input, got N"
   - "content_bytes not provided in metadata"
   - "Invalid ContentVerifier config: {error}"

2. ValidationError (Integrity Mismatch):
   - "Integrity mismatch. Expected hash: {expected}, computed: {computed}"
   - Raised when verify_integrity=True and hashes don't match

3. ExecutionError (Configuration):
   - "Unsupported hash algorithm: {algorithm}"
   - Raised when hash algorithm is invalid

All failures are explicit, typed, and non-silent.
No silent failures. No partial outputs on error.
"""

