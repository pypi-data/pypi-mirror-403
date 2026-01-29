# SPDX-License-Identifier: MIT
"""Classified error types for MK10-PRO."""


class MK10Error(Exception):
    """Base exception for all MK10-PRO errors."""
    pass


class DeterminismError(MK10Error):
    """Violation of determinism requirement."""
    pass


class PolicyError(MK10Error):
    """Policy rule violation."""
    pass


class ValidationError(MK10Error):
    """Format or specification validation failure."""
    pass


class EvidenceError(MK10Error):
    """Evidence generation or verification failure."""
    pass


class ExecutionError(MK10Error):
    """Node execution failure."""
    pass


class DAGError(MK10Error):
    """DAG structure or ordering error."""
    pass


class MTBError(MK10Error):
    """MTB build, seal, or verification error."""
    pass


class StateError(MK10Error):
    """Invalid state transition."""
    pass


class IngestError(MK10Error):
    """Ingest manifest or binding failure."""
    pass

