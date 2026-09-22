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
3. **Sequential Execution & Declarative Routing:** Feed tickets one-by-one to Maid via `agy -p --conversation "$MAID_CONV_ID"` using model parameters loaded from `routing.json`.
4. **Milestone Two-Axis Review:** Conduct `/code-review` only after ALL tickets in the milestone pass local verification (`make check`) and ticket gate (`no-mistakes axi run --skip ci`).

---

## 🚀 Takeover Execution Pipeline

### Step 1: Ingest Handoff, Pin Baseline & Load Routing
1. Read `handoff.md` in the project root to extract:
   - Target Frontier ID
   - Target Spec
   - Milestone ticket list
2. Pin the exact baseline commit SHA:
   ```bash
   BASE_SHA=$(git rev-parse HEAD)
   ```
3. Load model routing and gate command from `routing.json`:
   - Inspect `~/.gemini/config/plugins/code-manor/routing.json` (or `.agents/routing.json` if overridden).
   - Extract `maid.model`, `maid.effort`, `maid.flags`, `maid.gate_command` (default: `"no-mistakes axi run --skip ci"`), and `maid.context_gauge` (`green_zone_max: 180000`, `yellow_zone_max: 250000`, `hard_ceiling_dump_zone: 250000`).

### Step 2: Maid Worker Execution (`agy -p` Subprocess Mode with Fallback)
Butler delegates vertical-slice tickets sequentially using clean CLI subprocesses, or falls back to native subagents if `agy` is not installed:

1. **Engine Detection & Graceful Fallback:**
   Butler checks if `agy` exists in PATH (`which agy || which agy.exe || test -f ~/.local/bin/agy || test -f /usr/local/bin/agy`):
   - **Mode A: Subprocess Mode (`agy` found - Recommended):** Proceed with steps 2-4 below for 100% deterministic model routing, zero zombie processes, and 3-tier context gauge.
   - **Mode B: In-Process Fallback Mode (`agy` missing):** Butler falls back to native `invoke_subagent(Role: "maid", Model: "flash", Workspace: "branch")` and dispatches via `send_message`. Emits a short warning: *"Notice: agy CLI not found; operating in native in-process subagent mode. Installing antigravity-cli is highly recommended."* Note: Fallback subagents must be killed immediately via `manage_subagents(Action: "kill")` upon ticket completion to prevent token leakage.

2. **Manage Worker Session (`MAID_CONV_ID`):**
   - If `MAID_CONV_ID` is unset (milestone start or post-retirement), initialize a fresh UUID:
     ```bash
     MAID_CONV_ID=$(uuidgen 2>/dev/null || python3 -c 'import uuid; print(uuid.uuid4())')
     ```
3. **Dispatch Ticket via Synchronous Subprocess:**
   Run the ticket execution command via `run_command`:
   ```bash
   agy --model <maid.model> --effort <maid.effort> <maid.flags> --conversation "$MAID_CONV_ID" -p "## New Ticket Assignment: #<ticket-id> - <title>

### What to build
<spec-content>

### Acceptance Criteria
<criteria>

### Instructions:
THINKING EFFORT: LOW / EXECUTION-ONLY.
1. Implement red test in tests/ based on Acceptance Criteria. Do not tamper with existing tests.
2. ⛔ TEST QUALITY RULE (ZERO-TOLERANCE):
   - Never write tests that inspect source code via fs.readFileSync, readFile, or string regex.
   - Tests must strictly assert on runtime function I/O or rendered user behavior. Violations will fail the gate immediately.
3. Implement code in src/ to make tests green without tampering with existing tests.
4. Run mandatory local gate: make check and confirm exit code 0 (must be hermetic, zero DB/network required).
5. MANDATORY VERIFICATION GATE:
   - Run the gate command: <maid.gate_command> (e.g. no-mistakes axi run --skip ci)
   - Confirm exit code 0.
6. Report exit code, raw terminal output of the gate command, and git diff summary."
   ```
4. **Process Safety & Graceful Termination:**
   - Because `agy -p` is run-to-completion, the process terminates immediately upon ticket completion (`exit 0`).
   - Zero background daemon or orphan RAM process is left behind.
   - Context is preserved on disk in `<MAID_CONV_ID>.db` for warm reuse in subsequent tickets.

### Step 3: Ticket Iteration Loop & 3-Tier Traffic Light Context Gauge
1. Await Maid subprocess exit code:
   - Confirm `make check` exited 0 (hermetic local gate).
   - Confirm `<maid.gate_command>` was executed and exited 0 (ticket gate).
   - Verify test files in `tests/` were not tampered with and no fake `fs.readFileSync`/regex tests were written.
2. Mark ticket as done: `tasks-axi done <ticket-id>`.
3. **The 3-Tier Traffic Light Context Gauge Protocol:**
   Butler evaluates token consumption against the thresholds declared in `routing.json`:
   - 🟢 **Green Zone (0 – 180,000 Tokens) — Smart Execution Zone:**
     - Healthy context momentum. Butler preserves `$MAID_CONV_ID` warm and dispatches the next unblocked ticket from `tasks-axi ready`.
   - 🟡 **Yellow Zone (180,000 – 250,000 Tokens) — Graceful Wrap / No New Tickets:**
     - **During Execution:** If token count crossed 180k *while* a ticket was running, Butler strictly **DOES NOT interrupt or kill** the active run. Maid is permitted to complete the current ticket gracefully.
     - **At Ticket Boundary:** Once the active ticket finishes and passes verification, Butler detects the Yellow Zone ($\ge 180\text{k}$). Butler **refuses to assign any new tickets** to this session.
     - Butler gracefully retires the session (`unset MAID_CONV_ID`). The next ticket will automatically initialize a fresh, clean `$MAID_CONV_ID`.
   - 🔴 **Red Zone (> 250,000 Tokens) — Dump Zone / Panic & Stagnation Circuit Breaker:**
     - Triggered if an active ticket fails to finish and context balloons past the 250k hard ceiling (indicating a retry loop, test thrashing, or severe context rot).
     - **Emergency Intervention:** Butler aborts/terminates the runaway subprocess immediately.
     - Butler inspects git state (`git status`, `git diff`), salvages clean changes or reverts broken edits, records the stagnation incident in `.memory/LESSONS.md`, and injects a distilled recovery prompt (`/btw` corrective instruction) into a brand-new `$MAID_CONV_ID` session.

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
