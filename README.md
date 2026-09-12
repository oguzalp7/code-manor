# 🏰 Code-Manor

<p align="center">
  <strong>The Antigravity-Native Multi-Project Orchestration Distro</strong><br>
  <em>Blending Matt Pocock's Cognitive Domain Craft with Kun Chen's Principal AXI Systems & Deterministic Gates</em>
</p>

---

## 🎩 What is Code-Manor?

Most AI coding setups suffer from two failure modes:
1. **The Vibe Coding Trap:** Letting agents write code unguided, leading to hallucinations, broken tests, and context rot.
2. **The Tab-Juggling Bottleneck:** Trying to juggle 3-4 repositories, copy-pasting diffs, and drowning in terminal noise.

**Code-Manor** solves this by establishing a disciplined, British household estate hierarchy (**Steward $\rightarrow$ Butler $\rightarrow$ Maid**), engineered specifically for **Google Antigravity** and **Gemini Flash (High Reasoning / Lean Workers)**:

```
                      👑 HUMAN (Master of the Estate)
                                    │
                                    ▼
                      🎩 /steward (Grand Conductor)
                         • Multi-Project Portfolio
                         • Zero-Search projects.json
                         • Context Insulation
                                    │
             ┌──────────────────────┴──────────────────────┐
             ▼                                             ▼
   🎩 /butler (Project A)                        🎩 /butler (Project B)
      • tasks-axi DAG                               • tasks-axi DAG
      • .memory/ Architecture                       • .memory/ Architecture
      • /to-tickets Decomposition                   • /to-tickets Decomposition
      • Two-Axis Code Review                        • Two-Axis Code Review
             │                                             │
             ▼                                             ▼
      🧹 maid (Subagent)                            🧹 maid (Subagent)
         • /tdd (Test-First)                           • /tdd (Test-First)
         • no-mistakes Gate                            • no-mistakes Gate
         • Zero Test Tampering                         • Zero Test Tampering
```

---

## ⚡ Quick Start

### 1. Installation

Install via universal Agent Skills:
```bash
npx skills@latest add oguzalp7/code-manor
```

Or clone directly into your Antigravity plugins directory:
```bash
cd ~/.gemini/config/plugins/
git clone https://github.com/oguzalp7/code-manor.git
```

### 2. Run Setup Wizard

In Antigravity chat, run:
```
/setup-code-manor
```
This will:
- Auto-discover projects from Antigravity 2.0 desktop (`workspaceStorage`).
- Populate `~/.gemini/antigravity/projects.json` for instant, zero-token project lookups.
- Verify WSL2 Ubuntu toolchains (`tasks-axi`, `no-mistakes`, `git`, `gh`).

### 3. Talk to Your Estate

- **Across Projects:** Talk to `/steward` from any central conversation:
  - *"What did we ship recently on Project PulseFlow?"*
  - *"Prepare a feature charter connecting API Service to Mobile App."*
- **Inside a Project:** Talk to `/butler` directly from a project workspace:
  - *"Grab the next unblocked ticket from tasks-axi ready and dispatch a maid to implement it."*

---

## 🛡️ Core Guardrails

1. **Zero-Tolerance Test Tampering:** Modifying existing test assertion lines in `tests/` or removing tests to force green is strictly prohibited. Green tests must be achieved exclusively by fixing implementation files in `src/`.
2. **Single Source of Truth (SSOT):** Task backlog lives exclusively in `tasks-axi` (`.tasks.toml` / `backlog.md`). Architectural memory lives in `.memory/`. Loose `TODO.md` files are banned.
3. **Context Pointers:** Conversations communicate through structured specs paired with Antigravity pointers (`conversation://<id>`). If an agent hits ambiguity, it uses targeted `grep` on `transcript.jsonl` rather than bloating the context window with raw history.
4. **Deterministic Outer Gate:** Every ticket must exit with code 0 from `no-mistakes axi run --skip ci` before Butler accepts it.

---

## 📦 What's Included

- **Core Orchestrators:** `/steward`, `/butler`, `/setup-code-manor`.
- **Upstream Matt Pocock Skills (v1.2.3):** `/ask-matt`, `/to-spec`, `/to-tickets`, `/implement`, `/implement-spec`, `/retro`, `/tdd`, `/code-review`, `/diagnosing-bugs` (secret redacted), `/codebase-design`, `/improve-codebase-architecture`, `/wayfinder`, `/prototype`, `/wizard`, `/grill-with-docs`, `/grill-me`, `/grilling`, `/wait-what`, `/to-questionnaire`.
- **Kun Chen AXI & Verification Tools:** `frontend-axi-tdd` (zero-vision token UI testing), `/kun` (living L8 Principal knowledge base).
- **UI/UX Excellence:** `ui-ux-pro-max`, `frontend-design`.

---

## 📜 License

MIT © Oguz Alp
