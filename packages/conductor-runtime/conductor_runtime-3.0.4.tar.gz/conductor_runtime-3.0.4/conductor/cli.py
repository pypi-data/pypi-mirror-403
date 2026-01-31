"""
Conductor CLI.
Exploratory orchestration with self-repair and learning.

Commands:
  explore <goal>  - Run with forked strategies
  build <goal>    - Run single strategy
  status          - Show current status
  resume          - Resume halted plan
  events          - Show event log
  explain <step>  - Explain decision/failure
  simulate        - What-if analysis
  policy          - Show/manage policies
"""
import asyncio
import click
from pathlib import Path

from conductor.conductor import Conductor
from conductor.config import ConductorConfig


@click.group()
@click.option("--project", "-p", default=".", help="Project root directory")
@click.option("--verbose/--quiet", "-v/-q", default=True, help="Verbose output")
@click.pass_context
def cli(ctx, project, verbose):
    """Conductor - Post-Conductor Orchestration System."""
    ctx.ensure_object(dict)
    ctx.obj["project"] = str(Path(project).absolute())
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("project_name")
@click.option("--target-dir", "-t", default=".", help="Parent directory for project")
@click.pass_context
def init(ctx, project_name, target_dir):
    """Initialize a new Conductor project."""
    import shutil
    
    target = Path(target_dir).absolute() / project_name
    template_root = Path(__file__).parent.parent
    
    if target.exists():
        click.echo(f"[X] Directory already exists: {target}")
        raise SystemExit(1)
    
    click.echo(f"Creating Conductor project: {project_name}")
    click.echo(f"Location: {target}\n")
    
    # Create project directory
    target.mkdir(parents=True)
    
    # Copy project workspace only (NOT the runtime)
    src_project = template_root / "project"
    if src_project.exists():
        shutil.copytree(src_project, target / "project")
        click.echo("  + Created workspace: project/")
    
    # Create .conductor state directory
    (target / ".conductor").mkdir(exist_ok=True)
    click.echo("  + Created: .conductor/")
    
    # Copy policy example if available
    src_policy = template_root / ".conductor" / "policy.yaml.example"
    if src_policy.exists():
        shutil.copy2(src_policy, target / ".conductor" / "policy.yaml.example")
        click.echo("  + Created: .conductor/policy.yaml.example")
    
    # Create pyproject.toml with conductor-runtime dependency
    pyproject = f'''[project]
name = "{project_name}"
version = "0.1.0"
dependencies = ["conductor-runtime"]

[project.scripts]
conductor = "conductor.cli:main"
'''
    (target / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    click.echo("  + Created: pyproject.toml")
    
    # Create .env.example
    env_content = '''# Conductor Configuration
GEMINI_API_KEY=your_api_key_here
'''
    (target / ".env.example").write_text(env_content, encoding="utf-8")
    click.echo("  + Created: .env.example")
    
    # Create README
    readme = f"""# {project_name}

> Powered by Conductor

## Setup

```bash
pip install conductor-runtime
cp .env.example .env
# Edit .env with your API key
```

## Usage

```bash
conductor explore "your goal here"
conductor status
```

## Project Context

Edit files in `project/` to guide the system.
"""
    (target / "README.md").write_text(readme, encoding="utf-8")
    click.echo("  + Created: README.md")
    
    click.echo(f"\n[OK] Project '{project_name}' created!")
    click.echo(f"\nNext: cd {project_name} && conductor explore \"your goal\"")


@cli.command()
@click.argument("goal")
@click.option("--strategies", "-s", default=2, help="Number of parallel strategies")
@click.pass_context
def explore(ctx, goal, strategies):
    """Explore a goal with multiple forked strategies."""
    config = ConductorConfig(verbose=ctx.obj["verbose"])
    conductor = Conductor(ctx.obj["project"], config)
    
    async def run():
        return await conductor.explore(goal, num_strategies=strategies)
    
    winner_id = asyncio.run(run())
    
    if winner_id:
        click.echo(f"\n✓ Exploration complete. Winner: {winner_id}")
    else:
        click.echo("\n✗ Exploration failed")
        raise SystemExit(1)


@cli.command()
@click.argument("goal")
@click.pass_context
def build(ctx, goal):
    """Start orchestration with single strategy (no forking)."""
    config = ConductorConfig(verbose=ctx.obj["verbose"])
    conductor = Conductor(ctx.obj["project"], config)
    
    async def run():
        plan = await conductor.create_plan(goal)
        return await conductor.run(plan.id)
    
    success = asyncio.run(run())
    
    if success:
        click.echo("\n✓ Build completed")
    else:
        click.echo("\n✗ Build incomplete or halted")


@cli.command()
@click.option("--plan-id", "-i", default=None, help="Specific plan ID")
@click.pass_context
def resume(ctx, plan_id):
    """Resume a halted plan."""
    config = ConductorConfig(verbose=ctx.obj["verbose"])
    conductor = Conductor(ctx.obj["project"], config)
    
    conductor.resume(plan_id)
    
    async def run():
        return await conductor.run(plan_id)
    
    success = asyncio.run(run())
    click.echo("\n✓ Resumed" if success else "\n✗ Still incomplete")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current execution status."""
    config = ConductorConfig(verbose=False)
    conductor = Conductor(ctx.obj["project"], config)
    
    s = conductor.status()
    
    click.echo("\n=== Conductor Status ===\n")
    
    if s.get("status") == "no_plan":
        click.echo("No active plan. Use 'explore <goal>' or 'build <goal>'")
        return
    
    click.echo(f"Plan: {s.get('plan_id')}")
    click.echo(f"Goal: {s.get('goal', 'N/A')[:70]}...")
    click.echo(f"Status: {s.get('status')}")
    click.echo(f"Strategy: {s.get('strategy', 'default')}")
    
    if s.get("score"):
        click.echo(f"Score: {s.get('score'):.2f}")
    
    click.echo(f"\nProgress: {s.get('steps_completed', 0)}/{s.get('steps_total', 0)} steps")
    
    if s.get("forks", 0) > 0:
        click.echo(f"Forks: {s.get('forks')}")
    
    if s.get("halted"):
        click.echo("\n⚠️  Plan is HALTED. Use 'resume' to continue.")


@cli.command()
@click.option("--limit", "-n", default=20, help="Number of events")
@click.pass_context
def events(ctx, limit):
    """Show recent events from the log."""
    from conductor.db import Repository
    
    config = ConductorConfig(verbose=False)
    db_path = f"{ctx.obj['project']}/{config.db_path}"
    repo = Repository(db_path)
    
    events = repo.get_events(limit=limit)
    
    click.echo("\n=== Event Log ===\n")
    
    for event in reversed(events):
        click.echo(f"[{event.created_at or 'N/A'}] {event.event_type.value}")
        if event.step_key:
            click.echo(f"  └ Step: {event.step_key}")
        if event.agent:
            click.echo(f"  └ Agent: {event.agent}")


@cli.command("explain")
@click.argument("step_key")
@click.pass_context
def explain_cmd(ctx, step_key):
    """Explain why a step failed or a decision was made."""
    config = ConductorConfig(verbose=False)
    conductor = Conductor(ctx.obj["project"], config)
    
    explanation = conductor.explain_decision(step_key)
    
    click.echo(f"\n=== Explanation: {step_key} ===\n")
    
    click.echo(f"Description: {explanation.get('description', 'N/A')}")
    click.echo(f"Error: {explanation.get('error', 'None')}")
    click.echo(f"Attempts: {explanation.get('attempts', 0)}")
    
    if explanation.get("causal_chain"):
        click.echo("\nCausal Chain:")
        for cause in explanation["causal_chain"]:
            click.echo(f"  ← {cause['step']}: {cause['type']}")
    
    if explanation.get("mcp_calls"):
        click.echo("\nMCP Calls:")
        for call in explanation["mcp_calls"]:
            status = "✓" if call["success"] else "✗"
            click.echo(f"  {status} {call['server']}.{call['action']}")


@cli.command()
@click.option("--skip", "-s", multiple=True, help="Steps to skip")
@click.option("--force-success", "-f", multiple=True, help="Steps to force success")
@click.pass_context
def simulate(ctx, skip, force_success):
    """Simulate what-if scenarios."""
    config = ConductorConfig(verbose=False)
    conductor = Conductor(ctx.obj["project"], config)
    
    status = conductor.status()
    if status.get("status") == "no_plan":
        click.echo("No plan to simulate")
        return
    
    modifications = {
        "skip_steps": list(skip),
        "force_success": list(force_success),
    }
    
    result = conductor.simulate(status["plan_id"], modifications)
    
    click.echo("\n=== Simulation Result ===\n")
    click.echo(f"Projected Outcome: {result.get('projected_outcome')}")
    
    if result.get("steps_affected"):
        click.echo("\nModifications:")
        for step in result["steps_affected"]:
            click.echo(f"  {step['step']}: {step['modification']}")
    
    if result.get("warnings"):
        click.echo("\n⚠️  Warnings:")
        for w in result["warnings"]:
            click.echo(f"  - {w}")


@cli.command()
@click.pass_context
def policy(ctx):
    """Show active policies."""
    from conductor.policy import PolicyEngine
    
    engine = PolicyEngine()
    
    click.echo("\n=== Active Policies ===\n")
    
    for p in engine._policies:
        status = "✓" if p.enabled else "✗"
        click.echo(f"{status} [{p.priority}] {p.name}")
        click.echo(f"    Type: {p.policy_type.value}")
        click.echo(f"    Scope: {p.scope}")
        click.echo(f"    Action: {p.action}")
        click.echo()


@cli.command()
@click.pass_context
def replay(ctx):
    """Show available replay points."""
    from conductor.db import Repository
    
    config = ConductorConfig(verbose=False)
    db_path = f"{ctx.obj['project']}/{config.db_path}"
    repo = Repository(db_path)
    
    plan = repo.get_active_plan()
    if not plan:
        click.echo("No active plan")
        return
    
    steps = repo.get_steps(plan.id)
    
    click.echo("\n=== Replay Points ===\n")
    click.echo("Use 'explain <step_key>' to inspect any point:\n")
    
    for step in steps:
        status_icon = {"completed": "✓", "failed": "✗", "pending": "○"}.get(step.status.value, "?")
        click.echo(f"{status_icon} {step.step_key}: {step.description[:50]}...")


@cli.command("handoff-metrics")
@click.pass_context
def handoff_metrics(ctx):
    """Show handoff execution metrics."""
    from conductor.handoff import HandoffAdapter
    
    project_path = ctx.obj["project"]
    adapter = HandoffAdapter(project_path)
    metrics = adapter.metrics
    
    click.echo("\nHandoff Metrics")
    click.echo("===============")
    click.echo(f"Tasks Created:   {metrics.tasks_created}")
    click.echo(f"Tasks Completed: {metrics.tasks_completed}")
    click.echo(f"Tasks Failed:    {metrics.tasks_failed}")
    click.echo(f"Timeouts:        {metrics.tasks_timeout}")
    click.echo(f"Success Rate:    {metrics.success_rate:.1%}")
    click.echo(f"Avg Exec Time:   {metrics.avg_execution_time_ms:.0f}ms")
    click.echo("")


@cli.command()
@click.option("--expired", is_flag=True, help="Remove expired pending tasks")
@click.option("--completed", is_flag=True, help="Remove completed task files (keeps metrics)")
@click.option("--failed", is_flag=True, help="Remove failed task files")
@click.option("--logs", is_flag=True, help="Remove old log files (keeps last 7 days)")
@click.option("--all", "clean_all", is_flag=True, help="Remove all cleanable items")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without removing")
@click.pass_context
def cleanup(ctx, expired, completed, failed, logs, clean_all, dry_run):
    """Clean up handoff state files."""
    from pathlib import Path
    from datetime import datetime, timedelta
    import shutil
    
    project_path = ctx.obj["project"]
    handoff_root = Path(project_path) / ".conductor" / "handoff"
    
    if not handoff_root.exists():
        click.echo("No handoff directory found.")
        return
    
    if clean_all:
        expired = completed = failed = logs = True
    
    if not any([expired, completed, failed, logs]):
        click.echo("Specify what to clean: --expired, --completed, --failed, --logs, or --all")
        return
    
    removed_count = 0
    
    # Walk through all plan/fork directories
    for plan_dir in handoff_root.iterdir():
        if not plan_dir.is_dir() or not plan_dir.name.startswith("plan_"):
            continue
        
        for fork_dir in plan_dir.iterdir():
            if not fork_dir.is_dir() or not fork_dir.name.startswith("fork_"):
                continue
            
            # Clean expired pending tasks
            if expired:
                pending_dir = fork_dir / "pending"
                if pending_dir.exists():
                    for task_file in pending_dir.glob("*.task.json"):
                        try:
                            import json
                            data = json.loads(task_file.read_text())
                            expires = datetime.fromisoformat(data.get("expires_at", "2099-01-01"))
                            if expires < datetime.utcnow():
                                if dry_run:
                                    click.echo(f"Would remove: {task_file}")
                                else:
                                    task_file.unlink()
                                removed_count += 1
                        except Exception:
                            pass
            
            # Clean completed tasks
            if completed:
                completed_dir = fork_dir / "completed"
                if completed_dir.exists():
                    for f in completed_dir.iterdir():
                        if dry_run:
                            click.echo(f"Would remove: {f}")
                        else:
                            f.unlink()
                        removed_count += 1
            
            # Clean failed tasks
            if failed:
                failed_dir = fork_dir / "failed"
                if failed_dir.exists():
                    for f in failed_dir.iterdir():
                        if dry_run:
                            click.echo(f"Would remove: {f}")
                        else:
                            f.unlink()
                        removed_count += 1
    
    # Clean old logs
    if logs:
        logs_dir = Path(project_path) / ".conductor" / "logs"
        if logs_dir.exists():
            cutoff = datetime.now() - timedelta(days=7)
            for log_file in logs_dir.glob("*.log"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
                    if dry_run:
                        click.echo(f"Would remove: {log_file}")
                    else:
                        log_file.unlink()
                    removed_count += 1
    
    action = "Would remove" if dry_run else "Removed"
    click.echo(f"\n{action} {removed_count} items.")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
