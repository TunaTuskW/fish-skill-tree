#!/bin/bash
# ==============================================================================
# tests/tier1_features/test_f4_precommit_hook.sh
# Tier 1 Feature 4: Git Pre-Commit Hook Enforcement
# 5 Test Cases: E2E-T1-F4-01 to E2E-T1-F4-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T1-F4-01: Executable Permissions Check"
    echo "E2E-T1-F4-02: Clean Commit Allowed"
    echo "E2E-T1-F4-03: Secret Staged Commit Blocked"
    echo "E2E-T1-F4-04: Masked Output on Veto"
    echo "E2E-T1-F4-05: Multi-File Staging Interception"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t1_f4_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

# Resolve candidate hook source
HOOK_SRC="$REPO_ROOT/.git/hooks/pre-commit"
if [ ! -f "$HOOK_SRC" ] || [ ! -x "$HOOK_SRC" ]; then
    HOOK_SRC="$HARNESS_DIR/reference_stubs/pre-commit"
fi

# Resolve candidate secret scanner for isolated sandboxes
export E2E_SCANNER_PATH="$HARNESS_DIR/reference_stubs/scan_secrets.py"
if [ -f "$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py" ]; then
    if python3 "$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py" --help 2>&1 | grep -q -- "--staged"; then
        export E2E_SCANNER_PATH="$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
    fi
fi
export E2E_AST_SCANNER_PATH="$HARNESS_DIR/reference_stubs/scan_security_ast.py"
if [ -f "$REPO_ROOT/scripts/scan_security_ast.py" ]; then
    export E2E_AST_SCANNER_PATH="$REPO_ROOT/scripts/scan_security_ast.py"
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

# --- E2E-T1-F4-01: Executable Permissions Check ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F4-01"
repo1="$(create_temp_git_repo "$SANDBOX/repo1")"
install_hook_to_repo "$repo1"
assert_file_exists "$repo1/.git/hooks/pre-commit" "Hook file must exist"
assert_file_executable "$repo1/.git/hooks/pre-commit" "Hook file must be executable (+x)"
out=$(bash "$HARNESS_DIR/verify_hook_executable.sh" "$repo1" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "verify_hook_executable.sh should exit 0"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F4-01" "Executable Permissions Check" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F4-01" "Executable Permissions Check" "FAIL" "$dur" "Permissions check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F4-02: Clean Commit Allowed ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F4-02"
repo2="$(create_temp_git_repo "$SANDBOX/repo2")"
install_hook_to_repo "$repo2"
echo "Clean documentation text" > "$repo2/docs.md"
(cd "$repo2" && git add docs.md)
out=$(cd "$repo2" && git commit -m "docs: add clean docs" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Clean commit should succeed"
last_msg=$(cd "$repo2" && git log -1 --pretty=%B)
assert_contains "$last_msg" "add clean docs" "Commit should be created in git history"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F4-02" "Clean Commit Allowed" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F4-02" "Clean Commit Allowed" "FAIL" "$dur" "Clean commit failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F4-03: Secret Staged Commit Blocked ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F4-03"
repo3="$(create_temp_git_repo "$SANDBOX/repo3")"
install_hook_to_repo "$repo3"
head_before=$(cd "$repo3" && git rev-parse HEAD)
create_synthetic_secret_file "$repo3/config.py" "openai"
(cd "$repo3" && git add config.py)
out=$(cd "$repo3" && git commit -m "feat: leaked openai key" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Commit with staged secret must be blocked"
head_after=$(cd "$repo3" && git rev-parse HEAD)
assert_equals "$head_before" "$head_after" "HEAD must remain unchanged when commit is blocked"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F4-03" "Secret Staged Commit Blocked" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F4-03" "Secret Staged Commit Blocked" "FAIL" "$dur" "Commit blocking failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F4-04: Masked Output on Veto ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F4-04"
repo4="$(create_temp_git_repo "$SANDBOX/repo4")"
install_hook_to_repo "$repo4"
P_OAI="sk-proj-"
raw_key="${P_OAI}mockOpenAIKey1234567890123456789012345678"
create_synthetic_secret_file "$repo4/auth_config.py" "openai"
(cd "$repo4" && git add auth_config.py)
out=$(cd "$repo4" && git commit -m "feat: staged openai key" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Pre-commit hook must reject commit with staged secret"
assert_secret_masked "$out" "$raw_key" "Pre-commit hook output must mask secret"
assert_contains "$out" "sk-p...5678" "Expected masked pattern in output"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F4-04" "Masked Output on Veto" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F4-04" "Masked Output on Veto" "FAIL" "$dur" "Masking verification failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F4-05: Multi-File Staging Interception ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F4-05"
repo5="$(create_temp_git_repo "$SANDBOX/repo5")"
install_hook_to_repo "$repo5"
echo "Clean file 1" > "$repo5/clean1.txt"
echo "Clean file 2" > "$repo5/clean2.txt"
create_synthetic_secret_file "$repo5/secret.txt" "aws"
(cd "$repo5" && git add clean1.txt clean2.txt secret.txt)
out=$(cd "$repo5" && git commit -m "batch commit" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Batch commit with 1 secret must be completely aborted"
status_out=$(cd "$repo5" && git status --porcelain)
assert_contains "$status_out" "A  clean1.txt" "clean1.txt should remain in staging index"
assert_contains "$status_out" "A  secret.txt" "secret.txt should remain in staging index"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F4-05" "Multi-File Staging Interception" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F4-05" "Multi-File Staging Interception" "FAIL" "$dur" "Multi-file veto failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
