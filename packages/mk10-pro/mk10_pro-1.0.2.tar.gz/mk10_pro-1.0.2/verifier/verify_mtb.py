# SPDX-License-Identifier: MIT
"""
Standalone public MTB verifier.

No engine, no trust, no authority required.
Any third party can verify an MTB using only public rules.
"""

from pathlib import Path
from typing import Dict, Any
import sys

from verifier.verify import verify_mtb


def find_schema_path() -> Path:
    """
    Find MTB schema path relative to verifier.
    
    Returns:
        Path to MTB schema file
    """
    # Schema is in mtb/schema/ relative to project root
    # Verifier is in verifier/ relative to project root
    verifier_dir = Path(__file__).parent
    project_root = verifier_dir.parent
    schema_path = project_root / "mtb" / "schema" / "mtb.schema.json"
    return schema_path


def main():
    """CLI entry point for MTB verification."""
    if len(sys.argv) < 2:
        print("Usage: verify_mtb <mtb_path>")
        sys.exit(1)
    
    mtb_path = Path(sys.argv[1])
    
    if not mtb_path.exists():
        print(f"Error: MTB file not found: {mtb_path}")
        sys.exit(1)
    
    schema_path = find_schema_path()
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    print(f"Verifying MTB: {mtb_path}")
    results = verify_mtb(mtb_path, schema_path)
    
    if results["valid"]:
        print("✓ MTB is valid")
        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")
        sys.exit(0)
    else:
        print("✗ MTB is invalid")
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
