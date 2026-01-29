# SPDX-License-Identifier: MIT
"""Policy enforcement - law, not preference."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from engine.core.errors import PolicyError
from engine.evidence.recorder import EvidenceRecorder


class Policy:
    """
    Policy enforcement system.
    
    Policy is law. Configuration cannot override rules.
    """
    
    def __init__(
        self,
        rules_file: Optional[Path] = None,
        states_file: Optional[Path] = None,
    ):
        self.rules: List[Dict[str, Any]] = []
        self.states: List[Dict[str, Any]] = []
        self.transition_rules: List[Dict[str, Any]] = []
        
        if rules_file and rules_file.exists():
            self._load_rules(rules_file)
        if states_file and states_file.exists():
            self._load_states(states_file)
    
    def _load_rules(self, rules_file: Path) -> None:
        """Load policy rules from YAML."""
        with open(rules_file, "r") as f:
            data = yaml.safe_load(f)
            self.rules = data.get("rules", [])
    
    def _load_states(self, states_file: Path) -> None:
        """Load state definitions from YAML."""
        with open(states_file, "r") as f:
            data = yaml.safe_load(f)
            self.states = data.get("states", [])
            self.transition_rules = data.get("transition_rules", [])
    
    def check_rules(
        self,
        evidence: List[Dict[str, Any]],
        recorder: EvidenceRecorder,
        lineage_dag: Optional[Dict[str, Any]] = None,
        ingest_manifest: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check all policy rules against evidence.
        
        Args:
            evidence: List of evidence events
            recorder: Evidence recorder for logging
            lineage_dag: Lineage DAG structure (for lineage checks)
            ingest_manifest: Ingest manifest (for lineage checks)
            
        Returns:
            Dictionary mapping rule IDs to check results with:
            - passed: bool
            - reason_code: str (if failed)
            - details: Dict[str, Any]
            
        Raises:
            PolicyError: If strict enforcement and rule fails
        """
        results: Dict[str, Dict[str, Any]] = {}
        
        for rule in self.rules:
            rule_id = rule["id"]
            
            try:
                passed = self._check_rule(rule, evidence, lineage_dag, ingest_manifest)
                # reason_code is required when passed == False
                reason_code = None if passed else f"RULE_CHECK_FAILED: {rule_id}"
            except PolicyError as e:
                passed = False
                reason_code = f"POLICY_CHECK_ERROR: {str(e)}"
            
            result = {
                "passed": passed,
                "reason_code": reason_code,
                "details": {
                    "rule_id": rule_id,
                    "rule_name": rule.get("name"),
                    "rule_type": rule.get("type"),
                },
            }
            
            results[rule_id] = result
            
            # Record full policy check payload (including reason_code)
            # Evidence must be the product, not a derived artifact
            recorder.record_policy_check(
                rule_id=rule_id,
                passed=passed,
                reason_code=reason_code,
                details=result["details"],
            )
            
            if not passed and rule.get("severity") == "error":
                if self._is_strict():
                    raise PolicyError(
                        f"Policy rule {rule_id} failed: {rule.get('name')}. "
                        f"Reason: {reason_code or 'Rule check returned False'}"
                    )
        
        return results
    
    def _check_rule(
        self,
        rule: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        lineage_dag: Optional[Dict[str, Any]] = None,
        ingest_manifest: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check a single rule.
        
        Returns:
            True if rule passes, False if rule fails
            
        Raises:
            PolicyError: If rule type is unknown or unhandled
        """
        check_type = rule.get("type")
        rule_id = rule.get("id", "unknown")
        
        if not check_type:
            raise PolicyError(
                f"Policy rule {rule_id} missing 'type' field. "
                "Cannot determine check type."
            )
        
        if check_type == "evidence_check":
            return self._check_evidence(rule, evidence)
        elif check_type == "execution_check":
            return self._check_execution(rule, evidence)
        elif check_type == "lineage_check":
            return self._check_lineage(rule, evidence, lineage_dag, ingest_manifest)
        elif check_type == "validation_check":
            return self._check_validation(rule, evidence)
        elif check_type == "integrity_check":
            return self._check_integrity(rule, evidence)
        else:
            # Unknown check type - fatal error
            raise PolicyError(
                f"Policy rule {rule_id} has unknown check type: {check_type}. "
                "Valid types: evidence_check, execution_check, lineage_check, "
                "validation_check, integrity_check"
            )
    
    def _check_evidence(self, rule: Dict[str, Any], evidence: List[Dict[str, Any]]) -> bool:
        """Check evidence-based rule."""
        evidence_type = rule.get("evidence_type")
        condition = rule.get("condition")
        
        relevant_events = [
            e for e in evidence
            if e.get("event_type") == evidence_type
        ]
        
        if not relevant_events:
            return False
        
        if condition:
            # Evaluate condition (simplified)
            return all(self._evaluate_condition(e, condition) for e in relevant_events)
        
        return len(relevant_events) > 0
    
    def _check_execution(self, rule: Dict[str, Any], evidence: List[Dict[str, Any]]) -> bool:
        """
        Check execution-based rule.
        
        Returns:
            True if rule passes, False if rule fails
            
        Raises:
            PolicyError: If check name is unknown or unhandled
        """
        check_name = rule.get("check")
        rule_id = rule.get("id", "unknown")
        
        if not check_name:
            raise PolicyError(
                f"Policy rule {rule_id} (execution_check) missing 'check' field. "
                "Cannot determine check name."
            )
        
        if check_name == "deterministic_execution":
            # Check for execution_complete events
            complete_events = [
                e for e in evidence
                if e.get("event_type") == "execution_complete"
            ]
            
            if len(complete_events) == 0:
                return False
            
            # Verify all node executions have determinism proofs
            node_executions = [
                e for e in evidence
                if e.get("event_type") == "node_execution"
            ]
            
            for event in node_executions:
                evidence_data = event.get("evidence", {})
                determinism_proof = evidence_data.get("determinism_proof")
                
                if not determinism_proof:
                    return False
                
                if determinism_proof.get("verified") != True:
                    return False
                
                if determinism_proof.get("method") != "double_execution":
                    return False
                
                if determinism_proof.get("executions") != 2:
                    return False
            
            return True
        else:
            # Unknown check name - fatal error
            raise PolicyError(
                f"Policy rule {rule_id} (execution_check) has unknown check name: {check_name}. "
                "Valid names: deterministic_execution"
            )
    
    def _check_lineage(
        self,
        rule: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        lineage_dag: Optional[Dict[str, Any]] = None,
        ingest_manifest: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check lineage-based rule using mechanical graph proof.
        
        Returns:
            True if lineage is complete, False otherwise
            
        Raises:
            PolicyError: If required data is missing or lineage check cannot be performed
        """
        check_name = rule.get("check")
        rule_id = rule.get("id", "unknown")
        
        if not check_name:
            raise PolicyError(
                f"Policy rule {rule_id} (lineage_check) missing 'check' field. "
                "Cannot determine check name."
            )
        
        if check_name == "lineage_complete":
            # Require lineage_dag and ingest_manifest for mechanical check
            if lineage_dag is None:
                raise PolicyError(
                    f"Policy rule {rule_id} (lineage_check) requires lineage_dag, "
                    "but none provided. Cannot perform mechanical lineage check."
                )
            
            if ingest_manifest is None:
                raise PolicyError(
                    f"Policy rule {rule_id} (lineage_check) requires ingest_manifest, "
                    "but none provided. Cannot perform mechanical lineage check."
                )
            
            # Mechanical lineage completeness check
            # Use algorithms from LINEAGE_COMPLETENESS_POLICY.md
            
            # Check 1: Ingest traceability
            if not self._verify_ingest_traceability(lineage_dag, ingest_manifest):
                return False
            
            # Check 2: No orphan nodes
            if not self._verify_no_orphan_nodes(lineage_dag, ingest_manifest):
                return False
            
            # Check 3: No cycles
            if not self._verify_no_cycles(lineage_dag):
                return False
            
            # Check 4: No skipped transformations
            if not self._verify_no_skipped_transformations(lineage_dag, evidence):
                return False
            
            # Check 5: Complete dependency graph
            if not self._verify_complete_dependency_graph(lineage_dag):
                return False
            
            # Check 6: Input-output consistency
            if not self._verify_input_output_consistency(lineage_dag):
                return False
            
            return True
        elif check_name == "root_ingest_binding":
            # Require lineage_dag and ingest_manifest for mechanical check
            if lineage_dag is None:
                raise PolicyError(
                    f"Policy rule {rule_id} (lineage_check) requires lineage_dag, "
                    "but none provided. Cannot perform root ingest binding check."
                )
            
            if ingest_manifest is None:
                raise PolicyError(
                    f"Policy rule {rule_id} (lineage_check) requires ingest_manifest, "
                    "but none provided. Cannot perform root ingest binding check."
                )
            
            # Mechanical root ingest binding check
            # All root nodes must have ingest-bound inputs
            # All ingest assets must be used
            # All DAG inputs must be traceable
            
            # Check 1: All root nodes have ingest-bound inputs
            if not self._verify_root_nodes_have_ingest_inputs(lineage_dag, ingest_manifest):
                return False
            
            # Check 2: All ingest assets are used
            if not self._verify_all_ingest_assets_used(lineage_dag, ingest_manifest):
                return False
            
            # Check 3: All DAG inputs are traceable (covered by _verify_ingest_traceability)
            if not self._verify_ingest_traceability(lineage_dag, ingest_manifest):
                return False
            
            return True
        else:
            # Unknown check name - fatal error
            raise PolicyError(
                f"Policy rule {rule_id} (lineage_check) has unknown check name: {check_name}. "
                "Valid names: lineage_complete, root_ingest_binding"
            )
    
    def _extract_hash(self, content_address: str) -> str:
        """Extract hash from content address."""
        parts = content_address.split('.')
        hash_part = parts[0]
        return hash_part
    
    def _find_node(self, node_id: str, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find node by ID in nodes list."""
        for node in nodes:
            if node.get("id") == node_id:
                return node
        return None
    
    def _verify_ingest_traceability(
        self,
        lineage_dag: Dict[str, Any],
        ingest_manifest: Dict[str, Any],
    ) -> bool:
        """Verify every output traces back to ingest."""
        # Build traceability map
        traceable_hashes = set()
        
        # Add all ingest asset hashes
        for asset in ingest_manifest.get("assets", []):
            content_hash = asset.get("content_hash") or asset.get("hash")
            if content_hash:
                traceable_hashes.add(content_hash)
        
        # Build node output map
        node_outputs = {}
        for node in lineage_dag.get("nodes", []):
            node_id = node.get("id")
            if "output" in node and "content_address" in node["output"]:
                output_hash = self._extract_hash(node["output"]["content_address"])
                node_outputs[node_id] = output_hash
                traceable_hashes.add(output_hash)
        
        # Verify all node inputs are traceable
        for node in lineage_dag.get("nodes", []):
            if "inputs" in node:
                for input_item in node["inputs"]:
                    input_hash = self._extract_hash(input_item.get("content_address", ""))
                    if input_hash and input_hash not in traceable_hashes:
                        return False
        
        # Verify all outputs are reachable from ingest
        reachable_from_ingest = set()
        for asset in ingest_manifest.get("assets", []):
            content_hash = asset.get("content_hash") or asset.get("hash")
            if content_hash:
                reachable_from_ingest.add(content_hash)
        
        # Propagate through DAG
        changed = True
        while changed:
            changed = False
            for node in lineage_dag.get("nodes", []):
                node_id = node.get("id")
                
                if "inputs" in node:
                    all_inputs_reachable = True
                    for input_item in node["inputs"]:
                        input_hash = self._extract_hash(input_item.get("content_address", ""))
                        if input_hash and input_hash not in reachable_from_ingest:
                            all_inputs_reachable = False
                            break
                    
                    if all_inputs_reachable and node_id in node_outputs:
                        output_hash = node_outputs[node_id]
                        if output_hash not in reachable_from_ingest:
                            reachable_from_ingest.add(output_hash)
                            changed = True
        
        # Check all outputs are reachable
        for node_id, output_hash in node_outputs.items():
            if output_hash not in reachable_from_ingest:
                return False
        
        return True
    
    def _verify_no_orphan_nodes(
        self,
        lineage_dag: Dict[str, Any],
        ingest_manifest: Dict[str, Any],
    ) -> bool:
        """Verify no orphan nodes exist."""
        # Build dependency map
        dependencies = {}
        for edge in lineage_dag.get("edges", []):
            target = edge.get("target")
            source = edge.get("source")
            if target not in dependencies:
                dependencies[target] = []
            dependencies[target].append(source)
        
        # Identify root nodes
        root_nodes = set()
        for node in lineage_dag.get("nodes", []):
            node_id = node.get("id")
            if node_id not in dependencies:
                root_nodes.add(node_id)
        
        # Verify root nodes have ingest-bound inputs
        ingest_asset_hashes = set()
        for asset in ingest_manifest.get("assets", []):
            content_hash = asset.get("content_hash") or asset.get("hash")
            if content_hash:
                ingest_asset_hashes.add(content_hash)
        
        for root_node_id in root_nodes:
            root_node = self._find_node(root_node_id, lineage_dag.get("nodes", []))
            if root_node and "inputs" in root_node:
                has_ingest_input = False
                for input_item in root_node["inputs"]:
                    input_hash = self._extract_hash(input_item.get("content_address", ""))
                    if input_hash in ingest_asset_hashes:
                        has_ingest_input = True
                        break
                if not has_ingest_input:
                    return False
        
        # Verify all nodes are reachable from roots
        reachable_from_roots = set(root_nodes)
        dependents = {}
        for edge in lineage_dag.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if source not in dependents:
                dependents[source] = []
            dependents[source].append(target)
        
        changed = True
        while changed:
            changed = False
            for node_id in list(reachable_from_roots):
                if node_id in dependents:
                    for dependent_id in dependents[node_id]:
                        if dependent_id not in reachable_from_roots:
                            reachable_from_roots.add(dependent_id)
                            changed = True
        
        all_node_ids = {node.get("id") for node in lineage_dag.get("nodes", [])}
        unreachable_nodes = all_node_ids - reachable_from_roots
        
        return len(unreachable_nodes) == 0
    
    def _verify_no_cycles(self, lineage_dag: Dict[str, Any]) -> bool:
        """Verify DAG contains no cycles using topological sort."""
        # Build dependency map
        dependencies = {}
        for edge in lineage_dag.get("edges", []):
            target = edge.get("target")
            if target not in dependencies:
                dependencies[target] = []
            dependencies[target].append(edge.get("source"))
        
        # Initialize in-degree map
        in_degree = {node.get("id"): 0 for node in lineage_dag.get("nodes", [])}
        for edge in lineage_dag.get("edges", []):
            in_degree[edge.get("target")] += 1
        
        # Topological sort (Kahn's algorithm)
        from collections import deque
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for edge in lineage_dag.get("edges", []):
                if edge.get("source") == node_id:
                    target = edge.get("target")
                    in_degree[target] -= 1
                    if in_degree[target] == 0:
                        queue.append(target)
        
        # If result length != total nodes, cycle exists
        return len(result) == len(lineage_dag.get("nodes", []))
    
    def _verify_no_skipped_transformations(
        self,
        lineage_dag: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> bool:
        """Verify no transformations are skipped."""
        # Build node output map from DAG
        dag_outputs = {}
        for node in lineage_dag.get("nodes", []):
            node_id = node.get("id")
            if "output" in node and "content_address" in node["output"]:
                output_hash = self._extract_hash(node["output"]["content_address"])
                dag_outputs[output_hash] = node_id
        
        # Build node output map from evidence
        evidence_outputs = {}
        for event in evidence:
            if event.get("event_type") == "node_execution":
                node_id = event.get("node_id")
                evidence_data = event.get("evidence", {})
                if "output" in evidence_data and "content_address" in evidence_data["output"]:
                    output_hash = self._extract_hash(evidence_data["output"]["content_address"])
                    evidence_outputs[output_hash] = node_id
        
        # Verify all evidence outputs are in DAG
        for output_hash, evidence_node_id in evidence_outputs.items():
            if output_hash not in dag_outputs:
                return False
            if dag_outputs[output_hash] != evidence_node_id:
                return False
        
        # Verify all DAG outputs have evidence
        for output_hash, dag_node_id in dag_outputs.items():
            if output_hash not in evidence_outputs:
                return False
            if evidence_outputs[output_hash] != dag_node_id:
                return False
        
        return True
    
    def _verify_complete_dependency_graph(self, lineage_dag: Dict[str, Any]) -> bool:
        """Verify dependency graph is complete."""
        node_ids = {node.get("id") for node in lineage_dag.get("nodes", [])}
        
        # Verify all edges reference existing nodes
        for edge in lineage_dag.get("edges", []):
            if edge.get("source") not in node_ids:
                return False
            if edge.get("target") not in node_ids:
                return False
        
        # Verify execution_order if present
        execution_order = lineage_dag.get("execution_order", [])
        if execution_order:
            if set(execution_order) != node_ids:
                return False
            
            # Verify execution_order respects dependencies
            node_positions = {node_id: i for i, node_id in enumerate(execution_order)}
            dependencies = {}
            for edge in lineage_dag.get("edges", []):
                target = edge.get("target")
                if target not in dependencies:
                    dependencies[target] = []
                dependencies[target].append(edge.get("source"))
            
            for edge in lineage_dag.get("edges", []):
                source_pos = node_positions.get(edge.get("source"))
                target_pos = node_positions.get(edge.get("target"))
                if source_pos is not None and target_pos is not None:
                    if source_pos >= target_pos:
                        return False
        
        return True
    
    def _verify_input_output_consistency(self, lineage_dag: Dict[str, Any]) -> bool:
        """Verify input-output consistency for all nodes."""
        # Build dependency map
        dependencies = {}
        for edge in lineage_dag.get("edges", []):
            target = edge.get("target")
            if target not in dependencies:
                dependencies[target] = []
            dependencies[target].append(edge.get("source"))
        
        # Verify each node
        for node in lineage_dag.get("nodes", []):
            node_id = node.get("id")
            
            # Count declared inputs
            declared_input_count = len(node.get("inputs", []))
            
            # Count dependencies
            dependency_count = len(dependencies.get(node_id, []))
            
            # Verify consistency
            if declared_input_count != dependency_count:
                return False
            
            # Verify all inputs have content_address
            for input_item in node.get("inputs", []):
                if "content_address" not in input_item:
                    return False
            
            # Verify output is produced
            if "output" not in node:
                return False
            if "content_address" not in node["output"]:
                return False
        
        return True
    
    def _check_validation(self, rule: Dict[str, Any], evidence: List[Dict[str, Any]]) -> bool:
        """Check validation-based rule."""
        validation_events = [
            e for e in evidence
            if e.get("event_type") == "validation"
        ]
        
        if not validation_events:
            return False
        
        # Check all validations passed
        return all(e.get("passed", False) for e in validation_events)
    
    def _check_integrity(self, rule: Dict[str, Any], evidence: List[Dict[str, Any]]) -> bool:
        """
        Check integrity-based rule.
        
        Returns:
            True if integrity check passes, False otherwise
            
        Raises:
            PolicyError: If check name is unknown or unhandled
        """
        check_name = rule.get("check")
        rule_id = rule.get("id", "unknown")
        
        if not check_name:
            raise PolicyError(
                f"Policy rule {rule_id} (integrity_check) missing 'check' field. "
                "Cannot determine check name."
            )
        
        if check_name == "mtb_sealed":
            # Check for integrity_proof in evidence
            # Integrity proof should be in MTB, not evidence events
            # For now, verify that evidence events have integrity proofs
            
            # Check all evidence events have integrity_proof
            for event in evidence:
                if "integrity_proof" not in event:
                    return False
                
                integrity_proof = event.get("integrity_proof", {})
                
                if "hash" not in integrity_proof:
                    return False
                
                if "algorithm" not in integrity_proof:
                    return False
                
                if integrity_proof.get("algorithm") != "sha256":
                    return False
            
            return True
        else:
            # Unknown check name - fatal error
            raise PolicyError(
                f"Policy rule {rule_id} (integrity_check) has unknown check name: {check_name}. "
                "Valid names: mtb_sealed"
            )
    
    def _evaluate_condition(self, event: Dict[str, Any], condition: str) -> bool:
        """
        Evaluate condition string.
        
        Supported operators:
        - == (equality)
        - != (inequality)
        - > (greater than, numeric)
        - < (less than, numeric)
        - >= (greater than or equal, numeric)
        - <= (less than or equal, numeric)
        - in (membership)
        - not in (non-membership)
        
        Returns:
            True if condition evaluates to true, False otherwise
            
        Raises:
            PolicyError: If condition is malformed or operator is unknown
        """
        if not condition or not condition.strip():
            raise PolicyError(
                f"Empty or invalid condition string: '{condition}'"
            )
        
        condition = condition.strip()
        
        # Operator table (ordered by precedence - longest first)
        operators = [
            ("!=", "ne"),
            ("==", "eq"),
            (">=", "ge"),
            ("<=", "le"),
            (">", "gt"),
            ("<", "lt"),
            (" not in ", "not_in"),
            (" in ", "in"),
        ]
        
        # Try each operator
        for op_str, op_name in operators:
            if op_str in condition:
                parts = condition.split(op_str, 1)
                if len(parts) != 2:
                    raise PolicyError(
                        f"Malformed condition: '{condition}'. "
                        f"Operator '{op_str}' found but condition is invalid."
                    )
                
                key = parts[0].strip()
                value_str = parts[1].strip()
                
                # Get event value
                event_value = event.get(key)
                
                if op_name == "eq":
                    return str(event_value) == value_str
                elif op_name == "ne":
                    return str(event_value) != value_str
                elif op_name in ["gt", "ge", "lt", "le"]:
                    # Numeric comparison
                    try:
                        event_num = float(event_value) if event_value is not None else 0.0
                        value_num = float(value_str)
                        
                        if op_name == "gt":
                            return event_num > value_num
                        elif op_name == "ge":
                            return event_num >= value_num
                        elif op_name == "lt":
                            return event_num < value_num
                        elif op_name == "le":
                            return event_num <= value_num
                    except (ValueError, TypeError):
                        raise PolicyError(
                            f"Numeric comparison failed in condition: '{condition}'. "
                            f"Event value '{event_value}' or condition value '{value_str}' "
                            "cannot be converted to number."
                        )
                elif op_name == "in":
                    # Membership check (value_str should be a list or string)
                    try:
                        # Try to parse as list
                        import json
                        value_list = json.loads(value_str)
                        if isinstance(value_list, list):
                            return event_value in value_list
                        else:
                            # Treat as string membership
                            return str(event_value) in value_str
                    except (json.JSONDecodeError, TypeError):
                        # Treat as string membership
                        return str(event_value) in value_str
                elif op_name == "not_in":
                    # Non-membership check
                    try:
                        import json
                        value_list = json.loads(value_str)
                        if isinstance(value_list, list):
                            return event_value not in value_list
                        else:
                            return str(event_value) not in value_str
                    except (json.JSONDecodeError, TypeError):
                        return str(event_value) not in value_str
        
        # No operator found - fatal error
        raise PolicyError(
            f"Unknown or unsupported operator in condition: '{condition}'. "
            f"Supported operators: ==, !=, >, <, >=, <=, in, not in"
        )
    
    def _is_strict(self) -> bool:
        """Check if strict enforcement is enabled."""
        return True  # Always strict - policy is law
    
    def can_transition(
        self,
        from_state: str,
        to_state: str,
        evidence: List[Dict[str, Any]],
    ) -> bool:
        """
        Check if state transition is allowed.
        
        Args:
            from_state: Current state
            to_state: Target state
            evidence: Evidence events
            
        Returns:
            True if transition is allowed
        """
        # Find state definition
        state_def = next(
            (s for s in self.states if s["id"] == from_state),
            None
        )
        
        if not state_def:
            return False
        
        # Find transition
        transition = next(
            (t for t in state_def.get("transitions", []) if t["to"] == to_state),
            None
        )
        
        if not transition:
            return False
        
        # Check requirements
        requires = transition.get("requires", [])
        for req_name in requires:
            req_rule = next(
                (r for r in self.transition_rules if r["name"] == req_name),
                None
            )
            
            if not req_rule:
                return False
            
            if not self._check_rule(req_rule, evidence):
                return False
        
        return True

