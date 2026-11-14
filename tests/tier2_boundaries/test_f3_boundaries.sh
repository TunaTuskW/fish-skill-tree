#!/bin/bash
# ==============================================================================
# tests/tier2_boundaries/test_f3_boundaries.sh
# Tier 2 Feature 3: AST Security Scanner Boundaries & Edge Cases
# 5 Test Cases: E2E-T2-F3-01 to E2E-T2-F3-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T2-F3-01: Malformed Python Syntax Handled Cleanly"
    echo "E2E-T2-F3-02: Base64 Obfuscated Dynamic Execution"
    echo "E2E-T2-F3-03: Shell Script Unpinned Binary Download"
    echo "E2E-T2-F3-04: Legitimate Subprocess Arg List Pass"
    echo "E2E-T2-F3-05: Non-Existent Target Path Handled"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t2_f3_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

PROD_SCANNER="$REPO_ROOT/scripts/scan_security_ast.py"
STUB_SCANNER="$HARNESS_DIR/reference_stubs/scan_security_ast.py"

USE_SCANNER="$STUB_SCANNER"
if [ -f "$PROD_SCANNER" ]; then
    USE_SCANNER="$PROD_SCANNER"
fi

OVERALL_EXIT=0

# --- E2E-T2-F3-01: Malformed Python Syntax Handled Cleanly ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F3-01"
create_ast_malware_file "$SANDBOX/syntax_error.py" "syntax_error"
out=$(python3 "$USE_SCANNER" "$SANDBOX/syntax_error.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Syntax error file must exit 1 without unhandled traceback"
assert_contains "$out" "Syntax Error" "Expected clean syntax error notice"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F3-01" "Malformed Python Syntax Handled Cleanly" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F3-01" "Malformed Python Syntax Handled Cleanly" "FAIL" "$dur" "Syntax handling failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F3-02: Base64 Obfuscated Dynamic Execution ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F3-02"
create_ast_malware_file "$SANDBOX/b64_exec.py" "obfuscated_b64"
out=$(python3 "$USE_SCANNER" "$SANDBOX/b64_exec.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Base64 obfuscated eval/exec must exit 1"
assert_matches "$out" "OBFUSCATED_DYNAMIC_EXEC|DYNAMIC_CODE_EXECUTION" "Expected dynamic code execution finding"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F3-02" "Base64 Obfuscated Dynamic Execution" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F3-02" "Base64 Obfuscated Dynamic Execution" "FAIL" "$dur" "Base64 detection failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F3-03: Shell Script Unpinned Binary Download ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F3-03"
create_ast_malware_file "$SANDBOX/unpinned.sh" "unpinned_curl"
out=$(python3 "$USE_SCANNER" "$SANDBOX/unpinned.sh" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Unpinned binary execution in shell script must exit 1"
assert_matches "$out" "UNPINNED_BINARY_EXECUTION|UNCHECKSUMMED_REMOTE_EXEC|SUPPLY_CHAIN" "Expected supply chain finding"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F3-03" "Shell Script Unpinned Binary Download" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F3-03" "Shell Script Unpinned Binary Download" "FAIL" "$dur" "Shell script check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F3-04: Legitimate Subprocess Arg List Pass ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F3-04"
create_ast_malware_file "$SANDBOX/safe_proc.py" "safe_subprocess"
out=$(python3 "$USE_SCANNER" "$SANDBOX/safe_proc.py" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Safe subprocess call with argument list must pass"
assert_contains "$out" "AST security scan passed" "Expected clean AST scan"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F3-04" "Legitimate Subprocess Arg List Pass" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F3-04" "Legitimate Subprocess Arg List Pass" "FAIL" "$dur" "Safe subprocess check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F3-05: Non-Existent Target Path Handled ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F3-05"
out=$(python3 "$USE_SCANNER" "/nonexistent/target/path/to/script.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Non-existent path must exit 1"
assert_contains "$out" "does not exist" "Expected path does not exist error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F3-05" "Non-Existent Target Path Handled" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F3-05" "Non-Existent Target Path Handled" "FAIL" "$dur" "Non-existent path check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
