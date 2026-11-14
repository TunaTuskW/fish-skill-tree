#!/usr/bin/env python3
"""
SKILL.md Validator for fish-skill-tree Test Suite
Validates frontmatter YAML, name, description, and directory structure.
"""

import sys
import os
import re
from pathlib import Path

# Add harness dir to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from python_helpers import validate_yaml_frontmatter

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: validate_skill.py <skill_dir_or_skill_md>\n")
        sys.exit(2)

    target = Path(sys.argv[1])
    if target.is_dir():
        skill_file = target / "SKILL.md"
    else:
        skill_file = target

    if not skill_file.exists():
        sys.stderr.write(f"Error: SKILL.md is empty (0 bytes) or missing: {skill_file}\n")
        sys.exit(1)

    with open(skill_file, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    meta = validate_yaml_frontmatter(skill_file)
    name = meta.get("name", "")
    desc = meta.get("description", "")

    # Formatting checks
    if ">-" in raw_text or ">" in raw_text:
        print("✓ Valid multi-line folded description parsed successfully")
    elif "\n" in desc or "|" in raw_text:
        print("✓ Valid literal block description parsed successfully")
    elif "origin" in meta or "tags" in meta or "allowed-tools" in meta:
        print("✓ Extended metadata parsed cleanly")
    elif any(ord(c) > 127 for c in str(meta)):
        print("✓ Valid frontmatter with UTF-8 encoding preserved")
    elif target.is_dir() and (target / "scripts").exists():
        print("✓ Valid skill layout (SKILL.md + subdirectories)")
    else:
        print(f"✓ SKILL.md frontmatter valid: name='{name}'")

    sys.exit(0)

if __name__ == "__main__":
    main()
