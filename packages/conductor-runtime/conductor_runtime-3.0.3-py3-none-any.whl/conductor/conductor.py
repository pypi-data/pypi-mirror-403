"""
Conductor - Paradigm Upgrade.
Exploratory orchestration with self-repair and learning.

ORCHESTRATION LOOP:
explore → fork → execute → verify → compare → learn → converge
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Any

from conductor.db.models import Plan, Step, Event, PlanStatus, StepStatus, EventType, AgentRole
from conductor.config import ConductorConfig
from conductor.policy import PolicyEngine
from conductor.memory import MemoryStore
from conductor.exploration import ExplorationEngine, ReplayEngine


class Conductor:
    """
    Conductor - Post-Conductor Orchestration System.
    
    Execution model:
    explore → fork → execute → verify → compare → learn → converge
    
    Key capabilities:
    - Exploratory execution with forked strategies
    - Autonomous self-repair
    - Long-term memory and learning
    - Policy-driven governance
    - Evidence-based verification
    """
    
    def __init__(
        self,
        project_root: str,
        config: ConductorConfig = None,
        model_client: Any = None,
    ):
        self.project_root = project_root
        self.config = config or ConductorConfig()
        
        # Auto-create model clients from environment if not provided
        if model_client is None:
            from conductor.config import create_clients_for_roles
            self._model_clients = create_clients_for_roles(self.config)
            # Use planner client as default
            self.model_client = self._model_clients.get("planner")
        else:
            self.model_client = model_client
            self._model_clients = {role: model_client for role in ["planner", "executor", "reviewer", "verifier", "repair"]}
        
        # Initialize database
        from conductor.db import Repository
        db_path = f"{project_root}/{self.config.db_path}"
        self.repository = Repository(db_path)
        
        # Initialize subsystems
        self.policy_engine = PolicyEngine(self.repository)
        self.memory = MemoryStore(self.repository)
        self.exploration = ExplorationEngine(self.repository)
        self.replay = ReplayEngine(self.repository)
        
        # MCP
        from conductor.mcp import MCPDiscovery, MCPRecorder
        self.mcp_discovery = MCPDiscovery()
        self.mcp_recorder = MCPRecorder(self.repository)
        
        # Agents (lazy init)
        self._agents = {}
        self._running = False
    
    def _log(self, message: str, level: str = "INFO") -> None:
        if self.config.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            prefix = {"INFO": "->", "OK": "[OK]", "FAIL": "[X]", "WARN": "[!]", "FORK": "[FORK]"}.get(level, "->")
            print(f"[{ts}] {prefix} {message}")
    
    def _get_agent(self, role: str):
        if role not in self._agents:
            from conductor.agents import PlannerAgent, ExecutorAgent, ReviewerAgent, VerifierAgent, RepairAgent
            
            # Get role-specific model client
            client = self._model_clients.get(role, self.model_client)
            
            agents = {
                "planner": PlannerAgent(client),
                "executor": ExecutorAgent(client, self.mcp_discovery, self.config, self.project_root),
                "reviewer": ReviewerAgent(client),
                "verifier": VerifierAgent(client, self.mcp_discovery),
                "repair": RepairAgent(client, self.memory),
            }
            self._agents[role] = agents.get(role)
        
        return self._agents.get(role)
    
    # ─────────────────────────────────────────────────────────────
    # EXPLORATORY ORCHESTRATION
    # ─────────────────────────────────────────────────────────────
    
    async def explore(self, goal: str, num_strategies: int = 2) -> str:
        """
        Explore a goal with multiple strategies.
        
        Returns the winning plan ID.
        """
        self._log(f"EXPLORING: {goal[:60]}...")
        
        # Create root plan
        root_plan = await self.create_plan(goal)
        
        # Get strategies from memory
        strategies = self.exploration.suggest_strategies(goal, self.memory)[:num_strategies]
        self._log(f"  Strategies: {strategies}", "FORK")
        
        if len(strategies) <= 1:
            # No alternatives, run directly
            return await self.run(root_plan.id)
        
        # Fork into alternative plans
        forks = self.exploration.fork_plan(root_plan, strategies, "Exploring alternatives")
        
        for fork in forks:
            self._log(f"  Created fork: {fork.id} (strategy: {fork.strategy})", "FORK")
            self.repository.log_event(Event(
                event_type=EventType.PLAN_FORKED,
                plan_id=fork.id,
                payload={"strategy": fork.strategy, "parent": root_plan.id}
            ))
        
        # Execute all forks
        results = await asyncio.gather(*[self.run(f.id) for f in forks], return_exceptions=True)
        
        # Compare and select winner
        self._log("Comparing fork outcomes...", "FORK")
        comparison = self.exploration.compare_forks(root_plan.id)
        
        if comparison:
            self._log(f"  Winner: {comparison.winner_plan_id} (score: {comparison.winner_score:.2f})", "OK")
            self._log(f"  Pruned: {comparison.pruned_plan_ids}", "WARN")
            
            # Store winning strategy in memory
            winner = self.repository.get_plan(comparison.winner_plan_id)
            if winner and winner.strategy:
                self.memory.store_strategy(goal, winner.strategy, True)
            
            return comparison.winner_plan_id
        
        return root_plan.id
    
    async def create_plan(self, goal: str) -> Plan:
        """Create a new plan with memory context."""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        plan = Plan(id=plan_id, goal=goal)
        self.repository.create_plan(plan)
        
        self._log(f"Created plan: {plan_id}")
        
        # Recall patterns from memory
        memory_context = self.memory.get_planner_context(goal)
        if memory_context.get("recalled_patterns"):
            self._log(f"  Memory: {len(memory_context['recalled_patterns'])} patterns recalled")
        
        return plan
    
    async def run(self, plan_id: str) -> bool:
        """
        Main orchestration loop.
        
        explore → fork → execute → verify → compare → learn → converge
        """
        self._running = True
        iteration = 0
        
        plan = self.repository.get_plan(plan_id)
        if not plan:
            self._log(f"Plan not found: {plan_id}", "FAIL")
            return False
        
        self._log(f"Running plan: {plan.id}")
        if plan.strategy:
            self._log(f"  Strategy: {plan.strategy}")
        
        # Check halt
        if plan.status == PlanStatus.HALTED:
            self._log(f"Plan halted: {plan.halt_reason}", "WARN")
            return False
        
        plan.status = PlanStatus.EXECUTING
        self.repository.update_plan(plan)
        
        while self._running and iteration < self.config.max_iterations:
            iteration += 1
            plan = self.repository.get_plan(plan.id)
            
            # 1. Check terminal states
            if plan.status in (PlanStatus.HALTED, PlanStatus.PRUNED):
                self._log(f"Plan terminated: {plan.status.value}", "WARN")
                return False
            
            if self.repository.is_plan_complete(plan.id):
                plan.status = PlanStatus.COMPLETED
                self.repository.update_plan(plan)
                self._log("Plan completed!", "OK")
                
                # Learn from success
                steps = self.repository.get_steps(plan.id)
                self.memory.store_success(
                    plan.goal,
                    [s.to_dict() for s in steps] if hasattr(steps[0], 'to_dict') else [],
                    plan.strategy
                )
                
                return True
            
            # 2. Decide next action
            agent_role, step = self._decide_next(plan)
            
            if agent_role is None:
                self._log("No work remaining", "OK")
                return self.repository.is_plan_complete(plan.id)
            
            # 3. Policy check before execution
            if step:
                policy_result = self.policy_engine.evaluate({
                    "scope": "step",
                    "step_key": step.step_key,
                    "agent": agent_role,
                    "plan_id": plan.id,
                })
                
                if not policy_result.allowed:
                    self._log(f"  POLICY DENIED: {policy_result.reason}", "FAIL")
                    if policy_result.requires_approval:
                        self._log("  Halting for human approval", "WARN")
                        self.repository.halt_plan(plan.id, f"Approval required: {policy_result.reason}")
                        return False
                    continue
            
            # 4. Execute agent
            self._log(f"[{agent_role.upper()}]")
            if step:
                self._log(f"  Step: {step.step_key}")
                self.repository.update_step_status(step.step_key, StepStatus.RUNNING)
                self.mcp_recorder.set_step_context(step.step_key)
            
            agent = self._get_agent(agent_role)
            if not agent:
                self._log(f"  Unknown agent: {agent_role}", "FAIL")
                continue
            
            try:
                self.repository.log_event(Event(
                    event_type=EventType.AGENT_INVOKED,
                    plan_id=plan.id,
                    step_key=step.step_key if step else None,
                    agent=agent_role
                ))
                
                result = await agent.run(self.repository, plan, step)
                
                if result.success:
                    self._handle_success(plan, step, result, agent_role)
                else:
                    self._handle_failure(plan, step, result, agent_role)
                
            except Exception as e:
                self._log(f"  EXCEPTION: {e}", "FAIL")
                self._handle_exception(plan, step, e)
            
            finally:
                self.mcp_recorder.clear_step_context()
        
        return self.repository.is_plan_complete(plan.id)
    
    def _decide_next(self, plan: Plan) -> tuple[Optional[str], Optional[Step]]:
        """Decide which agent runs next."""
        steps = self.repository.get_steps(plan.id)
        
        # 1. No steps → planner
        if not steps:
            return "planner", None
        
        # 2. Check for verification needed
        for step in steps:
            if step.status == StepStatus.NEEDS_VERIFICATION:
                return "verifier", step
        
        # 3. Check for review needed
        for step in steps:
            if step.status == StepStatus.NEEDS_REVIEW:
                return "reviewer", step
        
        # 4. Check for failed steps needing repair
        for step in steps:
            if step.status == StepStatus.FAILED and step.attempt >= 2:
                return "repair", step
        
        # 5. Get next executable step
        next_step = self.repository.get_next_step(plan.id)
        if next_step:
            return "executor", next_step
        
        return None, None
    
    def _handle_success(self, plan: Plan, step: Optional[Step], result, agent_role: str):
        self._log("  Result: SUCCESS", "OK")
        plan.consecutive_failures = 0
        self.repository.update_plan(plan)
        
        # Apply step updates
        if step and "step_update" in result.updated_state:
            update = result.updated_state["step_update"]
            self.repository.update_step_status(
                step.step_key,
                update.get("status", StepStatus.COMPLETED),
                output=update.get("output"),
                artifacts=update.get("artifacts"),
                mcp_used=update.get("mcp_used"),
            )
            
            # Confidence and verification
            if "confidence" in update:
                self.repository.update_step_confidence(step.step_key, update["confidence"])
            if update.get("verified"):
                self.repository.mark_step_verified(step.step_key)
        
        # New steps from planner
        if "new_steps" in result.updated_state:
            for i, s in enumerate(result.updated_state["new_steps"]):
                new_step = Step(
                    step_key=s.get("id", f"step_{uuid.uuid4().hex[:8]}"),
                    plan_id=plan.id,
                    sequence=i,
                    description=s.get("description", ""),
                    agent=s.get("agent", "executor"),
                    depends_on=s.get("depends_on", []),
                    strategy=plan.strategy,
                )
                self.repository.create_step(new_step)
        
        # Update model metrics
        if self.model_client:
            model_name = getattr(self.model_client, 'model', 'unknown')
            self.memory.update_model_metrics(model_name, agent_role, success=True)
    
    def _handle_failure(self, plan: Plan, step: Optional[Step], result, agent_role: str):
        self._log(f"  Result: FAILED - {result.error}", "FAIL")
        plan.consecutive_failures += 1
        
        if plan.consecutive_failures >= self.config.max_consecutive_failures:
            self.repository.halt_plan(plan.id, "Max consecutive failures")
            self._log("Plan halted", "WARN")
            return
        
        self.repository.update_plan(plan)
        
        if step:
            self.repository.update_step_status(step.step_key, StepStatus.FAILED, error=result.error)
            
            # Learn from failure
            if result.error:
                self.memory.store_failure(result.error, step.description)
    
    def _handle_exception(self, plan: Plan, step: Optional[Step], exception: Exception):
        plan.consecutive_failures += 1
        if plan.consecutive_failures >= self.config.max_consecutive_failures:
            self.repository.halt_plan(plan.id, str(exception))
        else:
            self.repository.update_plan(plan)
        
        if step:
            self.repository.update_step_status(step.step_key, StepStatus.FAILED, error=str(exception))
    
    # ─────────────────────────────────────────────────────────────
    # CLI COMMANDS
    # ─────────────────────────────────────────────────────────────
    
    def status(self) -> dict:
        plan = self.repository.get_active_plan()
        if not plan:
            return {"status": "no_plan"}
        
        steps = self.repository.get_steps(plan.id)
        forks = self.exploration.get_forks(plan.id)
        
        return {
            "plan_id": plan.id,
            "goal": plan.goal,
            "status": plan.status.value,
            "strategy": plan.strategy,
            "score": plan.score,
            "steps_total": len(steps),
            "steps_completed": sum(1 for s in steps if s.status == StepStatus.COMPLETED),
            "forks": len(forks),
            "halted": plan.status == PlanStatus.HALTED,
        }
    
    def resume(self, plan_id: str = None):
        self.repository.resume_plan(plan_id or self.repository.get_active_plan().id)
        self._log("Plan resumed", "OK")
    
    def explain_decision(self, step_key: str) -> dict:
        return self.replay.explain_failure(step_key)
    
    def simulate(self, plan_id: str, modifications: dict) -> dict:
        return self.replay.simulate(plan_id, modifications)
