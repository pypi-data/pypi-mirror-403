"""
Handoff package for Conductor.

Manages file-based communication with Antigravity IDE agents.
"""
from conductor.handoff.schema import (
    TaskFile,
    ResultFile,
    TaskStatus,
    HandoffMode,
    FailurePattern,
    HandoffMetrics,
    ProvenanceRecord,
    ConfidenceScore,
    ConfidenceLevel,
    CONTRACT_VERSION,
)
from conductor.handoff.adapter import HandoffAdapter
from conductor.handoff.explainer import generate_explanation
from conductor.handoff.provenance import generate_provenance, verify_provenance
from conductor.handoff.confidence import compute_confidence

__all__ = [
    "TaskFile",
    "ResultFile",
    "TaskStatus",
    "HandoffMode",
    "FailurePattern",
    "HandoffMetrics",
    "ProvenanceRecord",
    "ConfidenceScore",
    "ConfidenceLevel",
    "HandoffAdapter",
    "CONTRACT_VERSION",
    "generate_explanation",
    "generate_provenance",
    "verify_provenance",
    "compute_confidence",
]


