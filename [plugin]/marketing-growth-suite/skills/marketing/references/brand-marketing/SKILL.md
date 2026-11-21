---
name: brand-marketing
description: >-
  Unified Brand Marketing Studio that turns a product brief, repo, or founder interview
  into a complete brand book, positioning and messaging matrix, verbal voice rules,
  visual direction handoff, and humanized launch copy without AI cliches.
metadata:
  origin: fish-coding-agent
  version: "1.0.0"
---

# Brand Marketing Studio

Build a coherent brand foundation and ship conversion-ready messaging in one pass. This skill connects brand strategy (`brand-discovery` and `brand-voice`), positioning and messaging architecture, visual creative direction, and `humanizer` v4.0.0 prose cleanup.

## When to use

- Creating positioning, messaging hierarchy, taglines, and brand guidelines for a new product, studio, or creator brand.
- Rebranding or tightening muddy, generic marketing copy into specific, verifiable claims.
- Turning raw founder notes, product codebases, or `brand-discovery` modules (`90_SYNTHESIS.md`) into launch-ready assets.

## Intake check

Inspect what context is already available before asking questions:

1. Check the current workspace or project docs (`README.md`, product specs, landing page copy, or existing `90_SYNTHESIS.md` and `VOICE PROFILE` artifacts).
2. If you already have the product mechanism, target customer, alternatives they use today, and primary differentiator, start immediately.
3. If key inputs are missing, ask 3 to 5 specific questions covering:
   - What buyers currently use or do instead (the real status quo).
   - The single capability you deliver that alternatives cannot match easily.
   - Who buys or adopts first (role, company stage, or buyer trigger).
   - Proof points on hand (numbers, benchmarks, customer quotes, architecture facts).
   - Tone examples or brands whose writing voice matches what you want.

Never invent customer metrics, case studies, pricing, or benchmark numbers. Mark unverified slots as `[NEED PROOF: ...]` so the user can fill them cleanly.

## Five-stage pipeline

Execute stages in order so downstream copy inherits verified strategy.

### Stage 1: Competitive positioning and category frame

Anchor positioning on buyer reality before writing taglines:

- **Competitive alternatives**: What the buyer compares you against (incumbent tools, spreadsheets, agencies, internal scripts, or doing nothing).
- **Unique attributes**: Specific product, workflow, pricing, or distribution differences.
- **Concrete value**: Translate each attribute into time saved, risk lowered, money earned, or friction removed.
- **Best-fit ICP**: Define the primary buyer segment where those attributes matter most, plus who is *not* a fit.
- **Market category and claim**: Name the category buyers already understand (or the wedge within it) and write a single-sentence positioning statement:
  `[Brand] helps [specific ICP] achieve [measurable outcome] by [concrete mechanism], unlike [primary alternative].`

### Stage 2: Messaging matrix and objection handling

Build the messaging hierarchy using [references/messaging-matrix-template.md](references/messaging-matrix-template.md):

1. **Core narrative**: One sharp thesis explaining why the old way breaks and what changes now.
2. **Three supporting pillars (or fewer if cleaner)**: Each pillar pairs a **Buyer Pain** with **Your Mechanism** and **Verifiable Proof**.
3. **Persona adaptations**: Adjust framing by buyer role (economic buyer vs hands-on user vs technical evaluator) without contradicting the core claim.
4. **Objection table**: Capture top 3 to 5 buyer doubts (switching cost, trust, learning curve, price, lock-in) and draft direct, factual answers.
5. **Headline and tagline candidates**: Draft 5 angles (outcome-led, mechanism-led, contrast-led, speed/cost-led, category-led) and stress-test each against:
   - **Competitor swap test**: Would this headline still work if you pasted a competitor's logo over yours? If yes, rewrite with a specific mechanism.
   - **Five-second test**: Can a first-time visitor tell who it is for, what it does, and why act now in under five seconds?

### Stage 3: Verbal identity and voice rules

Lock voice rules before generating channel copy:

- If writing samples exist, extract a concrete `VOICE PROFILE` matching sentence rhythm, compression, capitalization, claim style, and punctuation rules (`brand-voice`).
- Define **Voice Boundaries**:
  - **We sound like**: 3 concrete writing traits paired with an example sentence.
  - **We never sound like**: Specific traits and words to block paired with a bad example.
- Build a **Lexicon** table: preferred plain terms vs banned corporate/AI words.

### Stage 4: Visual direction handoff

Provide a focused creative direction brief designers or frontend workflows (`/design`) can execute immediately:

- **Visual posture**: Density, surface polarity (light vs dark default), mood grounded in buyer expectations rather than generic templates.
- **Color intent**: Primary surface, ink contrast target (`>= 4.5:1` WCAG AA body contrast), restrained brand accent, semantic states.
- **Typography character**: Display vs body voice (technical monospace/grotesque vs editorial serif/humanist sans), numeric tabular alignment for metrics.
- **Imagery and motion discipline**: Real product screenshots, schematics, and restraint rules (ban decorative gradients, stock 3D abstractions, and gratuitous animation).

### Stage 5: Launch assets and Anti-AI-Slop gate

Generate only the deliverables requested (or the default starter kit: **Brand Book** + **Messaging Matrix** + **Landing Hero Copy** + **2 Launch Angles**), then run a full `humanizer` (`v4.0.0`) edit across every sentence:

- Cut `Not X but Y` false contrasts unless correcting a real misconception.
- Cut staged openers (*Let's dive in*, *Here's the thing*), pseudo-deep sayings (*At its core*), unprompted defenses (*I'm not saying X*), and one-line closers (*Let that sink in.*).
- Break forced three-item lists when two or four concrete items fit better.
- Remove em-dashes added out of habit unless the brand voice sample explicitly uses them.
- Replace bloated verbs (*serves as*, *boasts*, *showcases*) with *is*, *are*, *has*, and concrete verbs.
- Delete stock AI words (*delve, tapestry, testament, underscore, pivotal, crucial, landscape, seamless, robust, revolutionary, game-changer, cutting-edge*).
- Strip unnecessary **Bold:** bullet labels and convert Title Case headings to sentence case where appropriate.

## Output contract and file exports

1. Present an executive summary in chat with the core positioning line, top 3 messaging pillars, voice summary, and headline options.
2. When building a durable brand kit for a workspace or named brand, write structured markdown files into `~/vibe/<brand-slug>/`:
   - `brand-book.md` using [references/brand-book-template.md](references/brand-book-template.md)
   - `messaging-matrix.md` using [references/messaging-matrix-template.md](references/messaging-matrix-template.md)
   - Flag missing proof inline (`[NEED PROOF: ...]`) so claims stay honest.
