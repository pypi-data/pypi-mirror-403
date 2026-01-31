"""
Handoff Adapter for Conductor.

Manages file-based communication with Antigravity IDE agents:
- Writes task files to pending/
- Polls for results in completed/
- Enforces safety checks and timeouts
- Handles retries and escalation
"""
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

from conductor.handoff.schema import (
    TaskFile,
    ResultFile,
    TaskStatus,
    FailurePattern,
    HandoffMetrics,
    CONTRACT_VERSION,
)


logger = logging.getLogger("conductor.handoff")


class HandoffAdapter:
    """
    Adapter for file-based handoff to Antigravity agents.
    
    Directory structure per fork:
        .conductor/handoff/plan_<id>/fork_<id>/
            ├── pending/       # Tasks waiting for agent
            ├── in_progress/   # Currently being executed
            ├── completed/     # Finished successfully
            ├── failed/        # Failed tasks
            └── audit.log      # Append-only log
    """
    
    MAX_RETRIES = 3
    POLL_INTERVAL_SECONDS = 2
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.handoff_root = self.project_root / ".conductor" / "handoff"
        self._metrics: Optional[HandoffMetrics] = None
    
    # ─────────────────────────────────────────────────────────────
    # METRICS
    # ─────────────────────────────────────────────────────────────
    
    @property
    def metrics(self) -> HandoffMetrics:
        """Load or create metrics."""
        if self._metrics is None:
            self._metrics = self._load_metrics()
        return self._metrics
    
    def _load_metrics(self) -> HandoffMetrics:
        """Load metrics from disk."""
        metrics_path = self.handoff_root / "metrics.json"
        if metrics_path.exists():
            try:
                data = json.loads(metrics_path.read_text(encoding="utf-8"))
                return HandoffMetrics(**data)
            except Exception as e:
                logger.warning(f"Failed to load metrics, using defaults: {e}")
        return HandoffMetrics()
    
    def _save_metrics(self) -> None:
        """Persist metrics to disk."""
        self.handoff_root.mkdir(parents=True, exist_ok=True)
        metrics_path = self.handoff_root / "metrics.json"
        metrics_path.write_text(self.metrics.model_dump_json(indent=2), encoding="utf-8")
    
    # ─────────────────────────────────────────────────────────────
    # DIRECTORY MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    
    def _get_fork_dir(self, plan_id: str, fork_id: str) -> Path:
        """Get the handoff directory for a specific fork."""
        return self.handoff_root / f"plan_{plan_id}" / f"fork_{fork_id}"
    
    def _ensure_dirs(self, plan_id: str, fork_id: str) -> dict[str, Path]:
        """Create all required directories for a fork."""
        fork_dir = self._get_fork_dir(plan_id, fork_id)
        
        dirs = {
            "pending": fork_dir / "pending",
            "in_progress": fork_dir / "in_progress",
            "completed": fork_dir / "completed",
            "failed": fork_dir / "failed",
        }
        
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        
        return dirs
    
    # ─────────────────────────────────────────────────────────────
    # TASK WRITING
    # ─────────────────────────────────────────────────────────────
    
    def write_task(
        self,
        task_id: str,
        plan_id: str,
        fork_id: str,
        instruction: str,
        allowed_files: list[str],
        timeout_seconds: int = 300,
        context: Optional[dict] = None,
        expected_output: Optional[str] = None,
        max_diff_lines: int = 500,
        step_constraints: Optional[list[str]] = None,
    ) -> Path:
        """
        Write a task file for Antigravity to execute.
        
        Constraints are merged: project-level + step-level.
        
        Returns: Path to the created task file
        """
        dirs = self._ensure_dirs(plan_id, fork_id)
        
        # Load project policy
        from conductor.policy.loader import load_policy, merge_constraints, merge_allowed_files
        policy = load_policy(str(self.project_root))
        
        # Merge constraints: project + step
        merged_constraints = merge_constraints(
            project_constraints=policy.global_constraints,
            plan_constraints=[],  # Reserved for future plan-level constraints
            step_constraints=step_constraints or [],
        )
        
        # Merge allowed files: task-specific takes precedence
        final_allowed_files = merge_allowed_files(
            project_patterns=policy.file_rules.allowed_patterns,
            task_files=allowed_files,
        )
        
        # Use policy defaults if not overridden
        final_timeout = timeout_seconds or policy.behavior.timeout_seconds
        final_max_diff = max_diff_lines or policy.behavior.max_diff_lines
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=final_timeout + 60)
        
        task = TaskFile(
            task_id=task_id,
            plan_id=plan_id,
            fork_id=fork_id,
            expires_at=expires_at,
            timeout_seconds=final_timeout,
            instruction=instruction,
            allowed_files=final_allowed_files,
            context=context or {},
            expected_output=expected_output,
            max_diff_lines=final_max_diff,
        )
        
        # Override constraints with merged (project + defaults + step)
        if merged_constraints:
            # Prepend project constraints to defaults, then add step-specific
            task.constraints = merged_constraints + [c for c in task.constraints if c not in merged_constraints]
        
        # Compute and set checksum
        task.checksum = task.compute_checksum()
        
        # Compute pre-execution confidence
        from conductor.handoff.confidence import compute_confidence
        confidence_score = compute_confidence(task, self.metrics)
        task.confidence = {
            "score": confidence_score.score,
            "level": confidence_score.level.value,
            "factors": confidence_score.factors,
        }
        
        # Write to pending/
        task_path = dirs["pending"] / f"{task_id}.task.json"
        task_path.write_text(task.model_dump_json(indent=2), encoding="utf-8")
        
        # Update metrics
        self.metrics.record_created()
        self._save_metrics()
        
        # Log to audit
        self._append_audit(plan_id, fork_id, f"TASK_CREATED: {task_id} checksum={task.checksum}")
        
        logger.info(f"[{task_id}] Task written to {task_path}")
        return task_path
    
    # ─────────────────────────────────────────────────────────────
    # RESULT POLLING
    # ─────────────────────────────────────────────────────────────
    
    def poll_result(
        self,
        task_id: str,
        plan_id: str,
        fork_id: str,
        timeout_seconds: int = 300,
    ) -> Optional[ResultFile]:
        """
        Poll for task completion.
        
        Returns: ResultFile if completed, None if timeout
        """
        dirs = self._ensure_dirs(plan_id, fork_id)
        
        start_time = time.time()
        result_path = dirs["completed"] / f"{task_id}.result.json"
        failed_path = dirs["failed"] / f"{task_id}.result.json"
        
        logger.info(f"[{task_id}] Polling for result (timeout: {timeout_seconds}s)")
        
        while time.time() - start_time < timeout_seconds:
            # Check completed/
            if result_path.exists():
                result = self._read_result(result_path)
                self._append_audit(plan_id, fork_id, f"RESULT_RECEIVED: {task_id} status={result.status.value}")
                # Update metrics
                if result.status.value == "done":
                    self.metrics.record_completed(result.execution_time_ms)
                else:
                    self.metrics.record_failed()
                self._save_metrics()
                
                # Generate explanation
                self._generate_explanation(task_id, plan_id, fork_id, result)
                
                # Generate provenance
                self._generate_provenance(task_id, plan_id, fork_id, result)
                
                return result
            
            # Check failed/
            if failed_path.exists():
                result = self._read_result(failed_path)
                self._append_audit(plan_id, fork_id, f"RESULT_RECEIVED: {task_id} status={result.status.value}")
                self.metrics.record_failed()
                self._save_metrics()
                return result
            
            time.sleep(self.POLL_INTERVAL_SECONDS)
        
        # Timeout
        logger.warning(f"[{task_id}] Polling timeout after {timeout_seconds}s")
        self._append_audit(plan_id, fork_id, f"TIMEOUT: {task_id}")
        
        # Update metrics
        self.metrics.record_timeout()
        self._save_metrics()
        
        # Move task to failed/
        self._move_to_failed(task_id, plan_id, fork_id, "Timeout: agent did not respond")
        
        return None
    
    def _read_result(self, path: Path) -> ResultFile:
        """Read and parse a result file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return ResultFile(**data)
    
    # ─────────────────────────────────────────────────────────────
    # STATE MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    
    def move_to_in_progress(self, task_id: str, plan_id: str, fork_id: str) -> None:
        """Move task from pending/ to in_progress/."""
        dirs = self._ensure_dirs(plan_id, fork_id)
        
        src = dirs["pending"] / f"{task_id}.task.json"
        dst = dirs["in_progress"] / f"{task_id}.task.json"
        
        if src.exists():
            src.rename(dst)
            self._append_audit(plan_id, fork_id, f"IN_PROGRESS: {task_id}")
    
    def _move_to_failed(self, task_id: str, plan_id: str, fork_id: str, error: str) -> None:
        """Move task to failed/ and create error result."""
        dirs = self._ensure_dirs(plan_id, fork_id)
        
        # Move task file
        for src_dir in [dirs["pending"], dirs["in_progress"]]:
            src = src_dir / f"{task_id}.task.json"
            if src.exists():
                dst = dirs["failed"] / f"{task_id}.task.json"
                src.rename(dst)
                break
        
        # Create failure result
        result = ResultFile(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error,
        )
        
        result_path = dirs["failed"] / f"{task_id}.result.json"
        result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    
    # ─────────────────────────────────────────────────────────────
    # SAFETY VERIFICATION
    # ─────────────────────────────────────────────────────────────
    
    def verify_result(
        self,
        task: TaskFile,
        result: ResultFile,
        file_hashes_before: dict[str, str],
    ) -> tuple[bool, list[str]]:
        """
        Verify result against task constraints.
        
        Returns: (is_valid, list of violations)
        """
        violations = []
        
        # Check contract version
        if result.contract_version != CONTRACT_VERSION:
            violations.append(f"Contract version mismatch: {result.contract_version} != {CONTRACT_VERSION}")
        
        # Check allowed_files
        if task.allowed_files:
            for change in result.files_changed:
                if change.path not in task.allowed_files:
                    violations.append(f"Unauthorized file change: {change.path}")
        
        # Check max_diff_lines
        total_diff = result.total_lines_added + result.total_lines_removed
        if total_diff > task.max_diff_lines:
            violations.append(f"Diff too large: {total_diff} > {task.max_diff_lines}")
        
        # Check for unexpected file changes
        current_hashes = self._compute_file_hashes([Path(p) for p in task.allowed_files])
        for path, old_hash in file_hashes_before.items():
            if path not in task.allowed_files:
                new_hash = self._hash_file(Path(path))
                if new_hash != old_hash:
                    violations.append(f"Unexpected change to {path}")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def compute_file_hashes(self, files: list[str]) -> dict[str, str]:
        """Compute hashes of files for later comparison."""
        return self._compute_file_hashes([self.project_root / f for f in files])
    
    def _compute_file_hashes(self, paths: list[Path]) -> dict[str, str]:
        """Compute MD5 hashes of files."""
        hashes = {}
        for p in paths:
            full_path = self.project_root / p if not p.is_absolute() else p
            if full_path.exists():
                hashes[str(p)] = self._hash_file(full_path)
        return hashes
    
    def _hash_file(self, path: Path) -> str:
        """Compute MD5 hash of a file."""
        if not path.exists():
            return ""
        content = path.read_bytes()
        return hashlib.md5(content).hexdigest()
    
    # ─────────────────────────────────────────────────────────────
    # RETRY & REPAIR
    # ─────────────────────────────────────────────────────────────
    
    def create_repair_task(
        self,
        original_task: TaskFile,
        error: str,
        retry_count: int,
    ) -> TaskFile:
        """Create a repair task based on the original failure."""
        
        repair_instruction = f"""REPAIR TASK (Attempt {retry_count + 1}/{self.MAX_RETRIES})

The previous attempt failed with error:
{error}

Original instruction:
{original_task.instruction}

Please try again, addressing the error above."""
        
        return TaskFile(
            task_id=f"{original_task.task_id}_repair_{retry_count + 1}",
            plan_id=original_task.plan_id,
            fork_id=original_task.fork_id,
            expires_at=datetime.utcnow() + timedelta(seconds=original_task.timeout_seconds + 60),
            timeout_seconds=original_task.timeout_seconds,
            instruction=repair_instruction,
            allowed_files=original_task.allowed_files,
            context={**original_task.context, "is_repair": True, "retry_count": retry_count + 1},
            expected_output=original_task.expected_output,
            max_diff_lines=original_task.max_diff_lines,
        )
    
    def record_failure_pattern(
        self,
        task_id: str,
        plan_id: str,
        fork_id: str,
        task_type: str,
        failure_reason: str,
        retry_count: int,
        resolution: str = "abandoned",
    ) -> None:
        """Record failure pattern for future learning."""
        
        pattern = FailurePattern(
            task_id=task_id,
            task_type=task_type,
            failure_reason=failure_reason,
            retry_count=retry_count,
            resolution=resolution,
        )
        
        self._append_audit(
            plan_id, fork_id,
            f"FAILURE_PATTERN: {pattern.model_dump_json()}"
        )
    
    # ─────────────────────────────────────────────────────────────
    # AUDIT LOG
    # ─────────────────────────────────────────────────────────────
    
    def _append_audit(self, plan_id: str, fork_id: str, message: str) -> None:
        """Append to the audit log (append-only)."""
        fork_dir = self._get_fork_dir(plan_id, fork_id)
        fork_dir.mkdir(parents=True, exist_ok=True)
        
        audit_path = fork_dir / "audit.log"
        timestamp = datetime.utcnow().isoformat()
        
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    # ─────────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────────
    
    def cleanup_expired_tasks(self, plan_id: str, fork_id: str) -> int:
        """Remove expired tasks from pending/. Returns count removed."""
        dirs = self._ensure_dirs(plan_id, fork_id)
        
        removed = 0
        now = datetime.utcnow()
        
        for task_path in dirs["pending"].glob("*.task.json"):
            try:
                data = json.loads(task_path.read_text(encoding="utf-8"))
                expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
                
                if expires_at.replace(tzinfo=None) < now:
                    self._move_to_failed(data["task_id"], plan_id, fork_id, "Expired before execution")
                    removed += 1
            except Exception:
                pass
        
        return removed
    
    # ─────────────────────────────────────────────────────────────
    # EXPLANATION GENERATION
    # ─────────────────────────────────────────────────────────────
    
    def _generate_explanation(
        self,
        task_id: str,
        plan_id: str,
        fork_id: str,
        result: ResultFile,
    ) -> None:
        """
        Generate an explanation markdown file for a completed task.
        
        The explanation.md is written to the same directory as the result.
        """
        try:
            from conductor.handoff.explainer import generate_explanation
            
            dirs = self._ensure_dirs(plan_id, fork_id)
            
            # Load the original task file
            task_path = dirs["completed"] / f"{task_id}.task.json"
            if not task_path.exists():
                task_path = dirs["failed"] / f"{task_id}.task.json"
            
            if not task_path.exists():
                logger.warning(f"[{task_id}] Cannot generate explanation: task file not found")
                return
            
            task_data = json.loads(task_path.read_text(encoding="utf-8"))
            task = TaskFile(**task_data)
            
            # Generate explanation
            explanation = generate_explanation(task, result)
            
            # Determine output directory based on result status
            if result.status == TaskStatus.DONE:
                output_dir = dirs["completed"]
            else:
                output_dir = dirs["failed"]
            
            explanation_path = output_dir / f"{task_id}.explanation.md"
            explanation_path.write_text(explanation, encoding="utf-8")
            
            self._append_audit(plan_id, fork_id, f"EXPLANATION_GENERATED: {task_id}")
            logger.info(f"[{task_id}] Explanation written to {explanation_path}")
            
        except Exception as e:
            # Explanation generation should not block result processing
            logger.warning(f"[{task_id}] Failed to generate explanation: {e}")

    # ─────────────────────────────────────────────────────────────
    # PROVENANCE GENERATION
    # ─────────────────────────────────────────────────────────────
    
    def _generate_provenance(
        self,
        task_id: str,
        plan_id: str,
        fork_id: str,
        result: ResultFile,
    ) -> None:
        """
        Generate a provenance record for a completed task.
        
        The provenance.json is written to the same directory as the result.
        """
        try:
            from conductor.handoff.provenance import generate_provenance
            
            dirs = self._ensure_dirs(plan_id, fork_id)
            
            # Load the original task file
            task_path = dirs["completed"] / f"{task_id}.task.json"
            if not task_path.exists():
                task_path = dirs["failed"] / f"{task_id}.task.json"
            
            if not task_path.exists():
                logger.warning(f"[{task_id}] Cannot generate provenance: task file not found")
                return
            
            task_data = json.loads(task_path.read_text(encoding="utf-8"))
            task = TaskFile(**task_data)
            
            # Generate provenance
            provenance = generate_provenance(task, result, executor="antigravity")
            
            # Determine output directory based on result status
            if result.status == TaskStatus.DONE:
                output_dir = dirs["completed"]
            else:
                output_dir = dirs["failed"]
            
            provenance_path = output_dir / f"{task_id}.provenance.json"
            provenance_path.write_text(provenance.model_dump_json(indent=2), encoding="utf-8")
            
            self._append_audit(plan_id, fork_id, f"PROVENANCE_GENERATED: {task_id}")
            logger.info(f"[{task_id}] Provenance written to {provenance_path}")
            
        except Exception as e:
            # Provenance generation should not block result processing
            logger.warning(f"[{task_id}] Failed to generate provenance: {e}")

