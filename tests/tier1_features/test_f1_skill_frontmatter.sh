#!/bin/bash
# ==============================================================================
# tests/tier1_features/test_f1_skill_frontmatter.sh
# Tier 1 Feature 1: Skill Specification Standards & YAML Frontmatter
# 5 Test Cases: E2E-T1-F1-01 to E2E-T1-F1-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T1-F1-01: Standard Standalone Frontmatter"
    echo "E2E-T1-F1-02: Folded Scalar Description (>-)"
    echo "E2E-T1-F1-03: Literal Block Scalar Description (pipe block)"
    echo "E2E-T1-F1-04: Extended Metadata Frontmatter"
    echo "E2E-T1-F1-05: Full Directory Layout with Subdirs"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t1_f1_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

OVERALL_EXIT=0

# --- E2E-T1-F1-01: Standard Standalone Frontmatter ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F1-01"
create_valid_skill_fixture "$SANDBOX" "my-skill" "Basic skill description." "standard"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/my-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Standard skill validation should pass"
assert_contains "$out" "SKILL.md frontmatter valid: name='my-skill'" "Expected valid name in output"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F1-01" "Standard Standalone Frontmatter" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F1-01" "Standard Standalone Frontmatter" "FAIL" "$dur" "Validation failed"
    OVERALL_EXIT=1
fi

# Reset assertion counters for next test
ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F1-02: Folded Scalar Description (>-) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F1-02"
create_valid_skill_fixture "$SANDBOX" "folded-skill" "Multi-line folded skill description." "folded"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/folded-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Folded skill validation should pass"
assert_contains "$out" "Valid multi-line folded description parsed successfully" "Expected folded description confirmation"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F1-02" "Folded Scalar Description (>-)" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F1-02" "Folded Scalar Description (>-)" "FAIL" "$dur" "Folded parsing failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F1-03: Literal Block Scalar Description (pipe block) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F1-03"
create_valid_skill_fixture "$SANDBOX" "literal-skill" "Literal block skill description." "literal"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/literal-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Literal skill validation should pass"
assert_contains "$out" "Valid literal block description parsed successfully" "Expected literal description confirmation"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F1-03" "Literal Block Scalar Description (pipe block)" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F1-03" "Literal Block Scalar Description (pipe block)" "FAIL" "$dur" "Literal parsing failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F1-04: Extended Metadata Frontmatter ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F1-04"
create_valid_skill_fixture "$SANDBOX" "extended-skill" "Skill with extended metadata." "extended"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/extended-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Extended metadata validation should pass"
assert_contains "$out" "Extended metadata parsed cleanly" "Expected extended metadata confirmation"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F1-04" "Extended Metadata Frontmatter" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F1-04" "Extended Metadata Frontmatter" "FAIL" "$dur" "Extended metadata failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F1-05: Full Directory Layout with Subdirs ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F1-05"
create_valid_skill_fixture "$SANDBOX" "full-layout-skill" "Full layout skill." "full_layout"
out=$(python3 "$HARNESS_DIR/validate_skill.py" "$SANDBOX/full-layout-skill" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Full directory layout validation should pass"
assert_dir_exists "$SANDBOX/full-layout-skill/scripts" "scripts directory must exist"
assert_dir_exists "$SANDBOX/full-layout-skill/references" "references directory must exist"
assert_contains "$out" "Valid skill layout (SKILL.md + subdirectories)" "Expected full layout confirmation"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F1-05" "Full Directory Layout with Subdirs" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F1-05" "Full Directory Layout with Subdirs" "FAIL" "$dur" "Full layout validation failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
