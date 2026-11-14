#!/bin/bash
# ==============================================================================
# tests/tier2_boundaries/test_f1_boundaries.sh
# Tier 2 Feature 1: Skill Specification Boundaries & Edge Cases
# 5 Test Cases: E2E-T2-F1-01 to E2E-T2-F1-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T2-F1-01: Missing YAML Delimiters"
    echo "E2E-T2-F1-02: Missing Mandatory Fields"
    echo "E2E-T2-F1-03: Corrupted YAML Syntax"
    echo "E2E-T2-F1-04: Empty File (0 Bytes) or Missing SKILL.md"
    echo "E2E-T2-F1-05: UTF-8 Special Symbols and Accents"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t2_f1_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

OVERALL_EXIT=0

# --- E2E-T2-F1-01: Missing YAML Delimiters ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F1-01"
create_malformed_skill_fixture "$SANDBOX" "no-delimiter-skill" "missing_frontmatter"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/no-delimiter-skill" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Missing delimiters must fail validation"
assert_contains "$out" "Missing YAML frontmatter boundary delimiters" "Expected delimiter error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F1-01" "Missing YAML Delimiters" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F1-01" "Missing YAML Delimiters" "FAIL" "$dur" "Delimiter check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F1-02: Missing Mandatory Fields ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F1-02"
create_malformed_skill_fixture "$SANDBOX" "missing-name-skill" "missing_name"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/missing-name-skill" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Missing name must fail validation"
assert_contains "$out" "Missing mandatory frontmatter field: name" "Expected missing name error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F1-02" "Missing Mandatory Fields" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F1-02" "Missing Mandatory Fields" "FAIL" "$dur" "Missing field check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F1-03: Corrupted YAML Syntax ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F1-03"
create_malformed_skill_fixture "$SANDBOX" "corrupted-yaml-skill" "corrupted_yaml_syntax"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/corrupted-yaml-skill" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Corrupted syntax must fail validation"
assert_contains "$out" "YAML Parser Error" "Expected parser error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F1-03" "Corrupted YAML Syntax" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F1-03" "Corrupted YAML Syntax" "FAIL" "$dur" "Corrupted syntax check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F1-04: Empty File (0 Bytes) or Missing SKILL.md ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F1-04"
create_malformed_skill_fixture "$SANDBOX" "empty-skill" "empty_file"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/empty-skill" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Empty file must fail validation"
assert_contains "$out" "empty (0 bytes)" "Expected empty file error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F1-04" "Empty File (0 Bytes) or Missing SKILL.md" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F1-04" "Empty File (0 Bytes) or Missing SKILL.md" "FAIL" "$dur" "Empty file check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F1-05: UTF-8 Special Symbols and Accents ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F1-05"
create_valid_skill_fixture "$SANDBOX" "unicode-skill" "Unicode description with accents" "unicode"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/unicode-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Unicode content must parse cleanly"
assert_contains "$out" "Valid frontmatter with UTF-8 encoding preserved" "Expected UTF-8 confirmation"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F1-05" "UTF-8 Special Symbols and Accents" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F1-05" "UTF-8 Special Symbols and Accents" "FAIL" "$dur" "Unicode check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
