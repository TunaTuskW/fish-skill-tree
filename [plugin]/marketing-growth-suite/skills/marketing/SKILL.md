---
name: marketing
description: Master sector router for Technical & Programmatic SEO, Brand Voice & Positioning, Multi-Channel Content Engine (X, LinkedIn, Video Scripts), Product Launch Campaigns, Market Research, and Anti-AI-Slop Writing. When invoked, the agent automatically selects and loads the exact sub-playbooks needed.
metadata:
  origin: fish-coding-agent
---

# Marketing, Brand, SEO & Content Engine Sector Router (`/marketing`)

You have activated the **Marketing, Brand, SEO & Content Engine** sector.

## Autonomous Sub-Skill Selection Protocol (Agent-Driven Routing)

Do **NOT** load every sub-playbook at once. Analyze the user's request, decide which specific sub-modules below are required, and read **only** the matching `SKILL.md` and reference files inside `references/`:

| Sub-Domain | When to Select & Load | Path to Read |
| :--- | :--- | :--- |
| **1. Technical & Programmatic SEO** | Auditing crawlability, indexability, Core Web Vitals, `schema.org` JSON-LD, or keyword-to-URL mapping | [`references/seo/SKILL.md`](references/seo/SKILL.md) |
| **2. End-to-End Marketing Campaigns** | Planning product launches, positioning angles, landing page copy, email sequences, ad variants, and calendars | [`references/marketing-campaign/SKILL.md`](references/marketing-campaign/SKILL.md) |
| **3. Multi-Channel Content Engine** | Writing platform-native X threads, LinkedIn posts, TikTok/YouTube scripts, newsletters, or crossposting | [`references/content-engine/SKILL.md`](references/content-engine/SKILL.md) & [`references/crosspost/SKILL.md`](references/crosspost/SKILL.md) |
| **4. Brand Voice & Brand Discovery** | Extracting a durable writing style profile from real posts/docs or running structured brand positioning interviews | [`references/brand-voice/SKILL.md`](references/brand-voice/SKILL.md) & [`references/brand-discovery/SKILL.md`](references/brand-discovery/SKILL.md) |
| **5. Market Research & Lead Intelligence** | Competitor teardowns, market sizing, ICP profiling, warm path discovery, and outbound sequencing | [`references/market-research/SKILL.md`](references/market-research/SKILL.md) & [`references/lead-intelligence/SKILL.md`](references/lead-intelligence/SKILL.md) |
| **6. Anti-AI-Slop & Technical Copywriting** | Writing, editing, or humanizing articles, RFCs, whitepapers, READMEs, and high-signal product copy | [`references/content-writing/SKILL.md`](references/content-writing/SKILL.md) |

## Execution Workflow
1. Identify the 1–3 relevant sub-modules from the routing table above based on the user's marketing, SEO, or writing task.
2. State briefly which sub-modules you are activating (e.g., *"Activating `seo` + `content-engine`"*).
3. Read the corresponding `references/<sub-module>/SKILL.md` and execute its workflow end-to-end.
