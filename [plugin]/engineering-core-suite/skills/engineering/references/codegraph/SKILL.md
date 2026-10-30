---
name: codegraph
description: |
  Navigate, explore, audit, and trace codebases using the local Tree-sitter CodeGraph engine.
  Trigger when:
  - User starts a new coding project or scaffolds a new repository.
  - User asks to audit, inspect, review, or understand an existing codebase or architecture.
  - User asks to find functions that call or are called by a specific symbol (`callers`/`callees`).
  - User asks to analyze the blast radius or impact of modifying a class or function (`impact`).
  - User asks to find test files affected by changes (`affected`).
  - User wants to initialize or sync CodeGraph indexing (`codegraph init` or `codegraph sync`).
---

# CodeGraph Intelligence Skill

Workflows for starting new projects, auditing existing codebases, and tracing architectural call graphs using CodeGraph.

## Core Workflows

### 1. Starting a New Coding Project (Bootstrap Protocol)
Whenever you start a new coding project or create a new repository directory:
1. Initialize project files and dependencies (e.g., `package.json`, `pyproject.toml`, or `Cargo.toml`).
2. Run `codegraph init` in the project root:
   ```bash
   codegraph init
   ```
3. This creates the `.codegraph/` index directory and enables live AST relationship tracking for all newly authored files.
4. Verify indexing with:
   ```bash
   codegraph status
   ```

---

### 2. Auditing an Existing Codebase (Audit Protocol)
Whenever tasked with auditing, reviewing, or exploring an unfamiliar or existing codebase, execute this 4-phase audit methodology:

#### Phase A: Graph Verification & Topology Mapping
1. Check if the project is indexed. If not, build the graph:
   ```bash
   codegraph init
   ```
2. Inspect the project file structure and total symbols:
   ```bash
   codegraph files
   codegraph status
   ```

#### Phase B: Entry Point & Core Abstraction Discovery
1. Extract architectural context across main feature domains:
   ```bash
   codegraph explore "entry points routing architecture"
   ```
2. Pinpoint central router, controller, or orchestration functions.

#### Phase C: Critical Path & Security Flow Tracing
Trace sensitive operations without reading dozens of files manually:
- **Authentication & Authorization**:
  ```bash
  codegraph callers authenticate
  codegraph callees verifyToken
  ```
- **Database & Persistence Boundaries**:
  ```bash
  codegraph callers dbQuery
  codegraph callers prisma
  ```
- **External API & Network Integration**:
  ```bash
  codegraph callees httpClient
  ```

#### Phase D: Fragility, Coupling & Impact Analysis (God Node Detection)
1. **Detect "God Nodes" (Architectural Bottlenecks)**:
   Identify central hubs with extreme in-degree (called by everything) or out-degree (calling everything). These singletons or monolithic utilities are primary failure points and refactoring hazards:
   ```bash
   codegraph impact <CoreModelOrUtility>
   ```
2. **Graph-First Token Conservation (71.5x Principle)**:
   Never dump full files into context to understand symbol interactions. Traverse exact caller/callee hops with `codegraph explore` or `codegraph callers/callees` to preserve token budget.
3. Identify symbols with abnormally high fan-in or fan-out to detect tight coupling and modularity gaps.
4. Synthesize the findings into an audit report highlighting:
   - Architecture & Module Boundaries (Functional Community Clusters)
   - God Nodes & Heavily Coupled Central Components
   - Missing Error Handling or Validation on Critical Call Chains
   - Recommended Refactorings or Test Coverage Gaps

---

### 3. Pre-Refactoring & Modifying Code
Before executing refactors or breaking changes:
- **Verify blast radius**:
  ```bash
  codegraph impact <symbol_name>
  ```
- **Find affected tests**:
  ```bash
  codegraph affected src/module.ts
  ```
