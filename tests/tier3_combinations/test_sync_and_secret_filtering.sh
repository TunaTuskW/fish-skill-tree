#!/bin/bash
# ==============================================================================
# tests/tier3_combinations/test_sync_and_secret_filtering.sh
# Tier 3 Combination: Sync Script & Secret Filtering / .gitignore Boundaries
# 2 Test Cases: TC-T3-003, TC-T3-007
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T3-003: Multi-Target Sync and Secret File Exclusion Filtering"
    echo "TC-T3-007: Multi-Target Sync and Gitignore Boundary Enforcement"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t3_c2_sandbox")"
activate_sandbox "$SANDBOX"
trap cleanup_all_sandboxes EXIT INT TERM HUP

PROD_SYNC="$REPO_ROOT/scripts/sync_ecosystem.py"
STUB_SYNC="$HARNESS_DIR/reference_stubs/sync_ecosystem.py"

USE_SYNC="$STUB_SYNC"
if [ -f "$PROD_SYNC" ]; then
    USE_SYNC="$PROD_SYNC"
fi

OVERALL_EXIT=0

MOCK_REPO="$SANDBOX/mock_repo"
init_mock_git_repo "$MOCK_REPO"

# Setup active plugins in sandbox with both clean skills and sensitive secrets
ACTIVE_PLUGINS="$(mock_active_plugins_dir "$SANDBOX")"
ACTIVE_CONFIG="$SANDBOX/fake_home/.gemini/config"

# --- TC-T3-003: Multi-Target Sync and Secret File Exclusion Filtering ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T3-003"

out=$(python3 "$USE_SYNC" --direction active-to-repo --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_CONFIG" 2>&1)
exit_code=$?

assert_exit_code 0 "$exit_code" "active-to-repo sync should succeed"

# Verify legitimate skills/plugins copied
assert_file_exists "$MOCK_REPO/[plugin]/gdocs/plugin.json" "Legitimate plugin.json must be synced"
assert_file_exists "$MOCK_REPO/[plugin]/gsheets/plugin.json" "Legitimate gsheets plugin.json must be synced"
assert_file_exists "$MOCK_REPO/[plugin]/context7/plugin.json" "Legitimate context7 plugin.json must be synced"

# Verify sensitive files strictly excluded (Zero-Leak)
assert_file_not_exists "$MOCK_REPO/[plugin]/gdocs/auth.json" "gdocs auth.json must NOT be copied"
assert_file_not_exists "$MOCK_REPO/[plugin]/gsheets/auth.json" "gsheets auth.json must NOT be copied"
assert_file_not_exists "$MOCK_REPO/[plugin]/gdocs/.env.local" "Environment file must NOT be copied"
assert_dir_not_exists "$MOCK_REPO/[plugin]/gsheets/.agents" ".agents directory must NOT be copied"
assert_dir_not_exists "$MOCK_REPO/[plugin]/gsheets/.codegraph" ".codegraph directory must NOT be copied"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 3 "TC-T3-003" "Multi-Target Sync and Secret File Exclusion Filtering" "PASS" "$dur"
else
    emit_test_result 3 "TC-T3-003" "Multi-Target Sync and Secret File Exclusion Filtering" "FAIL" "$dur" "Exclusion filtering failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- TC-T3-007: Multi-Target Sync and Gitignore Boundary Enforcement ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T3-007"

# Copy project .gitignore if available or install hardened .gitignore
if [ -f "$REPO_ROOT/.gitignore" ]; then
    cp "$REPO_ROOT/.gitignore" "$MOCK_REPO/.gitignore"
else
    cat << 'EOF' > "$MOCK_REPO/.gitignore"
.agents/
.codegraph/
auth.json
*.key
.env*
EOF
fi

# Run git status in mock repo with -uall to inspect individual untracked files
status_out=$(cd "$MOCK_REPO" && git status --porcelain -uall)

# Legitimate synced files must appear as untracked candidates for staging
assert_contains "$status_out" "[plugin]/gdocs/plugin.json" "New legitimate plugin should be visible in git status"

# Excluded patterns must NOT appear anywhere in git status
assert_not_contains "$status_out" "auth.json" "auth.json must not appear in git status"
assert_not_contains "$status_out" ".agents" ".agents must not appear in git status"
assert_not_contains "$status_out" ".codegraph" ".codegraph must not appear in git status"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 3 "TC-T3-007" "Multi-Target Sync and Gitignore Boundary Enforcement" "PASS" "$dur"
else
    emit_test_result 3 "TC-T3-007" "Multi-Target Sync and Gitignore Boundary Enforcement" "FAIL" "$dur" "Gitignore boundary check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
