---
name: ui-ux-pro-max
description: Ensures UI/UX excellence, accessibility (a11y), responsive layouts, form validation states, empty states, loading skeletons, interactive feedback toasts, and design reasoning using UI UX Pro Max.
---

# UI UX Pro Max (Core Engine & Guidelines)

This skill provides comprehensive design intelligence from [UI UX Pro Max](https://uupm.cc) including:

- **161 Reasoning Rules**: Design patterns, component UX, color theory, typography pairing, and layout grid mathematics.
- **84 UI Styles**: Glassmorphism, modern dark mode, minimal clean, enterprise dashboard, and custom aesthetic signatures.
- **Framework Support**: React, Next.js, TypeScript, Tailwind CSS, Chakra UI, Vue, Svelte, and custom CSS module integration.

---

## Core UX Rules

### 1. Interactive Feedback & State Guards
- **Loading State**: Show pulse skeletons or non-blocking spinners when fetching asynchronous data.
- **Empty State**: Render clear illustrations or actionable callouts when lists or tables are empty.
- **Error State**: Provide human-friendly error toasts and field-level validation messages using schema validators (e.g., Zod) and form hooks.
- **Success Feedback**: Trigger distinct toast feedback on successful create, update, or delete operations.

### 2. Accessibility (a11y)
- Visible focus rings (`focus-visible:ring-2`).
- Descriptive `aria-label` tags on icon buttons and interactive elements.
- Keyboard accessibility for modals, dropdowns, and forms.
- High color contrast meeting WCAG AA standards.

### 3. Responsive Scaling
- Seamless scaling across Desktop (>1200px), Tablet (768px - 1024px), and Mobile (<768px).
- Adaptive layouts: multi-column desktop collapsing cleanly into single-column mobile flows.

---

## Bundled Assets & Reference Data

- Reasoning data files are available in `src/ui-ux-pro-max/data/` (typography, styles, colors, UX guidelines, stacks).
- Core inspection scripts are located in `src/ui-ux-pro-max/scripts/`.
