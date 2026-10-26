# fish-skill-tree

Modular AI coding agent skill tree built for **Google Antigravity**, **Claude Code**, **Cursor**, and **Codex**.

Instead of loading hundreds of individual skill descriptions into every prompt, `fish-skill-tree` routes domain work through **4 single-entry sector plugins** (`/finance`, `/engineering`, `/design`, `/marketing`). Idle system-prompt overhead stays at **`~3.4K` tokens** while keeping **`~906K` tokens** of specialized playbooks, scripts, and schemas available on disk via progressive disclosure.

---

## Repository Structure

```text
fish-skill-tree/
├── [plugin]/                  # 4 Master Sector Suites + 2 Workspace Connectors
│   ├── finance-quant-suite/   # /finance router (13 sub-playbooks: DCF, LBO, 3-Statement, Polars, Quant, Prediction Markets)
│   ├── engineering-core-suite/# /engineering router (10 sub-playbooks: CodeGraph AST, SQL safety, Secret Guard, Gemini SDKs)
│   ├── design-frontend-suite/ # /design router (10 sub-playbooks: UI/UX audit, Design Tokens, Liquid Glass, Motion, Web APIs)
│   ├── marketing-growth-suite/# /marketing router (9 sub-playbooks: Technical/Programmatic SEO, Positioning, Content, Launch)
│   ├── gdocs/                 # Google Docs read/write/markdown sync plugin
│   └── gsheets/               # Google Sheets read/write/formula/chart plugin
├── [skill]/                   # 320 standalone domain & framework skills (on-demand vault)
└── [mcp]/                     # Model Context Protocol (MCP) server configs & multi-IDE context rules
    ├── mcp_config.json
    ├── financial_services_mcp.json
    ├── context_mode_configs/  # Context-mode configs for Claude Code, Cursor, Codex, Zed, VS Code, etc.
    └── mcp_servers/           # Lazy-loaded MCP tool schemas (CodeGraph, Chrome DevTools)
```

---

## 4-Sector Router Architecture

When you invoke a sector router (or describe a task in that domain), the agent reads a lightweight routing table (`~600` tokens) and loads **only** the 1–3 reference playbooks required for that task:

| Sector Command | Plugin Bundle | Included Sub-Playbooks |
| :--- | :--- | :--- |
| `/finance` | `finance-quant-suite` | Corporate Valuation (`dcf-model`, `lbo-model`, `comps-analysis`, `3-statements`), Quant & Math (`quant-analyst`, `backtesting-frameworks`), Data Science (`polars`, `duckdb`), Accounting, Prediction Market Ticket Engine |
| `/engineering` | `engineering-core-suite` | `codegraph` AST navigation, `database-assistant` (transactional SQL & `EXPLAIN`), `sensitive-data-guard` (`scan_secrets.py`), `billion-context` ACP folding, Gemini & Antigravity SDKs, REST/Backend patterns |
| `/design` | `design-frontend-suite` | `ui-ux-conversion-design`, 10-Dimension UI Audit, `design-systems` & W3C tokens, SaaS dashboards, Apple `liquid-glass`, Framer Motion / GSAP choreography, Modern Web APIs |
| `/marketing` | `marketing-growth-suite` | `seo-audit`, `programmatic-seo`, `brand-voice` & ICP positioning, multi-channel content engine (X, LinkedIn, video scripts), `launch-strategy`, `market-research`, Anti-AI-Slop writing gate |

---

## Quick Start

### 1. Install Sector Plugins (Google Antigravity)
Copy the plugins from `[plugin]/` into your Antigravity plugins directory:

```bash
mkdir -p ~/.gemini/config/plugins
cp -R "[plugin]/"* ~/.gemini/config/plugins/
```

### 2. Pull Standalone Vault Skills On Demand
Keep `[skill]/` outside your active prompt directory as a zero-token vault and symlink specific framework skills (e.g., `rust-engineer`, `playwright-pro`, `docker-expert`) only into workspaces that need them:

```bash
ln -s "$(pwd)/[skill]/rust-engineer" /path/to/your-project/.agents/skills/rust-engineer
```

### 3. Pre-Commit Secret Scanning
Run the zero-dependency secret scanner inside `[skill]/sensitive-data-guard` before committing code:

```bash
python3 "[skill]/sensitive-data-guard/scripts/scan_secrets.py" --staged
```
