# SPDX-License-Identifier: MIT
"""Deterministic execution engine."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from engine.core.dag import DAG
from engine.core.node import Node, NodeInput, NodeOutput
from engine.core.context import ExecutionContext
from engine.core.errors import ExecutionError, DeterminismError, IngestError
from engine.evidence.recorder import EvidenceRecorder
from engine.util.time import utc_now, to_iso8601
from engine.util.fs import content_hash, ensure_dir
from engine.util.json import canonical_json
from engine.evidence.hash import compute_sha256
import inspect
import json
from pathlib import Path


class Engine:
    """
    Deterministic execution engine.
    
    Executes DAG-based workflows as pure, deterministic functions.
    All transformations are content-addressed and evidence is recorded.
    """
    
    def __init__(self, context: ExecutionContext, ingest_manifest: Optional[Dict[str, Any]] = None):
        self.context = context
        # Pass execution context's started_at for deterministic timestamps
        self.recorder = EvidenceRecorder(
            context.evidence_dir,
            base_time=context.started_at,
        )
        self._outputs: Dict[str, NodeOutput] = {}
        self._execution_order: List[str] = []
        # Load ingest manifest from context metadata or provided parameter
        self.ingest_manifest = ingest_manifest or context.metadata.get("ingest_manifest")
        if self.ingest_manifest is None:
            # Try to load from workspace if path provided
            ingest_path = context.metadata.get("ingest_manifest_path")
            if ingest_path:
                ingest_path = Path(ingest_path)
                if ingest_path.exists():
                    with open(ingest_path, "r") as f:
                        self.ingest_manifest = json.load(f)
                else:
                    raise IngestError(f"Ingest manifest not found at {ingest_path}")
    
    def execute(self, dag: DAG) -> Dict[str, NodeOutput]:
        """
        Execute DAG workflow.
        
        Args:
            dag: DAG to execute
            
        Returns:
            Dictionary mapping node IDs to outputs
            
        Raises:
            ExecutionError: If execution fails
            DeterminismError: If determinism is violated
        """
        dag.validate()
        execution_order = dag.topological_sort()
        self._execution_order = execution_order
        self._outputs = {}
        
        # Record execution start
        self.recorder.record_execution_start(
            execution_id=self.context.execution_id,
            dag_id=dag.dag_id,
            node_order=execution_order,
        )
        
        try:
            for node_id in execution_order:
                node = dag.nodes[node_id]
                dependencies = dag.get_dependencies(node_id)
                
                # Collect inputs from dependencies
                inputs = self._collect_inputs(node_id, dependencies, dag)
                
                # Execute node
                output = self._execute_node(node, inputs)
                
                # Store output
                self._outputs[node_id] = output
                
                # Record evidence
                self.recorder.record_node_execution(
                    node_id=node_id,
                    node_type=node.node_type,
                    inputs=[inp.content_address for inp in inputs],
                    output=output.content_address,
                    evidence=output.evidence,
                )
            
            # Record execution completion
            self.recorder.record_execution_complete(
                execution_id=self.context.execution_id,
                outputs={node_id: out.content_address for node_id, out in self._outputs.items()},
            )
            
            return self._outputs.copy()
        
        except Exception as e:
            self.recorder.record_execution_failure(
                execution_id=self.context.execution_id,
                error=str(e),
            )
            raise ExecutionError(f"Execution failed: {e}") from e
    
    def _collect_inputs(
        self,
        node_id: str,
        dependencies: List[str],
        dag: DAG,
    ) -> List[NodeInput]:
        """
        Collect inputs for a node from its dependencies or ingest manifest.
        
        For root nodes (no dependencies), inputs MUST come from ingest manifest.
        Absence of ingest binding causes immediate fatal abort.
        
        Args:
            node_id: Node identifier
            dependencies: List of dependency node IDs
            dag: DAG definition
            
        Returns:
            List of NodeInput objects
            
        Raises:
            IngestError: If root node has no ingest binding
            ExecutionError: If dependency output not found
        """
        inputs: List[NodeInput] = []
        
        if not dependencies:
            # Root node - inputs MUST come from ingest manifest
            if self.ingest_manifest is None:
                raise IngestError(
                    f"Root node {node_id} requires ingest manifest, but none provided. "
                    "Execution cannot proceed with unresolved root inputs."
                )
            
            # Get node to determine required input roles
            node = dag.nodes[node_id]
            
            # Determine required roles from node config or metadata
            # Node config should specify 'required_input_roles' or similar
            required_roles = node.config.get("required_input_roles", [])
            
            # If no explicit roles in config, try to infer from node type or metadata
            # But this is a fallback - prefer explicit declaration
            if not required_roles:
                # Try metadata
                required_roles = node.config.get("metadata", {}).get("input_roles", [])
            
            # If still no roles, check if node has a default role expectation
            # This is the minimal case - single input with role matching node_id or node_type
            if not required_roles:
                # Last resort: use node_id as role (for simple cases)
                # This is acceptable only if explicitly documented
                required_roles = [node_id]
            
            # Bind each required role to ingest assets
            for role in required_roles:
                matching_assets = [
                    asset for asset in self.ingest_manifest.get("assets", [])
                    if asset.get("role") == role
                ]
                
                if not matching_assets:
                    raise IngestError(
                        f"Root node {node_id} requires input with role '{role}', "
                        f"but no matching asset found in ingest manifest. "
                        f"Execution cannot proceed with unresolved root inputs."
                    )
                
                # Create NodeInput for each matching asset
                for asset in matching_assets:
                    # Construct content address from hash
                    content_address = f"{asset['content_hash']}"
                    
                    # Create NodeInput with content-addressed reference
                    # Path is optional for content-addressed inputs (can be resolved later)
                    inputs.append(NodeInput(
                        content_address=content_address,
                        path=Path(),  # Empty path - content is addressed by hash
                        metadata={
                            **asset.get("metadata", {}),
                            "asset_id": asset["asset_id"],
                            "role": asset["role"],
                            "hash_algorithm": asset["hash_algorithm"],
                        },
                    ))
            
            # Verify we have at least one input
            if not inputs:
                raise IngestError(
                    f"Root node {node_id} has no bound inputs from ingest manifest. "
                    f"Required roles: {required_roles}. "
                    "Execution cannot proceed with unresolved root inputs."
                )
        else:
            # Collect outputs from dependencies
            for dep_id in dependencies:
                if dep_id not in self._outputs:
                    raise ExecutionError(
                        f"Node {node_id} depends on {dep_id} but output not found"
                    )
                dep_output = self._outputs[dep_id]
                inputs.append(NodeInput(
                    content_address=dep_output.content_address,
                    path=dep_output.path,
                    metadata=dep_output.metadata,
                ))
        
        return inputs
    
    def _execute_node(self, node: Node, inputs: List[NodeInput]) -> NodeOutput:
        """
        Deterministic execution with mechanical enforcement.
        Any mismatch aborts execution.
        
        Args:
            node: Node to execute
            inputs: Node inputs
            
        Returns:
            Node output
            
        Raises:
            ExecutionError: If execution fails
            DeterminismError: If determinism is violated
        """
        # 1. Validate inputs
        if not node.validate_inputs(inputs):
            raise ExecutionError(f"Node {node.node_id} input validation failed")

        # 2. Canonicalize inputs
        inputs_canonical = canonical_json([
            {
                "content_address": i.content_address,
                "metadata": i.metadata,
            }
            for i in inputs
        ])

        # 3. Hash node code
        try:
            node_source = inspect.getsource(node.__class__)
        except OSError as e:
            # If source unavailable, execution must abort
            # No fallback - code identity cannot be proven
            raise DeterminismError(
                f"Cannot extract source for node {node.node_id}. "
                "Node code identity cannot be proven."
            ) from e
        node_code_hash = compute_sha256(node_source.encode("utf-8"))

        # 4. Canonicalize execution context
        context_canonical = canonical_json({
            "execution_id": self.context.execution_id,
            "workspace": str(self.context.workspace),
            "policy_rules": self.context.policy_rules,
            "config": self.context.config,
            "metadata": self.context.metadata,
            "started_at": to_iso8601(self.context.started_at),
        })
        context_hash = compute_sha256(context_canonical.encode("utf-8"))

        # 5. Execute twice
        output_1 = node.execute(inputs, self.context)
        
        # 5a. Re-verify inputs were not mutated after first execution
        inputs_canonical_after_1 = canonical_json([
            {
                "content_address": i.content_address,
                "metadata": i.metadata,
            }
            for i in inputs
        ])
        if inputs_canonical != inputs_canonical_after_1:
            raise DeterminismError(
                f"Node {node.node_id} mutated its inputs after first execution"
            )
        
        output_2 = node.execute(inputs, self.context)
        
        # 5b. Re-verify inputs were not mutated after second execution
        inputs_canonical_after_2 = canonical_json([
            {
                "content_address": i.content_address,
                "metadata": i.metadata,
            }
            for i in inputs
        ])
        if inputs_canonical != inputs_canonical_after_2:
            raise DeterminismError(
                f"Node {node.node_id} mutated its inputs after second execution"
            )

        # 6. Compare outputs (canonical) - BEFORE adding determinism_proof
        # Extract evidence without determinism_proof for comparison
        evidence_1 = {k: v for k, v in output_1.evidence.items() if k != "determinism_proof"}
        evidence_2 = {k: v for k, v in output_2.evidence.items() if k != "determinism_proof"}
        
        out_1 = canonical_json({
            "content_address": output_1.content_address,
            "metadata": output_1.metadata,
            "evidence": evidence_1,
        })
        out_2 = canonical_json({
            "content_address": output_2.content_address,
            "metadata": output_2.metadata,
            "evidence": evidence_2,
        })

        if out_1 != out_2:
            raise DeterminismError(
                f"Node {node.node_id} is non-deterministic: outputs differ"
            )

        # 7. Compare file existence and bytes
        exists_1 = output_1.path and output_1.path.exists()
        exists_2 = output_2.path and output_2.path.exists()
        
        if exists_1 != exists_2:
            raise DeterminismError(
                f"Node {node.node_id} output existence differs: exists_1={exists_1}, exists_2={exists_2}"
            )
        
        # Only hash contents if both files exist
        if exists_1 and exists_2:
            h1 = content_hash(output_1.path)
            h2 = content_hash(output_2.path)
            if h1 != h2:
                raise DeterminismError(
                    f"Node {node.node_id} output bytes differ: hash1={h1}, hash2={h2}"
                )

        # 8. Emit determinism proof (add to output_1 which we return)
        output_1.evidence["determinism_proof"] = {
            "verified": True,
            "method": "double_execution",
            "node_code_hash": node_code_hash,
            "context_hash": context_hash,
            "inputs_hash": compute_sha256(inputs_canonical.encode("utf-8")),
            "outputs_hash": compute_sha256(out_1.encode("utf-8")),
            "executions": 2,
        }

        return output_1
    
    def get_lineage(self) -> Dict[str, Any]:
        """Get full lineage DAG from execution."""
        return {
            "execution_id": self.context.execution_id,
            "execution_order": self._execution_order,
            "outputs": {
                node_id: {
                    "content_address": out.content_address,
                    "metadata": out.metadata,
                }
                for node_id, out in self._outputs.items()
            },
        }

