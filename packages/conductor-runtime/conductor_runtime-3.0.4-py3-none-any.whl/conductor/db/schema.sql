-- Conductor++ v3.0 Database Schema
-- Exploratory orchestration with memory and policies

-- ═══════════════════════════════════════════════════════════════
-- EXPLORATION: Forks and Branches
-- ═══════════════════════════════════════════════════════════════

-- Plans now support forking
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    parent_plan_id TEXT,  -- NULL for root plans
    fork_reason TEXT,     -- Why this fork was created
    strategy TEXT,        -- Strategy name for this branch
    status TEXT DEFAULT 'exploring' CHECK(status IN ('exploring', 'executing', 'completed', 'failed', 'halted', 'pruned', 'winner')),
    score REAL,           -- Comparative score after execution
    halt_reason TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_plan_id) REFERENCES plans(id)
);

-- Steps with confidence and verification
CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_key TEXT UNIQUE NOT NULL,
    plan_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    description TEXT NOT NULL,
    agent TEXT NOT NULL CHECK(agent IN ('executor', 'reviewer', 'verifier', 'repair')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed', 'halted', 'needs_review', 'needs_verification', 'skipped')),
    confidence REAL DEFAULT 0.0,  -- 0.0-1.0 output confidence
    verified INTEGER DEFAULT 0,    -- Has Verifier confirmed?
    depends_on TEXT,
    attempt INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    strategy TEXT,                 -- Which strategy was used
    output TEXT,
    artifacts TEXT,
    mcp_used TEXT,
    last_error TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

-- ═══════════════════════════════════════════════════════════════
-- LONG-TERM MEMORY: Cross-plan learning
-- ═══════════════════════════════════════════════════════════════

-- Successful patterns to reuse
CREATE TABLE IF NOT EXISTS memory_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL CHECK(pattern_type IN ('success', 'failure', 'strategy', 'policy_override')),
    goal_signature TEXT NOT NULL,  -- Hashed/normalized goal for matching
    pattern_data TEXT NOT NULL,    -- JSON: steps, strategies, etc.
    success_count INTEGER DEFAULT 1,
    failure_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Failure modes to avoid
CREATE TABLE IF NOT EXISTS memory_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_signature TEXT NOT NULL,   -- Normalized error pattern
    context_signature TEXT,          -- What was being attempted
    avoidance_strategy TEXT,         -- How to avoid this
    occurrence_count INTEGER DEFAULT 1,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance history
CREATE TABLE IF NOT EXISTS model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    role TEXT NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0,
    avg_confidence REAL DEFAULT 0,
    last_failure_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, role)
);

-- ═══════════════════════════════════════════════════════════════
-- POLICIES: Governance as code
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    policy_type TEXT NOT NULL CHECK(policy_type IN ('allow', 'deny', 'require_approval', 'require_verification')),
    scope TEXT NOT NULL,             -- 'mcp', 'step', 'plan', 'global'
    condition TEXT NOT NULL,         -- JSON condition expression
    action TEXT,                     -- What to do when matched
    priority INTEGER DEFAULT 50,     -- Higher = evaluated first
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policy evaluation log
CREATE TABLE IF NOT EXISTS policy_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER,
    step_key TEXT,
    plan_id TEXT,
    result TEXT NOT NULL CHECK(result IN ('allowed', 'denied', 'approval_required', 'verification_required')),
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(id)
);

-- ═══════════════════════════════════════════════════════════════
-- EVENTS: Enhanced for replay
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    plan_id TEXT,
    step_key TEXT,
    agent TEXT,
    payload TEXT,
    state_snapshot TEXT,  -- Full state at this point for replay
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MCP calls with verification data
CREATE TABLE IF NOT EXISTS mcp_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_key TEXT,
    mcp_server TEXT NOT NULL,
    action TEXT NOT NULL,
    request TEXT,
    response TEXT,
    success INTEGER DEFAULT 1,
    verified INTEGER DEFAULT 0,    -- Has Verifier checked this?
    evidence TEXT,                 -- Verification evidence
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════
-- REPAIR: Self-healing metadata
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    step_key TEXT,
    failure_pattern TEXT NOT NULL,
    repair_action TEXT NOT NULL,   -- What was changed
    repair_type TEXT CHECK(repair_type IN ('step_modification', 'plan_mutation', 'strategy_switch', 'model_switch')),
    success INTEGER,               -- Did the repair work?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_plans_parent ON plans(parent_plan_id);
CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);
CREATE INDEX IF NOT EXISTS idx_steps_plan_id ON steps(plan_id);
CREATE INDEX IF NOT EXISTS idx_steps_status ON steps(status);
CREATE INDEX IF NOT EXISTS idx_memory_patterns_goal ON memory_patterns(goal_signature);
CREATE INDEX IF NOT EXISTS idx_memory_failures_error ON memory_failures(error_signature);
CREATE INDEX IF NOT EXISTS idx_events_plan_id ON events(plan_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_policies_scope ON policies(scope, enabled);
