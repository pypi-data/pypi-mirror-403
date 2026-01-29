# SPDX-License-Identifier: MIT
"""Master Truth Bundle builder."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from engine.core.errors import MTBError
from engine.util.time import utc_now, to_iso8601
from engine.util.json import canonical_json_bytes
from engine.evidence.hash import compute_sha256
from engine.evidence.recorder import EvidenceRecorder
from mtb.seal import seal_mtb


class MTBBuilder:
    """
    Builds Master Truth Bundle.
    
    MTB is the product - a sealed, self-contained, verifiable object.
    All timestamps must be deterministic from execution context.
    """
    
    def __init__(
        self,
        title: str,
        version: str,
        state: str = "DRAFT",
        base_time: Optional[datetime] = None,
    ):
        self.title = title
        self.version = version
        self.state = state
        self.base_time = base_time  # Deterministic base time from execution context
        self.ingest_manifest: Dict[str, Any] = {
            "assets": [],
            "ingest_timestamp": to_iso8601(base_time) if base_time else to_iso8601(utc_now()),
        }
        self.lineage_dag: Dict[str, Any] = {
            "nodes": [],
            "edges": [],
            "execution_order": [],
        }
        self.build_evidence: Dict[str, Any] = {
            "execution_id": "",
            "events": [],
        }
        self.policy_evidence: Dict[str, Any] = {
            "rule_checks": [],
        }
        self.validation_evidence: Dict[str, Any] = {
            "validations": [],
        }
        self.approval_events: List[Dict[str, Any]] = []
        self.archive_declaration: Optional[Dict[str, Any]] = None
    
    def add_ingest_asset(
        self,
        content_address: str,
        path: Path,
        hash_value: str,
        size: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add asset to ingest manifest."""
        asset = {
            "content_address": content_address,
            "path": str(path),
            "hash": hash_value,
            "size": size,
            "metadata": metadata or {},
        }
        self.ingest_manifest["assets"].append(asset)
    
    def set_lineage_dag(self, dag_data: Dict[str, Any]) -> None:
        """Set lineage DAG."""
        self.lineage_dag = dag_data
    
    def set_build_evidence(
        self,
        execution_id: str,
        events: List[Dict[str, Any]],
    ) -> None:
        """Set build evidence."""
        self.build_evidence = {
            "execution_id": execution_id,
            "events": events,
        }
    
    def add_policy_check(
        self,
        rule_id: str,
        passed: bool,
        reason_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add policy rule check result.
        
        Policy evidence must be sealed into MTB.
        Each check includes:
        - rule_id: Rule identifier
        - passed: Binary result (True/False)
        - reason_code: Failure reason if passed=False
        - details: Additional check details
        """
        check = {
            "rule_id": rule_id,
            "passed": passed,
            "details": details or {},
        }
        # Only include reason_code if present (schema requires string type)
        if reason_code is not None:
            check["reason_code"] = reason_code
        self.policy_evidence["rule_checks"].append(check)
    
    def add_validation(
        self,
        format_type: str,
        passed: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add validation result."""
        validation = {
            "format_type": format_type,
            "passed": passed,
            "details": details or {},
        }
        self.validation_evidence["validations"].append(validation)
    
    def add_approval_event(
        self,
        from_state: str,
        to_state: str,
        signer: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add approval/promotion event.
        
        Args:
            from_state: Source state
            to_state: Target state
            signer: Optional signer identifier
            timestamp: Deterministic timestamp (uses base_time + offset if not provided)
        """
        # Use provided timestamp, or base_time + event count offset, or fallback to utc_now
        if timestamp:
            event_timestamp = timestamp
        elif self.base_time:
            from datetime import timedelta
            event_timestamp = self.base_time + timedelta(seconds=len(self.approval_events))
        else:
            event_timestamp = utc_now()  # Fallback for non-execution contexts
        
        event = {
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": to_iso8601(event_timestamp),
            "signer": signer,
        }
        self.approval_events.append(event)
        self.state = to_state
    
    def set_archive_declaration(
        self,
        intent: str,
        retention_policy: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Set archive declaration.
        
        Args:
            intent: Archive intent
            retention_policy: Optional retention policy
            timestamp: Deterministic timestamp (uses base_time if not provided)
        """
        # Use provided timestamp, or base_time, or fallback to utc_now
        if timestamp:
            declared_at = timestamp
        elif self.base_time:
            declared_at = self.base_time
        else:
            declared_at = utc_now()  # Fallback for non-execution contexts
        
        self.archive_declaration = {
            "declared_at": to_iso8601(declared_at),
            "intent": intent,
            "retention_policy": retention_policy,
        }
    
    def build(self) -> Dict[str, Any]:
        """
        Build MTB structure.
        
        Returns:
            MTB dictionary (not yet sealed)
            
        Raises:
            MTBError: If required fields are missing
        """
        # Validate required fields
        if not self.ingest_manifest["assets"]:
            raise MTBError("Ingest manifest must contain at least one asset")
        
        if not self.build_evidence["execution_id"]:
            raise MTBError("Build evidence must have execution_id")
        
        # Build non_claims section (required to prevent scope creep)
        non_claims = {
            "cross_platform_determinism": False,
            "hardware_equivalence": False,
            "library_equivalence": False,
            "cpu_feature_equivalence": False,
            "simd_equivalence": False,
            "external_dependency_equivalence": False,
        }
        
        mtb = {
            "mtb_version": "1.0",
            "title": self.title,
            "version": self.version,
            "state": self.state,
            "ingest_manifest": self.ingest_manifest,
            "lineage_dag": self.lineage_dag,
            "build_evidence": self.build_evidence,
            "policy_evidence": self.policy_evidence,
            "validation_evidence": self.validation_evidence,
            "approval_events": self.approval_events,
            "archive_declaration": self.archive_declaration or {
                "declared_at": to_iso8601(self.base_time) if self.base_time else to_iso8601(utc_now()),
                "intent": "not_declared",
            },
            "non_claims": non_claims,
        }
        
        return mtb
    
    def build_and_seal(self) -> Dict[str, Any]:
        """
        Build and seal MTB.
        
        Returns:
            Sealed MTB with integrity proof
        """
        mtb = self.build()
        sealed = seal_mtb(mtb)
        return sealed
    
    def save(self, output_path: Path, sealed: bool = True) -> None:
        """
        Save MTB to file.
        
        Args:
            output_path: Output file path
            sealed: Whether to seal before saving
        """
        if sealed:
            mtb = self.build_and_seal()
        else:
            mtb = self.build()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mtb, f, indent=2, ensure_ascii=False)

