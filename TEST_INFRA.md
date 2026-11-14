# E2E Test Infrastructure & Master Runner Specification

**Project**: `fish-skill-tree` Production Audit & Hardening  
**Track**: E2E Testing Track  
**Runner Path**: `tests/run_e2e_tests.sh`  
**Total Test Cases**: 62 across 4 Tiers  
**Platform**: macOS Darwin arm64 (Bash 3.2.57 / Python 3.9.6 / Git 2.54.0)

---

## 1. Architectural Overview

The `fish-skill-tree` End-to-End Test Suite provides an independent, opaque-box verification framework that exercises the skill ecosystem as an external consumer and security auditor. It evaluates the ecosystem across four progressive tiers without depending on internal implementation details.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MASTER TEST RUNNER: tests/run_e2e_tests.sh            │
│                 (Bash 3.2.57 / POSIX Compatible / ANSI Color Output)        │
└───────────────┬─────────────────────────────────────────────┬───────────────┘
                │                                             │
   ┌────────────┴────────────┐                   ┌────────────┴────────────┐
   │  Tier 1: Feature Specs  │                   │   Tier 2: Boundaries    │
   │  (25 Happy-Path Tests)  │                   │   (25 Negative Tests)   │
   └────────────┬────────────┘                   └────────────┬────────────┘
                │                                             │
   ┌────────────┴────────────┐                   ┌────────────┴────────────┐
   │  Tier 3: Combinations   │                   │   Tier 4: Workloads     │
   │   (7 Interaction Tests) │                   │  (5 Lifecycle Workloads)│
   └────────────┬────────────┘                   └────────────┬────────────┘
                │                                             │
                ▼                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHARED HARNESS (tests/harness/)                     │
│  assertions.sh | isolation.sh | fixtures.sh | reporters.sh | python_helpers │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Master Test Runner CLI (`tests/run_e2e_tests.sh`)

### 2.1 Synopsis
```bash
bash tests/run_e2e_tests.sh [OPTIONS]
```

### 2.2 CLI Flags & Arguments
| Flag | Name | Description | Default |
|:---|:---|:---|:---|
| `-t, --tier` | Tier Selection | Run specific tier (`1`, `2`, `3`, `4`, or `all`) | `all` |
| `-f, --filter` | Name Filter | Regex or substring filter matching test ID or title | `""` |
| `-v, --verbose` | Verbose Tracing | Display stdout/stderr traces for every test | Disabled |
| `-q, --quiet` | Quiet Mode | Suppress per-test output; show summary table and errors | Disabled |
| `-x, --fail-fast`| Fail Fast | Halt test execution immediately upon the first failure | Disabled |
| `-l, --list` | List Tests | Discover and list matching test cases without executing | Disabled |
| `--no-color` | Disable Colors | Disable ANSI color codes (autodetected on non-TTY) | Enabled on TTY |
| `-h, --help` | Help Menu | Display CLI options and usage | N/A |

### 2.3 Exit Code Contract
- `0`: All executed test cases passed cleanly.
- `1`: One or more test cases failed.
- `2`: CLI usage syntax error or invalid argument.

---

## 3. Shared Test Harness Components (`tests/harness/`)

| Module | Location | Purpose & Capabilities |
|:---|:---|:---|
| `assertions.sh` | `tests/harness/assertions.sh` | Bash 3.2 / POSIX assertion primitives: `assert_exit_code`, `assert_equals`, `assert_contains`, `assert_not_contains`, `assert_matches`, `assert_file_exists`, `assert_file_not_exists`, `assert_dir_exists`, `assert_dir_not_exists`, `assert_file_executable`, `assert_secret_masked`, `assert_yaml_valid`, `assert_json_valid`, `assert_less_than`, `emit_test_result`. |
| `isolation.sh` | `tests/harness/isolation.sh` | Sandboxing framework: `create_sandbox`, `create_temp_dir`, `init_mock_git_repo`, `create_temp_git_repo`, `mock_active_plugins_dir`, `mock_active_skills_dir`. Virtualizes `HOME` to `$SANDBOX/fake_home` and registers POSIX cleanup traps (`EXIT INT TERM HUP`). |
| `sandbox.sh` | `tests/harness/sandbox.sh` | Compatibility wrapper sourcing `isolation.sh`. |
| `fixtures.sh` | `tests/harness/fixtures.sh` | Deterministic synthetic artifact generator: valid skill frontmatter styles (`standard`, `folded`, `literal`, `extended`, `full_layout`, `unicode`), malformed frontmatters, synthetic secrets (AWS, PAT, Gemini, OpenAI, Anthropic, JSON OAuth), and AST malware vectors (`eval`, `shell_true`, `webhook_ssrf`, `obfuscated_b64`, `unpinned_curl`). |
| `reporters.sh` | `tests/harness/reporters.sh` | ANSI terminal formatting, real-time status banners (`log_pass`, `log_fail`, `log_skip`), and structured 4-tier summary table formatting (`print_summary_table`). |
| `python_helpers.py` | `tests/harness/python_helpers.py` | Python 3.9 helper providing PyYAML frontmatter parser (`validate-yaml`), Shannon entropy evaluator (`calc-entropy`), AST vulnerability scanner (`check-ast`), and JSON validator (`validate-json`). |
| `validate_skill.py` | `tests/harness/validate_skill.py` | Standalone CLI validator for `SKILL.md` frontmatters and directory layout. |
| `verify_hook_executable.sh` | `tests/harness/verify_hook_executable.sh` | Verification helper ensuring `.git/hooks/pre-commit` exists and has executable permissions (`+x`). |
| `reference_stubs/` | `tests/harness/reference_stubs/` | Genuine, self-contained reference engines (`scan_secrets.py`, `scan_security_ast.py`, `sync_ecosystem.py`, `pre-commit`) enabling isolated progressive testability prior to milestone implementations. |

---

## 4. Test Suite Structure & Tier Breakdown

```text
tests/
├── run_e2e_tests.sh
├── harness/
│   ├── assertions.sh
│   ├── isolation.sh
│   ├── sandbox.sh
│   ├── fixtures.sh
│   ├── reporters.sh
│   ├── python_helpers.py
│   ├── validate_skill.py
│   ├── verify_hook_executable.sh
│   └── reference_stubs/
│       ├── scan_secrets.py
│       ├── scan_security_ast.py
│       ├── sync_ecosystem.py
│       └── pre-commit
├── tier1_features/
│   ├── test_f1_skill_frontmatter.sh    # 5 test cases (E2E-T1-F1-01 .. 05)
│   ├── test_f2_secret_scanner.sh       # 5 test cases (E2E-T1-F2-01 .. 05)
│   ├── test_f3_ast_scanner.sh          # 5 test cases (E2E-T1-F3-01 .. 05)
│   ├── test_f4_precommit_hook.sh       # 5 test cases (E2E-T1-F4-01 .. 05)
│   └── test_f5_sync_ecosystem.sh       # 5 test cases (E2E-T1-F5-01 .. 05)
├── tier2_boundaries/
│   ├── test_f1_boundaries.sh           # 5 test cases (E2E-T2-F1-01 .. 05)
│   ├── test_f2_boundaries.sh           # 5 test cases (E2E-T2-F2-01 .. 05)
│   ├── test_f3_boundaries.sh           # 5 test cases (E2E-T2-F3-01 .. 05)
│   ├── test_f4_boundaries.sh           # 5 test cases (E2E-T2-F4-01 .. 05)
│   └── test_f5_boundaries.sh           # 5 test cases (E2E-T2-F5-01 .. 05)
├── tier3_combinations/
│   ├── test_precommit_and_secrets.sh   # 2 test cases (TC-T3-001, TC-T3-002)
│   ├── test_sync_and_secret_filtering.sh# 2 test cases (TC-T3-003, TC-T3-007)
│   ├── test_ast_and_secret_dual_scan.sh# 1 test case  (TC-T3-004)
│   ├── test_sync_path_translation.sh   # 1 test case  (TC-T3-005)
│   └── test_precommit_ast_malware.sh   # 1 test case  (TC-T3-006)
└── tier4_workloads/
    ├── workload_full_tree_audit.sh     # 1 test case  (TC-T4-001)
    ├── workload_malicious_injection.sh # 1 test case  (TC-T4-002)
    ├── workload_sync_dryrun.sh         # 1 test case  (TC-T4-003)
    ├── workload_developer_lifecycle.sh # 1 test case  (TC-T4-004)
    └── workload_batch_deployment.sh    # 1 test case  (TC-T4-005)
```

---

## 5. Verification Commands

1. **Discovery Verification**:
   ```bash
   bash tests/run_e2e_tests.sh --list
   ```
2. **Execute Tier 1 (Feature Coverage)**:
   ```bash
   bash tests/run_e2e_tests.sh --tier 1
   ```
3. **Execute Tier 2 (Boundaries & Negative Cases)**:
   ```bash
   bash tests/run_e2e_tests.sh --tier 2
   ```
4. **Execute Tier 3 (Cross-Feature Combinations)**:
   ```bash
   bash tests/run_e2e_tests.sh --tier 3
   ```
5. **Execute Tier 4 (Real-World Workloads)**:
   ```bash
   bash tests/run_e2e_tests.sh --tier 4
   ```
6. **Full Regression Execution**:
   ```bash
   bash tests/run_e2e_tests.sh
   ```
