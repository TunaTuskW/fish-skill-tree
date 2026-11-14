# Core Engineering, CodeGraph, Database Safety & Zero-Leak Security Rules

## 1. CodeGraph Navigation & Audit Protocol
- **Mandatory Initialization**: Whenever starting a new coding project or working in a codebase without `.codegraph/`, run `~/.local/bin/codegraph init` (or `codegraph init`) immediately.
- **Graph-First Exploration**: Use `codegraph files`, `codegraph explore`, `codegraph callers`, `codegraph callees`, and `codegraph impact <symbol>` before brute-force grepping or reading dozens of files.
- **Post-Edit Sync**: After modifying source code, run `codegraph sync` and `codegraph affected <files>` to identify affected tests.

## 2. Database Safety & Query Discipline
- **Strict Confirmation for Destructive Operations**: Never run or generate `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or unconstrained `DELETE` without explicit user confirmation.
- **Transactional Migrations**: Always wrap schema migrations in `BEGIN; ... COMMIT;` blocks unless prohibited by the engine (e.g., `CONCURRENTLY` index builds).
- **Bounded Reads & Parameterized Queries**: Always append `LIMIT` clauses to exploratory read queries and enforce parameterized inputs to prevent SQL injection.

## 3. Sensitive Data & Zero-Leak Invariant
- **Zero-Leak Policy**: Under NO circumstances commit, stage, push, or transmit API keys, cryptographic private keys (`.pem`, `.key`, `id_rsa`), database URIs with passwords, JWT/OAuth tokens, or PII to Git or external endpoints.
- **Automated Security & Secret Verification**: Run `scan_secrets.py --staged` and `scan_security_ast.py --staged` (enforced via `.git/hooks/pre-commit`) before every commit, and audit third-party skills/scripts for dynamic execution, unpinned binary downloads, and outbound exfiltration sinks before integration.
- **Explicit Git Staging**: Never run `git add .` or `git add -A`. Stage audited files explicitly by path and verify `git diff --cached` before every commit.
- **Mandatory `.gitignore`**: Ensure `.env*` (except `.env.example`), `*.pem`, `*.key`, `id_rsa*`, `auth.json`, `.agents/`, `.codegraph/`, and `*secret*`/`*credential*` files are excluded in `.gitignore`.

## 4. Execution Discipline & Anti-Slop Communication
- **Zero Busy-Wait Polling**: Never loop on `manage_task`, `schedule`, or shell `sleep` to poll background jobs; rely on reactive completion wakeups and batch multi-step shell operations into single deterministic scripts.
- **BLUF & Zero Glaze**: Lead with concrete findings, exact file links, and verified command results (Bottom Line Up Front). Never emit sycophantic filler or duplicate walkthrough artifacts.

## 5. Mandatory Exports Mirror
- Whenever source code, database schemas, migration scripts, or engineering reports are generated or updated, ALWAYS save or copy a duplicate into `~/vibe/` following the project subdirectory taxonomy.
