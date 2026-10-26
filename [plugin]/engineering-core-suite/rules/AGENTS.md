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
- **Explicit Git Staging**: Never run `git add .` or `git add -A`. Stage audited files explicitly by path and verify `git diff --cached` before every commit.
- **Mandatory `.gitignore`**: Ensure `.env*` (except `.env.example`), `*.pem`, `*.key`, `id_rsa*`, and `*secret*`/`*credential*` files are excluded in `.gitignore`.

## 4. Mandatory Exports Mirror
- Whenever source code, database schemas, migration scripts, or engineering reports are generated or updated, ALWAYS save or copy a duplicate into `~/vibe/` following the project subdirectory taxonomy.
