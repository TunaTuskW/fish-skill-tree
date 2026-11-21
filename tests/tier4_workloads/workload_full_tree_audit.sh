#!/bin/bash
# ==============================================================================
# tests/tier4_workloads/workload_full_tree_audit.sh
# Tier 4 Workload 1: Full Skill Tree Production Audit Pass (320+ Skills & 6 Plugins)
# 1 Test Case: TC-T4-001
# ==============================================================================

if [ "$1" = "--list" ]; then
    echo "TC-T4-001: Full Skill Tree Security and Malware Audit Pass"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/../harness" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

source "$HARNESS_DIR/assertions.sh"
source "$HARNESS_DIR/isolation.sh"
source "$HARNESS_DIR/fixtures.sh"

SANDBOX="$(create_temp_dir "t4_w1_sandbox")"
trap 'rm -rf "$SANDBOX"' EXIT INT TERM

PROD_SCANNER="$REPO_ROOT/[skill]/sensitive-data-guard/scripts/scan_secrets.py"
STUB_SCANNER="$HARNESS_DIR/reference_stubs/scan_secrets.py"

USE_SECRET_SCANNER="$STUB_SCANNER"
if [ -f "$PROD_SCANNER" ]; then
    if python3 "$PROD_SCANNER" --help 2>&1 | grep -q -- "--staged"; then
        USE_SECRET_SCANNER="$PROD_SCANNER"
    fi
fi

PROD_AST="$REPO_ROOT/scripts/scan_security_ast.py"
STUB_AST="$HARNESS_DIR/reference_stubs/scan_security_ast.py"

USE_AST_SCANNER="$STUB_AST"
if [ -f "$PROD_AST" ]; then
    USE_AST_SCANNER="$PROD_AST"
fi

OVERALL_EXIT=0

# --- TC-T4-001: Full Skill Tree Security and Malware Audit Pass ---
t_start=$(python3 -c "import time; print(time.time())")
set_test_name "TC-T4-001"

SKILLS_DIR="$REPO_ROOT/[skill]"
PLUGINS_DIR="$REPO_ROOT/[plugin]"

if [ ! -d "$SKILLS_DIR" ] || [ ! -d "$PLUGINS_DIR" ]; then
    emit_test_result 4 "TC-T4-001" "Full Skill Tree Security and Malware Audit Pass" "FAIL" "0.00s" "Target directories missing"
    exit 1
fi

# Count skills and plugins directly from genuine repository
total_skills=$(python3 -c '
from pathlib import Path
p = Path("'"$SKILLS_DIR"'")
print(len([d for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")]))
')

total_plugins=$(python3 -c '
from pathlib import Path
p = Path("'"$PLUGINS_DIR"'")
print(len([d for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")]))
')

total_modules=$(( total_skills + total_plugins ))

# Execute Pass 1: Secret Scan across standalone skills and plugins
secret_scan_skills_out=$(python3 "$USE_SECRET_SCANNER" "$SKILLS_DIR" 2>&1)
secret_skills_exit=$?

secret_scan_plugins_out=$(python3 "$USE_SECRET_SCANNER" "$PLUGINS_DIR" 2>&1)
secret_plugins_exit=$?

secret_exit=0
if [ "$secret_skills_exit" -ne 0 ] || [ "$secret_plugins_exit" -ne 0 ]; then
    secret_exit=1
fi

# Execute Pass 2: AST Security Scan across standalone skills and plugins
json_report_skills="$SANDBOX/audit_report_skills.json"
ast_scan_skills_out=$(python3 "$USE_AST_SCANNER" --target "$SKILLS_DIR" --json "$json_report_skills" 2>&1)
ast_skills_exit=$?

json_report_plugins="$SANDBOX/audit_report_plugins.json"
ast_scan_plugins_out=$(python3 "$USE_AST_SCANNER" --target "$PLUGINS_DIR" --json "$json_report_plugins" 2>&1)
ast_plugins_exit=$?

ast_exit=0
if [ "$ast_skills_exit" -ne 0 ] || [ "$ast_plugins_exit" -ne 0 ]; then
    ast_exit=1
fi

# Merge into unified JSON audit report
json_report="$SANDBOX/audit_report.json"
python3 -c '
import json
from pathlib import Path

skills_json = Path("'"$json_report_skills"'")
plugins_json = Path("'"$json_report_plugins"'")

s_data = json.loads(skills_json.read_text(encoding="utf-8")) if skills_json.exists() else {"scanned_files": 0, "clean": False, "findings": []}
p_data = json.loads(plugins_json.read_text(encoding="utf-8")) if plugins_json.exists() else {"scanned_files": 0, "clean": False, "findings": []}

combined = {
    "standalone_skills_count": int("'"$total_skills"'"),
    "plugin_suites_count": int("'"$total_plugins"'"),
    "total_modules": int("'"$total_modules"'"),
    "scanned_files": s_data.get("scanned_files", 0) + p_data.get("scanned_files", 0),
    "clean": s_data.get("clean", False) and p_data.get("clean", False),
    "findings": s_data.get("findings", []) + p_data.get("findings", [])
}

with open("'"$json_report"'", "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)
'

t_end=$(python3 -c "import time; print(time.time())")
elapsed=$(python3 -c "print(f'{$t_end - $t_start:.2f}')")
dur="${elapsed}s"

# Assertions
assert_exit_code 0 "$secret_skills_exit" "Standalone skills secret scan must pass with 0 secrets"
assert_exit_code 0 "$secret_plugins_exit" "Plugin suites secret scan must pass with 0 secrets"
assert_exit_code 0 "$ast_skills_exit" "Standalone skills AST security scan must pass with 0 vulnerabilities"
assert_exit_code 0 "$ast_plugins_exit" "Plugin suites AST security scan must pass with 0 vulnerabilities"
assert_file_exists "$json_report" "Audit report JSON must exist"
assert_json_valid "$json_report" "Audit report JSON must be valid"

# Verify scale (323 standalone skills + 8 plugins)
assert_equals "323" "$total_skills" "Full tree must contain all 323 standalone skills"
assert_equals "8" "$total_plugins" "Full tree must contain all 8 plugin suites"

# Benchmark check (< 60 seconds)
elapsed_int=$(python3 -c "print(int(float('$elapsed')))")
assert_less_than "$elapsed_int" 60 "Full tree audit must complete in under 60 seconds"

if [ "$secret_exit" -eq 0 ] && [ "$ast_exit" -eq 0 ] && [ "$ASSERTIONS_FAILED" -eq 0 ]; then
    emit_test_result 4 "TC-T4-001" "Full Skill Tree Security and Malware Audit Pass" "PASS" "$dur"
else
    emit_test_result 4 "TC-T4-001" "Full Skill Tree Security and Malware Audit Pass" "FAIL" "$dur" "Tree audit failed"
    OVERALL_EXIT=1
fi

exit "$OVERALL_EXIT"
