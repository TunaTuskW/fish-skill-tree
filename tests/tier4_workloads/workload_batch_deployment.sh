#!/bin/bash
# ==============================================================================
# tests/tier4_workloads/workload_batch_deployment.sh
# Tier 4 Workload 5: Batch Ecosystem Update & Synchronized Deployment Pipeline
# 1 Test Case: TC-T4-005
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T4-005: Batch Ecosystem Update and Synchronized Deployment Pipeline"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t4_w5_sandbox")"
activate_sandbox "$SANDBOX"
trap cleanup_all_sandboxes EXIT INT TERM HUP

HOOK_SRC="$REPO_ROOT/.git/hooks/pre-commit"
if [ ! -f "$HOOK_SRC" ] || [ ! -x "$HOOK_SRC" ]; then
    HOOK_SRC="$HARNESS_DIR/reference_stubs/pre-commit"
fi

export E2E_SCANNER_PATH="$HARNESS_DIR/reference_stubs/scan_secrets.py"
if [ -f "$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py" ]; then
    if python3 "$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py" --help 2>&1 | grep -q -- "--staged"; then
        export E2E_SCANNER_PATH="$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
    fi
fi

install_hook_to_repo() {
    local target_repo="$1"
    mkdir -p "$target_repo/.git/hooks"
    mkdir -p "$target_repo/[skill]/sensitive-data-guard/scripts"
    cp "$E2E_SCANNER_PATH" "$target_repo/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
    cp "$HOOK_SRC" "$target_repo/.git/hooks/pre-commit"
    chmod +x "$target_repo/.git/hooks/pre-commit"
}

PROD_SYNC="$REPO_ROOT/scripts/sync_ecosystem.py"
STUB_SYNC="$HARNESS_DIR/reference_stubs/sync_ecosystem.py"
USE_SYNC="$STUB_SYNC"
if [ -f "$PROD_SYNC" ]; then
    USE_SYNC="$PROD_SYNC"
fi

OVERALL_EXIT=0

# --- TC-T4-005: Batch Ecosystem Update and Synchronized Deployment Pipeline ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T4-005"

MOCK_REPO="$SANDBOX/mock_repo"
mkdir -p "$MOCK_REPO"
init_mock_git_repo "$MOCK_REPO"
install_hook_to_repo "$MOCK_REPO"
(cd "$MOCK_REPO" && git add . && git commit -q -m "chore: initial baseline")

ACTIVE_CONFIG="$SANDBOX/fake_home/.gemini/config"
mkdir -p "$ACTIVE_CONFIG/plugins" "$ACTIVE_CONFIG/skills"

# 1. Update 1 master sector rule
mkdir -p "$MOCK_REPO/[plugin]/design-frontend-suite/rules"
cat << 'EOF' > "$MOCK_REPO/[plugin]/design-frontend-suite/rules/AGENTS.md"
# Design Frontend Suite Rules
- All tokens must be mirrored into ~/vibe/design-tokens.json.
EOF

# 2. Update 5 core skills
skills=("billion-context" "dcf-model" "rules-distill" "terminal-opener" "skill-comply")
for s in "${skills[@]}"; do
    mkdir -p "$MOCK_REPO/[skill]/$s"
    create_valid_skill_fixture "$MOCK_REPO/[skill]" "$s" "Batch updated specification for $s" "standard"
done

# Step 1: Pre-commit audit and batch commit
(cd "$MOCK_REPO" && git add "[plugin]" "[skill]")
commit_out=$(cd "$MOCK_REPO" && git commit -m "chore(ecosystem): batch update sector rules and core skill specs" 2>&1)
commit_exit=$?

assert_exit_code 0 "$commit_exit" "Batch commit must pass pre-commit security gates"

# Step 2: Deploy to active runtime mirror via sync
sync_out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_CONFIG" 2>&1)
sync_exit=$?

assert_exit_code 0 "$sync_exit" "Deployment sync to active runtime must succeed"

# Step 3: Verify all 6 items deployed cleanly to active runtime with path translation
active_rule="$ACTIVE_CONFIG/plugins/design-frontend-suite/rules/AGENTS.md"
assert_file_exists "$active_rule" "Active design suite rule must exist"
assert_contains "$(cat "$active_rule")" "/Users/mac/vibe/design-tokens.json" "Rule path must be translated to /Users/mac/vibe/"

for s in "${skills[@]}"; do
    active_skill="$ACTIVE_CONFIG/skills/$s/SKILL.md"
    assert_file_exists "$active_skill" "Active skill for $s must exist"
    assert_contains "$(cat "$active_skill")" "name: $s" "Active skill must match repo specification"
done

# Step 4: Verify zero temporary or lock residue files
tmp_residue=$(find "$SANDBOX" -name "*.tmp" -o -name "*.lock" 2>/dev/null | wc -l | tr -d ' ')
assert_equals "0" "$tmp_residue" "Zero leftover temporary or lock files should exist"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$commit_exit" -eq 0 ] && [ "$sync_exit" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 4 "TC-T4-005" "Batch Ecosystem Update and Synchronized Deployment Pipeline" "PASS" "$dur"
else
    emit_test_result 4 "TC-T4-005" "Batch Ecosystem Update and Synchronized Deployment Pipeline" "FAIL" "$dur" "Batch deployment failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
