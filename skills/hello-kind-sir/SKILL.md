---
name: hello-kind-sir
description: Rapid, zero-fluff estate status catch-up and decision matrix (inspired by Kun Chen's /ahoy). Delivers Landed, Underway, Captain's Call, and live Context Gauge with zero prose bloat.
---

# 🎩 /hello-kind-sir — Rapid Estate Catch-Up & Captain's Call

Inspired by Kun Chen's `/ahoy` workflow and tailored for the razor-sharp, zero-fluff nature of Gemini 3.8 Flash, **`/hello-kind-sir`** provides an instant executive snapshot across the estate without drowning the Master in long paragraphs or terminal diffs.

---

## 🎯 Core Rules
1. **Zero Fluff (No Filler Words):** Maximum 10-15 lines total output.
2. **Deterministic Information Only:**
   - What finished since last check (`Landed`).
   - What is actively running (`Underway`).
   - What needs a decision (`Captain's Call`).
   - Live Token/Context Gauge (`Context Gauge`).

---

## 📋 Response Format Template

```markdown
### ⚓ İnenler (Landed)
- `<task-id>` / `<repo>`: <1 satır özet ve durum>

### 🌊 Seyirde Olanlar (Underway)
- `<agent/task>`: <Şu an ne yapılıyor?>

### 🎯 Kaptanın Çağrısı (Captain's Call)
- [ ] **Karar 1:** <Kısa soru> $\rightarrow$ [Seçenek A] | [Seçenek B]
*(Eğer açık karar yoksa: "Açık karar bulunmuyor, seyir sakin.")*

### 🧭 Bağlam & Hız Göstergesi (Context Gauge)
- **Oturum:** `<convo-title>`
- **Bağlam Penceresi:** `<current-tokens>` / 250,000 Token (%<percentage>)
- **Önbellek (Cache Hit):** %<cache-percentage>
- **Durum:** 🟢 Güvenli Bölge (<150k) | 🟡 Dikkatli Seyir (150k-250k) | 🔴 Sıkıştırma/Handoff Önerilir (>250k)
```

---

## 🛠️ Execution Recipe for Steward / Butler
1. Check `tasks-axi done` (last completed tasks) and `.memory/LESSONS.md`.
2. Inspect active background tasks or subagents (`manage_task list`, `manage_subagents list`).
3. Query unresolved decisions and open questions via `frontier-axi list` (or `frontier.md` / `.memory/FRONTIER.md`).
4. Read current conversation tokens from `conversations/<conversation-id>.db` using the token inspector helper.
5. Render the 4-part concise card immediately.
