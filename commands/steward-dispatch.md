---
name: steward-dispatch
description: Autonomous dispatch protocol from Steward to Butler. Compacts settled frontier milestone into handoff.md.
---

# 🎩 Command: /steward-dispatch

> **Role:** Grand Conductor Milestone Dispatch  
> **Input:** Settled frontier-axi milestone  
> **Output:** `handoff.md`  
> **Handoff Target:** Project Butler

Run `/steward-dispatch` once a frontier milestone is settled, specs are formalized, and tickets are registered in `tasks-axi`. This generates `handoff.md` and signals Butler to execute autonomously.
