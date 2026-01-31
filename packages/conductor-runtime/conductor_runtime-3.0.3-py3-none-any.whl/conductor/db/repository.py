"""
Enhanced Repository for Conductor.
Handles forks, memory, policies, and verification.
"""
import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from conductor.db.models import (
    Plan, Step, Event, MCPCall, PlanStatus, StepStatus, EventType,
    MemoryPattern, MemoryFailure, ModelMetrics, Policy, Repair
)


class Repository:
    """Database repository with full v3 support."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        schema_path = Path(__file__).parent / "schema.sql"
        
        with self._connect() as conn:
            if schema_path.exists():
                conn.executescript(schema_path.read_text(encoding='utf-8'))
    
    # ─────────────────────────────────────────────────────────────
    # PLANS
    # ─────────────────────────────────────────────────────────────
    
    def create_plan(self, plan: Plan):
        with self._connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO plans 
                (id, goal, parent_plan_id, fork_reason, strategy, status, consecutive_failures)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (plan.id, plan.goal, plan.parent_plan_id, plan.fork_reason, 
                  plan.strategy, plan.status.value, plan.consecutive_failures))
        
        self.log_event(Event(event_type=EventType.PLAN_CREATED, plan_id=plan.id))
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
            return self._row_to_plan(row) if row else None
    
    def get_active_plan(self) -> Optional[Plan]:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM plans 
                WHERE parent_plan_id IS NULL AND status NOT IN ('completed', 'pruned')
                ORDER BY created_at DESC LIMIT 1
            """).fetchone()
            return self._row_to_plan(row) if row else None
    
    def get_forks(self, parent_plan_id: str) -> list[Plan]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM plans WHERE parent_plan_id = ?", (parent_plan_id,)
            ).fetchall()
            return [self._row_to_plan(r) for r in rows]
    
    def update_plan(self, plan: Plan):
        with self._connect() as conn:
            conn.execute("""
                UPDATE plans SET 
                    status = ?, score = ?, halt_reason = ?, consecutive_failures = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (plan.status.value, plan.score, plan.halt_reason, 
                  plan.consecutive_failures, plan.id))
    
    def halt_plan(self, plan_id: str, reason: str):
        with self._connect() as conn:
            conn.execute("""
                UPDATE plans SET status = 'halted', halt_reason = ? WHERE id = ?
            """, (reason, plan_id))
        self.log_event(Event(event_type=EventType.PLAN_HALTED, plan_id=plan_id, payload={"reason": reason}))
    
    def resume_plan(self, plan_id: str):
        with self._connect() as conn:
            conn.execute("""
                UPDATE plans SET status = 'executing', halt_reason = NULL WHERE id = ?
            """, (plan_id,))
        self.log_event(Event(event_type=EventType.PLAN_RESUMED, plan_id=plan_id))
    
    def is_plan_complete(self, plan_id: str) -> bool:
        steps = self.get_steps(plan_id)
        if not steps:
            return False
        return all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED) for s in steps)
    
    def _row_to_plan(self, row) -> Plan:
        return Plan(
            id=row["id"],
            goal=row["goal"],
            parent_plan_id=row["parent_plan_id"],
            fork_reason=row["fork_reason"],
            strategy=row["strategy"],
            status=PlanStatus(row["status"]),
            score=row["score"],
            halt_reason=row["halt_reason"],
            consecutive_failures=row["consecutive_failures"],
        )
    
    # ─────────────────────────────────────────────────────────────
    # STEPS
    # ─────────────────────────────────────────────────────────────
    
    def create_step(self, step: Step):
        with self._connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO steps
                (step_key, plan_id, sequence, description, agent, status, depends_on, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (step.step_key, step.plan_id, step.sequence, step.description,
                  step.agent, step.status.value, json.dumps(step.depends_on), step.strategy))
    
    def get_step(self, step_key: str) -> Optional[Step]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM steps WHERE step_key = ?", (step_key,)).fetchone()
            return self._row_to_step(row) if row else None
    
    def get_steps(self, plan_id: str) -> list[Step]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM steps WHERE plan_id = ? ORDER BY sequence", (plan_id,)
            ).fetchall()
            return [self._row_to_step(r) for r in rows]
    
    def get_next_step(self, plan_id: str) -> Optional[Step]:
        steps = self.get_steps(plan_id)
        completed = {s.step_key for s in steps if s.status == StepStatus.COMPLETED}
        
        # Priority: running > retryable failed > pending
        for step in steps:
            if step.status == StepStatus.RUNNING:
                return step
        
        for step in steps:
            if step.status == StepStatus.FAILED and step.can_retry():
                return step
        
        for step in steps:
            if step.status == StepStatus.PENDING:
                deps_met = all(d in completed for d in step.depends_on)
                if deps_met:
                    return step
        
        return None
    
    def update_step_status(
        self, step_key: str, status: StepStatus,
        output: str = None, artifacts: list = None, mcp_used: list = None, error: str = None
    ):
        with self._connect() as conn:
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            values = [status.value]
            
            if status == StepStatus.RUNNING:
                updates.append("started_at = CURRENT_TIMESTAMP")
                updates.append("attempt = attempt + 1")
            elif status in (StepStatus.COMPLETED, StepStatus.FAILED):
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            if output:
                updates.append("output = ?")
                values.append(output)
            if artifacts:
                updates.append("artifacts = ?")
                values.append(json.dumps(artifacts))
            if mcp_used:
                updates.append("mcp_used = ?")
                values.append(json.dumps(mcp_used))
            if error:
                updates.append("last_error = ?")
                values.append(error)
            
            values.append(step_key)
            conn.execute(f"UPDATE steps SET {', '.join(updates)} WHERE step_key = ?", values)
    
    def update_step_confidence(self, step_key: str, confidence: float):
        with self._connect() as conn:
            conn.execute("UPDATE steps SET confidence = ? WHERE step_key = ?", (confidence, step_key))
    
    def mark_step_verified(self, step_key: str):
        with self._connect() as conn:
            conn.execute("UPDATE steps SET verified = 1 WHERE step_key = ?", (step_key,))
        self.log_event(Event(event_type=EventType.STEP_VERIFIED, step_key=step_key))
    
    def _row_to_step(self, row) -> Step:
        return Step(
            id=row["id"],
            step_key=row["step_key"],
            plan_id=row["plan_id"],
            sequence=row["sequence"],
            description=row["description"],
            agent=row["agent"],
            status=StepStatus(row["status"]),
            confidence=row["confidence"] or 0.0,
            verified=bool(row["verified"]),
            depends_on=json.loads(row["depends_on"] or "[]"),
            attempt=row["attempt"],
            max_retries=row["max_retries"],
            strategy=row["strategy"],
            output=row["output"],
            artifacts=json.loads(row["artifacts"] or "[]"),
            mcp_used=json.loads(row["mcp_used"] or "[]"),
            last_error=row["last_error"],
        )
    
    # ─────────────────────────────────────────────────────────────
    # EVENTS
    # ─────────────────────────────────────────────────────────────
    
    def log_event(self, event: Event):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO events (event_type, plan_id, step_key, agent, payload, state_snapshot)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event.event_type.value, event.plan_id, event.step_key,
                  event.agent, json.dumps(event.payload) if event.payload else None,
                  json.dumps(event.state_snapshot) if event.state_snapshot else None))
    
    def get_events(self, plan_id: str = None, limit: int = 100) -> list[Event]:
        with self._connect() as conn:
            if plan_id:
                rows = conn.execute(
                    "SELECT * FROM events WHERE plan_id = ? ORDER BY created_at DESC LIMIT ?",
                    (plan_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_to_event(r) for r in rows]
    
    def get_events_before(self, plan_id: str, timestamp: datetime) -> list[Event]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM events WHERE plan_id = ? AND created_at <= ? ORDER BY created_at
            """, (plan_id, timestamp.isoformat())).fetchall()
            return [self._row_to_event(r) for r in rows]
    
    def _row_to_event(self, row) -> Event:
        return Event(
            id=row["id"],
            event_type=EventType(row["event_type"]),
            plan_id=row["plan_id"],
            step_key=row["step_key"],
            agent=row["agent"],
            payload=json.loads(row["payload"]) if row["payload"] else None,
        )
    
    # ─────────────────────────────────────────────────────────────
    # MCP CALLS
    # ─────────────────────────────────────────────────────────────
    
    def log_mcp_call(self, call: MCPCall):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO mcp_calls (step_key, mcp_server, action, request, response, success, verified, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (call.step_key, call.mcp_server, call.action,
                  json.dumps(call.request) if call.request else None,
                  json.dumps(call.response) if call.response else None,
                  1 if call.success else 0, 1 if call.verified else 0, call.duration_ms))
    
    def get_mcp_calls_for_step(self, step_key: str) -> list[MCPCall]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mcp_calls WHERE step_key = ?", (step_key,)
            ).fetchall()
            return [MCPCall(
                id=r["id"],
                step_key=r["step_key"],
                mcp_server=r["mcp_server"],
                action=r["action"],
                success=bool(r["success"]),
            ) for r in rows]
    
    # ─────────────────────────────────────────────────────────────
    # MEMORY
    # ─────────────────────────────────────────────────────────────
    
    def store_memory_pattern(self, pattern: MemoryPattern):
        with self._connect() as conn:
            # Upsert pattern
            conn.execute("""
                INSERT INTO memory_patterns (pattern_type, goal_signature, pattern_data, success_count, failure_count)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(goal_signature, pattern_type) DO UPDATE SET
                    success_count = success_count + excluded.success_count,
                    failure_count = failure_count + excluded.failure_count,
                    last_used_at = CURRENT_TIMESTAMP
            """, (pattern.pattern_type.value, pattern.goal_signature,
                  json.dumps(pattern.pattern_data), pattern.success_count, pattern.failure_count))
    
    def recall_memory_patterns(self, goal_signature: str, limit: int = 5) -> list[MemoryPattern]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM memory_patterns WHERE goal_signature = ?
                ORDER BY success_count DESC LIMIT ?
            """, (goal_signature, limit)).fetchall()
            return [MemoryPattern(
                id=r["id"],
                pattern_type=r["pattern_type"],
                goal_signature=r["goal_signature"],
                pattern_data=json.loads(r["pattern_data"]),
                success_count=r["success_count"],
                failure_count=r["failure_count"],
            ) for r in rows]
    
    def store_memory_failure(self, failure: MemoryFailure):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO memory_failures (error_signature, context_signature, avoidance_strategy)
                VALUES (?, ?, ?)
                ON CONFLICT(error_signature) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    last_seen_at = CURRENT_TIMESTAMP
            """, (failure.error_signature, failure.context_signature, failure.avoidance_strategy))
    
    def recall_memory_failures(self, error_signature: str) -> list[MemoryFailure]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM memory_failures WHERE error_signature = ?
            """, (error_signature,)).fetchall()
            return [MemoryFailure(
                id=r["id"],
                error_signature=r["error_signature"],
                avoidance_strategy=r["avoidance_strategy"],
                occurrence_count=r["occurrence_count"],
            ) for r in rows]
    
    def update_model_metrics(self, model_name: str, role: str, success: bool, latency_ms: float = 0, confidence: float = 0.5):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO model_metrics (model_name, role, success_count, failure_count, avg_latency_ms, avg_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_name, role) DO UPDATE SET
                    success_count = success_count + CASE WHEN ? THEN 1 ELSE 0 END,
                    failure_count = failure_count + CASE WHEN ? THEN 0 ELSE 1 END,
                    updated_at = CURRENT_TIMESTAMP
            """, (model_name, role, 1 if success else 0, 0 if success else 1,
                  latency_ms, confidence, success, success))
    
    def get_model_metrics_for_role(self, role: str) -> list[ModelMetrics]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM model_metrics WHERE role = ?", (role,)
            ).fetchall()
            return [ModelMetrics(
                id=r["id"],
                model_name=r["model_name"],
                role=r["role"],
                success_count=r["success_count"],
                failure_count=r["failure_count"],
            ) for r in rows]
    
    # ─────────────────────────────────────────────────────────────
    # REPAIRS
    # ─────────────────────────────────────────────────────────────
    
    def log_repair(self, repair: Repair):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO repairs (plan_id, step_key, failure_pattern, repair_action, repair_type, success)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (repair.plan_id, repair.step_key, repair.failure_pattern,
                  repair.repair_action, repair.repair_type.value, repair.success))
        self.log_event(Event(
            event_type=EventType.STEP_REPAIRED,
            plan_id=repair.plan_id,
            step_key=repair.step_key,
            payload={"action": repair.repair_action}
        ))
