#!/bin/bash
# ==============================================================================
# tests/tier3_combinations/test_sync_path_translation.sh
# Tier 3 Combination: Sync Path Translation & Frontmatter Preservation Round-Trip
# 1 Test Case: TC-T3-005
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T3-005: Sync Path Translation and Frontmatter Preservation Round-Trip"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_sandbox "t3_c4_sandbox")"
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
init_mock_git_repo "$MOCK_REPO"
ACTIVE_ROOT="$SANDBOX/fake_home/.gemini/config"
mkdir -p "$ACTIVE_ROOT/plugins" "$ACTIVE_ROOT/skills"

# --- TC-T3-005: Sync Path Translation and Frontmatter Preservation Round-Trip ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T3-005"

# Setup initial rule file in repository with exact YAML frontmatter and ~/vibe/ paths
RULE_FILE="$MOCK_REPO/[plugin]/engineering-core-suite/rules/AGENTS.md"
mkdir -p "$(dirname "$RULE_FILE")"
cat << 'EOF' > "$RULE_FILE"
---
name: engineering-core-suite
description: Master sector router for Core Software Engineering
metadata:
  version: 1.0.0
  author: fish-coding-agent
---
# Core Engineering Rules

## 4. Mandatory Exports Mirror
- Whenever source code is generated, ALWAYS save a duplicate into ~/vibe/ following project taxonomy.
- Reference configuration stored at ~/vibe/config/settings.json.
EOF

# Capture original frontmatter block
orig_frontmatter=$(sed -n '/^---$/,/^---$/p' "$RULE_FILE")

# Step 1: Sync repo -> active plugins
out1=$(python3 "$USE_SYNC" --direction repo-to-active --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_ROOT" 2>&1)
exit1=$?
assert_exit_code 0 "$exit1" "repo-to-active sync must succeed"

ACTIVE_FILE="$ACTIVE_ROOT/plugins/engineering-core-suite/rules/AGENTS.md"
assert_file_exists "$ACTIVE_FILE" "Active rule file must exist"

# Verify active file translation
active_content=$(cat "$ACTIVE_FILE")
assert_contains "$active_content" "/Users/mac/vibe/ following project taxonomy." "Path must be translated to /Users/mac/vibe/"
assert_contains "$active_content" "/Users/mac/vibe/config/settings.json." "Path must be translated to /Users/mac/vibe/"
assert_not_contains "$active_content" "~/vibe/" "Original ~/vibe/ path must not remain in active plugin"

# Verify frontmatter preserved byte-for-byte in active plugin
active_frontmatter=$(sed -n '/^---$/,/^---$/p' "$ACTIVE_FILE")
assert_equals "$orig_frontmatter" "$active_frontmatter" "Frontmatter block must remain identical after translation"

# Step 2: Sync active plugins -> repo
out2=$(python3 "$USE_SYNC" --direction active-to-repo --repo-dir "$MOCK_REPO" --active-dir "$ACTIVE_ROOT" 2>&1)
exit2=$?
assert_exit_code 0 "$exit2" "active-to-repo return sync must succeed"

# Verify returned repo file
repo_content=$(cat "$RULE_FILE")
assert_contains "$repo_content" "~/vibe/ following project taxonomy." "Path must be translated back to ~/vibe/"
assert_not_contains "$repo_content" "/Users/mac/vibe/" "Absolute path must be removed on return sync"
assert_not_contains "$repo_content" "~/~/vibe/" "Duplicate path prefixes must not occur"

return_frontmatter=$(sed -n '/^---$/,/^---$/p' "$RULE_FILE")
assert_equals "$orig_frontmatter" "$return_frontmatter" "Frontmatter block must remain identical after round-trip"

t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit1" -eq 0 ] && [ "$exit2" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 3 "TC-T3-005" "Sync Path Translation and Frontmatter Preservation Round-Trip" "PASS" "$dur"
else
    emit_test_result 3 "TC-T3-005" "Sync Path Translation and Frontmatter Preservation Round-Trip" "FAIL" "$dur" "Round-trip check failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
