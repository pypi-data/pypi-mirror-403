# SPDX-License-Identifier: MIT
"""Pure transformation nodes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

from engine.core.context import ExecutionContext
from engine.core.errors import ExecutionError


@dataclass
class NodeInput:
    """Input to a node."""
    content_address: str
    path: Path
    metadata: Dict[str, Any]


@dataclass
class NodeOutput:
    """Output from a node."""
    content_address: str
    path: Path
    metadata: Dict[str, Any]
    evidence: Dict[str, Any]


class Node(ABC):
    """
    Pure transformation node.
    
    Nodes are deterministic functions with no side effects.
    All inputs and outputs are content-addressed.
    """
    
    def __init__(self, node_id: str, node_type: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
    
    @abstractmethod
    def execute(
        self,
        inputs: List[NodeInput],
        context: ExecutionContext,
    ) -> NodeOutput:
        """
        Execute node transformation.
        
        Args:
            inputs: List of input assets
            context: Execution context
            
        Returns:
            Node output with evidence
            
        Raises:
            ExecutionError: If execution fails
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, inputs: List[NodeInput]) -> bool:
        """Validate inputs before execution."""
        pass
    
    def get_evidence(self, inputs: List[NodeInput], output: NodeOutput) -> Dict[str, Any]:
        """
        Generate execution evidence.
        
        Default implementation. Override for custom evidence.
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "inputs": [
                {
                    "content_address": inp.content_address,
                    "metadata": inp.metadata,
                }
                for inp in inputs
            ],
            "output": {
                "content_address": output.content_address,
                "metadata": output.metadata,
            },
            "config": self.config,
        }


class PassthroughNode(Node):
    """Node that passes through input unchanged (for testing)."""
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, "passthrough", config or {})
    
    def validate_inputs(self, inputs: List[NodeInput]) -> bool:
        return len(inputs) == 1
    
    def execute(
        self,
        inputs: List[NodeInput],
        context: ExecutionContext,
    ) -> NodeOutput:
        if not self.validate_inputs(inputs):
            raise ExecutionError(f"PassthroughNode requires exactly 1 input, got {len(inputs)}")
        
        inp = inputs[0]
        return NodeOutput(
            content_address=inp.content_address,
            path=inp.path,
            metadata=inp.metadata,
            evidence=self.get_evidence(inputs, NodeOutput(
                content_address=inp.content_address,
                path=inp.path,
                metadata=inp.metadata,
                evidence={},
            )),
        )

