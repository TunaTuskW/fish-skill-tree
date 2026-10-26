---
name: database-assistant
description: |
  Inspect, design, query, and migrate SQL databases (PostgreSQL, MySQL, SQLite, Supabase).
  Trigger when:
  - User asks to inspect or visualize database schemas, ER diagrams, foreign keys, or indexes.
  - User asks to draft database migrations (Prisma, Drizzle, Alembic, raw SQL).
  - User requests query optimization, indexing strategies, or execution plan (EXPLAIN ANALYZE) reviews.
  - User wants safe read-only queries or analytical data extraction from local/remote databases.
---

# Database Assistant Skill

Guidance and workflows for working with relational databases safely, efficiently, and with best engineering practices.

## Core Workflows

### 1. Schema Inspection & ERD Visualization
When asked to examine database structure:
1. Identify database engine (PostgreSQL, MySQL, SQLite, etc.) and ORM in use (Prisma, Drizzle, TypeORM, SQLAlchemy, Alembic).
2. Inspect schema definitions or run information schema introspection queries:
   - PostgreSQL: Query `information_schema.columns`, `pg_indexes`, and `information_schema.table_constraints`.
   - SQLite: Query `sqlite_master` and `PRAGMA table_info(<table>)`.
   - MySQL: Query `information_schema.columns` and `SHOW CREATE TABLE`.
3. Synthesize the schema into a concise Mermaid ERD (`erDiagram`) showing entity relations (`||--o{`, `||--||`) and primary/foreign keys.

### 2. Writing Safe Database Migrations
Always follow zero-downtime, non-destructive migration patterns:
- **Adding Columns**:
  - Prefer nullable columns or columns with sensible defaults (`DEFAULT ...`).
  - In PostgreSQL, adding a column with a constant default is metadata-only in modern versions (11+), but avoid volatile functions in defaults without verification.
- **Renaming / Dropping Columns**:
  - Never drop or rename columns directly in a single step in production code. Use the expand-contract pattern:
    1. Add the new column.
    2. Dual-write in application code.
    3. Backfill existing data asynchronously in batches.
    4. Switch reads to the new column.
    5. Drop the old column after confirmation.
- **Adding Indexes Concurrently**:
  - In PostgreSQL, use `CREATE INDEX CONCURRENTLY` to avoid blocking read/write queries on high-traffic tables.
  - Ensure migrations are wrapped in transactions where supported, or appropriately flagged when concurrent index creation prohibits outer transactions.

### 3. Query Optimization & Indexing Strategies
When troubleshooting slow queries:
1. Inspect the execution plan (`EXPLAIN (ANALYZE, BUFFERS)` in Postgres).
2. Look for common bottlenecks:
   - Sequential scans (`Seq Scan`) on large tables with selective predicates.
   - Missing indexes on `JOIN` foreign keys or `WHERE` / `ORDER BY` clauses.
   - High buffer hits or disk spills (`Sort Method: external merge Disk`).
3. Suggest targeted indexing:
   - Composite indexes with columns ordered by equality first, then range/sort (`WHERE status = 'ACTIVE' ORDER BY created_at DESC` -> `(status, created_at)`).
   - Partial indexes (`CREATE INDEX ON orders (user_id) WHERE status = 'PENDING'`) to minimize index bloat.

### 4. Safe Query Execution Rules
- Default to `SELECT` and read-only transactions.
- Always include explicit `LIMIT` clauses on exploratory queries.
- For write queries (`UPDATE`, `DELETE`), require an explicit `WHERE` clause and preview affected row counts (`SELECT count(*)`) before execution.
