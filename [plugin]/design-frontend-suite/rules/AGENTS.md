# UI/UX Design, Visual Systems & Modern Frontend Rules

## 1. Design Direction & Visual Hierarchy First
- **Intentional Direction**: Before building or styling any UI, establish the interface job, target user scan order, density profile (dense utilitarian workspace vs. expressive editorial/landing page), and design tokens.
- **Strict Typography & Spacing Scale**: Enforce a mathematical spacing rhythm (`4px` / `8px` / `12px` / `16px` / `24px` / `32px` / `48px`) and distinct typographic hierarchy (`display` > `h1` > `h2` > `h3` > `body` > `caption` / `mono` tabular numerals for financial/quant metrics).

## 2. Anti-AI-Slop Visual Standard
- **Ban Generic AI Patterns**: Never default to unrequested purple-to-blue neon gradients, arbitrary box-shadows, mismatched border radii, or 3-column generic icon cards with vague lorem-ipsum copy.
- **Complete State Coverage**: Every interactive view and component must account for all 5 states: **Default**, **Loading (skeleton/shimmer)**, **Empty (actionable zero-state)**, **Error (inline recovery)**, and **Success/Populated**.

## 3. Accessibility & Modern Web APIs
- **Contrast & Keyboard Parity**: Maintain WCAG AA contrast ($\ge 4.5:1$ body text, $\ge 3:1$ large text/UI controls), visible `:focus-visible` rings, and full keyboard operability.
- **Modern Native Primitives**: Prefer native `<dialog>`, Popover API, CSS Grid/Subgrid, Container Queries (`@container`), `:has()`, and `tabular-nums` over brittle legacy JS layout hacks.

## 4. Mandatory Exports Mirror
- Whenever design systems (`DESIGN.md`, `design-tokens.json`), HTML previews, UI prototypes, or frontend components are generated or updated, ALWAYS save or copy a duplicate into `~/vibe/` following the project subdirectory taxonomy.
