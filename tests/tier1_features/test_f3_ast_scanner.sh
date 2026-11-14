#!/bin/bash
# ==============================================================================
# tests/tier1_features/test_f3_ast_scanner.sh
# Tier 1 Feature 3: AST Security & Malware Scanner Engine
# 5 Test Cases: E2E-T1-F3-01 to E2E-T1-F3-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T1-F3-01: Clean Codebase Analysis"
    echo "E2E-T1-F3-02: AST Dynamic Code Exec (eval)"
    echo "E2E-T1-F3-03: AST Shell Injection (shell=True)"
    echo "E2E-T1-F3-04: Webhook Exfiltration Detection"
    echo "E2E-T1-F3-05: Structured JSON Output Flag"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t1_f3_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

PROD_SCANNER="$REPO_ROOT/scripts/scan_security_ast.py"
STUB_SCANNER="$HARNESS_DIR/reference_stubs/scan_security_ast.py"

USE_SCANNER="$STUB_SCANNER"
if [ -f "$PROD_SCANNER" ]; then
    USE_SCANNER="$PROD_SCANNER"
fi

OVERALL_EXIT=0

# --- E2E-T1-F3-01: Clean Codebase Analysis ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F3-01"
create_ast_malware_file "$SANDBOX/clean_script.py" "clean"
out=$(python3 "$USE_SCANNER" "$SANDBOX/clean_script.py" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Clean script should pass AST scan"
assert_contains "$out" "AST security scan passed" "Expected scan passed message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F3-01" "Clean Codebase Analysis" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F3-01" "Clean Codebase Analysis" "FAIL" "$dur" "Clean scan failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F3-02: AST Dynamic Code Exec (eval) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F3-02"
create_ast_malware_file "$SANDBOX/eval_hazard.py" "eval"
out=$(python3 "$USE_SCANNER" "$SANDBOX/eval_hazard.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Dynamic eval should fail AST scan"
assert_contains "$out" "DYNAMIC_CODE_EXECUTION" "Expected dynamic execution alert"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F3-02" "AST Dynamic Code Exec (eval)" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F3-02" "AST Dynamic Code Exec (eval)" "FAIL" "$dur" "Eval detection failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F3-03: AST Shell Injection (shell=True) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F3-03"
create_ast_malware_file "$SANDBOX/shell_hazard.py" "shell_true"
out=$(python3 "$USE_SCANNER" "$SANDBOX/shell_hazard.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Subprocess with shell=True should fail AST scan"
assert_contains "$out" "SHELL_INJECTION_RISK" "Expected shell injection risk alert"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F3-03" "AST Shell Injection (shell=True)" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F3-03" "AST Shell Injection (shell=True)" "FAIL" "$dur" "Shell=True detection failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F3-04: Webhook Exfiltration Detection ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F3-04"
create_ast_malware_file "$SANDBOX/webhook_sink.py" "webhook_ssrf"
out=$(python3 "$USE_SCANNER" "$SANDBOX/webhook_sink.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Exfiltration webhook should fail AST scan"
assert_contains "$out" "OUTBOUND_EXFILTRATION_SINK" "Expected exfiltration sink alert"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F3-04" "Webhook Exfiltration Detection" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F3-04" "Webhook Exfiltration Detection" "FAIL" "$dur" "Webhook detection failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F3-05: Structured JSON Output Flag ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F3-05"
report_file="$SANDBOX/report.json"
out=$(python3 "$USE_SCANNER" "$SANDBOX/eval_hazard.py" --json "$report_file" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Hazard scan should return exit code 1"
assert_file_exists "$report_file" "JSON report file must be written"
assert_json_valid "$report_file" "Output report must be valid JSON"
assert_contains "$(cat "$report_file")" '"clean": false' "Report must state clean is false"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F3-05" "Structured JSON Output Flag" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F3-05" "Structured JSON Output Flag" "FAIL" "$dur" "JSON report check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
