# SPDX-License-Identifier: MIT
"""MTB verification."""

from pathlib import Path
from typing import Dict, Any, List
import json
import jsonschema

from engine.core.errors import MTBError
from mtb.seal import verify_seal
def load_schema() -> Dict[str, Any]:
    """Load MTB JSON schema."""
    schema_path = Path(__file__).parent / "schema" / "mtb.schema.json"
    with open(schema_path, "r") as f:
        return json.load(f)


def verify_mtb_structure(mtb: Dict[str, Any]) -> List[str]:
    """
    Verify MTB structure against schema.
    
    Args:
        mtb: MTB dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors: List[str] = []
    
    try:
        schema = load_schema()
        validator = jsonschema.Draft7Validator(schema)
        
        for error in validator.iter_errors(mtb):
            errors.append(f"{error.json_path}: {error.message}")
    
    except Exception as e:
        errors.append(f"Schema validation error: {e}")
    
    return errors


def verify_mtb(mtb_path: Path) -> Dict[str, Any]:
    """
    Verify MTB file.
    
    Args:
        mtb_path: Path to MTB file (JSON or ZIP)
        
    Returns:
        Verification results dictionary
        
    Raises:
        MTBError: If MTB cannot be loaded
    """
    results = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "details": {},
    }
    
    try:
        # Load MTB
        if mtb_path.suffix == ".zip":
            import zipfile
            with zipfile.ZipFile(mtb_path, "r") as zf:
                mtb_files = [f for f in zf.namelist() if f.endswith(".json")]
                if not mtb_files:
                    results["errors"].append("No MTB JSON file found in ZIP")
                    return results
                mtb_data = zf.read(mtb_files[0])
                mtb = json.loads(mtb_data)
        else:
            with open(mtb_path, "r") as f:
                mtb = json.load(f)
        
        # Verify structure
        structure_errors = verify_mtb_structure(mtb)
        if structure_errors:
            results["errors"].extend(structure_errors)
            return results
        
        results["details"]["structure"] = "valid"
        
        # Verify seal
        if not verify_seal(mtb):
            results["errors"].append("Integrity proof verification failed")
            return results
        
        results["details"]["seal"] = "valid"
        
        # Verify required sections
        required_sections = [
            "ingest_manifest",
            "lineage_dag",
            "build_evidence",
            "policy_evidence",
            "validation_evidence",
            "approval_events",
            "integrity_proof",
        ]
        
        for section in required_sections:
            if section not in mtb:
                results["errors"].append(f"Required section missing: {section}")
            elif not mtb[section]:
                results["warnings"].append(f"Section empty: {section}")
        
        if not results["errors"]:
            results["valid"] = True
        
        return results
    
    except json.JSONDecodeError as e:
        results["errors"].append(f"Invalid JSON: {e}")
        return results
    except Exception as e:
        results["errors"].append(f"Verification error: {e}")
        return results

