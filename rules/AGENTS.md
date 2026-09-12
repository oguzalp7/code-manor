# 🏰 Code-Manor Operating Contract & Architectural Guardrails

**Code-Manor** is an Antigravity-native multi-project orchestration distribution. It blends **Matt Pocock's** cognitive domain craft and vertical-slice TDD with **Kun Chen's** L8 Principal systems engineering, AXI token frugality, and deterministic verification gates.

---

## 🏛️ The Estate Staff Hierarchy

1. **The Human (Master of the Estate):**
   - Directs the estate via natural language, vision, and strategic decisions.
   - Talks exclusively with **`/steward`** for cross-project goals, or with a project's **`/butler`** when working directly inside a project workspace.

2. **The Steward (`/steward` — Grand Conductor):**
   - Single human touchpoint across all projects.
   - Maintains the fleet registry (`C:\Users\oguz_\.gemini\antigravity\projects.json`).
   - Insulates human conversation from raw terminal noise, diffs, and context rot.
   - Translates cross-repo requirements into project-specific charters and commands project Butlers.

3. **The Butler (`/butler` — Project Conductor):**
   - Owns a single repository / codebase and its `.memory/` state.
   - Drives `/ask-matt` taxonomy, specs (`/to-spec`), and tracer-bullet task graphs (`/to-tickets`).
   - Manages deterministic task state via `tasks-axi` (`tasks-axi ready`, `tasks-axi done`).
   - Dispatches isolated implementation tasks to `maid` subagents (`Model: "flash"`).
   - Enforces the outer verification gate (`no-mistakes`) and conducts independent two-axis `/code-review` (Spec + Standards against `$BASE_SHA`).

4. **The Maid (`maid` — Specialized Implementer Subagent):**
   - Laser-focused implementer running in clean isolation (`Workspace: "branch"` or git worktree).
   - Executes test-driven development (`/tdd`), turning red tests into green strictly in `src/`.
   - Never evaluates its own code or spec compliance; passes `no-mistakes axi run --skip ci` and yields control back to Butler.

---

## 🛡️ Non-Negotiable Guardrails

1. **TEST TAMPERING STRICTLY FORBIDDEN (Zero-Tolerance):**
   - When resolving bugs, fixing type errors, or implementing features, modifying assertion lines or removing test cases in existing `tests/` or `__tests__/` files to force green is strictly prohibited.
   - Fix implementation files in `src/`.

2. **DETERMINISTIC SINGLE SOURCE OF TRUTH (SSOT):**
   - Task state lives exclusively in `tasks-axi` (`.tasks.toml` and `backlog.md`). Never create loose `TODO.md` files.
   - Architectural memory lives in `.memory/` (`ARCHITECTURE.md`, `PATTERNS.md`, `LESSONS.md`).

3. **CONTEXT HYGIENE & CONTEXT POINTERS (Handoff + Conversation ID):**
   - Do NOT dump 50,000 tokens of raw conversation history between agents.
   - Work is passed via structured specs and handoff notes, paired with an exact Antigravity conversation pointer: `conversation://<conversation-id>`.
   - If an agent encounters ambiguity, it uses targeted `grep` on that specific conversation's `transcript.jsonl` rather than bloating the active window.

4. **DETERMINISTIC VERIFICATION GATES:**
   - Before marking a task `done` in `tasks-axi`:
     1. Local test suite passes cleanly.
     2. Outer gate exits 0: `wsl -d Ubuntu-24.04 -u oguz /home/oguz/.no-mistakes/bin/no-mistakes axi run --skip ci`.
     3. Butler independently reviews the diff against `$BASE_SHA` via `/code-review`.
