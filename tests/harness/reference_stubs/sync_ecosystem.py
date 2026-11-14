#!/usr/bin/env python3
"""
Reference Implementation of Multi-Target Ecosystem Synchronizer for fish-skill-tree
Implements: bidirectional sync, path translation, strict secret exclusion, and non-destructive dry-run.
"""

import sys
import os
import re
import shutil
from pathlib import Path

EXCLUDED_NAMES = {
    "auth.json", ".git", ".agents", ".codegraph", "credentials.json", ".quarantine"
}

EXCLUDED_PREFIXES = (
    ".env", "client_secret"
)

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDED_NAMES:
            return True
        for pfx in EXCLUDED_PREFIXES:
            if part.startswith(pfx):
                return True
    return False

def normalize_path_string(text: str, direction: str) -> str:
    # First normalize duplicate slashes in ~/vibe/ and /Users/mac/vibe/
    text = re.sub(r'~/vibe/+', '~/vibe/', text)
    text = re.sub(r'/Users/mac/vibe/+', '/Users/mac/vibe/', text)

    if direction == "repo-to-active":
        return text.replace("~/vibe/", "/Users/mac/vibe/")
    elif direction == "active-to-repo":
        return text.replace("/Users/mac/vibe/", "~/vibe/")
    return text

def sync_directories(src_dir: Path, dst_dir: Path, direction: str, dry_run: bool):
    if not src_dir.exists():
        sys.stderr.write(f"Error: Source directory does not exist: {src_dir}\n")
        return False
    if not dst_dir.exists() and not dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(src_dir):
        # Prevent recursing into circular symlinks or excluded dirs
        rel_root = Path(root).relative_to(src_dir)
        dirs[:] = [d for d in dirs if not is_excluded(rel_root / d)]

        for file in files:
            src_file = Path(root) / file
            rel_file = src_file.relative_to(src_dir)
            if is_excluded(rel_file):
                if dry_run:
                    print(f"[EXCLUDE] {rel_file} (Zero-Leak exclusion)")
                continue

            dst_file = dst_dir / rel_file

            if dry_run:
                print(f"[PLAN] Copy {src_file} -> {dst_file}")
                continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # Check if file is text or binary
            is_text = False
            try:
                with open(src_file, "r", encoding="utf-8") as tf:
                    content = tf.read()
                is_text = True
            except (UnicodeDecodeError, Exception):
                is_text = False

            if is_text:
                new_content = normalize_path_string(content, direction)
                with open(dst_file, "w", encoding="utf-8") as out_f:
                    out_f.write(new_content)
            else:
                shutil.copy2(src_file, dst_file)

    return True

def main():
    dry_run = False
    direction = None
    repo_dir = None
    active_dir = None
    vault_dir = None

    args = sys.argv[1:]
    idx = 0
    while idx < len(args):
        a = args[idx]
        if a == "--dry-run":
            dry_run = True
            idx += 1
        elif a == "--direction" and idx + 1 < len(args):
            direction = args[idx + 1]
            idx += 2
        elif a == "--repo-dir" and idx + 1 < len(args):
            repo_dir = Path(args[idx + 1])
            idx += 2
        elif a == "--active-dir" and idx + 1 < len(args):
            active_dir = Path(args[idx + 1])
            idx += 2
        elif a == "--vault-dir" and idx + 1 < len(args):
            vault_dir = Path(args[idx + 1])
            idx += 2
        else:
            sys.stderr.write(f"Error: Unknown argument '{a}'\n")
            sys.exit(1)

    if direction not in ("repo-to-active", "active-to-repo", "both"):
        sys.stderr.write(f"Error: Invalid direction '{direction}'. Must be 'repo-to-active', 'active-to-repo', or 'both'.\n")
        sys.exit(1)

    # Defaults
    home = Path(os.environ.get("HOME", str(Path.home())))
    if repo_dir is None:
        repo_dir = Path.cwd()
    if active_dir is None:
        active_dir = home / ".gemini" / "config"
    if vault_dir is None:
        vault_dir = home / ".gemini" / "skill_vault"

    if not repo_dir.exists() and not dry_run:
        sys.stderr.write(f"Error: Destination directory does not exist: {repo_dir}\n")
        sys.exit(1)
    if not active_dir.exists() and not dry_run:
        sys.stderr.write(f"Error: Destination directory does not exist: {active_dir}\n")
        sys.exit(1)

    success = True
    if direction in ("repo-to-active", "both"):
        print(f"=== Syncing repo -> active (dry_run={dry_run}) ===")
        # Sync plugins
        if (repo_dir / "[plugin]").exists():
            success &= sync_directories(repo_dir / "[plugin]", active_dir / "plugins", "repo-to-active", dry_run)
        # Sync skills
        if (repo_dir / "[skill]").exists():
            success &= sync_directories(repo_dir / "[skill]", active_dir / "skills", "repo-to-active", dry_run)

    if direction in ("active-to-repo", "both"):
        print(f"=== Syncing active -> repo (dry_run={dry_run}) ===")
        if (active_dir / "plugins").exists():
            success &= sync_directories(active_dir / "plugins", repo_dir / "[plugin]", "active-to-repo", dry_run)
        if (active_dir / "skills").exists():
            success &= sync_directories(active_dir / "skills", repo_dir / "[skill]", "active-to-repo", dry_run)

    if not success:
        sys.exit(1)

    print("✓ Ecosystem synchronization completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
