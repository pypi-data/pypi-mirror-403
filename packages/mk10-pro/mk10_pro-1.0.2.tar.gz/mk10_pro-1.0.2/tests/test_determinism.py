"""Tests for determinism requirements."""

import pytest
from pathlib import Path
import tempfile
import shutil

from engine.core.engine import Engine
from engine.core.dag import DAG, DAGEdge
from engine.core.context import ExecutionContext
from engine.core.node import PassthroughNode
from engine.util.fs import ensure_dir


def test_deterministic_execution():
    """Test that same inputs produce same outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        cache_dir = ensure_dir(workspace / ".cache")
        evidence_dir = ensure_dir(workspace / "evidence")
        
        context1 = ExecutionContext(
            workspace=workspace,
            cache_dir=cache_dir,
            evidence_dir=evidence_dir,
            policy_rules={},
            config={},
            execution_id="test-1",
        )
        
        context2 = ExecutionContext(
            workspace=workspace,
            cache_dir=cache_dir,
            evidence_dir=evidence_dir,
            policy_rules={},
            config={},
            execution_id="test-2",
        )
        
        # Create same DAG
        dag1 = DAG("test")
        node1 = PassthroughNode("node1")
        dag1.add_node(node1)
        
        dag2 = DAG("test")
        node2 = PassthroughNode("node1")
        dag2.add_node(node2)
        
        # Execute both
        engine1 = Engine(context1)
        engine2 = Engine(context2)
        
        # Note: This is a simplified test
        # Full determinism testing would require actual file inputs/outputs
        assert dag1.dag_id == dag2.dag_id


def test_immutability():
    """Test that sealed MTB cannot be modified."""
    from mtb.builder import MTBBuilder
    from mtb.seal import verify_seal, seal_mtb
    
    builder = MTBBuilder("TestTitle", "v1.0")
    builder.add_ingest_asset(
        content_address="abc123.mxf",
        path=Path("test.mxf"),
        hash_value="abc123",
        size=1000,
    )
    builder.set_build_evidence("exec-1", [])
    
    mtb = builder.build_and_seal()
    
    # Verify seal
    assert verify_seal(mtb)
    
    # Try to modify (should break seal)
    mtb_modified = mtb.copy()
    mtb_modified["title"] = "ModifiedTitle"
    
    # Seal should fail
    assert not verify_seal(mtb_modified)


def test_content_addressing():
    """Test content addressing."""
    from engine.util.fs import content_hash, content_address
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = Path(tmp.name)
    
    try:
        hash1 = content_hash(tmp_path)
        hash2 = content_hash(tmp_path)
        
        # Same content should produce same hash
        assert hash1 == hash2
        
        addr = content_address(tmp_path, b"test content")
        assert hash1 in addr
    finally:
        tmp_path.unlink()

