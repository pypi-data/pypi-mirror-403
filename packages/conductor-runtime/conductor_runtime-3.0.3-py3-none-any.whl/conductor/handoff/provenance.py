"""
Provenance Generator for Conductor Handoff.

Generates cryptographic provenance records for audit compliance.
Uses SHA-256 hashes to verify integrity of inputs and outputs.
"""
import hashlib
import json
from datetime import datetime
from typing import Optional, Literal

from conductor.handoff.schema import (
    TaskFile,
    ResultFile,
    ProvenanceRecord,
    CONTRACT_VERSION,
)


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_task_hash(task: TaskFile) -> str:
    """Compute hash of task file content."""
    # Use JSON representation for deterministic hashing
    task_json = task.model_dump_json(indent=None, exclude={"checksum"})
    return compute_hash(task_json)


def compute_constraint_hash(constraints: list[str]) -> str:
    """Compute hash of constraints list."""
    # Sort for deterministic ordering
    sorted_constraints = sorted(constraints)
    content = json.dumps(sorted_constraints, sort_keys=True)
    return compute_hash(content)


def compute_result_hash(result: ResultFile) -> str:
    """Compute hash of result file content."""
    result_json = result.model_dump_json(indent=None)
    return compute_hash(result_json)


def generate_provenance(
    task: TaskFile,
    result: ResultFile,
    executor: Literal["antigravity", "llm"] = "antigravity",
    previous_hash: Optional[str] = None,
) -> ProvenanceRecord:
    """
    Generate a provenance record for a completed task.
    
    Args:
        task: The original task file
        result: The execution result
        executor: Who executed the task
        previous_hash: Hash of previous provenance (for chaining)
    
    Returns:
        ProvenanceRecord with all integrity hashes
    """
    return ProvenanceRecord(
        task_id=task.task_id,
        plan_id=task.plan_id,
        fork_id=task.fork_id,
        task_hash=compute_task_hash(task),
        constraint_hash=compute_constraint_hash(task.constraints),
        executor=executor,
        started_at=task.created_at,
        completed_at=result.completed_at,
        result_hash=compute_result_hash(result),
        previous_hash=previous_hash,
        contract_version=CONTRACT_VERSION,
    )


def verify_provenance(
    provenance: ProvenanceRecord,
    task: TaskFile,
    result: ResultFile,
) -> dict:
    """
    Verify a provenance record against task and result.
    
    Returns:
        Dict with verification results and any mismatches
    """
    mismatches = []
    
    # Verify task hash
    actual_task_hash = compute_task_hash(task)
    if provenance.task_hash != actual_task_hash:
        mismatches.append(f"task_hash: expected {provenance.task_hash}, got {actual_task_hash}")
    
    # Verify constraint hash
    actual_constraint_hash = compute_constraint_hash(task.constraints)
    if provenance.constraint_hash != actual_constraint_hash:
        mismatches.append(f"constraint_hash: expected {provenance.constraint_hash}, got {actual_constraint_hash}")
    
    # Verify result hash
    actual_result_hash = compute_result_hash(result)
    if provenance.result_hash != actual_result_hash:
        mismatches.append(f"result_hash: expected {provenance.result_hash}, got {actual_result_hash}")
    
    return {
        "valid": len(mismatches) == 0,
        "mismatches": mismatches,
        "verified_at": datetime.utcnow().isoformat(),
    }
