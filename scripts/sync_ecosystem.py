#!/usr/bin/env python3
"""
Production Multi-Target Ecosystem Synchronizer for fish-skill-tree
Implements bidirectional synchronization, path normalization (~/vibe/ <-> /Users/mac/vibe/),
strict Zero-Leak secret exclusion, host vault synchronization, and non-destructive dry-run mode.
"""

import os
import re
import shutil
import stat
import sys
from pathlib import Path

EXCLUDED_NAMES = {
    "auth.json",
    ".git",
    ".agents",
    ".codegraph",
    "credentials.json",
    ".quarantine",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
    "science",
    "trading-log-sync",
}

EXCLUDED_PREFIXES = (
    ".env",
    "client_secret",
    "service-account",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
)

EXCLUDED_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".keystore",
    ".jks",
    ".pyc",
)


def is_excluded(path: Path) -> bool:
    """Return True if any path segment matches Zero-Leak or metadata exclusion rules."""
    for part in path.parts:
        if part in EXCLUDED_NAMES:
            return True
        lower = part.lower()
        for pfx in EXCLUDED_PREFIXES:
            if lower.startswith(pfx):
                return True
        for sfx in EXCLUDED_SUFFIXES:
            if lower.endswith(sfx):
                return True
    return False


def normalize_path_string(text: str, direction: str) -> str:
    """Normalize duplicate slashes and translate between ~/vibe/ and /Users/mac/vibe/."""
    text = re.sub(r"~/vibe/+", "~/vibe/", text)
    text = re.sub(r"/Users/mac/vibe/+", "/Users/mac/vibe/", text)

    if direction == "repo-to-active":
        return text.replace("~/vibe/", "/Users/mac/vibe/")
    elif direction == "active-to-repo":
        return text.replace("/Users/mac/vibe/", "~/vibe/")
    return text


def sync_directories(
    src_dir: Path,
    dst_dir: Path,
    direction: str,
    dry_run: bool,
    only_existing_subdirs: bool = False,
) -> bool:
    """Synchronize directory contents with symlink loop protection and Zero-Leak filtering."""
    if not src_dir.exists():
        sys.stderr.write(f"Error: Source directory does not exist: {src_dir}\n")
        return False
    if not dst_dir.exists() and not dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)

    visited_real_dirs = set()

    for root, dirs, files in os.walk(src_dir, followlinks=False):
        try:
            real_root = os.path.realpath(root)
            if real_root in visited_real_dirs:
                dirs[:] = []
                continue
            visited_real_dirs.add(real_root)
        except OSError:
            dirs[:] = []
            continue

        rel_root = Path(root).relative_to(src_dir)

        filtered_dirs = []
        for d in dirs:
            candidate_rel = rel_root / d
            if is_excluded(candidate_rel):
                continue
            full_d = Path(root) / d
            if full_d.is_symlink():
                try:
                    target_real = os.path.realpath(full_d)
                    if target_real in visited_real_dirs or not os.path.exists(target_real):
                        continue
                except OSError:
                    continue
            if only_existing_subdirs and rel_root == Path("."):
                if not (dst_dir / d).exists():
                    continue
            filtered_dirs.append(d)
        dirs[:] = filtered_dirs

        for file in files:
            src_file = Path(root) / file
            rel_file = src_file.relative_to(src_dir)
            if is_excluded(rel_file):
                if dry_run:
                    print(f"[EXCLUDE] {rel_file} (Zero-Leak exclusion)")
                continue

            if src_file.is_symlink():
                try:
                    if not os.path.exists(os.path.realpath(src_file)):
                        continue
                except OSError:
                    continue

            dst_file = dst_dir / rel_file

            if dry_run:
                print(f"[PLAN] Copy {src_file} -> {dst_file}")
                continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            is_text = False
            content = ""
            try:
                with open(src_file, "r", encoding="utf-8") as tf:
                    content = tf.read()
                if "\x00" not in content:
                    is_text = True
            except (UnicodeDecodeError, OSError):
                is_text = False

            if is_text:
                new_content = normalize_path_string(content, direction)
                with open(dst_file, "w", encoding="utf-8") as out_f:
                    out_f.write(new_content)
                try:
                    src_mode = src_file.stat().st_mode
                    if src_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                        os.chmod(dst_file, src_mode)
                except OSError:
                    pass
            else:
                shutil.copy2(src_file, dst_file)

    return True


def main():
    dry_run = False
    host_sync = False
    direction = None
    repo_dir = None
    active_dir = None
    vault_dir = None

    args = sys.argv[1:]
    idx = 0
    while idx < len(args):
        a = args[idx]
        if a in ("--help", "-h"):
            print(
                "Usage: sync_ecosystem.py [--dry-run] [--host-sync] "
                "--direction <repo-to-active|active-to-repo|both> "
                "[--repo-dir <path>] [--active-dir <path>] [--vault-dir <path>]"
            )
            sys.exit(0)
        elif a == "--dry-run":
            dry_run = True
            idx += 1
        elif a == "--host-sync":
            host_sync = True
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
        sys.stderr.write(
            f"Error: Invalid direction '{direction}'. "
            "Must be 'repo-to-active', 'active-to-repo', or 'both'.\n"
        )
        sys.exit(1)

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
        if (repo_dir / "[plugin]").exists():
            success &= sync_directories(
                repo_dir / "[plugin]",
                active_dir / "plugins",
                "repo-to-active",
                dry_run,
            )
        if (repo_dir / "[skill]").exists():
            success &= sync_directories(
                repo_dir / "[skill]",
                active_dir / "skills",
                "repo-to-active",
                dry_run,
                only_existing_subdirs=host_sync,
            )
            if host_sync and (vault_dir / "skills").exists():
                success &= sync_directories(
                    repo_dir / "[skill]",
                    vault_dir / "skills",
                    "repo-to-active",
                    dry_run,
                )

    if direction in ("active-to-repo", "both"):
        print(f"=== Syncing active -> repo (dry_run={dry_run}) ===")
        if (active_dir / "plugins").exists():
            success &= sync_directories(
                active_dir / "plugins",
                repo_dir / "[plugin]",
                "active-to-repo",
                dry_run,
            )
        if (active_dir / "skills").exists():
            success &= sync_directories(
                active_dir / "skills",
                repo_dir / "[skill]",
                "active-to-repo",
                dry_run,
            )

    if not success:
        sys.exit(1)

    print("✓ Ecosystem synchronization completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
