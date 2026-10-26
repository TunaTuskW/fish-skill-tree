---
name: engineering
description: Master sector router for Core Software Engineering, CodeGraph AST Navigation, SQL Database Safety & Migrations, Zero-Leak Secret Protection, Billion-Context Folding, and Gemini/Antigravity AI SDKs. When invoked, the agent automatically selects and loads the exact sub-playbooks needed.
metadata:
  origin: fish-coding-agent
---

# Core Engineering, Security & AI SDK Sector Router (`/engineering`)

You have activated the **Core Software Engineering, Database, Security & AI SDK** sector.

## Autonomous Sub-Skill Selection Protocol (Agent-Driven Routing)

Do **NOT** load every sub-playbook at once. Analyze the user's request, decide which specific sub-modules below are required, and read **only** the matching `SKILL.md` and reference files inside `references/`:

| Sub-Domain | When to Select & Load | Path to Read |
| :--- | :--- | :--- |
| **1. CodeGraph AST Intelligence** | Starting a project, auditing architecture, tracing `callers`/`callees`, or checking refactor `impact` | [`references/codegraph/SKILL.md`](references/codegraph/SKILL.md) |
| **2. SQL Database Assistant** | Designing schemas, writing transactional migrations, optimizing indexes, or reviewing `EXPLAIN ANALYZE` | [`references/database-assistant/SKILL.md`](references/database-assistant/SKILL.md) |
| **3. Sensitive Data & Secret Guard** | Auditing staged git diffs or repositories for exposed API keys, `.env` leaks, or credentials | [`references/sensitive-data-guard/SKILL.md`](references/sensitive-data-guard/SKILL.md) & [`scripts/scan_secrets.py`](scripts/scan_secrets.py) |
| **4. Billion-Context Folding** | Managing long-running marathon sessions, context token composition, and `decompress-to-file` | [`references/billion-context/SKILL.md`](references/billion-context/SKILL.md) & [`scripts/check_acp_status.py`](scripts/check_acp_status.py) |
| **5. Google Antigravity SDK** | Designing and orchestrating autonomous multi-agent systems with the Antigravity Python SDK | [`references/google-antigravity-sdk/SKILL.md`](references/google-antigravity-sdk/SKILL.md) |
| **6. Gemini API (Text/Multimodal/Agents)** | Calling Gemini API via `google-genai` (Python) or `@google/genai` (TS) for structured output, tools, or TTS | [`references/gemini-api-dev/SKILL.md`](references/gemini-api-dev/SKILL.md) |
| **7. Gemini Live API (WebSockets)** | Real-time bidirectional audio/video streaming, VAD, and live session management | [`references/gemini-live-api-dev/SKILL.md`](references/gemini-live-api-dev/SKILL.md) |
| **8. Gemini Omni Flash Video API** | Generative video editing, text/image-to-video, and frame transitions (`gemini-omni-1.1-flash`) | [`references/gemini-omni-flash-api/SKILL.md`](references/gemini-omni-flash-api/SKILL.md) |
| **9. REST API & Backend Patterns** | Resource naming, pagination, rate limiting, error handling, and Node/Express/Next.js backend architecture | [`references/api-design/SKILL.md`](references/api-design/SKILL.md) & [`references/backend-patterns/SKILL.md`](references/backend-patterns/SKILL.md) |
| **10. Tech-Specific Vault Skills** | If the repository uses a framework not listed above (e.g., Rust, Django, Docker, Prisma, Playwright) | Run `~/.local/bin/pull-skill search <keyword>` and link from `~/.gemini/skill_vault/skills/` |

## Execution Workflow
1. Identify the 1–3 relevant sub-modules from the routing table above based on the user's coding task.
2. State briefly which sub-modules you are activating (e.g., *"Activating `codegraph` + `database-assistant`"*).
3. Read the corresponding `references/<sub-module>/SKILL.md` and execute its workflow end-to-end.
