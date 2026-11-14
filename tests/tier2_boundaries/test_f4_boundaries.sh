#!/bin/bash
# ==============================================================================
# tests/tier2_boundaries/test_f4_boundaries.sh
# Tier 2 Feature 4: Git Pre-Commit Hook Boundaries & Edge Cases
# 5 Test Cases: E2E-T2-F4-01 to E2E-T2-F4-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T2-F4-01: Non-Executable Pre-Commit Hook Veto"
    echo "E2E-T2-F4-02: Empty Commit With Allow-Empty Permitted"
    echo "E2E-T2-F4-03: Staged Secret Deletion Commit Permitted"
    echo "E2E-T2-F4-04: Staged Binary File Handled Cleanly"
    echo "E2E-T2-F4-05: Sensitive Filename (.env) Staged Blocked"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t2_f4_sandbox")"
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

# --- E2E-T2-F4-01: Non-Executable Pre-Commit Hook Veto ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F4-01"
repo1="$(create_temp_git_repo "$SANDBOX/repo1")"
install_hook_to_repo "$repo1"
chmod -x "$repo1/.git/hooks/pre-commit"
out=$(bash "$HARNESS_DIR/verify_hook_executable.sh" "$repo1" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Non-executable hook should be vetoed by verification helper"
assert_contains "$out" "not executable" "Expected not executable warning"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F4-01" "Non-Executable Pre-Commit Hook Veto" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F4-01" "Non-Executable Pre-Commit Hook Veto" "FAIL" "$dur" "Hook permissions check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F4-02: Empty Commit With Allow-Empty Permitted ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F4-02"
repo2="$(create_temp_git_repo "$SANDBOX/repo2")"
install_hook_to_repo "$repo2"
out=$(cd "$repo2" && git commit --allow-empty -m "chore: allow empty commit" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Empty commit should succeed"
last_msg=$(cd "$repo2" && git log -1 --pretty=%B)
assert_contains "$last_msg" "allow empty commit" "Commit message must appear in log"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F4-02" "Empty Commit With Allow-Empty Permitted" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F4-02" "Empty Commit With Allow-Empty Permitted" "FAIL" "$dur" "Empty commit check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F4-03: Staged Secret Deletion Commit Permitted ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F4-03"
repo3="$(create_temp_git_repo "$SANDBOX/repo3")"
echo "sk-ant-oldKey12345678901234567890" > "$repo3/config.py"
(cd "$repo3" && git add config.py && git commit -q -m "init with secret")
install_hook_to_repo "$repo3"
# Now delete the secret from config.py and replace with clean code
echo "import os" > "$repo3/config.py"
(cd "$repo3" && git add config.py)
out=$(cd "$repo3" && git commit -m "chore: remove secret from config" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Deletion commit must succeed"
assert_contains "$(cat "$repo3/config.py")" "import os" "Clean content should be present"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F4-03" "Staged Secret Deletion Commit Permitted" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F4-03" "Staged Secret Deletion Commit Permitted" "FAIL" "$dur" "Deletion commit failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F4-04: Staged Binary File Handled Cleanly ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F4-04"
repo4="$(create_temp_git_repo "$SANDBOX/repo4")"
install_hook_to_repo "$repo4"
# Generate mock PNG binary header (8 bytes: \x89PNG\r\n\x1a\n)
printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' > "$repo4/image.png"
(cd "$repo4" && git add image.png)
out=$(cd "$repo4" && git commit -m "feat: add binary image asset" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Binary file commit should succeed without encoding crash"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F4-04" "Staged Binary File Handled Cleanly" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F4-04" "Staged Binary File Handled Cleanly" "FAIL" "$dur" "Binary file check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F4-05: Sensitive Filename (.env) Staged Blocked ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F4-05"
repo5="$(create_temp_git_repo "$SANDBOX/repo5")"
install_hook_to_repo "$repo5"
touch "$repo5/.env"
(cd "$repo5" && git add .env)
out=$(cd "$repo5" && git commit -m "feat: stage .env file" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Commit staging .env must be blocked by pre-commit hook"
assert_contains "$out" ".env" "Expected sensitive filename alert"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F4-05" "Sensitive Filename (.env) Staged Blocked" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F4-05" "Sensitive Filename (.env) Staged Blocked" "FAIL" "$dur" ".env staging block failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
