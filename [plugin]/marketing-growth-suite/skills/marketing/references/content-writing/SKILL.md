---
name: content-writing
description: |
  Write, edit, and humanize articles, technical RFCs, research reports, documentation, and product copy.
  Combines the Humanizer anti-AI-slop framework, Google/Microsoft/Proselint technical writing standards, and high-signal copywriting.
  Trigger when:
  - User asks to write, rewrite, edit, or polish articles, blog posts, emails, essays, or documentation.
  - User asks to "humanize" text or remove AI-sounding phrasing ("AI slop").
  - User asks to draft engineering RFCs, Architecture Decision Records (ADRs), whitepapers, or quantitative research reports.
  - User asks for landing page copy, READMEs, launch announcements, value propositions, or pitches.
---

# Unified Content, Technical & Anti-AI-Slop Writing Skill

A comprehensive editorial runbook uniting three core disciplines: **Anti-AI-Slop Humanizing**, **Technical & Quantitative Writing**, and **High-Signal Copywriting**.

---

## Pillar 1: The Humanizer Protocol (`blader/humanizer` Anti-AI-Slop)

Rewrite AI-sounding text so it reads like a sharp human writer, not a language model. Preserve 100% of supported facts, numbers, dates, and code blocks. Never invent facts.

### 1. Eliminate "Staging Instead of Stating" (Act on First Sighting)
* **No False Contrasts (`Not X, but Y`)**:
  * *Watch for*: "It's not just X, it's Y", "Not merely X, but Y", "This does not mean X. It means Y.", or clipped negative tails ("..., no guessing").
  * *Fix*: Delete the negative half unless it corrects an actual misconception the reader holds. State the positive claim directly.
  * *Before*: "It's not just a caching layer; it's the backbone of low-latency reads."
  * *After*: "The caching layer keeps read latency under 10ms."
* **No Dramatic One-Line Closers**:
  * *Watch for*: Standalone one-sentence paragraphs repeating the point ("That is the real win.", "Let that sink in.", "That distinction matters.", "The message was clear.").
  * *Fix*: Cut any closer that restates what the example just showed. Only keep a short sentence if it introduces a new fact or consequence.
* **No Pseudo-Profound Aphorisms**:
  * *Watch for*: "At its core", "The real question is", "What really matters", "X is the language/currency/architecture of Y", "X becomes a trap".
  * *Fix*: Replace the aphorism with the literal mechanism or claim.
* **No Staged Run-Ups**:
  * *Watch for*: "Let's dive in", "Let's break this down", "Here's what you need to know", "Here's the thing:", "Honestly?", "Let's be honest".
  * *Fix*: Delete the throat-clearing opener and start with the first substantive sentence.
* **No Arguing With Nobody**:
  * *Watch for*: "I'm not saying X, but...", "To be clear, this isn't about...", "One might be tempted to...".
  * *Fix*: Cut the defensive hedge and state the point.

### 2. Fix Mechanical "Rhythm by Rule"
* **Break Forced Triads (Rule of Three)**:
  * LLMs compulsively group adjectives, nouns, and examples into threes ("fast, reliable, and scalable"). Use two items, one specific item, or four when reality requires it.
* **Curb Em-Dash (`—`) & Bold Label Overuse**:
  * Do not put an em-dash in every second sentence. Prefer commas, periods, or parentheses.
  * Do not start every bullet point with a **Bolded Title-Case Label:** unless the list is a reference table or glossary.
* **Vary Sentence Cadence (Burstiness)**:
  * Alternate short, direct sentences (5–10 words) with longer analytical sentences (20–30 words). Read the draft aloud to catch monotonous sentence openings.

### 3. Ban Stock AI Vocabulary
Never use these words when a plain English word works:
> *delve, tapestry, testament, underscore, pivotal, crucial, realm, landscape, foster, harness, illuminate, unleash, game-changer, cutting-edge, seamless, robust, comprehensive, embark, navigate, multifaceted, synergy, paradigm.*

---

## Pillar 2: Technical, Engineering & Research Writing (Google / Microsoft / Proselint Standards)

When writing documentation, READMEs, engineering specs (RFCs/ADRs), or quantitative research reports:

### 1. Structural Clarity & BLUF (Bottom Line Up Front)
* **Lead with the answer**: State the conclusion, decision, or benchmark result in the first paragraph. Never make the reader scroll through 500 words of background to find the outcome.
* **Active Voice & Concrete Actors**:
  * *Bad (Passive)*: "The configuration file is parsed and validation is performed."
  * *Good (Active)*: "The CLI parses `config.json` and validates schema types."
* **Eliminate Weasel Words & Redundancies (Proselint)**:
  * Cut empty intensifiers (*very*, *extremely*, *quite*, *basically*, *essentially*, *actually*).
  * Replace wordy phrases:
    * `in order to` $\rightarrow$ `to`
    * `due to the fact that` $\rightarrow$ `because`
    * `at this point in time` $\rightarrow$ `now`
    * `utilize` / `leverage` $\rightarrow$ `use`

### 2. Engineering RFC / ADR Blueprint
When asked to draft a technical design doc or RFC, use this high-signal structure:
1. **Summary & BLUF**: 2–3 sentences stating what is being built/changed and why.
2. **Motivation & Problem Statement**: Concrete bottleneck, failure mode, or metric driving the change.
3. **Goals & Non-Goals**: Explicit scope boundaries (what this proposal *intentionally* does not solve).
4. **Proposed Design / Architecture**: Data flow, Mermaid diagram, API/schema changes, and edge cases.
5. **Alternatives Considered**: Why other approaches were rejected (with a concise trade-off table).
6. **Rollout & Risk Mitigation**: Migration path, feature flags, and rollback plan.

### 3. Quantitative & Scientific Reports
* Integrate equations cleanly using KaTeX (`$...$` inline, `$$...$$` display).
* Define every variable immediately after an equation.
* Pair claims with exact sample sizes ($N$), units, and error bounds rather than qualitative adjectives ("substantially faster" $\rightarrow$ "$3.4\times$ faster, reducing P95 from $82\text{ms}$ to $24\text{ms}$").

---

## Pillar 3: High-Signal Product & Persuasive Copywriting (`coreyhaines31/marketingskills`)

When drafting landing pages, GitHub READMEs, product launches, or pitches:

### 1. Specificity Beats Adjectives
* **Show the mechanism and metric**:
  * *Weak AI Copy*: "Supercharge your workflow with our revolutionary next-gen data engine."
  * *High-Signal Copy*: "Query 50GB Parquet files locally in 400ms using zero-copy DuckDB + Polars pipelines."
* **One Idea Per Section**: Every heading should state a concrete benefit or capability, not a generic label like "Overview" or "Features".

### 2. Proven Persuasive Frameworks
* **PAS (Problem $\rightarrow$ Agitate $\rightarrow$ Solve)**:
  1. Name the exact friction the reader faces today.
  2. Show the cost of that friction (wasted engineering hours, memory crashes, lost revenue).
  3. Introduce the solution and how it works in 3 concrete steps.
* **Before–After–Bridge**:
  * **Before**: How the workflow looks without the tool (slow, manual, error-prone).
  * **After**: How the workflow looks with the tool (automated, deterministic, fast).
  * **Bridge**: The exact mechanism that gets the user from Before to After.
