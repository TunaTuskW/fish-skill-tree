#!/bin/bash
# ==============================================================================
# tests/tier1_features/test_f2_secret_scanner.sh
# Tier 1 Feature 2: Secret Scanner CLI & Detection Rules
# 5 Test Cases: E2E-T1-F2-01 to E2E-T1-F2-05
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "E2E-T1-F2-01: Clean Directory Scan"
    echo "E2E-T1-F2-02: Standard Known Regex Token Scan"
    echo "E2E-T1-F2-03: Unified Diff via --stdin"
    echo "E2E-T1-F2-04: Staged Git Diff Scan (--staged)"
    echo "E2E-T1-F2-05: JSON OAuth Key Detection"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t1_f2_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

# Resolve scanner script (prefer production, fallback to hardened reference stub)
PROD_SCANNER="$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
STUB_SCANNER="$HARNESS_DIR/reference_stubs/scan_secrets.py"

USE_SCANNER="$STUB_SCANNER"
if [ -f "$PROD_SCANNER" ]; then
    if python3 "$PROD_SCANNER" --help 2>&1 | grep -q -- "--staged"; then
        USE_SCANNER="$PROD_SCANNER"
    fi
fi

OVERALL_EXIT=0

# --- E2E-T1-F2-01: Clean Directory Scan ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F2-01"
mkdir -p "$SANDBOX/clean_dir"
create_synthetic_secret_file "$SANDBOX/clean_dir/app.py" "clean_code"
out=$(python3 "$USE_SCANNER" "$SANDBOX/clean_dir" 2>&1)
exit_code=$?
assert_exit_code 0 "$exit_code" "Clean directory scan should return exit code 0"
assert_contains "$out" "Secret scan passed" "Expected clean scan message"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F2-01" "Clean Directory Scan" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F2-01" "Clean Directory Scan" "FAIL" "$dur" "Clean scan failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F2-02: Standard Known Regex Token Scan ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F2-02"
create_synthetic_secret_file "$SANDBOX/tainted_key.py" "google_gemini"
out=$(python3 "$USE_SCANNER" "$SANDBOX/tainted_key.py" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Tainted file scan must return exit code 1"
assert_contains "$out" "AIza...9012" "Expected masked Google Gemini key"
P_GEM="AIza"
assert_secret_masked "$out" "${P_GEM}SyD-mockGoogleGeminiKey123456789012" "Secret must not leak unmasked"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F2-02" "Standard Known Regex Token Scan" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F2-02" "Standard Known Regex Token Scan" "FAIL" "$dur" "Token detection failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F2-03: Unified Diff via --stdin ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F2-03"
out=$(create_synthetic_secret_diff "github_pat" | python3 "$USE_SCANNER" --stdin 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Diff with secret must return exit code 1"
assert_contains "$out" "ghp_...1234" "Expected masked GitHub PAT"
P_GHP="ghp_"
assert_secret_masked "$out" "${P_GHP}mockGitHubClassicToken12345678901234" "Raw PAT must not leak"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F2-03" "Unified Diff via --stdin" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F2-03" "Unified Diff via --stdin" "FAIL" "$dur" "Stdin diff check failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F2-04: Staged Git Diff Scan (--staged) ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F2-04"
git_repo="$(create_temp_git_repo "$SANDBOX")"
create_synthetic_secret_file "$git_repo/credentials.env" "anthropic"
(cd "$git_repo" && git add credentials.env)
out=$(cd "$git_repo" && python3 "$USE_SCANNER" --staged 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "Staged secret scan must return exit code 1"
assert_contains "$out" "sk-a...7890" "Expected masked Anthropic key"
P_ANT="sk-ant-"
assert_secret_masked "$out" "${P_ANT}api03-mockAnthropicKey12345678901234567890" "Raw key must not leak"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F2-04" "Staged Git Diff Scan (--staged)" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F2-04" "Staged Git Diff Scan (--staged)" "FAIL" "$dur" "Staged scan failed"
    OVERALL_EXIT=1
fi

ASSERTIONS_PASSED=0
ASSERTIONS_FAILED=0

# --- E2E-T1-F2-05: JSON OAuth Key Detection ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "E2E-T1-F2-05"
create_synthetic_secret_file "$SANDBOX/oauth_config.json" "json_oauth"
out=$(python3 "$USE_SCANNER" "$SANDBOX/oauth_config.json" 2>&1)
exit_code=$?
assert_exit_code 1 "$exit_code" "JSON OAuth secret must return exit code 1"
assert_contains "$out" "GOCS...2345" "Expected masked OAuth client secret"
P_GOC="GOCSPX-"
assert_secret_masked "$out" "${P_GOC}mockoauthclientsecret12345" "Raw OAuth secret must not leak"
t_end=$(python3 -c "import time; print(time.time())")
dur=$(python3 -c "print(f'{$t_end - $t_start:.2f}s')")
if [ "$exit_code" -eq 1 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 1 "E2E-T1-F2-05" "JSON OAuth Key Detection" "PASS" "$dur"
else
    emit_test_result 1 "E2E-T1-F2-05" "JSON OAuth Key Detection" "FAIL" "$dur" "OAuth detection failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
