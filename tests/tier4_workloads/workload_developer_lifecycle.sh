#!/bin/bash
# ==============================================================================
# tests/tier4_workloads/workload_developer_lifecycle.sh
# Tier 4 Workload 4: Clean Developer Lifecycle End-to-End Workflow
# 1 Test Case: TC-T4-004
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T4-004: Clean Developer Commit and Validation Lifecycle"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t4_w4_sandbox")"
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

# --- TC-T4-004: Clean Developer Commit and Validation Lifecycle ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T4-004"

MOCK_REPO="$SANDBOX/mock_repo"
mkdir -p "$MOCK_REPO"
init_mock_git_repo "$MOCK_REPO"
install_hook_to_repo "$MOCK_REPO"
# Commit initial repo tooling baseline
(cd "$MOCK_REPO" && git add . && git commit -q -m "chore: initial tooling baseline")

# Step 1: Developer creates compliant new skill
NEW_SKILL="$MOCK_REPO/[skill]/data-visualizer"
mkdir -p "$NEW_SKILL/scripts" "$NEW_SKILL/references"

cat << 'EOF' > "$NEW_SKILL/SKILL.md"
---
name: data-visualizer
description: Generates clean SVG charts and terminal graphs from tabular datasets
allowed-tools:
  - run_command
  - read_file
  - write_file
---
# Data Visualizer Skill

## When to Activate
Activate when user requests data charts or SVG graph generation.

## Usage
Run `python3 scripts/visualize.py --data table.csv`.
EOF

cat << 'EOF' > "$NEW_SKILL/scripts/visualize.py"
#!/usr/bin/env python3
import sys
import math
import csv

def generate_svg(data_points):
    return f"<svg width='400' height='200'>{len(data_points)} points</svg>"

if __name__ == "__main__":
    print(generate_svg([1, 2, 3, 4]))
EOF

# Step 2: Developer validates skill frontmatter
val_out=$(python3 "$HARNESS_DIR/validate_skill.py" "$NEW_SKILL" 2>&1)
val_exit=$?
assert_exit_code 0 "$val_exit" "Frontmatter validator must pass"

# Step 3: Developer stages and commits
(cd "$MOCK_REPO" && git add "[skill]/data-visualizer")
commit_out=$(cd "$MOCK_REPO" && git commit -m "feat(skill): add data-visualizer skill with SVG chart support" 2>&1)
commit_exit=$?

assert_exit_code 0 "$commit_exit" "Git commit must pass pre-commit security gates"

# Verify commit history
last_commit=$(cd "$MOCK_REPO" && git log -1 --pretty=%B)
assert_contains "$last_commit" "add data-visualizer skill" "Commit must be recorded in git history"

# Verify index and working tree are clean
status_out=$(cd "$MOCK_REPO" && git status --porcelain)
assert_equals "" "$status_out" "Working tree must be completely clean after commit"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$val_exit" -eq 0 ] && [ "$commit_exit" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 4 "TC-T4-004" "Clean Developer Commit and Validation Lifecycle" "PASS" "$dur"
else
    emit_test_result 4 "TC-T4-004" "Clean Developer Commit and Validation Lifecycle" "FAIL" "$dur" "Developer lifecycle test failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
