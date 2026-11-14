#!/bin/bash
# ==============================================================================
# tests/harness/reporters.sh
# Terminal Formatters, ANSI Color Palette, and Summary Table Emitters
# Fully compatible with macOS default GNU bash 3.2.57
# ==============================================================================

init_colors() {
    local enable="${1:-1}"
    if [ "$enable" -eq 1 ]; then
        COLOR_RED=$'\033[0;31m'
        COLOR_GREEN=$'\033[0;32m'
        COLOR_YELLOW=$'\033[0;33m'
        COLOR_BLUE=$'\033[0;34m'
        COLOR_CYAN=$'\033[0;36m'
        COLOR_BOLD=$'\033[1m'
        COLOR_RESET=$'\033[0m'
    else
        COLOR_RED=""
        COLOR_GREEN=""
        COLOR_YELLOW=""
        COLOR_BLUE=""
        COLOR_CYAN=""
        COLOR_BOLD=""
        COLOR_RESET=""
    fi
}

log_pass() {
    local msg="$1"
    echo "  ${COLOR_GREEN}[PASS]${COLOR_RESET} $msg"
}

log_fail() {
    local msg="$1"
    echo "  ${COLOR_RED}[FAIL]${COLOR_RESET} $msg" >&2
}

log_skip() {
    local msg="$1"
    echo "  ${COLOR_YELLOW}[SKIP]${COLOR_RESET} $msg"
}

print_banner() {
    local repo_root="$1"
    echo "${COLOR_CYAN}${COLOR_BOLD}=====================================================================${COLOR_RESET}"
    echo "${COLOR_CYAN}${COLOR_BOLD}       fish-skill-tree E2E Test Suite (Opaque-Box Verification)       ${COLOR_RESET}"
    echo "${COLOR_CYAN}${COLOR_BOLD}=====================================================================${COLOR_RESET}"
    echo "  OS Platform:   $(uname -s) $(uname -m) ($(sw_vers -productVersion 2>/dev/null || echo 'macOS'))"
    echo "  Shell:         Bash ${BASH_VERSION}"
    echo "  Python:        $(python3 --version 2>&1)"
    echo "  Git:           $(git --version 2>&1)"
    echo "  Workspace:     $repo_root"
    echo "${COLOR_CYAN}---------------------------------------------------------------------${COLOR_RESET}"
}

print_summary_table() {
    local t1_tot="$1" t1_pas="$2" t1_fai="$3" t1_skp="$4"
    local t2_tot="$5" t2_pas="$6" t2_fai="$7" t2_skp="$8"
    local t3_tot="$9" t3_pas="${10}" t3_fai="${11}" t3_skp="${12}"
    local t4_tot="${13}" t4_pas="${14}" t4_fai="${15}" t4_skp="${16}"
    local tot="${17}" pas="${18}" fai="${19}" skp="${20}"
    local dur="${21}"

    echo ""
    echo "${COLOR_BOLD}+-------------------------------------------------------------------+${COLOR_RESET}"
    printf "${COLOR_BOLD}| %-35s | %5s | %5s | %5s | %4s |${COLOR_RESET}\n" "Test Suite Tier" "Total" "Pass" "Fail" "Skip"
    echo "${COLOR_BOLD}+-------------------------------------------------------------------+${COLOR_RESET}"
    printf "| %-35s | %5d | %5d | %5d | %4d |\n" "Tier 1: Feature Coverage (F1-F5)" "$t1_tot" "$t1_pas" "$t1_fai" "$t1_skp"
    printf "| %-35s | %5d | %5d | %5d | %4d |\n" "Tier 2: Boundary & Corner Cases" "$t2_tot" "$t2_pas" "$t2_fai" "$t2_skp"
    printf "| %-35s | %5d | %5d | %5d | %4d |\n" "Tier 3: Cross-Feature Interactions" "$t3_tot" "$t3_pas" "$t3_fai" "$t3_skp"
    printf "| %-35s | %5d | %5d | %5d | %4d |\n" "Tier 4: Real-World Workloads" "$t4_tot" "$t4_pas" "$t4_fai" "$t4_skp"
    echo "${COLOR_BOLD}+-------------------------------------------------------------------+${COLOR_RESET}"
    printf "${COLOR_BOLD}| %-35s | %5d | %5d | %5d | %4d |${COLOR_RESET}\n" "Grand Total" "$tot" "$pas" "$fai" "$skp"
    echo "${COLOR_BOLD}+-------------------------------------------------------------------+${COLOR_RESET}"
    
    if [ "$fai" -eq 0 ]; then
        echo "${COLOR_GREEN}${COLOR_BOLD}Elapsed: $dur | Result: ALL TESTS PASSED (${pas}/${tot})${COLOR_RESET}"
    else
        echo "${COLOR_RED}${COLOR_BOLD}Elapsed: $dur | Result: FAILED (${fai} failure(s) out of ${tot})${COLOR_RESET}"
    fi
}
