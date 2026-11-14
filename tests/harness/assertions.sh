#!/bin/bash
# ==============================================================================
# tests/harness/assertions.sh
# Core Assertion Library for fish-skill-tree E2E Test Suite
# Fully compatible with macOS default GNU bash 3.2.57
# ==============================================================================

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0
ASSERTION_ERRORS=()

CURRENT_TEST_NAME=""

set_test_name() {
    CURRENT_TEST_NAME="$1"
}

emit_test_result() {
    local tier="$1"
    local test_id="$2"
    local title="$3"
    local status="$4"
    local duration="$5"
    local msg="${6:-}"
    echo "TEST_RESULT|${tier}|${test_id}|${title}|${status}|${duration}|${msg}"
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-Exit code mismatch}"
    if [ "$actual" -eq "$expected" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (Expected: $expected, Got: $actual)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-Values do not match}"
    if [ "$expected" = "$actual" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (Expected: '$expected', Got: '$actual')"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-String does not contain expected substring}"
    if echo "$haystack" | grep -Fq "$needle"; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (Needle '$needle' not found in text)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local msg="${3:-String contains unexpected substring}"
    if echo "$haystack" | grep -Fq "$needle"; then
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (Needle '$needle' was unexpectedly found in text)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    else
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    fi
}

assert_matches() {
    local haystack="$1"
    local pattern="$2"
    local msg="${3:-String does not match regex pattern}"
    if echo "$haystack" | grep -Eq "$pattern"; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (Pattern '$pattern' did not match text)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_file_exists() {
    local file_path="$1"
    local msg="${2:-Expected file does not exist}"
    if [ -f "$file_path" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($file_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_file_not_exists() {
    local file_path="$1"
    local msg="${2:-File unexpectedly exists}"
    if [ ! -e "$file_path" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($file_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_dir_exists() {
    local dir_path="$1"
    local msg="${2:-Expected directory does not exist}"
    if [ -d "$dir_path" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($dir_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_dir_not_exists() {
    local dir_path="$1"
    local msg="${2:-Directory unexpectedly exists}"
    if [ ! -d "$dir_path" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($dir_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_file_executable() {
    local file_path="$1"
    local msg="${2:-File is not executable}"
    if [ -x "$file_path" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($file_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_secret_masked() {
    local text="$1"
    local raw_secret="$2"
    local msg="${3:-Secret was not properly masked in output}"
    # Verify raw secret does not appear anywhere in output
    if echo "$text" | grep -Fq "$raw_secret"; then
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg (CRITICAL: Raw unmasked secret leaked into output!)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
    # Verify mask pattern appears (... or ***)
    if echo "$text" | grep -Eq '(\.\.\.|\*\*\*)'; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: Output did not contain expected mask indicator ('...' or '***')"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_yaml_valid() {
    local file_path="$1"
    local msg="${2:-YAML file contains invalid syntax or frontmatter}"
    local helpers_py
    helpers_py="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/python_helpers.py"
    if python3 "$helpers_py" validate-yaml "$file_path" >/dev/null 2>&1; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($file_path)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_json_valid() {
    local file_or_str="$1"
    local msg="${2:-Invalid JSON content}"
    local helpers_py
    helpers_py="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/python_helpers.py"
    if python3 "$helpers_py" validate-json "$file_or_str" >/dev/null 2>&1; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

assert_less_than() {
    local val="$1"
    local threshold="$2"
    local msg="${3:-Value exceeds maximum threshold}"
    if [ "$val" -lt "$threshold" ]; then
        ASSERTIONS_PASSED=$((ASSERTIONS_PASSED + 1))
        return 0
    else
        ASSERTIONS_FAILED=$((ASSERTIONS_FAILED + 1))
        local err="[${CURRENT_TEST_NAME}] ASSERTION FAILED: $msg ($val >= $threshold)"
        echo "$err" >&2
        ASSERTION_ERRORS+=("$err")
        return 1
    fi
}

test_finish() {
    if [ "$ASSERTIONS_FAILED" -gt 0 ]; then
        echo "Test completed with $ASSERTIONS_FAILED failure(s) out of $((ASSERTIONS_PASSED + ASSERTIONS_FAILED)) assertion(s)." >&2
        return 1
    else
        return 0
    fi
}
