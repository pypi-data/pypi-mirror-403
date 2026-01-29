# SPDX-License-Identifier: MIT
"""Evidence recorder for execution events."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from engine.util.time import utc_now, to_iso8601
from engine.util.json import save_json
from engine.evidence.canonical import seal_evidence
from engine.evidence.signatures import Signer


class EvidenceRecorder:
    """
    Records execution evidence.
    
    All evidence is sealed with integrity proofs.
    Timestamps are deterministic based on execution context.
    """
    
    def __init__(
        self,
        evidence_dir: Path,
        signer: Optional[Signer] = None,
        base_time: Optional[datetime] = None,
    ):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.signer = signer
        self.base_time = base_time  # Deterministic base time from execution context
        self._events: List[Dict[str, Any]] = []
        self._event_counter = 0  # For deterministic ordering
    
    def record_execution_start(
        self,
        execution_id: str,
        dag_id: str,
        node_order: List[str],
    ) -> None:
        """Record execution start event."""
        # Use base_time if provided (deterministic), otherwise fallback to utc_now
        timestamp = self.base_time if self.base_time else utc_now()
        event = {
            "event_type": "execution_start",
            "execution_id": execution_id,
            "dag_id": dag_id,
            "node_order": node_order,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_node_execution(
        self,
        node_id: str,
        node_type: str,
        inputs: List[str],
        output: str,
        evidence: Dict[str, Any],
    ) -> None:
        """Record node execution event."""
        # Deterministic timestamp: base_time + event counter offset
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "node_execution",
            "node_id": node_id,
            "node_type": node_type,
            "inputs": inputs,
            "output": output,
            "evidence": evidence,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_execution_complete(
        self,
        execution_id: str,
        outputs: Dict[str, str],
    ) -> None:
        """Record execution completion event."""
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "execution_complete",
            "execution_id": execution_id,
            "outputs": outputs,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_execution_failure(
        self,
        execution_id: str,
        error: str,
    ) -> None:
        """Record execution failure event."""
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "execution_failure",
            "execution_id": execution_id,
            "error": error,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_policy_check(
        self,
        rule_id: str,
        passed: bool,
        reason_code: Optional[str] = None,
        details: Dict[str, Any] = None,
    ) -> None:
        """
        Record policy rule check.
        
        Evidence must be the product, not a derived artifact.
        Full policy check payload must be recorded, including reason_code.
        
        Args:
            rule_id: Policy rule identifier
            passed: Binary result (True/False)
            reason_code: Failure reason code (required if passed=False)
            details: Additional check details
        """
        if details is None:
            details = {}
        
        # reason_code is required if passed == False
        if passed == False and not reason_code:
            raise ValueError(
                f"Policy check for rule {rule_id} failed but reason_code is missing. "
                "Evidence must record full policy check payload."
            )
        
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "policy_check",
            "rule_id": rule_id,
            "passed": passed,
            "reason_code": reason_code,
            "details": details,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_validation(
        self,
        format_type: str,
        passed: bool,
        details: Dict[str, Any],
    ) -> None:
        """Record format validation."""
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "validation",
            "format_type": format_type,
            "passed": passed,
            "details": details,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def record_state_transition(
        self,
        title: str,
        version: str,
        from_state: str,
        to_state: str,
        signer: Optional[str] = None,
    ) -> None:
        """Record state transition (promotion)."""
        timestamp = self._get_deterministic_timestamp()
        event = {
            "event_type": "state_transition",
            "title": title,
            "version": version,
            "from_state": from_state,
            "to_state": to_state,
            "signer": signer,
            "timestamp": to_iso8601(timestamp),
        }
        self._record_event(event)
    
    def _get_deterministic_timestamp(self) -> datetime:
        """
        Get deterministic timestamp.
        
        Uses base_time from execution context if available,
        otherwise falls back to utc_now (for non-execution contexts).
        """
        if self.base_time:
            # Deterministic: base_time + event counter offset
            from datetime import timedelta
            return self.base_time + timedelta(seconds=self._event_counter)
        return utc_now()
    
    def _record_event(self, event: Dict[str, Any]) -> None:
        """Record event with sealing."""
        sealed = seal_evidence(event)
        
        # Add signature if signer available
        if self.signer:
            canonical = seal_evidence(event)
            from engine.util.json import canonical_json_bytes
            signature = self.signer.sign(canonical_json_bytes(canonical))
            sealed["signature"] = signature
        
        self._events.append(sealed)
        self._event_counter += 1
        
        # Write to file with deterministic naming
        event_file = self.evidence_dir / f"event_{self._event_counter:06d}.json"
        save_json(str(event_file), sealed, canonical=False)
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all recorded events."""
        return self._events.copy()
    
    def save_manifest(self, filepath: Path) -> None:
        """Save evidence manifest."""
        manifest = {
            "events": self._events,
            "total_events": len(self._events),
        }
        save_json(str(filepath), manifest, canonical=False)

