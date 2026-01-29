# SPDX-License-Identifier: MIT
"""Directed Acyclic Graph definition and ordering."""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from collections import defaultdict, deque

from engine.core.errors import DAGError
from engine.core.node import Node


@dataclass
class DAGEdge:
    """Edge in the DAG."""
    source: str
    target: str
    output_port: str = "default"
    input_port: str = "default"


class DAG:
    """
    Directed Acyclic Graph for workflow definition.
    
    Nodes are transformations. Edges define dependencies.
    """
    
    def __init__(self, dag_id: str):
        self.dag_id = dag_id
        self.nodes: Dict[str, Node] = {}
        self.edges: List[DAGEdge] = []
        self._incoming: Dict[str, List[str]] = defaultdict(list)
        self._outgoing: Dict[str, List[str]] = defaultdict(list)
    
    def add_node(self, node: Node) -> None:
        """Add node to DAG."""
        if node.node_id in self.nodes:
            raise DAGError(f"Node {node.node_id} already exists")
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: DAGEdge) -> None:
        """Add edge to DAG."""
        if edge.source not in self.nodes:
            raise DAGError(f"Source node {edge.source} does not exist")
        if edge.target not in self.nodes:
            raise DAGError(f"Target node {edge.target} does not exist")
        
        self.edges.append(edge)
        self._incoming[edge.target].append(edge.source)
        self._outgoing[edge.source].append(edge.target)
    
    def validate(self) -> None:
        """
        Validate DAG structure.
        
        Raises:
            DAGError: If DAG is invalid (cycles, missing nodes, etc.)
        """
        # Check for cycles using DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self._outgoing[node_id]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise DAGError(f"Cycle detected in DAG starting from {node_id}")
    
    def topological_sort(self) -> List[str]:
        """
        Return nodes in topological order.
        
        Returns:
            List of node IDs in execution order
            
        Raises:
            DAGError: If DAG has cycles
        """
        self.validate()
        
        # Kahn's algorithm
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] += 1
        
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result: List[str] = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for neighbor in self._outgoing[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            raise DAGError("Cycle detected during topological sort")
        
        return result
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get direct dependencies for a node."""
        return self._incoming.get(node_id, []).copy()
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get nodes that depend on this node."""
        return self._outgoing.get(node_id, []).copy()
    
    def get_roots(self) -> List[str]:
        """Get root nodes (no dependencies)."""
        return [node_id for node_id in self.nodes if not self._incoming.get(node_id)]

