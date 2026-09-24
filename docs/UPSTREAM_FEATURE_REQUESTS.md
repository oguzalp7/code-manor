# 📣 Upstream Feature Requests: Antigravity CLI & Subagent Architecture

**Origin:** Code-Manor Multi-Project Orchestration Distribution  
**Date:** 2026-09-23  
**Target:** Google Antigravity Core & CLI Engineering Teams  
**Contact:** Code-Manor Architecture Group  

---

## 🎯 1. Feature Request: Add `Effort` Parameter to `invoke_subagent` Tool Declaration

### Summary
Currently, the native IDE tool `invoke_subagent` allows configuring the model via `Model: "inherit" | "flash_lite" | "flash" | "pro"`, but provides **no reasoning effort parameter** (`Effort: "low" | "medium" | "high"`).

### Problem & Impact
When a conductor agent (like Butler) operates with High Reasoning (`Gemini 3.8 Flash (High)` or `Gemini 3.1 Pro (High)`) and delegates simple implementation amelelik tasks (e.g., reading a file, modifying a localized string, running a local test) to an in-process subagent, the subagent either inherits the parent's high thinking budget or defaults to high thinking.
- The subagent burns 2,000–5,000 thinking tokens on every single tool call.
- Over a 20-turn vertical-slice TDD loop, this consumes 60,000–100,000+ pure reasoning tokens.
- User API quotas and hourly limits are depleted rapidly on mechanical edits that do not require strategic thinking.

### Proposed Schema Enhancement
Update `invoke_subagent` parameter declarations in Antigravity:

```json
{
  "properties": {
    "Subagents": {
      "items": {
        "properties": {
          "Model": {
            "type": "STRING",
            "enum": ["inherit", "flash_lite", "flash", "pro"]
          },
          "Effort": {
            "type": "STRING",
            "enum": ["low", "medium", "high"],
            "description": "Optional reasoning effort for the subagent. When omitted, inherits parent effort."
          },
          "Prompt": { "type": "STRING" },
          "Role": { "type": "STRING" },
          "TypeName": { "type": "STRING" },
          "Workspace": { "type": "STRING" }
        }
      }
    }
  }
}
```

---

## 🎯 2. Feature Request: Add `--wait-for-tasks` / `--autonomous` to `agy` CLI Print Mode

### Summary
When `agy` is executed non-interactively via `--print` (`-p`), it exits after a single conversational turn. If the model dispatches a background task (e.g. `run_command` with a long-running check like `make check` or `npm test` that exceeds the 10-second `WaitMsBeforeAsync` threshold), `agy -p` enters a hardcoded 5-second grace window:

```text
root agent idle; waiting up to 5s for 1 background task(s)
terminating 1 background task(s) on exit
```

If the verification command takes longer than 5 seconds (as almost all real-world test/build suites do), `agy` terminates the background task with `SIGKILL` and exits with code 0 before the agent can ever receive the command's completion message or inspect the result.

### Problem & Impact
- Subprocess-based agent orchestration cannot execute automated TDD or verification loops natively in one command.
- Background tasks initiated by the agent are killed mid-execution.
- Orchestrators are forced to wrap `agy` in external bash loop drivers and manage turns externally.

### Proposed CLI Enhancements
1. **`--wait-for-tasks`:** In print mode (`-p`), instead of terminating active background tasks after 5 seconds, wait until all launched background tasks complete before evaluating turn completion.
2. **`--autonomous` / `--max-turns <N>`:** Allow `agy -p` to automatically continue sequential conversational turns when background tasks finish and send wake-up notifications, terminating only when the agent outputs a final completion token or reaches `--max-turns`.
