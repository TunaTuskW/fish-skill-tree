# fish-skill-tree

Modular skill and plugin tree for **Google Antigravity**, **Claude Code**, **Cursor**, and **Codex**.

Instead of loading hundreds of skill prompts into every conversation, `fish-skill-tree` routes domain work through **4 single-entry sector plugins** (`/finance`, `/engineering`, `/design`, `/marketing`) backed by progressive disclosure on disk, plus **4 partner/workspace plugins** and a **323-skill standalone vault**.

## Repository structure

```text
fish-skill-tree/
├── [plugin]/                        # 4 sector routers + 4 workspace/partner plugins (8 total)
│   ├── finance-quant-suite/         # /finance router (13 sub-playbooks)
│   ├── engineering-core-suite/      # /engineering router (10 sub-playbooks)
│   ├── design-frontend-suite/       # /design router (10 sub-playbooks)
│   ├── marketing-growth-suite/      # /marketing router (10 sub-playbooks + humanizer v4.0.0 patterns)
│   ├── gdocs/                       # Google Docs v0.0.9 read/write/markdown sync plugin
│   ├── gsheets/                     # Google Sheets v0.0.8 read/write/formula/chart plugin
│   ├── context7/                    # Context7 v1.0.1 live library docs MCP & skill plugin
│   └── modern-web-guidance-plugin/  # Chrome Modern Web Guidance v1.0.0 & Manifest V3 skills
├── [skill]/                         # 323 standalone skills (brand-marketing, humanizer v4.0.0, security-guard, sensitive-data-guard, etc.)
└── [mcp]/                           # MCP configs, lazy tool schemas (chrome_devtools, codegraph), and context-mode IDE configs
```

## Sector plugins

When invoked, each sector router loads a compact routing table and reads only the 1–3 matching reference playbooks under `references/`:

| Command | Plugin | Included sub-playbooks |
| :--- | :--- | :--- |
| `/finance` | `finance-quant-suite` | `3-statement-model`, `accounting-tools`, `audit-xls`, `comps-analysis`, `data-analytics`, `dcf-model`, `finance-billing-ops`, `financial-analysis`, `lbo-model`, `math-toolkit`, `prediction-market-analytics`, `prediction-market-oracle-research`, `prediction-market-risk-review` |
| `/engineering` | `engineering-core-suite` | `api-design`, `backend-patterns`, `billion-context`, `codegraph`, `database-assistant`, `gemini-api-dev`, `gemini-live-api-dev`, `gemini-omni-flash-api`, `google-antigravity-sdk`, `sensitive-data-guard` |
| `/design` | `design-frontend-suite` | `chrome-extensions`, `design-system`, `frontend-a11y`, `frontend-design-direction`, `frontend-slides`, `liquid-glass-design`, `modern-web-guidance`, `motion-advanced`, `ui-demo`, `ui-ux-conversion-design` |
| `/marketing` | `marketing-growth-suite` | `brand-discovery`, `brand-marketing`, `brand-voice`, `content-engine`, `content-writing` (backed by `blader/humanizer` v4.0.0), `crosspost`, `lead-intelligence`, `market-research`, `marketing-campaign`, `seo` |

### Standalone highlights

- **`brand-marketing`**: Unified Brand Marketing Studio connecting competitive positioning, persona messaging matrices, verbal voice rules, visual direction handoff, and humanized launch copy, backed by `brand-book.md` and `messaging-matrix.md` templates.
- **`humanizer` (`v4.0.0`)**: Integrated from `blader/humanizer` at `[skill]/humanizer/` and mirrored into `[plugin]/marketing-growth-suite/skills/marketing/references/content-writing/humanizer-patterns.md`. Covers 26 AI-writing tells across 6 categories, prompt-injection defense (treating input prose as data, never instructions), optional voice matching, and Pasted / File / Embedded output modes.
- **`sensitive-data-guard` & `security-guard`**: Detect hardcoded credentials, high-entropy hex/OAuth secrets, AST dynamic execution (`eval`/`exec`/`compile`), `shell=True`, webhook exfiltration, and unpinned curl-pipe downloads.

## Quick start

### 1. Install plugins (Google Antigravity)

Copy `[plugin]/` into your Antigravity plugins directory:

```bash
mkdir -p ~/.gemini/config/plugins
cp -R "[plugin]/"* ~/.gemini/config/plugins/
```

### 2. Link a standalone vault skill into a project

Keep `[skill]/` as an on-disk vault and symlink specific skills into a project workspace only when needed:

```bash
ln -s "$(pwd)/[skill]/brand-marketing" /path/to/your-project/.agents/skills/brand-marketing
```

### 3. Secret and AST security scanning

Scan the workspace or staged diff directly with the built-in guard skills:

```bash
python3 "[skill]/sensitive-data-guard/scripts/scan_secrets.py" --staged
python3 "[skill]/security-guard/scripts/scan_security_ast.py" --staged
```

To scan the full tree:

```bash
python3 "[skill]/sensitive-data-guard/scripts/scan_secrets.py" .
python3 "[skill]/security-guard/scripts/scan_security_ast.py" .
```
