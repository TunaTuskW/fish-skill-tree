# fish-skill-tree

Modular skill and plugin tree for **Google Antigravity**, **Claude Code**, **OpenAI Codex**, **Cursor**, and any `SKILL.md`-compatible agent.

`fish-skill-tree` packages domain expertise into **6 modular sector plugins** + **4 partner plugins** (`[plugin]/`) and keeps **`12` high-frequency direct tools** in `[skill]/` with zero plugin/skill duplication and 2-tier progressive disclosure (`SKILL.md` $\rightarrow$ `references/INDEX.md` $\rightarrow$ playbook).

## Repository structure

```text
fish-skill-tree/
├── [plugin]/                        # 6 domain sector suites + 4 partner plugins (10 total)
│   ├── finance-quant-suite/         # /finance router (valuation, quant, accounting, commerce/prediction ops)
│   ├── engineering-core-suite/      # /engineering router (core architecture, CodeGraph, 56 language/framework packs, 49 DevOps/DB/QA packs)
│   ├── engineering-ops-suite/       # /engineering-ops router (18 security/compliance packs, 55 agent/orchestration packs, 20 context/cost/ML packs)
│   ├── design-frontend-suite/       # /design router (UI/UX, design tokens, a11y, motion, slides, liquid glass + web guidance link)
│   ├── marketing-growth-suite/      # /marketing router (brand-marketing studio, SEO, content-writing + humanizer v4.0.0, research, growth)
│   ├── ops-research-suite/          # /ops-research router (media/video, homelab networking, scientific/healthcare, business/doc ops)
│   ├── gdocs/                       # Google Docs v0.0.9 read/write/markdown sync plugin
│   ├── gsheets/                     # Google Sheets v0.0.8 read/write/formula/chart plugin
│   ├── context7/                    # Context7 v1.0.1 live library docs MCP & skill plugin
│   └── modern-web-guidance-plugin/  # Chrome Modern Web Guidance v1.0.0 & Manifest V3 skills
├── [skill]/                         # 12 standalone direct slash/CLI tools (zero overlap with plugins)
├── AGENT_GUIDE.md                   # Multi-agent install guide (Claude Code, Codex, Antigravity, Cursor, and portable agents)
└── [mcp]/                           # Sanitized global GEMINI.md, MCP templates/bridges (codegraph, davinci-resolve, legalzoom, gmp-code-assist), and 18 IDE context-mode packs
```

## Standalone tools (`[skill]/`)

Kept directly at top level for single-command activation or lightweight per-repo symlinking:

`humanizer`, `security-guard`, `search-first`, `codebase-onboarding`, `tdd-workflow`, `git-workflow`, `verification-loop`, `documentation-lookup`, `terminal-ops`, `token-budget-advisor`, `workspace-surface-audit`, `conventional-commit-review`.

## Quick start

See [AGENT_GUIDE.md](AGENT_GUIDE.md) for copy-pasteable setup instructions for **Claude Code**, **OpenAI Codex**, **Google Antigravity**, **Cursor**, **Gemini CLI**, and other `.agents/skills/` tools.

### 1. Install modular plugins (Google Antigravity)

```bash
mkdir -p ~/.gemini/config/plugins
cp -R "[plugin]/"* ~/.gemini/config/plugins/
```

### 2. Link a standalone tool into a project

```bash
ln -s "$(pwd)/[skill]/humanizer" /path/to/your-project/.agents/skills/humanizer
```

### 3. Secret and AST security scanning

```bash
python3 "[plugin]/engineering-core-suite/skills/engineering/references/sensitive-data-guard/scripts/scan_secrets.py" --staged
python3 "[skill]/security-guard/scripts/scan_security_ast.py" --staged
```

To scan the full tree:

```bash
python3 "[plugin]/engineering-core-suite/skills/engineering/references/sensitive-data-guard/scripts/scan_secrets.py" .
python3 "[skill]/security-guard/scripts/scan_security_ast.py" .
```
