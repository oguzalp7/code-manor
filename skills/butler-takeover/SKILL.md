---
name: butler-takeover
description: Automated takeover protocol for Butler. Reads handoff.md, pins BASE_SHA, enforces Zero-Self-Code, and orchestrates a single reusable Maid worker pool without human micro-management.
---

# 🎩 /butler-takeover — Autonomous Milestone Conductor

**Butler-Takeover** is invoked when Butler takes over an approved frontier milestone from `/steward-dispatch`. It strictly enforces the **Zero-Self-Code** rule and manages a **Single-Worker Pool** (`maid`), eliminating the human errand-boy role and preventing zombie subagent sprawl.

---

## 🔒 Ironclad Operating Contract (Non-Negotiable)

1. **Zero Self-Code:** Butler is an architect, supervisor, and reviewer. Butler MUST NOT call `write_to_file` or `replace_file_content` on `src/` or `tests/`.
2. **Single-Worker Pool (Anti-Zombie Rule):** Butler maintains **at most ONE active Maid worker session** (`MAID_CONV_ID`) across tickets. Never spawn competing workers!
3. **Sequential Execution & Declarative Routing:** Feed tickets one-by-one to Maid via `bin/run_maid_loop.sh` using model parameters loaded from `routing.json` (or frugal `flash_lite` in-process fallback).
4. **Milestone Two-Axis Review:** Conduct `/code-review` only after ALL tickets in the milestone pass local verification (`make check`) and ticket gate (`no-mistakes axi run --skip ci`).

---

## 🚀 Takeover Execution Pipeline


### Step 1: Ingest Handoff, Pin Baseline, Git Sync Check & Load Routing
1. Read `handoff.md` in the project root to extract:
   - Target Frontier ID
   - Target Spec
   - Milestone ticket list
2. Pin the exact baseline commit SHA:
   ```bash
   BASE_SHA=$(git rev-parse HEAD)
   ```
3. **Pre-Flight Git Synchronization Check:**
   - Butler checks `git status --porcelain`.
   - **If working tree is clean and synchronized:** Baseline is verified clean; do NOT run redundant 60-second `make check` prior to ticket work.
   - **If working tree is dirty:** Run `make check` to verify pre-existing integrity. If it fails, halt and resolve baseline before delegating to Maid.
4. Load model routing and gate command from `routing.json`:
   - Inspect `~/.gemini/config/plugins/code-manor/routing.json` (or `.agents/routing.json` if overridden).
   - Extract `maid.model`, `maid.effort`, `maid.fallback_model` (`"flash_lite"`), `maid.loop_driver` (`"bin/run_maid_loop.sh"`), `maid.gate_command` (default: `"no-mistakes axi run --skip ci"`), and `maid.context_gauge`.
5. **Project Policy Lookup (`projects.json`):**
   - Read current project entry from `~/.gemini/antigravity/projects.json`.
   - Extract `policy` (`"yolo"`, `"staged"`, or `"strict"`).
   - Export `MAID_POLICY="$POLICY"` so the driver knows whether to execute or bypass the verification gate.

### Step 2: Maid Worker Execution (`run_maid_loop.sh` Driver Mode with Fallback)
Butler delegates vertical-slice tickets sequentially using clean CLI subprocesses, or falls back to native subagents if `agy` is not installed:

1. **Engine Detection & Graceful Fallback:**
   Butler checks if `agy` exists in PATH (`which agy || which agy.exe || test -f ~/.local/bin/agy || test -f /usr/local/bin/agy`):
   - **Mode A: Autonomous Driver Subprocess Mode (`agy` found - Recommended):**
     Butler writes the ticket assignment prompt to a scratch file (e.g. `.memory/scratch/ticket-<id>.txt`).

     > [!IMPORTANT]
     > **Mandatory Explicit Scope Definition (Anti-Scope-Creep Guardrail):**
     > To prevent worker wandering, test suite pollution, or existential scope creep, Butler MUST explicitly specify the following boundaries in every ticket prompt file:
     > - **`Target Implementation Files:`** The exact, exhaustive list of source files in `src/` to modify or create.
     > - **`Target Test Files:`** The exact test file(s) in `tests/` that verify this slice.
     > - **`Strict Boundary Prohibition:`** Explicitly forbid touching, modifying, or diagnosing any other files or unrelated test suites (e.g., *"Strictly do NOT touch, modify, or diagnose unrelated test suites or files outside the listed targets"*).

     Butler then executes the autonomous multi-turn driver with the project policy:
     ```bash
     export MAID_POLICY="<policy>"
     bash ~/.gemini/config/plugins/code-manor/bin/run_maid_loop.sh .memory/scratch/ticket-<id>.txt 10
     ```
     *(In Windows/WSL environments, run via canonical WSL recipe: `wsl -d Ubuntu-24.04 -e bash -lc "cd <wsl-repo> && export MAID_POLICY=<policy> && bash ~/.gemini/config/plugins/code-manor/bin/run_maid_loop.sh ..."`).*
   - **Mode B: In-Process Fallback Mode (`agy` missing):**
     Butler falls back to native `invoke_subagent` using **`Model: "flash_lite"`** (NOT `"flash"` or `"pro"`, to avoid thinking quota depletion) and `Workspace: "branch"`.
     *Note:* Antigravity's `invoke_subagent` tool does not support an `Effort` parameter in its schema; `flash_lite` is the strictly compliant, frugal in-process model. Fallback subagents must be killed immediately via `manage_subagents(Action: "kill")` upon ticket completion.

2. **Git-Status-Aware Synchronization Protocol in Driver:**
   - Maid focuses strictly on viewing files and implementing code in `tests/` and `src/`.
   - **When Maid completes a turn and becomes idle/exits:** The loop driver (`run_maid_loop.sh`) inspects `git status`.
   - If git synchronization is disrupted (code edits exist), the driver executes `make check` synchronously at the OS level (completely immune to tool timeout truncations).
   - **If `make check` exits 0:** If policy is `yolo`, skips gate; otherwise runs `<maid.gate_command>`, pushes verified commits to GitHub (`git push`), and exits 0 cleanly.
   - **If `make check` fails:** The driver captures compiler/test error traces and automatically invokes `agy --continue --effort low` with the error feedback, driving Maid iteratively until tests pass.

### Step 3: Ticket Iteration Loop & 3-Tier Traffic Light Context Gauge
1. **Await Maid Subprocess Exit Code:**
   - **Exit 0 (Success):**
     - Confirm `make check` exited 0 (hermetic local gate).
     - Confirm `<maid.gate_command>` passed (or was bypassed by `yolo`).
     - Verify test files in `tests/` were not tampered with and no fake `fs.readFileSync`/regex tests were written.
     - Mark ticket as done: `tasks-axi done <ticket-id>`.
   - **Exit 2 (Circuit Breaker Tripped — Tooling/Auth Failure):**
     - Driver detected an infrastructure, authentication (`401 Unauthorized`), or CLI flag failure in the external gate.
     - Code is structurally sound (`make check` passed), but external verification failed due to environment issues.
     - Butler **MUST NOT** retry in a loop. Butler halts execution, preserves working tree diffs, and escalates directly to the Master (Human) with the error log.
   - **Exit 1 (Failure / Stalled):**
     - `MAX_TURNS` reached without passing `make check`. Butler investigates the failure trace.
3. **The 3-Tier Traffic Light Context Gauge Protocol:**
   Butler evaluates token consumption against the thresholds declared in `routing.json`:
   - 🟢 **Green Zone (0 – 180,000 Tokens) — Smart Execution Zone:**
     - Healthy context momentum. Butler preserves warm worker momentum and dispatches the next unblocked ticket from `tasks-axi ready`.
   - 🟡 **Yellow Zone (180,000 – 250,000 Tokens) — Graceful Wrap / No New Tickets:**
     - **During Execution:** If token count crossed 180k *while* a ticket was running, Butler strictly **DOES NOT interrupt or kill** the active run. Maid is permitted to complete the current ticket gracefully.
     - **At Ticket Boundary:** Once the active ticket finishes and passes verification, Butler detects the Yellow Zone ($\ge 180\text{k}$). Butler **refuses to assign any new tickets** to this session.
     - Butler gracefully retires the session (`unset MAID_CONV_ID`). The next ticket will automatically initialize a fresh, clean worker session.
   - 🔴 **Red Zone (> 250,000 Tokens) — Dump Zone / Panic & Stagnation Circuit Breaker:**
     - Triggered if an active ticket fails to finish and context balloons past the 250k hard ceiling (indicating a retry loop, test thrashing, or severe context rot).
     - **Emergency Intervention:** Butler aborts/terminates the runaway subprocess immediately.
     - Butler inspects git state (`git status`, `git diff`), salvages clean changes or reverts broken edits, records the stagnation incident in `.memory/LESSONS.md`, and injects a distilled recovery prompt (`/btw` corrective instruction) into a brand-new session.

### Step 4: Milestone Finalization & Two-Axis Code Review
When all tickets for the frontier milestone are complete:
1. Butler independently executes `/code-review` comparing `$BASE_SHA...HEAD` along two canonical axes:
   - **Spec Axis:** Are all Acceptance Criteria in the target spec met?
   - **Standards Axis:** Clean architecture, no leaked abstractions, full typing.
2. If review findings require fixes: Dispatch a targeted patch prompt to `$MAID_CONV_ID` via `agy -p`.
3. When clean:
   - Run outer gate: `no-mistakes axi run` and verify exit code 0.
   - Retire the milestone worker session cleanly.
   - Record lessons learned in `.memory/LESSONS.md`.
   - Create PR:
     ```bash
     gh pr create --title "feat(<scope>): <frontier-title> (#<frontier-id>)" --body "Milestone completed. Verified via make check, no-mistakes, and Two-Axis Code Review."
     ```
   - Close Frontier: `frontier-axi done <frontier-id>`.
   - Update `handoff.md` with completion report for the Master and `/steward`.
