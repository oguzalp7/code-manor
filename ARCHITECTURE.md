# 🏰 Code-Manor Architecture & Orchestration Specification

> **Status:** Canonical Architectural Baseline (v1.2)  
> **Author:** Oguz Alp & Code-Manor Core System  
> **Scope:** Agent-Facing Operating Contract & Deterministic Machine State

---

## 🏛️ 1. Estate Hierarchy & Boundary Invariants

Code-Manor organizes agentic software delivery as a strict British household hierarchy. Each tier operates within a mathematically bounded scope to eliminate role bleed, context rot, and zombie process sprawl.

```
                      👑 HUMAN (Master of the Estate)
                                    │
                                    ▼
                      🎩 /steward (Grand Conductor)
                          • Multi-Project Portfolio
                          • Zero-Search projects.json
                          • Context Insulation & Frontier Dispatch
                                    │
                                    ▼
                      🎩 /butler (Project Conductor)
                          • Cognitive Seams (frontier-axi)
                          • Vertical Task State (tasks-axi)
                          • Memory & Specs (.memory/, specs/)
                          • Independent Two-Axis Review (/code-review)
                                    │
                                    ▼
                      🧹 maid (Subprocess Worker via agy -p)
                          • Single-Ticket Vertical TDD (/tdd)
                          • Zero Self-Review, Zero Tampering
                          • Tier 1 Gate (make check) + Ticket Gate (no-mistakes)
```

### 🔒 Core Invariants (Non-Negotiable)

1. **Butler Zero-Self-Code Boundary (Dual-Lane Model):** Butler is primarily an architect, conductor, and reviewer. Butler's default writing scope is restricted to `.memory/**`, `specs/**`, `.tasks.toml`, `CONTEXT.md`, and `handoff.md`.
   - *Fast-Path Threshold Exception:* For minor, surgical tasks touching $\le 3$ files and $\le 50$ lines (e.g. trivial typo fixes, single-column schema/Zod adjustments, minor config or type exports), Butler is authorized to edit directly in-context, run the fast targeted test (`npx vitest run <target>`), commit, and close the ticket without spinning up Maid.
   - *Deep-Path Delegation:* Multi-file refactoring, multi-step TDD, or architectural seams must be delegated to Maid via `bin/run_maid_loop.sh`.
2. **Maid Anti-Tampering & Anti-Fake-Testing Rule:** Modifying assertion lines or deleting existing tests in `tests/` to force green is strictly forbidden. Furthermore, writing fake tests that inspect source code via `fs.readFileSync`, `readFile`, or regex/string matching is strictly forbidden. Tests must assert against runtime function I/O, component rendering, or user behavior.
3. **No Dangling Background Daemons:** Maid is executed strictly as a synchronous run-to-completion CLI subprocess (`agy -p`). Zero dangling subagent daemons or orphaned background workers are permitted in RAM.
4. **Single Worker Session per Batch:** Butler reuses at most ONE warm worker session (`$MAID_CONV_ID`) per milestone batch, subject to the 3-Tier Traffic Light Context Gauge.

---

## 🌉 2. Upstream-to-Downstream Protocol Bridge & Execution Ladders

Ambiguous ideas never enter the vertical execution task graph directly. Code-Manor strictly bifurcates cognitive fog from executable slices.

```
[ Nascent Fog ] ──> frontier-axi add ──> /grilling ──> /to-spec ──> /to-tickets ──> tasks-axi add ──> [ Vertical Slices ]
                                                              │
                                                     /steward-dispatch
                                                              │
                                                         handoff.md
                                                              │
                                                     /butler-takeover
                                                              │
                                     ┌────────────────────────┴────────────────────────┐
                                     ▼                                                 ▼
                          ⚡ Fast-Path (In-Context)                          🛡️ Deep-Path (Maid)
                          • <= 3 files, minor fix                           • > 3 files, full TDD
                          • vitest run <target>                             • 5-Stage Outside-In Ladder
                          • Zero Maid Subprocess                            • Zero-Thinking Wait
```

### Operating Recipe:
1. **Upstream Frontier:** Nascent ideas, architectural questions, and seams are staged in `frontier-axi`.
2. **Grilling & Convergence:** Open questions are resolved via `/grilling` or `/wayfinder`.
3. **Specification & Slicing:** Settled frontiers synthesize into `specs/<slug>.md` (with numbered `[AC-xx]` criteria) and slice into atomic vertical tickets via `/to-tickets`.
4. **Autonomous Dispatch (`/steward-dispatch` $\rightarrow$ `/butler-takeover`):**
   - Steward runs `/steward-dispatch` to compact the frontier milestone into `handoff.md`.
   - Butler triggers `/butler-takeover` to ingest `handoff.md`, evaluate scope (Fast-Path vs. Deep-Path), pin `$BASE_SHA`, and begin execution without human errand-boy overhead.

### 🪜 5-Stage Outside-In Execution Ladder (Maid's Slicing Protocol):
To prevent low-effort worker models from horizontal collapse (touching UI, API, and DB simultaneously and breaking syntax across 6 files), Butler structures full-stack vertical slices into an explicit, top-down ladder:
1. **Step 1 [Frontend UI Layer]:** Create UI component with mock props/state + unit test. Verify loading, empty, and error render states.
2. **Step 2 [API / Server Action Layer]:** Create route handler / server action with mock database + unit test. Validate Zod request/response DTO schemas.
3. **Step 3 [DB Layer / Migration]:** Declare minimal schema changes and migration strictly required by Step 2.
4. **Step 4 [DB Integration]:** Run targeted integration test against local test database.
5. **Step 5 [Frontend Wire-up]:** Connect UI component to live Server Action / API and run wire-up integration test.

### 🔌 In-Memory Seam First Rule for 3rd-Party Infrastructure:
When a tracer bullet involves external or asynchronous services (Job Queues like BullMQ, Redis caching, Vector DBs, Schedulers):
- **Tracer Bullet Phase (Hermetic In-Memory Seam):** Maid **NEVER** connects live Docker/Redis/network daemons during the initial vertical slice. Butler requires defining a clean interface (Seam) and an `InMemory...` stub (e.g. `InMemoryJobQueue`). The entire slice executes end-to-end in $< 50\text{ ms}$, ensuring Tier 1 `make check` remains 100% hermetic.
- **Adapter Phase (Isolated Ticket):** The live infrastructure adapter (`BullMQJobQueue`, `RedisCache`) is implemented in a separate, follow-up ticket and tested exclusively in `test:integration`.

---

## ⚙️ 3. Declarative Model & Reasoning Routing (`routing.json`)

Model configurations and reasoning effort levels are never hardcoded inside prompt strings or Markdown instructions. They are resolved declaratively from `routing.json`.

### Schema (`~/.gemini/config/plugins/code-manor/routing.json`):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "1.1.0",
  "routing": {
    "steward": {
      "model": "gemini-3.1-pro-high",
      "effort": "high",
      "description": "Grand conductor for portfolio frontiers, interviews, specs, and tickets."
    },
    "butler": {
      "model": "gemini-3.1-pro-high",
      "effort": "high",
      "description": "Project conductor, ticket scheduler, and independent Two-Axis reviewer."
    },
    "maid": {
      "model": "gemini-3.8-flash-low",
      "effort": "low",
      "flags": [
        "--dangerously-skip-permissions"
      ],
      "gate_command": "no-mistakes axi run --skip ci",
      "context_gauge": {
        "green_zone_max": 180000,
        "yellow_zone_max": 250000,
        "hard_ceiling_dump_zone": 250000
      },
      "max_tickets_per_worker": 5,
      "description": "Frugal vertical-slice TDD implementer running via agy -p subprocess."
    }
  }
}
```

### Routing Resolution Precedence:
1. **Workspace Override:** `<workspace-root>/.agents/routing.json` (if present)
2. **Fleet Registry Override:** `projects.json` entry `model_routing` (if present)
3. **Global Plugin SSOT:** `~/.gemini/config/plugins/code-manor/routing.json`

---

## 🚀 4. Subprocess Worker Execution Engine (`run_maid_loop.sh`)

Butler drives Maid as an isolated operating system process managed by the autonomous multi-turn loop driver (`bin/run_maid_loop.sh`) rather than an in-memory high-reasoning GUI subagent.

### Invariants & Execution Protocols:
- **Autonomous Multi-Turn Looping:** Avoids the single-turn premature exit and 5-second background task teardown of bare `agy -p`. The driver coordinates turns via `agy --continue` until tests pass.
- **Two-Tier Test Execution Protocol (Inner TDD Loop vs. Outer Hermetic Exit Gate):**
  - *Inner TDD Loop (< 2s):* During implementation turns, Maid iterates strictly against the ticket's targeted test command (`TARGET_TEST_CMD`, e.g., `npx vitest run tests/unit/...`). Maid turns red tests into green in seconds without incurring the massive latency of the entire monorepo test suite.
  - *Outer Hermetic Exit Gate (~72s):* The full hermetic `make check` (linting + static typechecking + complete in-memory unit suite) executes strictly ONCE when Maid finishes edits and is ready to exit. If `make check` passes, it proceeds to commit and gate verification.
- **Feedback Black Hole Resolution (Trace Backpropagation):**
  - Previously, agent tool calls swallowed or truncated gate failure traces, leaving Maid blind to compiler and linter errors.
  - The driver captures failure traces into `GATE_LOG` and dynamically injects the exact compiler diagnostics, type errors, or assertion failures into `NEXT_PROMPT` on `agy --continue`. Maid never guesses why a gate failed.
- **Circuit Breaker Protocol (`exit 2` Human Escalation):**
  - Detects non-transient infrastructure and authentication failures (e.g., `401 Unauthorized`, `ACCESS_TOKEN_TYPE_UNSUPPORTED`, expired API keys, CLI argument syntax errors).
  - Immediately aborts execution with `exit 2`, surfacing a high-priority alert to the Human Master of the Estate rather than burning tokens across futile retry loops.
- **Dynamic Intent Injection:**
  - Extracts the Ticket ID and human objective from the prompt header and dynamically injects them into the ticket verification gate (`no-mistakes axi run --intent "..."`), ensuring full semantic alignment.
- **Git Pathspec Disruption Filter:**
  - Dirty tree checks explicitly exclude non-code artifacts: `git status --porcelain -- ':!backlog.md' ':!.tasks.toml' ':!.memory/**' ':!*.md'`. Architectural updates and task state transitions never trigger false-positive code synchronization violations.
- **Mandatory Explicit Scoping Contract:**
  - Prompts generated by Butler MUST declare `Target Implementation Files`, `Target Test Files`, and `Strict Boundary Prohibition` to eliminate lateral scope creep across unrelated monorepo modules.
- **Dual-Tee Logging & Real-Time Observability:**
  - Terminal output is simultaneously mirrored to `.memory/scratch/active_maid_loop.log` via `exec > >(tee "$LOG_FILE") 2>&1`, enabling real-time headless monitoring.
- **Frugal In-Process Fallback (`flash_lite`):** If `agy` CLI is unavailable, Butler falls back to native `invoke_subagent` using **`Model: "flash_lite"`** (NOT `"flash"` or `"pro"`), guaranteeing minimal/zero reasoning token consumption and protecting user quota.

### Execution Command Recipe:
```bash
# 1. Butler prepares ticket prompt file with explicit scope:
PROMPT_FILE=".memory/scratch/ticket-<id>.txt"

# 2. Dispatch via Autonomous Loop Driver:
bash ~/.gemini/config/plugins/code-manor/bin/run_maid_loop.sh "$PROMPT_FILE" 10
```

---

## 🚦 5. The 3-Tier Traffic Light Context Gauge

To balance warm prompt caching against context rot and SQLite database bloat, Maid's session token volume is governed by a 3-tier traffic light model.

```
0k ------------------------- 180k ------------------------- 250k ------------------> (Tokens)
[      🟢 GREEN ZONE       ] [       🟡 YELLOW ZONE        ] [   🔴 RED DUMP ZONE   ]
  • Smart Execution            • Wrap-Only Mode              • Stagnation Panic
  • Warm Context Momentum      • Do Not Kill Active Ticket   • Abort Subprocess
  • Dispatches Next Ticket     • Refuse New Ticket at Gate   • Salvage Diff & Recover
```

### Zone 1: 🟢 Green Zone (0 – 180,000 Tokens) — "Smart Execution Zone"
- **Status:** Optimal reasoning and caching efficiency.
- **Action:** Butler preserves `$MAID_CONV_ID` warm and immediately feeds the next unblocked ticket from `tasks-axi ready`.

### Zone 2: 🟡 Yellow Zone (180,000 – 250,000 Tokens) — "Graceful Wrap / Gate Refusal"
- **During Ticket Execution:** If context crosses 180k *mid-ticket*, Butler **NEVER** interrupts or kills the running worker. Maid is allowed to finish its active ticket gracefully.
- **At Ticket Boundary:** Once the active ticket passes verification, Butler checks the gauge. If tokens $\ge 180\text{k}$:
  - Butler **REFUSES** to assign a new ticket to this session.
  - Butler cleanly unsets `$MAID_CONV_ID` (retiring the worker session).
  - The next ticket automatically initializes a fresh, clean `$MAID_CONV_ID`.

### Zone 3: 🔴 Red Zone (> 250,000 Tokens) — "Dump Zone / Stagnation Circuit Breaker"
- **Trigger:** A ticket fails to finish and context balloons past the 250k hard ceiling (indicating a test thrashing loop, prompt injection confusion, or hallucination spiral).
- **Emergency Circuit Breaker Protocol:**
  1. Butler forcefully terminates the runaway `agy -p` process immediately.
  2. Butler inspects git status (`git status`, `git diff`).
  3. Butler salvages passing unit test slices or reverts broken code.
  4. Butler logs a `Stagnation Incident` in `.memory/LESSONS.md`.
  5. Butler synthesizes a distilled corrective prompt (`/btw` corrective guidance) and re-launches the ticket with a brand-new `$MAID_CONV_ID`.

---

## 🛡️ 6. Two-Tier Verification & Two-Axis Code Review

Quality gates are deterministic and policy-driven. Code is never merged on agent assertion alone.

```
[ Worker Ticket Phase ] ──> Tier 1: make check (Exit 0) ──> Ticket Gate: no-mistakes --skip ci (Exit 0)
                                                                            │
[ Milestone Done ] <────────────────────────────────────────────────────────┘
         │
         ▼
[ Butler Two-Axis Review ] ──> Spec Axis (AC Coverage) + Standards Axis (Architecture)
         │
         ▼
[ Outer Gate ] ──────────────> no-mistakes axi run (Exit 0) ──> gh pr create
```

### Verification Tiers:
- **Tier 1: Mandatory Hermetic Local Gate (`make check`):**
  - Strictly Hermetic: Lint + typecheck + unit tests (`test:unit`).
  - **Zero Daemon Invariant:** Must run completely in-memory without external PostgreSQL, Redis, Docker, or network dependencies.
  - Integration/E2E tests belong in `make test:integration` or remote CI, never in `make check`.
  - Must exit 0 before any ticket is marked done in `tasks-axi`.
- **Tier 2: Policy-Gated Verification (`projects.json`):**
  - `yolo`: Fast iteration. Requires `make check`. Skips heavy `no-mistakes` and two-axis review.
  - `staged`: Default. Requires `make check` + `no-mistakes axi run --skip ci` exit 0.
  - `strict`: High stakes. Requires `make check` + `no-mistakes axi run --skip ci` per ticket + Full `no-mistakes axi run` + Butler Two-Axis Code Review at PR milestone boundary.

### Two-Axis Review Protocol:
Butler reviews diff against baseline: `git diff $BASE_SHA...HEAD`.
1. **Spec Axis:** Are all Acceptance Criteria in `specs/<slug>.md` satisfied without scope creep?
2. **Standards Axis:** Does the code conform to Fowler clean architecture, explicit typing, and zero leaked abstractions?

### 🐙 GitHub Integration, PR Lifecycle & Branch Safety Invariants:
1. **Toolchain Dependency (`gh` CLI):** Autonomous PR creation and CI tracking rely on the GitHub CLI (`gh`), authenticated via `gh auth login`.
2. **Milestone PR Model (Accumulating Commits):**
   - Individual tickets commit locally to the active feature branch. PR emission occurs at the **Milestone Boundary** (`frontier-axi done`), never per micro-ticket.
   - If multiple sequential frontiers execute on the same feature branch before merge, all commits stack onto that single open PR cleanly.
3. **Squash and Merge Gating (`Human's Call`):**
   - Under `strict` policy, Butler emits the PR and watches remote checks (`gh pr checks --watch`). The final **Squash and Merge** action is strictly reserved for the human.
4. **Prompt-Based Policy Override:** The human may override any repository policy via natural language (e.g. *"Bypass PR and push directly to main this time"*). The agent complies immediately without dogmatic resistance.
5. **Zero-Branch-Deletion Invariant:** Agents are strictly forbidden from deleting, force-pushing, or pruning branches (`git branch -D`, `git push --delete`). Existing legacy or backup branches are preserved indefinitely.

---

## 🐧 7. Cross-Platform Bridge Architecture (Windows $\leftrightarrow$ WSL2)

For developers on Windows, Code-Manor achieves full Linux-native toolchain performance via WSL2 interop while keeping configuration unified.

```
Windows Host (Antigravity 2.0 GUI / IDE)
  └── C:\Users\<user>\.gemini\config\plugins\code-manor\
            │
            │ (NTFS-to-ext4 Symlink)
            ▼
WSL2 Ubuntu (/home/<user>/.gemini/config/plugins/code-manor/)
  ├── ~/.local/bin/agy (Symlink to Windows /mnt/c/.../agy.exe or Linux binary)
  ├── /usr/local/bin/tasks-axi & frontier-axi
  ├── /usr/local/bin/no-mistakes
  └── tmux sessions (Steward / Butler / Maid execution panes)
```

### Bridge Invariants:
1. **Single Physical Filesystem Source:** The Windows plugin directory is symlinked into WSL:
   ```bash
   mkdir -p ~/.gemini/config
   ln -s /mnt/c/Users/<user>/.gemini/config/plugins ~/.gemini/config/plugins
   ```
   Edits made on Windows immediately update WSL, and vice-versa.
2. **Execution Path & CLI Shim:**
   - On WSL, Windows `agy.exe` is symlinked into the Linux user PATH (`~/.local/bin/agy` or `/usr/local/bin/agy` -> `/mnt/c/.../agy.exe`).
   - Non-interactive and subagent calls execute via login shell (`bash -lc`) or global `/usr/local/bin` to ensure PATH resolution remains stable across all execution contexts.
   - CLI agents (`agy`), AXI tools (`tasks-axi`, `frontier-axi`), and gates (`no-mistakes`) execute natively in Linux to avoid Windows console escaping and file locking issues.
3. **Database Isolation:** CLI conversations reside in WSL SQLite (`~/.gemini/antigravity-cli/conversations/`), insulating the Desktop GUI from subagent cemetery bloat.

---

## 📊 8. Empirical Benchmarks & Production Performance Realities

The architectural evolution of Code-Manor from naive in-process subagents to the deterministic two-tier subprocess driver yielded radical, measurable benchmark improvements across real-world monorepos (e.g. monolithic Node.js/TypeScript codebases with 20+ service boundaries and 500+ tests).

### 📈 Comparative Benchmark Matrix: Before vs. After

| Metric Dimension | Before (Naive In-Process / Bare `make check`) | After (Code-Manor v1.3 Subprocess Driver) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Inner Loop TDD Latency** | ~72 seconds per turn (ran entire monorepo test suite & full static analysis on every micro-edit) | **< 2 seconds** per turn (laser-targeted test runner `TARGET_TEST_CMD` isolating the single test slice) | **~36x speedup**; eliminates wait fatigue and turns TDD into an interactive loop. |
| **Outer Verification Overhead** | Continuous thrashing on monolithic suite across all turns | Strictly **1 execution** (~72s) as the final hermetic exit gate prior to commit | Concentrates full verification cost only after implementation stabilizes. |
| **Average Token Consumption** | 150,000 – 250,000+ tokens per ticket (dumping massive monorepo error logs & hallucination spirals) | **25,000 – 35,000 tokens** per ticket (strict scope isolation, exact backpropagated trace) | **~80–85% token reduction**; protects 5-hour rolling quotas. |
| **Turn Count to Green** | 8 – 15 turns (often hitting max turns without knowing why the outer gate failed) | **2 – 5 turns** (Turn 1: red test $\rightarrow$ Turn 2: green implementation $\rightarrow$ exit) | **~3x fewer turns** required per vertical ticket. |
| **Fatal Infrastructure Faults** | 10+ wasted spinning turns until timeout on expired API keys, 401s, or syntax errors | **Instant Trip (Turn 1 / 0s delay)** via Circuit Breaker (`exit 2`) escalating directly to human | **Zero token burn** on infrastructure/auth outages. |
| **Error Feedback Fidelity** | Truncated tool outputs (Feedback Black Hole swallowed compiler & test assertion traces) | Full stderr/stdout capture (`GATE_LOG`) injected cleanly into `NEXT_PROMPT` | Eliminates blind guessing; agent fixes exact line numbers. |
| **Context Signal-to-Noise** | Massive log pollution from unrelated microservices flooding the context window | Laser-scoped diffs strictly confined to `Target Implementation` & `Target Test` files | Prevents model distraction and phantom regressions in unrelated services. |

---

## 🖥️ 9. Observability & Telemetry Testbed (`code-manor-dashboard`)

To validate real-world agent executions without polluting user conversation context with terminal noise, Code-Manor includes a lightweight, local telemetry testbed (`./bin/code-manor-dashboard` driven by Python Streamlit):

### Key Telemetry Capabilities:
- **Direct Antigravity Session Engine Inspection:** Connects in read-only mode (`mode=ro`) to `conversation_summaries.db` and parses `transcript_full.jsonl` step execution events directly from the Antigravity brain storage.
- **Default `agy -c` Tracking:** Automatically selects and displays the most recent active session that `agy -c` resumes, with configurable history depth ($N$ sessions).
- **Dedicated Chat Container & Natural Chronology:** Encapsulates the conversation event feed within a scrollable container starting at the latest step, equipped with instant client-side smooth-scroll controls (`⬆️ En Başa Git` and `⬇️ En Sona Git`).
- **Live Terminal & Gate Findings:** Mirrors the live `active_maid_loop.log` stream and parses structured `review.log` findings from `no-mistakes` with risk-level badges and recommended actions.

---

## 🤝 10. Open Technical Debts & Multi-Harness Community Call to Action

While Code-Manor was engineered with universal architectural principles, its current low-level subprocess orchestration has two open technical debts tied specifically to the Google Antigravity ecosystem:

1. **Subprocess Execution Engine (`agy -p` Dependency):**  
   The synchronous run-to-completion worker model currently relies on the `antigravity-cli` (`agy -p`) binary. For other harnesses (Claude Code, OpenAI Codex, Cursor, Grok), this requires provider-specific subprocess bridges or CLI adapters.
2. **3-Tier Context Gauge Monitoring:**  
   The Green/Yellow/Red context gauge thresholds (180k/250k) are currently monitored via `agy` token accounting and local SQLite logs. Different providers report token usage through different interfaces (APIs, hooks, or transcript files).

### 📢 Call to Action: Fork, Build & PR
We warmly invite external contributors, teams, and open-source practitioners to help make Code-Manor truly harness-universal:

1. **Fork the Repository:** Create your own branch or fork at `github.com/oguzalp7/code-manor`.
2. **Implement Your Harness Bridge:**
   - Under `skills/` or `.agents/`, develop the CLI adapter or hook for your target environment (e.g. `claude-code`, `codex-runner`, `cursor-agent`).
   - Implement the graceful fallback and token count monitor.
3. **Verify Locally:** Ensure `make check` and the multi-project fleet tests pass cleanly.
4. **Submit a Pull Request:** Open a PR back to `main`. Once reviewed along our Two-Axis Review Gate (Spec + Standards), we will merge your integration into the canonical distribution!

