#!/bin/bash
# ==============================================================================
# tests/tier2_boundaries/test_f2_boundaries.sh
# Tier 2 Feature 2: Secret Scanner Boundaries & Edge Cases
# 5 Test Cases: E2E-T2-F2-01 to E2E-T2-F2-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T2-F2-01: Real Secret on Line with example Comment"
    echo "E2E-T2-F2-02: Pure Placeholder Value Bypass"
    echo "E2E-T2-F2-03: High-Entropy Hex Secret (H > 4.5)"
    echo "E2E-T2-F2-04: Git Diff Deleting Old Secret"
    echo "E2E-T2-F2-05: File Exceeding 5MB Skipped"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t2_f2_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

PROD_SCANNER="$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
STUB_SCANNER="$HARNESS_DIR/reference_stubs/scan_secrets.py"

USE_SCANNER="$STUB_SCANNER"
if [ -f "$PROD_SCANNER" ]; then
    if python3 "$PROD_SCANNER" --help 2>&1 | grep -q -- "--staged"; then
        USE_SCANNER="$PROD_SCANNER"
    fi
fi

OVERALL_EXIT=0

# --- E2E-T2-F2-01: Real Secret on Line with example Comment ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F2-01"
create_synthetic_secret_file "$SANDBOX/anti_bypass.py" "anti_bypass_example"
out=$(python3 "$USE_SCANNER" "$SANDBOX/anti_bypass.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Real secret on line with 'example' must still trigger alert"
assert_contains "$out" "sk-a...3456" "Expected masked Anthropic key in output"
assert_secret_masked "$out" "sk-ant-mockRealKey1234567890123456" "Raw secret must not leak"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F2-01" "Real Secret on Line with example Comment" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F2-01" "Real Secret on Line with example Comment" "FAIL" "$dur" "Anti-bypass check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F2-02: Pure Placeholder Value Bypass ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F2-02"
create_synthetic_secret_file "$SANDBOX/placeholder.py" "pure_placeholder"
out=$(python3 "$USE_SCANNER" "$SANDBOX/placeholder.py" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Pure placeholder without token must not raise false positive"
assert_contains "$out" "Secret scan passed" "Expected clean scan message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F2-02" "Pure Placeholder Value Bypass" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F2-02" "Pure Placeholder Value Bypass" "FAIL" "$dur" "Placeholder check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F2-03: High-Entropy Hex Secret (H > 4.5) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F2-03"
create_synthetic_secret_file "$SANDBOX/entropy.py" "high_entropy_hex"
out=$(python3 "$USE_SCANNER" "$SANDBOX/entropy.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "High entropy string must trigger alert"
assert_matches "$out" "High[- ]Entropy" "Expected high entropy alert indicator"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F2-03" "High-Entropy Hex Secret (H > 4.5)" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F2-03" "High-Entropy Hex Secret (H > 4.5)" "FAIL" "$dur" "Entropy check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F2-04: Git Diff Deleting Old Secret ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F2-04"
out=$(create_synthetic_secret_diff "delete_secret" | python3 "$USE_SCANNER" --stdin 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Diff deleting secret should pass cleanly without alerting"
assert_contains "$out" "Secret scan passed" "Expected clean scan message on deletion diff"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F2-04" "Git Diff Deleting Old Secret" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F2-04" "Git Diff Deleting Old Secret" "FAIL" "$dur" "Deletion diff check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F2-05: File Exceeding 5MB Skipped ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F2-05"
create_synthetic_secret_file "$SANDBOX/large.dat" "large_file"
out=$(python3 "$USE_SCANNER" "$SANDBOX/large.dat" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "File larger than 5MB should be skipped safely without OOM"
assert_contains "$out" "Secret scan passed" "Large file must be skipped cleanly"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F2-05" "File Exceeding 5MB Skipped" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F2-05" "File Exceeding 5MB Skipped" "FAIL" "$dur" "Large file check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
