# SPDX-License-Identifier: MIT
"""Immutable execution context."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from engine.util.time import utc_now


@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable execution context.
    
    All execution state is contained here. No mutable global state.
    Platform context is recorded as evidence only, not used for determinism comparison.
    """
    workspace: Path
    cache_dir: Path
    evidence_dir: Path
    policy_rules: Dict[str, Any]
    config: Dict[str, Any]
    execution_id: str
    started_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    platform_context: Optional[Dict[str, Any]] = None
    
    def with_metadata(self, **kwargs) -> "ExecutionContext":
        """Create new context with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return ExecutionContext(
            workspace=self.workspace,
            cache_dir=self.cache_dir,
            evidence_dir=self.evidence_dir,
            policy_rules=self.policy_rules,
            config=self.config,
            execution_id=self.execution_id,
            started_at=self.started_at,
            metadata=new_metadata,
            platform_context=self.platform_context,
        )
    
    def with_platform_context(self, **kwargs) -> "ExecutionContext":
        """
        Create new context with platform context.
        
        Platform context is recorded as evidence only.
        NOT used for determinism comparison.
        """
        import sys
        import platform
        
        platform_ctx = {
            "os": platform.system(),
            "os_version": platform.release(),
            "cpu_architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "python_implementation": platform.python_implementation(),
            **kwargs,
        }
        
        return ExecutionContext(
            workspace=self.workspace,
            cache_dir=self.cache_dir,
            evidence_dir=self.evidence_dir,
            policy_rules=self.policy_rules,
            config=self.config,
            execution_id=self.execution_id,
            started_at=self.started_at,
            metadata=self.metadata,
            platform_context=platform_ctx,
        )

