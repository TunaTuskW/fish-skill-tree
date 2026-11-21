# Agentic setup guide (`fish-skill-tree`)

Use `fish-skill-tree` with **Claude Code**, **OpenAI Codex**, **Google Antigravity**, **Cursor**, **Gemini CLI**, **OpenCode**, **pi**, **VS Code / JetBrains Copilot**, or any agent supporting the open `SKILL.md` specification.

## How the tree works across agents

1. **Progressive disclosure**: Load the four compact sector routers under `[plugin]/` (`finance-quant-suite`, `engineering-core-suite`, `design-frontend-suite`, `marketing-growth-suite`) instead of indexing all `294` standalone skills into every prompt. Each router reads only the matching `references/*/SKILL.md` playbooks when a task triggers that domain.
2. **On-demand standalone vault**: Symlink or copy unique folders from `[skill]/` (such as `humanizer`, `security-guard`, `rust-engineer`, `playwright-pro`) into project or global skill directories only when needed — zero duplicates with `[plugin]/`.
3. **Global rules, context-mode, and sanitized MCP packs**: Use `[mcp]/GEMINI.md`, `[mcp]/mcp_config.json` (covering `codegraph`, `davinci-resolve`, `gmp-code-assist`, `legalzoom` with censored paths), `[mcp]/financial_services_mcp.json`, and `[mcp]/context_mode_configs/<agent>/` cleanly across workspaces.

Set an environment variable once to run the copy commands below from anywhere:

```bash
export FISH_TREE="/path/to/fish-skill-tree"
```

## Claude Code

Claude Code reads skills from `~/.claude/skills/` (global) or `.claude/skills/` (per project), project instructions from `CLAUDE.md`, and MCP servers from `~/.claude.json` or `.mcp.json`.

### 1. Install sector skills and vault picks

```bash
mkdir -p ~/.claude/skills
for suite in finance-quant-suite engineering-core-suite design-frontend-suite marketing-growth-suite; do
  ln -s "$FISH_TREE/[plugin]/$suite/skills/"* ~/.claude/skills/
done

# Optional standalone skills not inside a plugin
ln -s "$FISH_TREE/[skill]/humanizer" ~/.claude/skills/humanizer
ln -s "$FISH_TREE/[skill]/security-guard" ~/.claude/skills/security-guard
```

### 2. Add rules and MCP servers

```bash
# Append domain rules into project or global CLAUDE.md
cat "$FISH_TREE/[mcp]/context_mode_configs/claude-code/CLAUDE.md" >> ~/.claude/CLAUDE.md

# Or register CodeGraph / workspace MCP servers in a repo .mcp.json
cp "$FISH_TREE/[mcp]/mcp_config.json" ./.mcp.json
```

## OpenAI Codex CLI

Codex discovers `SKILL.md` folders under `~/.codex/skills/` (global) or `.codex/skills/` (project), reads instructions from `AGENTS.md`, and loads MCP servers from `~/.codex/config.toml`.

```bash
mkdir -p ~/.codex/skills ~/.codex

# Link the 4 sector routers
for suite in finance-quant-suite engineering-core-suite design-frontend-suite marketing-growth-suite; do
  ln -s "$FISH_TREE/[plugin]/$suite/skills/"* ~/.codex/skills/
done

# Link individual unique vault skills (example)
ln -s "$FISH_TREE/[skill]/humanizer" ~/.codex/skills/humanizer
ln -s "$FISH_TREE/[skill]/security-guard" ~/.codex/skills/security-guard

# Install context-mode instructions, hooks, and MCP config
cp "$FISH_TREE/[mcp]/context_mode_configs/codex/AGENTS.md" ~/.codex/AGENTS.md
cp "$FISH_TREE/[mcp]/context_mode_configs/codex/hooks.json" ~/.codex/hooks.json
cat "$FISH_TREE/[mcp]/context_mode_configs/codex/config.toml" >> ~/.codex/config.toml
```

In chat or scripts, trigger a skill explicitly with `$brand-marketing`, `$humanizer`, `$finance`, `$engineering`, `$design`, or `$marketing`, or let Codex match the `SKILL.md` description automatically.

## Google Antigravity

Antigravity loads bundled plugins from `~/.gemini/config/plugins/` and active standalone skills from `~/.gemini/config/skills/`.

```bash
mkdir -p ~/.gemini/config/plugins ~/.gemini/config/skills

# Install all 8 plugin bundles (4 sector suites + gdocs, gsheets, context7, modern-web-guidance-plugin)
cp -R "$FISH_TREE/[plugin]/"* ~/.gemini/config/plugins/

# Install active standalone skills on demand (keep built-in IDE skills and local-only skills separate)
cp -R "$FISH_TREE/[skill]/humanizer" ~/.gemini/config/skills/

# Global identity & context-mode config + sanitized MCP
cp "$FISH_TREE/[mcp]/GEMINI.md" ~/.gemini/GEMINI.md
cat "$FISH_TREE/[mcp]/context_mode_configs/antigravity/GEMINI.md" >> ~/.gemini/GEMINI.md
```

Use `/finance`, `/engineering`, `/design`, and `/marketing` or natural prompts matching each skill's description.

## Cursor

Cursor loads `.cursor/skills/`, `.cursor/rules/*.mdc`, `hooks.json`, and `mcp.json`.

```bash
mkdir -p .cursor/skills .cursor/rules

for suite in finance-quant-suite engineering-core-suite design-frontend-suite marketing-growth-suite; do
  ln -s "$FISH_TREE/[plugin]/$suite/skills/"* .cursor/skills/
done

cp "$FISH_TREE/[mcp]/context_mode_configs/cursor/context-mode.mdc" .cursor/rules/
cp "$FISH_TREE/[mcp]/context_mode_configs/cursor/hooks.json" .cursor/hooks.json
cp "$FISH_TREE/[mcp]/context_mode_configs/cursor/mcp.json" .cursor/mcp.json
```

## Any other agent (`AGENTS.md` and `.agents/skills/`)

Most portable coding agents (`Gemini CLI`, `OpenCode`, `pi`, `Zed`, `VS Code Copilot`, `JetBrains Copilot`, `Kiro`, `Qwen Code`, `Kilo`, `Kimi`, `OMP`, `OpenClaw`, `Copilot CLI`) support two open standards:

1. **Cross-agent skill directory (`.agents/skills/`)**:

```bash
mkdir -p .agents/skills
for suite in finance-quant-suite engineering-core-suite design-frontend-suite marketing-growth-suite; do
  ln -s "$FISH_TREE/[plugin]/$suite/skills/"* .agents/skills/
done

# Pull extra standalone framework/domain skills per repo
ln -s "$FISH_TREE/[skill]/rust-engineer" .agents/skills/rust-engineer
ln -s "$FISH_TREE/[skill]/playwright-pro" .agents/skills/playwright-pro
```

2. **Prebuilt IDE / agent rule pack**: Browse `[mcp]/context_mode_configs/` for the folder matching your CLI or editor (`gemini-cli/`, `opencode/`, `pi/`, `zed/`, `vscode-copilot/`, `jetbrains-copilot/`, etc.) and copy its `AGENTS.md` / `GEMINI.md` / `copilot-instructions.md` and MCP JSON into the project root or home config directory.

## Domain rules cheat sheet

If you want lightweight behavioral rules inside any agent system prompt (`CLAUDE.md`, `AGENTS.md`, or `GEMINI.md`), copy the rule files directly from `[plugin]/*/rules/AGENTS.md`:

| Domain | Source rules file | Enforces |
| :--- | :--- | :--- |
| Engineering | `[plugin]/engineering-core-suite/rules/AGENTS.md` | CodeGraph-first navigation, SQL transaction/LIMIT safety, secret/AST scanning, no blind `git add .` |
| Design / Frontend | `[plugin]/design-frontend-suite/rules/AGENTS.md` | Intentional spacing/typography scale, 5 UI states, WCAG AA contrast, native primitives, browser verification |
| Finance / Quant | `[plugin]/finance-quant-suite/rules/AGENTS.md` | Native Excel formulas, batched sheet writes, pipeline zero-leakage, N/p-value reporting |
| Marketing / Brand | `[plugin]/marketing-growth-suite/rules/AGENTS.md` | Positioning before copy, platform-native writing, technical SEO, Humanizer v4.0.0 gate |

## Security check before adopting any skill update

Run both repository scanners against staged diffs or newly added skills before syncing or committing:

```bash
python3 "$FISH_TREE/[plugin]/engineering-core-suite/skills/engineering/references/sensitive-data-guard/scripts/scan_secrets.py" --staged
python3 "$FISH_TREE/[skill]/security-guard/scripts/scan_security_ast.py" --staged
```
