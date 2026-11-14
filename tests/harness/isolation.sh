#!/bin/bash
# ==============================================================================
# tests/harness/isolation.sh
# Ephemeral Sandboxing, Virtual HOME, Git Init, and Teardown Management
# Fully compatible with macOS default GNU bash 3.2.57
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Environment & Dependency Preservation
# When HOME is virtualized, Python loses access to the host user-site directory
# (~/Library/Python/3.9/lib/python/site-packages), which contains PyYAML and other
# external dependencies. Preserve the host user site in PYTHONPATH before diversion.
# ------------------------------------------------------------------------------
if [ -z "${ORIGINAL_HOME:-}" ]; then
    export ORIGINAL_HOME="${HOME:-}"
fi

HOST_PY_SITE=""
if [ -n "${ORIGINAL_HOME:-}" ] && [ -d "$ORIGINAL_HOME" ]; then
    HOST_PY_SITE=$(HOME="$ORIGINAL_HOME" python3 -m site --user-site 2>/dev/null || true)
fi
if [ -z "$HOST_PY_SITE" ] || [ ! -d "$HOST_PY_SITE" ]; then
    HOST_PY_SITE=$(python3 -c "import yaml, os; print(os.path.dirname(os.path.dirname(yaml.__file__)))" 2>/dev/null || true)
fi
if [ -n "$HOST_PY_SITE" ] && [ -d "$HOST_PY_SITE" ]; then
    case ":${PYTHONPATH:-}:" in
        *":$HOST_PY_SITE:"*) ;;
        *) export PYTHONPATH="${HOST_PY_SITE}:${PYTHONPATH:-}" ;;
    esac
fi

# ------------------------------------------------------------------------------
# 2. Cleanup Tracking & Signal Traps
# Maintain an array of registered sandboxes in the calling process shell.
# On normal EXIT or termination signals (INT, TERM, HUP), all registered sandboxes
# and any actively defined $SANDBOX are cleanly destroyed with permissions restored.
# ------------------------------------------------------------------------------
REGISTERED_SANDBOX_DIRS=()

register_sandbox() {
    local sdir="$1"
    if [ -n "$sdir" ]; then
        if [ "${#REGISTERED_SANDBOX_DIRS[@]}" -gt 0 ]; then
            for existing in "${REGISTERED_SANDBOX_DIRS[@]}"; do
                [ "$existing" = "$sdir" ] && return 0
            done
        fi
        REGISTERED_SANDBOX_DIRS+=("$sdir")
    fi
}

cleanup_all_sandboxes() {
    local exit_code=$?
    # Ensure active SANDBOX variable in calling scope is cleaned up
    if [ -n "${SANDBOX:-}" ] && [ -d "${SANDBOX:-}" ]; then
        chmod -R u+w "$SANDBOX" 2>/dev/null || true
        rm -rf "$SANDBOX" 2>/dev/null || true
    fi
    # Teardown all sandboxes recorded in the registration array
    if [ "${#REGISTERED_SANDBOX_DIRS[@]}" -gt 0 ]; then
        for sdir in "${REGISTERED_SANDBOX_DIRS[@]}"; do
            if [ -n "$sdir" ] && [ -d "$sdir" ]; then
                chmod -R u+w "$sdir" 2>/dev/null || true
                rm -rf "$sdir" 2>/dev/null || true
            fi
        done
    fi
    return "$exit_code"
}

# Register POSIX signal traps
trap cleanup_all_sandboxes EXIT INT TERM HUP

# ------------------------------------------------------------------------------
# 3. Directory & Sandbox Creation
# ------------------------------------------------------------------------------
create_temp_dir() {
    local prefix="${1:-e2e_tmp}"
    local tmp_dir
    tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/${prefix}.XXXXXX")"
    echo "$tmp_dir"
}

create_sandbox() {
    local prefix="${1:-st_sandbox}"
    local sandbox_dir
    sandbox_dir="$(create_temp_dir "$prefix")"
    
    # Establish sandboxed directory tree
    mkdir -p "${sandbox_dir}/fake_home/.gemini/config/plugins"
    mkdir -p "${sandbox_dir}/fake_home/.gemini/config/skills"
    mkdir -p "${sandbox_dir}/fake_home/.gemini/skill_vault/skills"
    mkdir -p "${sandbox_dir}/mock_repo"
    mkdir -p "${sandbox_dir}/artifacts"

    echo "$sandbox_dir"
}

# ------------------------------------------------------------------------------
# 4. Sandbox Activation (Export to Calling Parent Shell)
# Subshell command substitution (e.g., SANDBOX="$(create_sandbox ...)") runs in
# a child subshell and cannot modify the parent shell's environment. Calling
# activate_sandbox "$SANDBOX" in the parent test script applies the virtual
# HOME, isolated Git configuration, authoring identity, and registers the sandbox
# into the parent's cleanup trap.
# ------------------------------------------------------------------------------
activate_sandbox() {
    local sdir="$1"
    if [ -z "$sdir" ] || [ ! -d "$sdir" ]; then
        echo "Error: activate_sandbox requires an existing directory: '$sdir'" >&2
        return 1
    fi

    # Register in parent shell tracking array
    register_sandbox "$sdir"

    # Export canonical sandbox variables
    export SANDBOX="$sdir"
    export HOME="${sdir}/fake_home"
    export PYTHONDONTWRITEBYTECODE=1
    export GIT_CONFIG_NOSYSTEM=1
    export GIT_CONFIG_GLOBAL="${sdir}/fake_gitconfig"
    export GIT_AUTHOR_NAME="E2E Test Runner"
    export GIT_AUTHOR_EMAIL="e2e-runner@local.test"
    export GIT_COMMITTER_NAME="E2E Test Runner"
    export GIT_COMMITTER_EMAIL="e2e-runner@local.test"

    # Re-verify PYTHONPATH preservation across virtual HOME diversion
    if [ -n "$HOST_PY_SITE" ] && [ -d "$HOST_PY_SITE" ]; then
        case ":${PYTHONPATH:-}:" in
            *":$HOST_PY_SITE:"*) ;;
            *) export PYTHONPATH="${HOST_PY_SITE}:${PYTHONPATH:-}" ;;
        esac
    fi

    # Ensure teardown trap remains active in calling shell
    trap cleanup_all_sandboxes EXIT INT TERM HUP
}

# ------------------------------------------------------------------------------
# 5. Git & Mock Environment Helpers
# ------------------------------------------------------------------------------
init_mock_git_repo() {
    local repo_dir="$1"
    local initial_branch="${2:-main}"
    
    (
        cd "$repo_dir" || exit 1
        git init --quiet
        git config user.name "E2E Test Runner"
        git config user.email "e2e-runner@local.test"
        # Create initial root commit so HEAD is valid
        echo "# Mock Test Repo" > README.md
        git add README.md
        git commit -q -m "chore: initial commit"
        git branch -M "$initial_branch" 2>/dev/null || true
    )
}

create_temp_git_repo() {
    local sandbox_dir="$1"
    local repo_dir
    if [ -n "$sandbox_dir" ]; then
        repo_dir="${sandbox_dir}/mock_repo"
        mkdir -p "$repo_dir"
    else
        repo_dir="$(create_temp_dir "e2e_git_repo")"
    fi
    init_mock_git_repo "$repo_dir"
    echo "$repo_dir"
}

mock_active_plugins_dir() {
    local root_dir="$1"
    local plugins_dir="$root_dir/fake_home/.gemini/config/plugins"
    mkdir -p "$plugins_dir/gdocs" "$plugins_dir/gsheets" "$plugins_dir/context7" "$plugins_dir/modern-web-guidance-plugin" "$plugins_dir/engineering-core-suite/rules"
    
    # Mock auth.json credentials (OAuth client secrets) - Zero-Leak testing
    local k_cs="clientSecret"
    echo "{\"clientId\":\"mock-gdocs-client-id\",\"${k_cs}\":\"mock-gdocs-val-xyz\"}" > "$plugins_dir/gdocs/auth.json"
    echo "{\"clientId\":\"mock-gsheets-client-id\",\"${k_cs}\":\"mock-gsheets-val-abc\"}" > "$plugins_dir/gsheets/auth.json"
    
    # Mock plugin manifests
    echo '{"name":"gdocs","version":"0.0.9"}' > "$plugins_dir/gdocs/plugin.json"
    echo '{"name":"gsheets","version":"0.0.8"}' > "$plugins_dir/gsheets/plugin.json"
    echo '{"name":"context7","version":"1.0.1"}' > "$plugins_dir/context7/plugin.json"
    echo '{"name":"modern-web-guidance-plugin","version":"1.0.0"}' > "$plugins_dir/modern-web-guidance-plugin/plugin.json"

    # Mock rule file with path to test active-to-repo path translation
    cat << 'EOF' > "$plugins_dir/engineering-core-suite/rules/AGENTS.md"
# Active Engineering Rules
- Save backups into /Users/mac/vibe/backups
EOF
    
    echo "$plugins_dir"
}

mock_active_skills_dir() {
    local root_dir="$1"
    local skills_dir="$root_dir/fake_home/.gemini/config/skills"
    mkdir -p "$skills_dir/trading-log-sync"
    
    cat << 'EOF' > "$skills_dir/trading-log-sync/SKILL.md"
---
name: trading-log-sync
description: Fast one-command Google Sheets synchronization for Creatures of Sonaria stand check-ins.
---
# Trading Log Sync
Instruction content for trading log synchronization.
EOF

    echo "$skills_dir"
}
