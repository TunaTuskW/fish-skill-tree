# fish-skill-tree

Modular skill and plugin tree for **Google Antigravity**, **Claude Code**, **Cursor**, and **Codex**.

Instead of loading hundreds of skill prompts into every conversation, `fish-skill-tree` separates modular **4 sector plugins** + **4 partner plugins** (`[plugin]/`) from **294 non-overlapping standalone skills** (`[skill]/`) with zero duplicate skills between plugins and standalone vaults.

## Repository structure

```text
fish-skill-tree/
├── [plugin]/                        # 4 sector routers + 4 workspace/partner plugins (8 total)
│   ├── finance-quant-suite/         # /finance router (13 sub-playbooks)
│   ├── engineering-core-suite/      # /engineering router (10 sub-playbooks, incl. sensitive-data-guard & billion-context)
│   ├── design-frontend-suite/       # /design router (8 native sub-playbooks + modern-web-guidance-plugin links)
│   ├── marketing-growth-suite/      # /marketing router (10 sub-playbooks + humanizer v4.0.0 patterns)
│   ├── gdocs/                       # Google Docs v0.0.9 read/write/markdown sync plugin
│   ├── gsheets/                     # Google Sheets v0.0.8 read/write/formula/chart plugin
│   ├── context7/                    # Context7 v1.0.1 live library docs MCP & skill plugin
│   └── modern-web-guidance-plugin/  # Chrome Modern Web Guidance v1.0.0 & Manifest V3 skills
├── [skill]/                         # 294 unique standalone skills (humanizer v4.0.0, security-guard, framework skills, etc.)
├── AGENT_GUIDE.md                   # Multi-agent install guide (Claude Code, Codex, Antigravity, Cursor, and portable agents)
└── [mcp]/                           # Sanitized global GEMINI.md, MCP templates/bridges (codegraph, davinci-resolve, legalzoom, gmp-code-assist), and 18 IDE context-mode packs
```

## Sector plugins

When invoked, each sector router loads a compact routing table and reads only the 1–3 matching reference playbooks under `references/`:

| Command | Plugin | Included sub-playbooks |
| :--- | :--- | :--- |
| `/finance` | `finance-quant-suite` | `3-statement-model`, `accounting-tools`, `audit-xls`, `comps-analysis`, `data-analytics`, `dcf-model`, `finance-billing-ops`, `financial-analysis`, `lbo-model`, `math-toolkit`, `prediction-market-analytics`, `prediction-market-oracle-research`, `prediction-market-risk-review` |
| `/engineering` | `engineering-core-suite` | `api-design`, `backend-patterns`, `billion-context`, `codegraph`, `database-assistant`, `gemini-api-dev`, `gemini-live-api-dev`, `gemini-omni-flash-api`, `google-antigravity-sdk`, `sensitive-data-guard` |
| `/design` | `design-frontend-suite` | `design-system`, `frontend-a11y`, `frontend-design-direction`, `frontend-slides`, `liquid-glass-design`, `motion-advanced`, `ui-demo`, `ui-ux-conversion-design` (routes web APIs & extensions to `modern-web-guidance-plugin`) |
| `/marketing` | `marketing-growth-suite` | `brand-discovery`, `brand-marketing`, `brand-voice`, `content-engine`, `content-writing` (backed by `blader/humanizer` v4.0.0), `crosspost`, `lead-intelligence`, `market-research`, `marketing-campaign`, `seo` |

### Standalone & security highlights

- **`humanizer` (`v4.0.0`)**: Integrated from `blader/humanizer` at `[skill]/humanizer/` for direct `/humanizer` invocation (with pattern reference shared inside `marketing-growth-suite/content-writing`). Covers 26 AI-writing tells across 6 categories, prompt-injection defense, optional voice matching, and Pasted / File / Embedded output modes.
- **`sensitive-data-guard` & `security-guard`**: Canonical secret scanner inside `engineering-core-suite` (`scan_secrets.py`) plus standalone `[skill]/security-guard/` (`scan_security_ast.py`) to detect leaked credentials, high-entropy hex/OAuth secrets, AST dynamic execution (`eval`/`exec`/`compile`), `shell=True`, webhook exfiltration, and unpinned curl-pipe downloads.

## Quick start

See [AGENT_GUIDE.md](AGENT_GUIDE.md) for copy-pasteable setup instructions for **Claude Code**, **OpenAI Codex**, **Google Antigravity**, **Cursor**, **Gemini CLI**, and other `.agents/skills/` tools.

### 1. Install plugins (Google Antigravity)

Copy `[plugin]/` into your Antigravity plugins directory:

```bash
mkdir -p ~/.gemini/config/plugins
cp -R "[plugin]/"* ~/.gemini/config/plugins/
```

### 2. Link a standalone vault skill into a project

Keep `[skill]/` as an on-disk vault and symlink specific framework or utility skills into a project workspace only when needed:

```bash
ln -s "$(pwd)/[skill]/rust-engineer" /path/to/your-project/.agents/skills/rust-engineer
```

### 3. Secret and AST security scanning

Scan the workspace or staged diff directly with the built-in guard skills:

```bash
python3 "[plugin]/engineering-core-suite/skills/engineering/references/sensitive-data-guard/scripts/scan_secrets.py" --staged
python3 "[skill]/security-guard/scripts/scan_security_ast.py" --staged
```

To scan the full tree:

```bash
python3 "[plugin]/engineering-core-suite/skills/engineering/references/sensitive-data-guard/scripts/scan_secrets.py" .
python3 "[skill]/security-guard/scripts/scan_security_ast.py" .
```
