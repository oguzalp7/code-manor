---
name: setup-code-manor
description: Setup and health-check wizard for Code-Manor. Auto-discovers workspaces from Antigravity 2.0, populates projects.json, and verifies environment toolchains across macOS, Linux, and Windows (WSL).
---

# 🛠️ Setup Code-Manor — Wizard & Environment Health Check

Run this skill to configure and verify the **Code-Manor** orchestration environment on your machine. It ensures all dependencies, toolchains, and `projects.json` registries are properly wired.

---

## 📋 What This Skill Performs

1. **Workspace Auto-Discovery (`projects.json` Sync):**
   - Automatically detects the host platform (Windows, macOS, or Linux).
   - On Windows: Inspects Antigravity desktop records (`$env:APPDATA\Antigravity\User\workspaceStorage`).
   - On macOS/Linux: Inspects `~/.config/Antigravity/User/workspaceStorage` or `~/Library/Application Support/Antigravity/User/workspaceStorage`.
   - Normalizes paths and indexes them into `~/.gemini/antigravity/projects.json` so **`/steward`** can locate any project instantly with zero token search overhead.

2. **Toolchain Verification:**
   - Checks `tasks-axi` executable availability (`which tasks-axi`).
   - Checks `no-mistakes` gate availability (`which no-mistakes` or default install path).
   - Checks `git` and `gh` authentication status.
   - For Windows users: Checks WSL2 status if Linux-native tools are bridged via WSL.

3. **Memory & SSOT Baseline:**
   - Checks whether target projects have `.memory/` directories and `.tasks.toml` configs.
   - Offers to initialize `.memory/` (`ARCHITECTURE.md`, `PATTERNS.md`, `LESSONS.md`) if missing.

---

## 🚀 Execution Steps

When invoked, the agent should run the diagnostic check:

```bash
# Verify CLI toolchains
which tasks-axi || echo "tasks-axi not found in PATH"
which no-mistakes || echo "no-mistakes not found in PATH"
gh auth status || echo "gh CLI not authenticated"

# Verify projects.json existence
if [ -f "$HOME/.gemini/antigravity/projects.json" ]; then
    echo "projects.json found. Registered projects:"
    cat "$HOME/.gemini/antigravity/projects.json" | grep '"name"' || true
else
    echo "projects.json not initialized yet. Auto-scanning workspace storage..."
fi
```

Finally, present a clean summary table to the user with the discovered projects and verification status.
