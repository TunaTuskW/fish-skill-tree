#!/bin/bash
# ==============================================================================
# tests/tier2_boundaries/test_f5_boundaries.sh
# Tier 2 Feature 5: Multi-Target Sync Boundaries & Edge Cases
# 5 Test Cases: E2E-T2-F5-01 to E2E-T2-F5-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T2-F5-01: Invalid Direction Argument Rejected"
    echo "E2E-T2-F5-02: Path Translation Duplicate Slashes Normalization"
    echo "E2E-T2-F5-03: Non-Existent Target Directory Handled"
    echo "E2E-T2-F5-04: Symlink Safety and Loop Prevention"
    echo "E2E-T2-F5-05: Mixed Binary and Text Asset Sync"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t2_f5_sandbox")"
activate_sandbox "$SANDBOX"
trap cleanup_all_sandboxes EXIT INT TERM HUP

PROD_SYNC="$REPO_ROOT/scripts/sync_ecosystem.py"
STUB_SYNC="$HARNESS_DIR/reference_stubs/sync_ecosystem.py"

USE_SYNC="$STUB_SYNC"
if [ -f "$PROD_SYNC" ]; then
    USE_SYNC="$PROD_SYNC"
fi

OVERALL_EXIT=0

MOCK_REPO="$SANDBOX/mock_repo"
MOCK_ACTIVE_PLUGINS="$(mock_active_plugins_dir "$SANDBOX")"
MOCK_ACTIVE_SKILLS="$(mock_active_skills_dir "$SANDBOX")"
MOCK_ACTIVE_ROOT="$SANDBOX/fake_home/.gemini/config"

# --- E2E-T2-F5-01: Invalid Direction Argument Rejected ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F5-01"
out=$(python3 "$USE_SYNC" --direction invalid-dir 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Invalid direction argument must exit 1"
assert_contains "$out" "Invalid direction" "Expected invalid direction error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F5-01" "Invalid Direction Argument Rejected" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F5-01" "Invalid Direction Argument Rejected" "FAIL" "$dur" "Direction check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F5-02: Path Translation Duplicate Slashes Normalization ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F5-02"
mkdir -p "$MOCK_REPO/[plugin]/test-suite/rules"
cat << 'EOF' > "$MOCK_REPO/[plugin]/test-suite/rules/AGENTS.md"
# Duplicate Slashes Test
Path is ~/vibe///[skill tree]/data.
EOF
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Sync should succeed with normalized path"
synced_file="$MOCK_ACTIVE_PLUGINS/test-suite/rules/AGENTS.md"
content=$(cat "$synced_file")
assert_contains "$content" "/Users/mac/vibe/[skill tree]/data" "Path must be normalized cleanly without duplicate slashes"
assert_not_contains "$content" "///" "Duplicate slashes must not be preserved"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F5-02" "Path Translation Duplicate Slashes Normalization" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F5-02" "Path Translation Duplicate Slashes Normalization" "FAIL" "$dur" "Slash normalization failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F5-03: Non-Existent Target Directory Handled ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F5-03"
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "/nonexistent/path/for/active/plugins" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Missing target directory must exit 1"
assert_contains "$out" "does not exist" "Expected missing directory error message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F5-03" "Non-Existent Target Directory Handled" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F5-03" "Non-Existent Target Directory Handled" "FAIL" "$dur" "Missing dir check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F5-04: Symlink Safety and Loop Prevention ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F5-04"
mkdir -p "$MOCK_REPO/[skill]/symlink-skill/sub"
echo "Valid content" > "$MOCK_REPO/[skill]/symlink-skill/sub/doc.txt"
# Create circular symlink inside
ln -s "$MOCK_REPO/[skill]/symlink-skill/sub" "$MOCK_REPO/[skill]/symlink-skill/sub/loop" 2>/dev/null || true
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Sync must complete without infinite loop on symlink"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F5-04" "Symlink Safety and Loop Prevention" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F5-04" "Symlink Safety and Loop Prevention" "FAIL" "$dur" "Symlink handling failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T2-F5-05: Mixed Binary and Text Asset Sync ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T2-F5-05"
mkdir -p "$MOCK_REPO/[skill]/mixed-skill"
echo "Text referencing ~/vibe/notes." > "$MOCK_REPO/[skill]/mixed-skill/note.txt"
printf '\x89PNG\r\n\x1a\nBINARY_RAW_BYTES' > "$MOCK_REPO/[skill]/mixed-skill/logo.png"
out=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$MOCK_ACTIVE_ROOT" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Mixed sync must succeed"
assert_file_exists "$MOCK_ACTIVE_SKILLS/mixed-skill/note.txt" "Text file must exist"
assert_file_exists "$MOCK_ACTIVE_SKILLS/mixed-skill/logo.png" "Binary file must exist"
assert_contains "$(cat "$MOCK_ACTIVE_SKILLS/mixed-skill/note.txt")" "/Users/mac/vibe/notes." "Text should undergo path translation"
# Check binary byte integrity
assert_contains "$(cat "$MOCK_ACTIVE_SKILLS/mixed-skill/logo.png")" "BINARY_RAW_BYTES" "Binary file must preserve bytes"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 2 "E2E-T2-F5-05" "Mixed Binary and Text Asset Sync" "PASS" "$dur"
else
    emit_test_result 2 "E2E-T2-F5-05" "Mixed Binary and Text Asset Sync" "FAIL" "$dur" "Mixed sync check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
