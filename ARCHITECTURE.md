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

1. **Butler Zero-Self-Code Boundary:** Butler is exclusively an architect, conductor, and reviewer. Butler MUST NOT modify files in `src/` or `tests/`. Writing scope is restricted to `.memory/**`, `specs/**`, `.tasks.toml`, `CONTEXT.md`, and `handoff.md`.
2. **Maid Anti-Tampering & Anti-Fake-Testing Rule:** Modifying assertion lines or deleting existing tests in `tests/` to force green is strictly forbidden. Furthermore, writing fake tests that inspect source code via `fs.readFileSync`, `readFile`, or regex/string matching is strictly forbidden. Tests must assert against runtime function I/O, component rendering, or user behavior.
3. **No Dangling Background Daemons:** Maid is executed strictly as a synchronous run-to-completion CLI subprocess (`agy -p`). Zero dangling subagent daemons or orphaned background workers are permitted in RAM.
4. **Single Worker Session per Batch:** Butler reuses at most ONE warm worker session (`$MAID_CONV_ID`) per milestone batch, subject to the 3-Tier Traffic Light Context Gauge.

---

## 🌉 2. Upstream-to-Downstream Protocol Bridge

Ambiguous ideas never enter the vertical execution task graph directly. Code-Manor strictly bifurcates cognitive fog from executable slices.

```
[ Nascent Fog ] ──> frontier-axi add ──> /grilling ──> /to-spec ──> /to-tickets ──> tasks-axi add ──> [ Vertical Slices ]
                                                              │
                                                     /steward-dispatch
                                                              │
                                                        handoff.md
                                                              │
                                                     /butler-takeover
```

### Operating Recipe:
1. **Upstream Frontier:** Nascent ideas, architectural questions, and seams are staged in `frontier-axi`.
2. **Grilling & Convergence:** Open questions are resolved via `/grilling` or `/wayfinder`.
3. **Specification & Slicing:** Settled frontiers synthesize into `specs/<slug>.md` (with numbered `[AC-xx]` criteria) and slice into atomic vertical tickets via `/to-tickets`.
4. **Autonomous Dispatch (`/steward-dispatch` $\rightarrow$ `/butler-takeover`):**
   - Steward runs `/steward-dispatch` to compact the frontier milestone into `handoff.md`.
   - Butler triggers `/butler-takeover` to ingest `handoff.md`, pin `$BASE_SHA`, and begin execution without human errand-boy overhead.

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

### Invariants:
- **Autonomous Multi-Turn Looping:** Avoids the single-turn premature exit and 5-second background task teardown of bare `agy -p`. The driver coordinates turns via `agy --continue` until tests pass.
- **Git-Status-Aware Synchronization Protocol:**
  - If the git working tree is clean and synchronized, redundant baseline `make check` is skipped.
  - When Maid completes a turn and becomes idle/exits, the driver inspects `git status`.
  - If sync is disrupted by code edits, the driver executes `make check` synchronously at the OS level (completely immune to tool timeout truncations).
  - If `make check` passes (exit 0), runs `<maid.gate_command>`, commits, and pushes verified changes to GitHub (`git push`).
  - If `make check` fails, the failure trace is fed back to Maid via `agy --continue` to fix in the next turn without deleting assertions.
- **Frugal In-Process Fallback (`flash_lite`):** If `agy` CLI is unavailable, Butler falls back to native `invoke_subagent` using **`Model: "flash_lite"`** (NOT `"flash"` or `"pro"`), guaranteeing minimal/zero reasoning token consumption and protecting user quota.

### Execution Command Recipe:
```bash
# 1. Butler prepares ticket prompt file:
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

## 🤝 8. Open Technical Debts & Multi-Harness Community Call to Action

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

