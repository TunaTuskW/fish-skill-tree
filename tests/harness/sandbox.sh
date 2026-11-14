#!/bin/bash
# tests/harness/sandbox.sh - Compatibility wrapper sourcing isolation.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/isolation.sh"
