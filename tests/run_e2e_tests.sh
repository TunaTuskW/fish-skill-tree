#!/bin/bash
# ==============================================================================
# tests/run_e2e_tests.sh
# Master E2E Test Runner for fish-skill-tree
# Compatible with macOS default GNU bash 3.2.57
# ==============================================================================
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source harness reporting utilities
source "$SCRIPT_DIR/harness/reporters.sh"

# Preserve host user-site in PYTHONPATH for PyYAML and system packages across all HOME diversions
ORIGINAL_HOME="${ORIGINAL_HOME:-$HOME}"
export ORIGINAL_HOME
HOST_PY_SITE=$(HOME="$ORIGINAL_HOME" python3 -m site --user-site 2>/dev/null || true)
if [ -z "$HOST_PY_SITE" ] || [ ! -d "$HOST_PY_SITE" ]; then
    HOST_PY_SITE=$(python3 -c "import yaml, os; print(os.path.dirname(os.path.dirname(yaml.__file__)))" 2>/dev/null || true)
fi
if [ -n "$HOST_PY_SITE" ] && [ -d "$HOST_PY_SITE" ]; then
    case ":${PYTHONPATH:-}:" in
        *":$HOST_PY_SITE:"*) ;;
        *) export PYTHONPATH="${HOST_PY_SITE}:${PYTHONPATH:-}" ;;
    esac
fi
export PYTHONDONTWRITEBYTECODE=1

TIER_SELECTION="all"
FILTER_PATTERN=""
VERBOSE=0
QUIET=0
FAIL_FAST=0
LIST_ONLY=0
USE_COLOR=1

# TTY autodetection
if [ ! -t 1 ]; then
    USE_COLOR=0
fi

# Parse CLI options
while [ $# -gt 0 ]; do
    case "$1" in
        -t|--tier)
            if [ -z "$2" ]; then
                echo "Error: Missing argument for --tier" >&2
                exit 2
            fi
            TIER_SELECTION="$2"
            shift 2
            ;;
        -f|--filter)
            if [ -z "$2" ]; then
                echo "Error: Missing argument for --filter" >&2
                exit 2
            fi
            FILTER_PATTERN="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -q|--quiet)
            QUIET=1
            shift
            ;;
        -x|--fail-fast)
            FAIL_FAST=1
            shift
            ;;
        -l|--list)
            LIST_ONLY=1
            shift
            ;;
        --no-color)
            USE_COLOR=0
            shift
            ;;
        -h|--help)
            echo "Usage: bash tests/run_e2e_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --tier <1|2|3|4|all>   Execute specific test tier (default: all)"
            echo "                             1 = Tier 1: Feature Coverage (25 tests)"
            echo "                             2 = Tier 2: Boundary & Corner Cases (25 tests)"
            echo "                             3 = Tier 3: Cross-Feature Interactions (7 tests)"
            echo "                             4 = Tier 4: Real-World Workloads (5 tests)"
            echo "  -f, --filter <pattern>      Filter test cases matching substring or regex"
            echo "  -v, --verbose               Display stdout/stderr traces for tests"
            echo "  -q, --quiet                 Quiet mode (summary table only)"
            echo "  -x, --fail-fast             Exit immediately on first test failure"
            echo "  -l, --list                  List discovered tests and exit"
            echo "  --no-color                  Disable ANSI colored output"
            echo "  -h, --help                  Display this help message"
            exit 0
            ;;
        *)
            echo "Error: Unknown argument '$1'. Run with --help for usage." >&2
            exit 2
            ;;
    esac
done

init_colors "$USE_COLOR"

# Determine target directories
TIER_DIRS=()
case "$TIER_SELECTION" in
    1) TIER_DIRS=("$SCRIPT_DIR/tier1_features") ;;
    2) TIER_DIRS=("$SCRIPT_DIR/tier2_boundaries") ;;
    3) TIER_DIRS=("$SCRIPT_DIR/tier3_combinations") ;;
    4) TIER_DIRS=("$SCRIPT_DIR/tier4_workloads") ;;
    all)
        TIER_DIRS=(
            "$SCRIPT_DIR/tier1_features"
            "$SCRIPT_DIR/tier2_boundaries"
            "$SCRIPT_DIR/tier3_combinations"
            "$SCRIPT_DIR/tier4_workloads"
        )
        ;;
    *)
        echo "Error: Invalid tier '$TIER_SELECTION'. Must be 1, 2, 3, 4, or all." >&2
        exit 2
        ;;
esac

# Collect executable test files across selected tiers
DISCOVERED_FILES=()
if [ "${#TIER_DIRS[@]}" -gt 0 ]; then
    for tdir in "${TIER_DIRS[@]}"; do
        if [ -d "$tdir" ]; then
            for tfile in "$tdir"/*.sh; do
                if [ -f "$tfile" ]; then
                    DISCOVERED_FILES+=("$tfile")
                fi
            done
        fi
    done
fi

# If --list requested, query test scripts for test cases
if [ "$LIST_ONLY" -eq 1 ]; then
    LISTED_CASES=()
    if [ "${#DISCOVERED_FILES[@]}" -gt 0 ]; then
        for tf in "${DISCOVERED_FILES[@]}"; do
            parent="$(basename "$(dirname "$tf")")"
            tier_label=""
            case "$parent" in
                tier1_features) tier_label="Tier 1" ;;
                tier2_boundaries) tier_label="Tier 2" ;;
                tier3_combinations) tier_label="Tier 3" ;;
                tier4_workloads) tier_label="Tier 4" ;;
            esac
            # Query test script
            raw_list=$(bash "$tf" --list 2>/dev/null || true)
            while IFS= read -r line; do
                if [ -n "$line" ]; then
                    if [ -n "$FILTER_PATTERN" ]; then
                        if echo "$line" | grep -Eq "$FILTER_PATTERN"; then
                            LISTED_CASES+=("  [$tier_label] $line")
                        fi
                    else
                        LISTED_CASES+=("  [$tier_label] $line")
                    fi
                fi
            done << EOF
$raw_list
EOF
        done
    fi

    echo "Discovered ${#LISTED_CASES[@]} test case(s) across tiers:"
    if [ "${#LISTED_CASES[@]}" -gt 0 ]; then
        for item in "${LISTED_CASES[@]}"; do
            echo "$item"
        done
    fi
    echo "Total: ${#LISTED_CASES[@]} test cases"
    exit 0
fi

# Print banner
if [ "$QUIET" -eq 0 ]; then
    print_banner "$REPO_ROOT"
fi

# Counters (Bash 3.2 indexed arrays for tier stats)
# Index: 1=Tier1, 2=Tier2, 3=Tier3, 4=Tier4
TIER_TOTAL=(0 0 0 0 0)
TIER_PASS=(0 0 0 0 0)
TIER_FAIL=(0 0 0 0 0)
TIER_SKIP=(0 0 0 0 0)

TOTAL_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

FAILED_TEST_LOGS=()
TEMP_RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/run_e2e.XXXXXX")"
trap 'rm -rf "$TEMP_RUN_DIR"' EXIT INT TERM

START_TIME=$(python3 -c "import time; print(time.time())")

# Execute test files
ABORT_RUN=0
if [ "${#DISCOVERED_FILES[@]}" -gt 0 ]; then
    for test_file in "${DISCOVERED_FILES[@]}"; do
        if [ "$ABORT_RUN" -eq 1 ]; then
            break
        fi

    file_name="$(basename "$test_file")"
    parent_dir="$(basename "$(dirname "$test_file")")"
    tier_num=1
    case "$parent_dir" in
        tier1_features) tier_num=1 ;;
        tier2_boundaries) tier_num=2 ;;
        tier3_combinations) tier_num=3 ;;
        tier4_workloads) tier_num=4 ;;
    esac

    out_file="$TEMP_RUN_DIR/${file_name}.out"
    err_file="$TEMP_RUN_DIR/${file_name}.err"

    # Run the test script
    REPO_ROOT="$REPO_ROOT" bash "$test_file" >"$out_file" 2>"$err_file"
    script_exit=$?

    # Parse output lines
    parsed_any=0
    file_had_failure=0
    while IFS= read -r line; do
        if echo "$line" | grep -q "^TEST_RESULT|"; then
            parsed_any=1
            r_tier=$(echo "$line" | awk -F'|' '{print $2}')
            r_id=$(echo "$line" | awk -F'|' '{print $3}')
            r_title=$(echo "$line" | awk -F'|' '{print $4}')
            r_status=$(echo "$line" | awk -F'|' '{print $5}')
            r_duration=$(echo "$line" | awk -F'|' '{print $6}')
            r_msg=$(echo "$line" | cut -d'|' -f7-)

            # Filter check
            if [ -n "$FILTER_PATTERN" ]; then
                if ! echo "$r_id $r_title" | grep -Eq "$FILTER_PATTERN"; then
                    continue
                fi
            fi

            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIER_TOTAL[$r_tier]=$((TIER_TOTAL[$r_tier] + 1))

            if [ "$r_status" = "PASS" ]; then
                PASS_COUNT=$((PASS_COUNT + 1))
                TIER_PASS[$r_tier]=$((TIER_PASS[$r_tier] + 1))
                if [ "$QUIET" -eq 0 ]; then
                    log_pass "[T$r_tier] $r_id: $r_title (${r_duration})"
                fi
            elif [ "$r_status" = "SKIP" ]; then
                SKIP_COUNT=$((SKIP_COUNT + 1))
                TIER_SKIP[$r_tier]=$((TIER_SKIP[$r_tier] + 1))
                if [ "$QUIET" -eq 0 ]; then
                    log_skip "[T$r_tier] $r_id: $r_title ($r_msg)"
                fi
            else
                file_had_failure=1
                FAIL_COUNT=$((FAIL_COUNT + 1))
                TIER_FAIL[$r_tier]=$((TIER_FAIL[$r_tier] + 1))
                log_fail "[T$r_tier] $r_id: $r_title ($r_msg)"
                FAILED_TEST_LOGS+=("$r_id - $r_title:::$out_file:::$err_file")
                if [ "$FAIL_FAST" -eq 1 ]; then
                    ABORT_RUN=1
                    break
                fi
            fi
        fi
    done < "$out_file"

    # If script produced no TEST_RESULT markers
    if [ "$parsed_any" -eq 0 ]; then
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        TIER_TOTAL[$tier_num]=$((TIER_TOTAL[$tier_num] + 1))
        if [ "$script_exit" -eq 0 ]; then
            PASS_COUNT=$((PASS_COUNT + 1))
            TIER_PASS[$tier_num]=$((TIER_PASS[$tier_num] + 1))
            log_pass "[T$tier_num] $file_name (script pass)"
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            TIER_FAIL[$tier_num]=$((TIER_FAIL[$tier_num] + 1))
            log_fail "[T$tier_num] $file_name (script exit $script_exit)"
            FAILED_TEST_LOGS+=("$file_name:::$out_file:::$err_file")
            if [ "$FAIL_FAST" -eq 1 ]; then
                ABORT_RUN=1
                break
            fi
        fi
    elif [ "$script_exit" -ne 0 ] && [ "$file_had_failure" -eq 0 ]; then
        # Script produced test markers, but exited non-zero without recording a failure (abnormal abort)
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        TIER_TOTAL[$tier_num]=$((TIER_TOTAL[$tier_num] + 1))
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TIER_FAIL[$tier_num]=$((TIER_FAIL[$tier_num] + 1))
        log_fail "[T$tier_num] $file_name aborted abnormally (exit code $script_exit)"
        FAILED_TEST_LOGS+=("$file_name (exit code $script_exit):::$out_file:::$err_file")
        if [ "$FAIL_FAST" -eq 1 ]; then
            ABORT_RUN=1
            break
        fi
    fi

    if [ "$VERBOSE" -eq 1 ]; then
        if [ -s "$out_file" ]; then
            echo "--- [$file_name STDOUT] ---"
            cat "$out_file"
        fi
        if [ -s "$err_file" ]; then
            echo "--- [$file_name STDERR] ---"
            cat "$err_file"
        fi
    fi
done
fi

END_TIME=$(python3 -c "import time; print(time.time())")
TOTAL_DURATION=$(python3 -c "print(f'{$END_TIME - $START_TIME:.2f}s')")

# Summary Table Output
print_summary_table \
    "${TIER_TOTAL[1]}" "${TIER_PASS[1]}" "${TIER_FAIL[1]}" "${TIER_SKIP[1]}" \
    "${TIER_TOTAL[2]}" "${TIER_PASS[2]}" "${TIER_FAIL[2]}" "${TIER_SKIP[2]}" \
    "${TIER_TOTAL[3]}" "${TIER_PASS[3]}" "${TIER_FAIL[3]}" "${TIER_SKIP[3]}" \
    "${TIER_TOTAL[4]}" "${TIER_PASS[4]}" "${TIER_FAIL[4]}" "${TIER_SKIP[4]}" \
    "$TOTAL_COUNT" "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT" \
    "$TOTAL_DURATION"

# Display diagnostics if any failures
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "${COLOR_RED}${COLOR_BOLD}=== FAILURE DIAGNOSTICS (${FAIL_COUNT} test(s) failed) ===${COLOR_RESET}"
    if [ "${#FAILED_TEST_LOGS[@]}" -gt 0 ]; then
        for item in "${FAILED_TEST_LOGS[@]}"; do
            tname=$(echo "$item" | awk -F':::' '{print $1}')
            t_out=$(echo "$item" | awk -F':::' '{print $2}')
            t_err=$(echo "$item" | awk -F':::' '{print $3}')
            echo ""
            echo "${COLOR_BOLD}Failed: $tname${COLOR_RESET}"
            if [ -s "$t_out" ]; then
                echo "STDOUT:"
                cat "$t_out"
            fi
            if [ -s "$t_err" ]; then
                echo "STDERR:"
                cat "$t_err"
            fi
        done
    fi
    exit 1
fi

exit 0
