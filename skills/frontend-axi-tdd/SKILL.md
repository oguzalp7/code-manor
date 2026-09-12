---
name: frontend-axi-tdd
description: Zero-vision-token Frontend TDD & Verification harness using headless Playwright and chrome-devtools-axi. Inspects Accessibility Tree snapshots, monitors console/network logs, and asserts UI state deterministically.
---

# 🌐 Frontend AXI TDD — Zero-Vision-Token UI Verification

This skill provides deterministic, token-efficient frontend test-driven development (TDD) and live browser verification without consuming vision tokens.

## 🎯 Core Operating Principles

1. **Zero Vision Tokens ($0 Overhead):**
   - Do NOT take and transmit visual screenshots for LLM consumption.
   - Use text-based **Accessibility Trees (`snapshot`)** and **DOM Locators** (`aria-role`, `data-testid`, text selectors) to verify UI existence and state.

2. **Dual-Log Diagnostics (Console & Network):**
   - Automatically monitor browser runtime errors (`console.error`, unhandled rejections, streaming errors) and network failures (HTTP 4xx/5xx).
   - If any unhandled console error occurs during interaction, verification is considered **FAILED**.

3. **Seam-Aware Testing:**
   - **Hook/Logic Seam:** Pure utility/state logic is tested with fast in-memory runners (Vitest/Jest).
   - **UI Component/Page Seam:** Driven headlessly via Playwright specs or `chrome-devtools-axi`.

---

## 🛠️ Verification Tooling

### Method A: Native Playwright E2E Runner (Recommended for CI & Repos)
Run headless tests with web-first assertions:
```bash
# In frontend directory
npx playwright test --reporter=list
```

**Assertion Style:**
```typescript
// Prefer role and testid over complex CSS selectors
await expect(page.getByRole('combobox', { name: 'Payment Type' })).toBeVisible();
await expect(page.locator('[data-testid="payment-type-option"]')).not.toHaveCount(0);
```

### Method B: Live Inspection via `chrome-devtools-axi`
When debugging or validating a live dev server (`http://127.0.0.1:3000`):

> [!TIP]
> **Platform Execution Note:**
> - **macOS & Linux:** Run `chrome-devtools-axi <command>` directly.
> - **Windows (WSL Bridge):** If installed in WSL, run `wsl chrome-devtools-axi <command>`.

1. **Open Target Page:**
   ```bash
   chrome-devtools-axi open "http://127.0.0.1:3000/dashboard"
   ```
2. **Inspect Accessibility Snapshot (Zero-Vision DOM Tree):**
   ```bash
   chrome-devtools-axi snapshot
   ```
3. **Interact via UID:**
   ```bash
   chrome-devtools-axi click @<uid>
   chrome-devtools-axi fill @<uid> "Text"
   ```
4. **Inspect Console & Network Errors:**
   ```bash
   chrome-devtools-axi console
   chrome-devtools-axi network
   ```

---

## 📋 TDD Execution Cycle for Frontend Bugs / Features

1. **Red (Reproduce):**
   Write a minimal Playwright test or run `chrome-devtools-axi snapshot` showing the missing element, empty state, or reproducing the console error.
2. **Green (Implement):**
   Fix the component, hydration logic, or API selector in `src/`.
3. **Refactor & Verify:**
   - Re-run test/snapshot: element is visible, options are populated.
   - Verify `chrome-devtools-axi console` reports 0 runtime errors.
   - Run repository gate (`no-mistakes axi run --skip ci`).
