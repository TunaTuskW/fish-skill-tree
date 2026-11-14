#!/bin/bash
# ==============================================================================
# tests/tier1_features/test_f5_sync_ecosystem.sh
# Tier 1 Feature 5: Multi-Target Ecosystem Synchronization
# 5 Test Cases: E2E-T1-F5-01 to E2E-T1-F5-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T1-F5-01: Dry-Run Simulation Mode"
    echo "E2E-T1-F5-02: repo-to-active Path Translation"
    echo "E2E-T1-F5-03: active-to-repo Path Translation"
    echo "E2E-T1-F5-04: Exclusion of auth.json"
    echo "E2E-T1-F5-05: Exclusion of .agents/.codegraph/.env"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t1_f5_sandbox")"
activate_sandbox "$SANDBOX"
trap cleanup_all_sandboxes EXIT INT TERM HUP

PROD_SYNC="$REPO_ROOT/scripts/sync_ecosystem.py"
STUB_SYNC="$HARNESS_DIR/reference_stubs/sync_ecosystem.py"

USE_SYNC="$STUB_SYNC"
if [ -f "$PROD_SYNC" ]; then
    USE_SYNC="$PROD_SYNC"
fi

OVERALL_EXIT=0

# Setup mock directories in sandbox
MOCK_REPO="$SANDBOX/mock_repo"
mkdir -p "$MOCK_REPO/[plugin]/engineering-core-suite/rules" "$MOCK_REPO/[skill]/sample-skill"
cat << 'EOF' > "$MOCK_REPO/[plugin]/engineering-core-suite/rules/AGENTS.md"
# Engineering Rules
Save exports to ~/vibe/exports.
EOF

MOCK_ACTIVE_PLUGINS="$(mock_active_plugins_dir "$SANDBOX")"
MOCK_ACTIVE_SKILLS="$(mock_active_skills_dir "$SANDBOX")"
MOCK_ACTIVE_ROOT="$SANDBOX/fake_home/.gemini/config"

# --- E2E-T1-F5-01: Dry-Run Simulation Mode ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F5-01"
out=$(python3 "$USE_SYNC" --dry-run --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Dry-run must exit 0"
assert_contains "$out" "[PLAN]" "Dry run output must describe planned actions"
# Verify target file did NOT get created/overwritten during dry run
assert_file_not_exists "$MOCK_ACTIVE_PLUGINS/engineering-core-suite/rules/AGENTS.md.tmp" "Dry run must not create tmp files"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F5-01" "Dry-Run Simulation Mode" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F5-01" "Dry-Run Simulation Mode" "FAIL" "$dur" "Dry run failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F5-02: repo-to-active Path Translation ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F5-02"
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "repo-to-active sync must exit 0"
active_rule_file="$MOCK_ACTIVE_PLUGINS/engineering-core-suite/rules/AGENTS.md"
assert_file_exists "$active_rule_file" "Synced rule file must exist in active plugins"
content=$(cat "$active_rule_file")
assert_contains "$content" "/Users/mac/vibe/exports" "Path ~/vibe/ must be translated to /Users/mac/vibe/"
assert_not_contains "$content" "~/vibe/exports" "Original ~/vibe/ path must not remain"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F5-02" "repo-to-active Path Translation" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F5-02" "repo-to-active Path Translation" "FAIL" "$dur" "Translation failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F5-03: active-to-repo Path Translation ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F5-03"
# Create active rule containing /Users/mac/vibe/
cat << 'EOF' > "$MOCK_ACTIVE_PLUGINS/engineering-core-suite/rules/AGENTS.md"
# Active Rules
Save logs to /Users/mac/vibe/logs.
EOF
out=$(python3 "$USE_SYNC" --direction active-to-repo --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "active-to-repo sync must exit 0"
repo_rule_file="$MOCK_REPO/[plugin]/engineering-core-suite/rules/AGENTS.md"
content=$(cat "$repo_rule_file")
assert_contains "$content" "~/vibe/logs" "Path /Users/mac/vibe/ must be translated back to ~/vibe/"
assert_not_contains "$content" "/Users/mac/vibe/logs" "Absolute path must be replaced with ~/vibe/"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F5-03" "active-to-repo Path Translation" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F5-03" "active-to-repo Path Translation" "FAIL" "$dur" "Reverse translation failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F5-04: Exclusion of auth.json ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F5-04"
# auth.json exists in active gdocs and gsheets
out=$(python3 "$USE_SYNC" --direction active-to-repo --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Sync must exit 0"
assert_file_not_exists "$MOCK_REPO/[plugin]/gdocs/auth.json" "auth.json MUST NOT be copied to repository"
assert_file_not_exists "$MOCK_REPO/[plugin]/gsheets/auth.json" "gsheets auth.json MUST NOT be copied to repository"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F5-04" "Exclusion of auth.json" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F5-04" "Exclusion of auth.json" "FAIL" "$dur" "auth.json leak"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F5-05: Exclusion of .agents/.codegraph/.env ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F5-05"
mkdir -p "$MOCK_REPO/[plugin]/.agents" "$MOCK_REPO/[plugin]/.codegraph"
touch "$MOCK_REPO/[plugin]/.env.local" "$MOCK_REPO/[plugin]/credentials.json"
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Sync must exit 0"
assert_dir_not_exists "$MOCK_ACTIVE_PLUGINS/.agents" ".agents directory must NOT be synced"
assert_dir_not_exists "$MOCK_ACTIVE_PLUGINS/.codegraph" ".codegraph directory must NOT be synced"
assert_file_not_exists "$MOCK_ACTIVE_PLUGINS/.env.local" ".env file must NOT be synced"
assert_file_not_exists "$MOCK_ACTIVE_PLUGINS/credentials.json" "credentials.json must NOT be synced"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F5-05" "Exclusion of .agents/.codegraph/.env" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F5-05" "Exclusion of .agents/.codegraph/.env" "FAIL" "$dur" "Sensitive file leak"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
