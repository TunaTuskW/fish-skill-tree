#!/bin/bash
# tests/harness/verify_hook_executable.sh
# Verifies that .git/hooks/pre-commit exists and is executable
REPO_DIR="${1:-.}"
HOOK_PATH="$REPO_DIR/.git/hooks/pre-commit"

if [ ! -f "$HOOK_PATH" ]; then
    echo "Veto: .git/hooks/pre-commit does not exist" >&2
    exit 1
fi

if [ ! -x "$HOOK_PATH" ]; then
    echo "Veto: .git/hooks/pre-commit is not executable" >&2
    exit 1
fi

echo "✓ Pre-commit hook is present and executable"
exit 0
