# Conductor

**Autonomous, Policy-Governed, Learning Orchestration Runtime**

> An operating system for complex work.

## What is Conductor?

Conductor is a **post-orchestration system** that goes beyond traditional workflow engines:

| Traditional Orchestrators | Conductor                   |
| ------------------------- | --------------------------- |
| Static DAGs               | Dynamic, forking plans      |
| Retry on failure          | Self-repair with learning   |
| Logs for debugging        | Time-travel replay          |
| Hardcoded rules           | Policy-as-code governance   |
| Trust assertions          | Evidence-based verification |

## Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│                        CONDUCTOR                            │
│  (Orchestrator: plans, delegates, verifies, learns)         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ File-Based Handoff
                          │ (.conductor/handoff/)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      ANTIGRAVITY                             │
│  (Executor: receives task files, executes code changes)      │
└─────────────────────────────────────────────────────────────┘
```

**Conductor plans. Antigravity executes. Files are the contract.**

---

## Execution Modes

Conductor supports two execution modes:

| Mode        | Description                                     | When to Use                              |
| ----------- | ----------------------------------------------- | ---------------------------------------- |
| **LLM**     | Direct API calls to Gemini                      | Simple tasks, quick iterations           |
| **Handoff** | File-based delegation to Antigravity IDE agents | Complex code changes, audit requirements |

### File-Based Handoff (Recommended for Production)

```
.conductor/handoff/
├── plan_<id>/
│   └── fork_<id>/
│       ├── pending/          # Tasks waiting for execution
│       │   └── step_001.task.json
│       ├── in_progress/      # Currently executing
│       ├── completed/        # Successfully finished
│       │   ├── step_001.task.json
│       │   ├── step_001.result.json
│       │   ├── step_001.explanation.md
│       │   └── step_001.provenance.json
│       ├── failed/           # Failed tasks
│       └── audit.log         # Complete event history
└── metrics.json              # Execution statistics
```

**Why use handoff mode?**

- ✅ Complete audit trail
- ✅ Constraint enforcement
- ✅ Pre-execution confidence scoring
- ✅ Human-readable explanations
- ✅ Cryptographic provenance

---

## CLI Commands

| Command                      | Description                    |
| ---------------------------- | ------------------------------ |
| `conductor init <name>`      | Create new project             |
| `conductor explore "<goal>"` | Run with forked strategies     |
| `conductor build "<goal>"`   | Run single strategy            |
| `conductor status`           | Show current status            |
| `conductor policy`           | View active policies           |
| `conductor explain <step>`   | Explain decision/failure       |
| `conductor events`           | View event log                 |
| `conductor resume`           | Resume halted plan             |
| `conductor handoff-metrics`  | Show handoff execution metrics |

---

## Task File Contract

Every handoff task includes:

```json
{
  "task_id": "step_001",
  "instruction": "Create a hello.py file...",
  "allowed_files": ["hello.py"],
  "constraints": [
    "Do NOT modify files outside allowed_files",
    "Do NOT run shell commands unless instructed"
  ],
  "timeout_seconds": 300,
  "confidence": {
    "score": 0.89,
    "level": "high"
  }
}
```

**Confidence Levels:**

- **HIGH (0.8-1.0):** Fully autonomous execution
- **MEDIUM (0.5-0.8):** Proceed with caution
- **LOW (0-0.5):** Human review recommended

---

## Project-Level Policies

Create `.conductor/policy.yaml` to define inherited constraints:

```yaml
global_constraints:
  - 'Never modify files in /core'
  - 'Always include tests for new functions'

file_rules:
  protected_patterns:
    - '*.lock'
    - 'migrations/*'

behavior:
  max_diff_lines: 500
  timeout_seconds: 300
```

**Merge behavior:** Project → Plan → Step (later overrides earlier)

---

## Common Failure Modes & Recovery

| Failure              | Cause                 | Recovery                   |
| -------------------- | --------------------- | -------------------------- |
| Task timeout         | Execution too slow    | Increase `timeout_seconds` |
| Constraint violation | Outside allowed_files | Fix task scope             |
| Low confidence       | Novel task pattern    | Add historical context     |
| Checksum mismatch    | Task tampered         | Re-create from source      |

**All failures are logged in `audit.log` with full context.**

---

## Quickstart

### 1. Create a Project

```bash
conductor init my-project
cd my-project
```

### 2. Set Your API Key

```bash
export GEMINI_API_KEY=your_key_here
```

### 3. Run Your First Goal

```bash
conductor explore "Create a Python CLI task manager"
```

### 4. Check Handoff Metrics

```bash
conductor handoff-metrics
```

---

## Requirements

- Python 3.11+
- Gemini API key (or compatible LLM)
- click (`pip install click`)

## License

MIT

---

**Built with ❤️ for autonomous execution**
