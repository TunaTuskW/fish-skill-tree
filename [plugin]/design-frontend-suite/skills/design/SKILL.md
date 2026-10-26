---
name: design
description: Master sector router for UI/UX Product Design, Design Systems & Tokens, 10-Dimension Visual Audits, SaaS Dashboards & Conversion Landing Pages, Apple Liquid Glass, Advanced Motion, and Modern Web APIs. When invoked, the agent automatically selects and loads the exact sub-playbooks needed.
metadata:
  origin: fish-coding-agent
---

# UI/UX Design, Visual Systems & Frontend Sector Router (`/design`)

You have activated the **UI/UX Design, Visual Systems & Modern Frontend** sector.

## Autonomous Sub-Skill Selection Protocol (Agent-Driven Routing)

Do **NOT** load every sub-playbook at once. Analyze the user's request, decide which specific sub-modules below are required, and read **only** the matching `SKILL.md` and reference files inside `references/`:

| Sub-Domain | When to Select & Load | Path to Read |
| :--- | :--- | :--- |
| **1. UI/UX Conversion & Wireframing** | Designing SaaS/quant dashboards, high-converting landing pages, wireframes, or 5-state component matrices | [`references/ui-ux-conversion-design/SKILL.md`](references/ui-ux-conversion-design/SKILL.md) |
| **2. Design System & 10-Point Visual Audit** | Extracting `design-tokens.json` + CSS variables, generating `DESIGN.md` & HTML previews, or scoring UI consistency | [`references/design-system/SKILL.md`](references/design-system/SKILL.md) |
| **3. Frontend Design Direction** | Setting product-specific art direction, typography hierarchy, layout density, and eliminating generic AI-slop styling | [`references/frontend-design-direction/SKILL.md`](references/frontend-design-direction/SKILL.md) |
| **4. Modern Web Guidance (Mandatory HTML/CSS/JS)** | Implementing modals (`<dialog>`), Popovers, container queries, `:has()`, View Transitions, or CWV optimization | [`references/modern-web-guidance/SKILL.md`](references/modern-web-guidance/SKILL.md) |
| **5. Apple iOS 26 Liquid Glass** | Building dynamic translucent glass materials, blur, reflection, and morphing in SwiftUI/UIKit/WidgetKit | [`references/liquid-glass-design/SKILL.md`](references/liquid-glass-design/SKILL.md) |
| **6. Advanced Motion & Choreography** | Drag & drop, gestures, spring animations, SVG path drawing, or `useAnimate` sequences in React/Next.js | [`references/motion-advanced/SKILL.md`](references/motion-advanced/SKILL.md) |
| **7. Frontend Accessibility (a11y)** | Semantic HTML, ARIA attributes, keyboard navigation, focus traps, and screen reader compliance | [`references/frontend-a11y/SKILL.md`](references/frontend-a11y/SKILL.md) |
| **8. Interactive Slides & UI Demos** | Building HTML presentations/pitch decks or recording Playwright UI walkthrough videos | [`references/frontend-slides/SKILL.md`](references/frontend-slides/SKILL.md) & [`references/ui-demo/SKILL.md`](references/ui-demo/SKILL.md) |
| **9. Chrome Extensions (Manifest V3)** | Building browser extensions, side panels, content scripts, service workers, or Chrome Web Store packages | [`references/chrome-extensions/SKILL.md`](references/chrome-extensions/SKILL.md) |

## Execution Workflow
1. Identify the 1–3 relevant sub-modules from the routing table above based on the user's design or frontend task.
2. State briefly which sub-modules you are activating (e.g., *"Activating `ui-ux-conversion-design` + `design-system`"*).
3. Read the corresponding `references/<sub-module>/SKILL.md` and execute its workflow end-to-end.
