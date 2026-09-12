---
name: ui-ux-pro-max
description: Ensures UI/UX excellence, accessibility (a11y), responsive layouts, form validation states, empty states, loading skeletons, interactive feedback toasts, and design reasoning using UI UX Pro Max.
---

# 🚀 Project Tech Stack & Stakeholder Overlay (MS-Randevu)

> [!IMPORTANT]
> **Project Design & UX Enforcement Rules**:
> 1. **Single Source of Truth Tokens**: Consume design tokens exclusively from [tokens.ts](file:///c:/Users/oguz_/Desktop/MS-Randevu/frontend/src/theme/tokens.ts).
> 2. **Modular Domain Boundaries**: Keep components inside `frontend/src/features/<domain>/components/` ([ADR 0002](file:///c:/Users/oguz_/Desktop/MS-Randevu/docs/adr/0002-frontend-feature-based-architecture.md)).
> 3. **Data Table UX Standard**: Conformance with [ADR 0005](file:///c:/Users/oguz_/Desktop/MS-Randevu/docs/adr/0005-frontend-data-table-standard.md).
> 4. **State Coverage**: Require explicit Loading (Skeleton), Empty State, Form Error (Zod/Hook Form), and Toast Feedback on every UI CRUD action.

---

# UI UX Pro Max (Core Engine & Guidelines)

This skill provides full design intelligence from [UI UX Pro Max](https://uupm.cc) including:

- **161 Reasoning Rules**: Design patterns, component UX, color theory, typography pairing, and layout grid mathematics.
- **84 UI Styles**: Glassmorphism, modern dark mode, minimal clean, enterprise dashboard, and custom aesthetic signatures.
- **Framework Support**: React, Next.js, TypeScript, Tailwind CSS, Chakra UI, and custom CSS module integration.

## Core UX Rules

### 1. Interactive Feedback & State Guards
- **Loading State**: Show pulse skeletons or non-blocking spinners when fetching GraphQL/REST data.
- **Empty State**: Render clear illustrations or actionable callouts when lists/tables are empty.
- **Error State**: Provide human-friendly error toasts and field-level validation messages using Zod + React Hook Form.
- **Success Feedback**: Trigger distinct toast feedback on successful create, update, or soft-delete operations.

### 2. Accessibility (a11y)
- Visible focus rings (`focus-visible:ring-2`).
- Descriptive `aria-label` tags on icon buttons.
- Keyboard accessibility for modals, dropdowns, and forms.

### 3. Responsive Scaling
- Seamless scaling across Desktop ($>1200px$), Tablet ($768px - 1024px$), and Mobile ($<768px$).

---

## 📁 Upstream Skill References & Documentation

- [Full UI UX Pro Max Documentation](file:///c:/Users/oguz_/Desktop/MS-Randevu/.agents/skills/ui-ux-pro-max/README.md)
- [Design Intelligence Guides](file:///c:/Users/oguz_/Desktop/MS-Randevu/.agents/skills/ui-ux-pro-max/docs/)
- [CLI Tools & Scripts](file:///c:/Users/oguz_/Desktop/MS-Randevu/.agents/skills/ui-ux-pro-max/scripts/)
