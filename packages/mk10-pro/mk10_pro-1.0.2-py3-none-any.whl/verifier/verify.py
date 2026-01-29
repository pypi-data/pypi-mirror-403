# SPDX-License-Identifier: MIT
"""Standalone MTB verification."""

from pathlib import Path
from typing import Dict, Any, List
import json
import jsonschema
import zipfile

from verifier.utils.errors import MTBError
from verifier.seal import verify_seal


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load MTB JSON schema.
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Schema dictionary
    """
    with open(schema_path, "r") as f:
        return json.load(f)


def verify_mtb_structure(mtb: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Verify MTB structure against schema.
    
    Args:
        mtb: MTB dictionary
        schema: JSON schema dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors: List[str] = []
    
    try:
        validator = jsonschema.Draft7Validator(schema)
        
        for error in validator.iter_errors(mtb):
            errors.append(f"{error.json_path}: {error.message}")
    
    except Exception as e:
        errors.append(f"Schema validation error: {e}")
    
    return errors


def load_mtb(mtb_path: Path) -> Dict[str, Any]:
    """
    Load MTB from file (JSON or ZIP).
    
    Args:
        mtb_path: Path to MTB file
        
    Returns:
        MTB dictionary
        
    Raises:
        MTBError: If MTB cannot be loaded
    """
    try:
        if mtb_path.suffix == ".zip":
            with zipfile.ZipFile(mtb_path, "r") as zf:
                mtb_files = [f for f in zf.namelist() if f.endswith(".json")]
                if not mtb_files:
                    raise MTBError("No MTB JSON file found in ZIP")
                mtb_data = zf.read(mtb_files[0])
                return json.loads(mtb_data)
        else:
            with open(mtb_path, "r") as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        raise MTBError(f"Invalid JSON: {e}")
    except Exception as e:
        raise MTBError(f"Failed to load MTB: {e}")


def verify_mtb(mtb_path: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Verify MTB file.
    
    Args:
        mtb_path: Path to MTB file (JSON or ZIP)
        schema_path: Path to MTB schema file
        
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
        mtb = load_mtb(mtb_path)
        
        # Load schema
        schema = load_schema(schema_path)
        
        # Verify structure
        structure_errors = verify_mtb_structure(mtb, schema)
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
            "non_claims",  # Required to prevent scope creep
        ]
        
        for section in required_sections:
            if section not in mtb:
                results["errors"].append(f"Required section missing: {section}")
            elif not mtb[section]:
                results["warnings"].append(f"Section empty: {section}")
        
        # Verify non_claims section
        if "non_claims" in mtb:
            non_claims = mtb["non_claims"]
            required_non_claims = [
                "cross_platform_determinism",
                "hardware_equivalence",
                "library_equivalence",
            ]
            
            for claim in required_non_claims:
                if claim not in non_claims:
                    results["errors"].append(
                        f"Required non_claim missing: {claim}"
                    )
                elif non_claims[claim] != False:
                    results["errors"].append(
                        f"Non-claim {claim} must be false, got: {non_claims[claim]}"
                    )
        
        # Verify policy evidence completeness
        if "policy_evidence" in mtb:
            policy_errors = verify_policy_evidence(mtb["policy_evidence"])
            if policy_errors:
                results["errors"].extend(policy_errors)
        
        # Verify root ingest binding
        root_binding_errors = verify_root_ingest_binding(mtb)
        if root_binding_errors:
            results["errors"].extend(root_binding_errors)
        
        if not results["errors"]:
            results["valid"] = True
        
        return results
    
    except MTBError as e:
        results["errors"].append(str(e))
        return results
    except Exception as e:
        results["errors"].append(f"Verification error: {e}")
        return results


def verify_root_ingest_binding(mtb: Dict[str, Any]) -> List[str]:
    """
    Verify root ingest binding.
    
    All root DAG nodes must have ingest-bound inputs.
    All ingest assets must be used by root nodes.
    All DAG inputs must be traceable to ingest.
    
    Returns:
        List of errors (empty if valid)
    """
    errors: List[str] = []
    
    # Step 1: Extract required data structures
    ingest_manifest = mtb.get("ingest_manifest")
    lineage_dag = mtb.get("lineage_dag")
    
    if ingest_manifest is None:
        errors.append("MISSING_INGEST_MANIFEST: MTB missing ingest_manifest")
        return errors
    
    if lineage_dag is None:
        errors.append("MISSING_LINEAGE_DAG: MTB missing lineage_dag")
        return errors
    
    # Step 2: Build ingest asset index by role and hash
    ingest_assets_by_role: Dict[str, List[Dict[str, Any]]] = {}
    ingest_asset_hashes: Dict[str, Dict[str, Any]] = {}
    
    for asset in ingest_manifest.get("assets", []):
        role = asset.get("role")
        content_hash = asset.get("content_hash")
        
        if not role:
            errors.append("INGEST_ASSET_MISSING_ROLE: Ingest asset missing role")
            continue
        
        if not content_hash:
            errors.append("INGEST_ASSET_MISSING_HASH: Ingest asset missing content_hash")
            continue
        
        if role not in ingest_assets_by_role:
            ingest_assets_by_role[role] = []
        ingest_assets_by_role[role].append(asset)
        
        ingest_asset_hashes[content_hash] = asset
    
    if not ingest_assets_by_role:
        errors.append("NO_INGEST_ASSETS: Ingest manifest has no assets")
        return errors
    
    # Step 3: Identify root nodes (nodes with no incoming edges)
    root_nodes: List[str] = []
    node_dependencies: Dict[str, List[str]] = {}
    
    for edge in lineage_dag.get("edges", []):
        target = edge.get("target")
        source = edge.get("source")
        if target not in node_dependencies:
            node_dependencies[target] = []
        node_dependencies[target].append(source)
    
    nodes = lineage_dag.get("nodes", [])
    node_map: Dict[str, Dict[str, Any]] = {node.get("id"): node for node in nodes}
    
    for node_id in node_map.keys():
        if node_id not in node_dependencies:
            root_nodes.append(node_id)
    
    if not root_nodes:
        errors.append("NO_ROOT_NODES: DAG has no root nodes (invalid DAG)")
        return errors
    
    # Step 4: Verify each root node has ingest-bound inputs
    used_asset_hashes: set = set()
    
    for root_node_id in root_nodes:
        root_node = node_map.get(root_node_id)
        
        if root_node is None:
            errors.append(f"ROOT_NODE_NOT_FOUND: Root node {root_node_id} not found in lineage_dag.nodes")
            continue
        
        # Determine required input roles for this root node
        config = root_node.get("config", {})
        required_roles = config.get("required_input_roles", [])
        
        if not required_roles:
            # Try metadata fallback
            metadata = config.get("metadata", {})
            required_roles = metadata.get("input_roles", [])
        
        if not required_roles:
            # Last resort: use node_id as role
            required_roles = [root_node_id]
        
        # Check if each required role has matching ingest assets
        for role in required_roles:
            if role not in ingest_assets_by_role:
                errors.append(
                    f"ROOT_INPUT_UNBOUND: Root node {root_node_id} requires role '{role}', "
                    f"but no matching asset in ingest manifest"
                )
                continue
            
            matching_assets = ingest_assets_by_role[role]
            
            if not matching_assets:
                errors.append(
                    f"ROOT_INPUT_UNBOUND: Root node {root_node_id} requires role '{role}', "
                    f"but no matching assets found"
                )
                continue
        
        # Verify root node inputs can be traced to ingest
        root_node_inputs = root_node.get("inputs", [])
        
        for input_item in root_node_inputs:
            input_content_address = input_item.get("content_address", "")
            
            # Extract hash from content address (format: "hash" or "hash.ext")
            input_hash = input_content_address.split('.')[0] if input_content_address else ""
            
            if not input_hash:
                errors.append(
                    f"ROOT_INPUT_INVALID: Root node {root_node_id} has invalid input content_address"
                )
                continue
            
            if input_hash not in ingest_asset_hashes:
                errors.append(
                    f"DAG_INPUT_UNTraceABLE: Root node {root_node_id} input {input_content_address} "
                    f"(hash: {input_hash}) cannot be traced to ingest manifest"
                )
            else:
                used_asset_hashes.add(input_hash)
    
    # Step 5: Verify all ingest assets are used
    for asset in ingest_manifest.get("assets", []):
        asset_hash = asset.get("content_hash")
        if asset_hash and asset_hash not in used_asset_hashes:
            asset_id = asset.get("asset_id", "unknown")
            role = asset.get("role", "unknown")
            errors.append(
                f"INGEST_ASSET_UNUSED: Ingest asset {asset_id} (role: {role}, hash: {asset_hash}) "
                f"is not used by any root DAG node"
            )
    
    # Step 6: Verify all DAG inputs can be traced to ingest
    # Build traceability map: hash -> source (ingest or node output)
    traceable_hashes: Dict[str, str] = {}
    
    # Add ingest assets
    for asset_hash in ingest_asset_hashes.keys():
        traceable_hashes[asset_hash] = "ingest"
    
    # Add node outputs to traceable hashes
    for node in nodes:
        node_output = node.get("output")
        if node_output:
            output_content_address = node_output.get("content_address", "")
            output_hash = output_content_address.split('.')[0] if output_content_address else ""
            if output_hash:
                traceable_hashes[output_hash] = f"node_output:{node.get('id')}"
    
    # Verify all inputs are traceable
    for node in nodes:
        node_id = node.get("id")
        node_inputs = node.get("inputs", [])
        
        for input_item in node_inputs:
            input_content_address = input_item.get("content_address", "")
            input_hash = input_content_address.split('.')[0] if input_content_address else ""
            
            if input_hash and input_hash not in traceable_hashes:
                errors.append(
                    f"DAG_INPUT_UNTraceABLE: Node {node_id} input {input_content_address} "
                    f"(hash: {input_hash}) cannot be traced to ingest or node output"
                )
    
    return errors


def verify_policy_evidence(policy_evidence: Dict[str, Any]) -> List[str]:
    """
    Verify policy evidence completeness and validity.
    
    Verifier does NOT trust engine execution.
    Verifier re-checks policy outcomes, not logic.
    
    Returns:
        List of errors (empty if valid)
    """
    errors: List[str] = []
    
    if "rule_checks" not in policy_evidence:
        errors.append("Policy evidence missing rule_checks")
        return errors
    
    rule_checks = policy_evidence["rule_checks"]
    
    if not rule_checks:
        errors.append("Policy evidence rule_checks is empty")
        return errors
    
    # Required policy rules (from policy_pack.yaml)
    required_rules = [
        "determinism_required",
        "evidence_required",
        "lineage_required",
        "validation_required",
        "immutability_required",
        "playability_required",
        "root_ingest_binding_required",
    ]
    
    # Build map of rule checks
    rule_check_map = {check.get("rule_id"): check for check in rule_checks}
    
    # Verify all required rules are present
    for rule_id in required_rules:
        if rule_id not in rule_check_map:
            errors.append(
                f"Required policy rule check missing: {rule_id}"
            )
            continue
        
        check = rule_check_map[rule_id]
        
        # Verify check structure
        if "passed" not in check:
            errors.append(
                f"Policy rule check {rule_id} missing 'passed' field"
            )
            continue
        
        # Verify all rules passed
        if check["passed"] != True:
            reason_code = check.get("reason_code", "Unknown reason")
            errors.append(
                f"Policy rule {rule_id} failed. Reason: {reason_code}"
            )
        
        # If failed, reason_code must be present
        if check.get("passed") == False:
            if "reason_code" not in check or not check["reason_code"]:
                errors.append(
                    f"Policy rule check {rule_id} failed but missing reason_code"
                )
    
    return errors

