#!/bin/bash
# ==============================================================================
# tests/tier4_workloads/workload_sync_dryrun.sh
# Tier 4 Workload 3: Bi-Directional Ecosystem Sync Dry-Run & Live Validation
# 1 Test Case: TC-T4-003
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T4-003: Bi-Directional Ecosystem Sync Dry-Run and Non-Destructive Validation"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t4_w3_sandbox")"
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
ACTIVE_CONFIG="$SANDBOX/fake_home/.gemini/config"

# --- TC-T4-003: Bi-Directional Ecosystem Sync Dry-Run and Non-Destructive Validation ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T4-003"

# Setup initial repo state
mkdir -p "$MOCK_REPO/[plugin]/engineering-core-suite/rules" "$MOCK_REPO/[skill]/local-tool"
cat << 'EOF' > "$MOCK_REPO/[plugin]/engineering-core-suite/rules/AGENTS.md"
# Engineering Guide
Mirror output into ~/vibe/artifacts.
EOF
create_valid_skill_fixture "$MOCK_REPO/[skill]" "local-tool" "Local workspace utility" "standard"

# Setup active state
ACTIVE_PLUGINS="$(mock_active_plugins_dir "$SANDBOX")"
ACTIVE_SKILLS="$(mock_active_skills_dir "$SANDBOX")"

# Record file states before dry run
chk_before="$SANDBOX/checksums_before.txt"
find "$SANDBOX" -type f -not -path "*/Library/Caches/*" -not -name "*.pyc" -exec cksum {} + | sort > "$chk_before"

# Step 1: Execute bidirectional dry-run
dryrun_log="$SANDBOX/dryrun.log"
out_dry=$(python3 "$USE_SYNC" --dry-run --direction both --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_CONFIG" 2>&1 | tee "$dryrun_log")
dry_exit=$?

assert_exit_code 0 "$dry_exit" "Dry run must exit code 0"

# Record file states after dry run (excluding the log files and python bytecode caches)
chk_after="$SANDBOX/checksums_after.txt"
find "$SANDBOX" -type f -not -path "*/Library/Caches/*" -not -name "*.pyc" -not -name "dryrun.log" -not -name "checksums_before.txt" -not -name "checksums_after.txt" -exec cksum {} + | sort > "$chk_after"

# Filter chk_before to exclude those as well
chk_before_filtered="$SANDBOX/checksums_before_filtered.txt"
grep -v "dryrun.log\|checksums_" "$chk_before" | sort > "$chk_before_filtered" || true

# Assert ZERO disk mutation occurred during dry-run
diff_count=$(diff "$chk_before_filtered" "$chk_after" | wc -l | tr -d ' ')
assert_equals "0" "$diff_count" "Dry run must cause 0 disk mutations"

# Step 2: Execute live sync
live_log="$SANDBOX/live.log"
out_live=$(python3 "$USE_SYNC" --direction both --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_CONFIG" 2>&1 | tee "$live_log")
live_exit=$?

assert_exit_code 0 "$live_exit" "Live sync must exit code 0"

# Verify active skills synced to repo
assert_file_exists "$MOCK_REPO/[skill]/trading-log-sync/SKILL.md" "Active skill must be mirrored into repository"
assert_file_exists "$MOCK_REPO/[plugin]/context7/plugin.json" "Active connector must be mirrored into repository"

# Verify Zero-Leak exclusion in live sync
assert_file_not_exists "$MOCK_REPO/[plugin]/gdocs/auth.json" "OAuth secret auth.json must NOT be synced into repository"
assert_file_not_exists "$MOCK_REPO/[plugin]/gsheets/auth.json" "gsheets auth.json must NOT be synced into repository"

# Verify path translation in active plugins
active_rule="$ACTIVE_PLUGINS/engineering-core-suite/rules/AGENTS.md"
assert_file_exists "$active_rule" "Active rule must exist"
assert_contains "$(cat "$active_rule")" "/Users/mac/vibe/artifacts" "Path ~/vibe/ must be translated to /Users/mac/vibe/"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$dry_exit" -eq 0 ] && [ "$live_exit" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 4 "TC-T4-003" "Bi-Directional Ecosystem Sync Dry-Run and Non-Destructive Validation" "PASS" "$dur"
else
    emit_test_result 4 "TC-T4-003" "Bi-Directional Ecosystem Sync Dry-Run and Non-Destructive Validation" "FAIL" "$dur" "Dry run validation failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
