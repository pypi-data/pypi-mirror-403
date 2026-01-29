# SPDX-License-Identifier: MIT
"""Execute command."""

import click
from pathlib import Path
import yaml
import hashlib

from engine.core.engine import Engine
from engine.core.dag import DAG, DAGEdge
from engine.core.context import ExecutionContext
from engine.core.node import PassthroughNode
from engine.evidence.recorder import EvidenceRecorder
from engine.policy.policy import Policy
from engine.util.fs import ensure_dir


@click.command()
@click.option("--dag", required=True, type=click.Path(exists=True), help="DAG definition file")
@click.option("--workspace", default=".workspace", help="Workspace directory")
@click.option("--config", default="mk10.config.yaml", help="Configuration file")
def execute(dag: str, workspace: str, config: str):
    """Execute mastering pipeline DAG."""
    dag_path = Path(dag)
    workspace_path = Path(workspace)
    config_path = Path(config)
    
    # Load configuration
    if config_path.exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
    else:
        config_data = {}
    
    # Setup workspace
    ensure_dir(workspace_path)
    cache_dir = ensure_dir(workspace_path / ".cache")
    evidence_dir = ensure_dir(workspace_path / "evidence")
    
    # Load DAG
    with open(dag_path, "r") as f:
        dag_data = yaml.safe_load(f)
    
    # Create DAG
    dag_obj = DAG(dag_id=dag_data.get("id", "default"))
    
    # Add nodes
    for node_def in dag_data.get("nodes", []):
        node = PassthroughNode(
            node_id=node_def["id"],
            config=node_def.get("config", {}),
        )
        dag_obj.add_node(node)
    
    # Add edges
    for edge_def in dag_data.get("edges", []):
        edge = DAGEdge(
            source=edge_def["source"],
            target=edge_def["target"],
            output_port=edge_def.get("output_port", "default"),
            input_port=edge_def.get("input_port", "default"),
        )
        dag_obj.add_edge(edge)
    
    # Create execution context with deterministic execution ID
    # Execution ID is hash of DAG content + workspace path for determinism
    dag_content = dag_path.read_bytes()
    workspace_str = str(workspace_path.resolve())
    execution_input = dag_content + workspace_str.encode('utf-8')
    execution_id = hashlib.sha256(execution_input).hexdigest()[:16]
    
    context = ExecutionContext(
        workspace=workspace_path,
        cache_dir=cache_dir,
        evidence_dir=evidence_dir,
        policy_rules={},
        config=config_data,
        execution_id=execution_id,
    )
    
    # Create engine
    engine = Engine(context)
    
    click.echo(f"Executing DAG: {dag_obj.dag_id}")
    click.echo(f"Execution ID: {execution_id}")
    
    try:
        # Execute
        outputs = engine.execute(dag_obj)
        
        click.echo(f"\nExecution complete: {len(outputs)} nodes executed")
        for node_id, output in outputs.items():
            click.echo(f"  {node_id}: {output.content_address}")
        
    except Exception as e:
        click.echo(f"Execution failed: {e}", err=True)
        raise click.Abort()

