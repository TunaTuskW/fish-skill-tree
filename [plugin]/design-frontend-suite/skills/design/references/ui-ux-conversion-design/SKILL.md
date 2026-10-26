---
name: ui-ux-conversion-design
description: Architect high-converting landing pages, dense SaaS/quant dashboards, UX user flows, wireframes, and complete component state matrices (loading, empty, error, populated). Use when designing new interfaces, wireframing user journeys, optimizing layout hierarchy, or translating product requirements into production UI.
metadata:
  origin: fish-coding-agent
---

# UI/UX Conversion & Product Architecture Skill

Use this skill when designing, wireframing, or restructuring web applications, SaaS dashboards, quantitative terminals, or conversion-focused landing pages.

---

## 1. Domain-Matched Layout Architecture

Never apply a marketing layout to a daily-use tool, or a dense dashboard layout to a cold-traffic landing page. Choose the right structural archetype first:

### Archetype A: Dense Operational / Quant Workspace (App / Terminal)
- **Primary Goal**: High scannability, zero wasted vertical space, rapid keyboard/mouse action.
- **Grid & Density**: 12-column fluid grid or CSS Grid workspace (`sidebar 240px` + `main 1fr` + `inspector 320px`), `8px`–`12px` compact gap, `12px`–`13px` body font, `font-variant-numeric: tabular-nums` on all numeric columns and tickers.
- **Above-the-Fold Priority**: Live status bar, primary KPI strip (max 4–5 cards with delta badges and sparklines), primary filter/command bar (`Cmd+K`), and the core data table or canvas immediately visible without scrolling.

### Archetype B: High-Converting Product Landing Page (Marketing / Growth)
- **Primary Goal**: Immediate comprehension within 3 seconds, trust building, friction-free conversion.
- **Visual Flow (The 7-Block Conversion Arc)**:
  1. **Hero Section**: Specific outcome headline + concrete subheadline + primary CTA (with micro-copy reducing risk, e.g., *"No credit card required · 2-min setup"*) + interactive product preview or high-signal visual.
  2. **Social Proof / Authority Bar**: Concrete metrics, recognizable logos, or verifiable benchmark badges.
  3. **Problem / Old Way vs. New Way**: Side-by-side contrast showing the exact pain of status-quo workflows vs. the product mechanism.
  4. **Interactive Feature Bento / Walkthrough**: 3–4 core capabilities paired with real UI states (never abstract stock illustrations).
  5. **Quantitative Proof / Case Study**: Before/after numbers, latency/speed benchmarks, or testimonial with specific attribution.
  6. **Pricing / Tier Matrix**: Clear anchor tier, highlighted recommended plan, and transparent feature comparison.
  7. **Objection-Crushing FAQ + Final CTA**: Address the top 5 buying hesitations directly, followed by a clean closing action block.

---

## 2. The 5-State Component Matrix (Mandatory)

Before writing component code, define all 5 operational states for every data-driven surface:

| State | Visual & UX Requirement |
| :--- | :--- |
| **1. Empty (Zero-Data)** | Explain *why* it is empty and provide a 1-click primary action or sample data loader to populate it. |
| **2. Loading (Pending)** | Match skeleton geometry to the exact final layout to ensure zero Cumulative Layout Shift (`CLS = 0`). |
| **3. Populated (Ideal)** | Enforce truncation (`text-overflow: ellipsis`), alignment (right-align numbers, left-align text), and hover affordances. |
| **4. Overflow / Edge** | Handle 10,000+ rows (virtualization/pagination), long unbroken strings, and narrow mobile/split-screen viewports. |
| **5. Error / Degraded** | State what failed in plain human language, preserve user input, and provide an inline **Retry** or fallback action. |

---

## 3. Wireframing & Design Token Handoff Workflow

When asked to design or revamp a UI:
1. **Information Architecture (IA) Spec**: List the page sections or workspace panes ranked by user priority (P0 = must see immediately, P1 = secondary context, P2 = progressive disclosure / drawer / modal).
2. **Token Definition**: Define CSS custom properties (`--bg-surface`, `--bg-elevated`, `--text-primary`, `--text-muted`, `--accent-primary`, `--border-subtle`, `--radius-md`) supporting both Light and Dark themes.
3. **Interactive Verification**: Pair with `design-system` to audit the resulting interface across all 10 visual quality dimensions.
