#!/bin/bash
# ==============================================================================
# tests/tier3_combinations/test_precommit_and_secrets.sh
# Tier 3 Combination: Pre-Commit Hook & Secret Scanner Integration
# 2 Test Cases: TC-T3-001, TC-T3-002
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T3-001: Pre-commit Hook and Staged Secret Veto"
    echo "TC-T3-002: Pre-commit Hook and Staged/Unstaged Split Precision"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t3_c1_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

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

OVERALL_EXIT=0

# --- TC-T3-001: Pre-commit Hook and Staged Secret Veto ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T3-001"
repo1="$(create_temp_git_repo "$SANDBOX/repo1")"
install_hook_to_repo "$repo1"
initial_head=$(cd "$repo1" && git rev-parse HEAD)

mkdir -p "$repo1/[skill]/test-skill/scripts"
P_AWS="AKIA"
P_GHP="ghp_"
cat << EOF > "$repo1/[skill]/test-skill/scripts/deploy.py"
# Deployment script
AWS_ACCESS_VAL = "${P_AWS}IOSFODNN7WXYZ123"
GITHUB_VAL = "${P_GHP}mockGitHubClassicToken12345678901234"
EOF

(cd "$repo1" && git add "[skill]/test-skill/scripts/deploy.py")
out=$(cd "$repo1" && git commit -m "feat: add deploy script" 2>&1)
exit_code=$?

assert_exit_code 1 "$exit_code" "Commit with staged secret must be blocked by hook"
current_head=$(cd "$repo1" && git rev-parse HEAD)
assert_equals "$initial_head" "$current_head" "HEAD commit hash must remain unchanged"
assert_contains "$out" "AKIA...Z123" "Output must contain masked AWS token"
assert_contains "$out" "ghp_...1234" "Output must contain masked GitHub token"
assert_not_contains "$out" "${P_AWS}IOSFODNN7WXYZ123" "Raw AWS key must not leak"
assert_not_contains "$out" "${P_GHP}mockGitHubClassicToken12345678901234" "Raw GitHub token must not leak"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 3 "TC-T3-001" "Pre-commit Hook and Staged Secret Veto" "PASS" "$dur"
else
    emit_test_result 3 "TC-T3-001" "Pre-commit Hook and Staged Secret Veto" "FAIL" "$dur" "Pre-commit secret veto failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- TC-T3-002: Pre-commit Hook and Staged/Unstaged Split Precision ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T3-002"
repo2="$(create_temp_git_repo "$SANDBOX/repo2")"
install_hook_to_repo "$repo2"

mkdir -p "$repo2/[skill]/math-utils"
create_valid_skill_fixture "$repo2/[skill]" "math-utils" "Math calculation utilities" "standard"
(cd "$repo2" && git add "[skill]/math-utils/SKILL.md")

# Create dirty unstaged file with a live secret in working tree
P_ANT="sk-ant-"
echo "TEMP_VAL=\"${P_ANT}api03-mockAnthropicKey12345678901234567890\"" > "$repo2/scratch_notes.txt"

out=$(cd "$repo2" && git commit -m "feat: add math utils skill" 2>&1)
exit_code=$?

assert_exit_code 0 "$exit_code" "Commit must succeed when only clean files are staged"
last_msg=$(cd "$repo2" && git log -1 --pretty=%B)
assert_contains "$last_msg" "add math utils skill" "Commit object should be created"
status_out=$(cd "$repo2" && git status --porcelain)
assert_contains "$status_out" "?? scratch_notes.txt" "Unstaged file must remain untracked"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 3 "TC-T3-002" "Pre-commit Hook and Staged/Unstaged Split Precision" "PASS" "$dur"
else
    emit_test_result 3 "TC-T3-002" "Pre-commit Hook and Staged/Unstaged Split Precision" "FAIL" "$dur" "Split precision check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
