#!/usr/bin/env python3
"""
Sensitive Data & Secret Scanner
Scans files, directories, or git diffs (via stdin) for exposed credentials, API keys, and private tokens.
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

# Comprehensive regex patterns for sensitive tokens
PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?:aws|amazon).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", "AWS Secret Key Candidate"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token (Classic)"),
    (r"github_pat_[0-9a-zA-Z_]{82}", "GitHub Fine-Grained Personal Access Token"),
    (r"sk-[a-zA-Z0-9-]{32,}", "OpenAI / Model API Key"),
    (r"sk-ant-[a-zA-Z0-9-]{32,}", "Anthropic API Key"),
    (r"AIzaSy[0-9a-zA-Z-_]{33}", "Google / Gemini API Key"),
    (r"sk_live_[0-9a-zA-Z]{24}", "Stripe Live Secret Key"),
    (r"rk_live_[0-9a-zA-Z]{24}", "Stripe Live Restricted Key"),
    (r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}", "Slack Token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Cryptographic Key"),
    (r"(?:postgres|mysql|mongodb(?:\+srv)?|redis):\/\/[^:\s]+:[^@\s]+@[^\s\/]+", "Database Connection URI with Credentials"),
    (r"(?:api[_-]?key|secret[_-]?key|auth[_-]?token|private[_-]?key)\s*[:=]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", "Hardcoded Secret Assignment"),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in PATTERNS]

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", ".codegraph",
    "dist", "build", ".next", ".cache", "brain", "conversations"
}

def scan_text(text: str, source_label: str) -> List[Tuple[int, str, str]]:
    findings = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        # Skip comment or example lines with obvious placeholders
        lower_line = line.lower()
        if (
            "your_key" in lower_line
            or "your_token" in lower_line
            or "your-api-key" in lower_line
            or "your-express-api-key" in lower_line
            or "example" in lower_line
            or "placeholder" in lower_line
            or "user:password" in lower_line
            or "user:pass@" in lower_line
            or "postgres:postgres@" in lower_line
            or "test-secret-key" in lower_line
            or "<password>" in lower_line
            or "<token>" in lower_line
        ):
            continue
        for regex, desc in COMPILED_PATTERNS:
            match = regex.search(line)
            if match:
                matched_str = match.group(0)
                # Mask secret for safe display
                if len(matched_str) > 8:
                    masked = matched_str[:4] + "..." + matched_str[-4:]
                else:
                    masked = "***"
                findings.append((idx, desc, masked))
    return findings

def scan_file(file_path: Path) -> List[Tuple[str, int, str, str]]:
    results = []
    try:
        # Skip binary files or massive files > 5MB
        if file_path.stat().st_size > 5 * 1024 * 1024:
            return results
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        file_findings = scan_text(content, str(file_path))
        for line_no, desc, masked in file_findings:
            results.append((str(file_path), line_no, desc, masked))
    except Exception:
        pass
    return results

def scan_directory(target_dir: Path) -> List[Tuple[str, int, str, str]]:
    all_findings = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            p = Path(root) / f
            # Check for suspicious file names
            lower_name = f.lower()
            if lower_name == ".env" or lower_name.endswith(".pem") or lower_name.endswith(".key") or "id_rsa" in lower_name:
                all_findings.append((str(p), 0, "Sensitive File Stored Plaintext on Disk", f))
            all_findings.extend(scan_file(p))
    return all_findings

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        diff_text = sys.stdin.read()
        findings = scan_text(diff_text, "stdin (git diff)")
        if not findings:
            print("✓ Secret scan passed: Zero sensitive tokens detected in diff.")
            sys.exit(0)
        else:
            print("🚨 ALERT: Potential sensitive token(s) detected in diff:")
            for line_no, desc, masked in findings:
                print(f"  Line {line_no}: [{desc}] -> {masked}")
            print("\nAborting: Scrub sensitive tokens before proceeding.")
            sys.exit(1)

    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    if not target.exists():
        print(f"Error: Target path {target} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning target: {target.resolve()} ...")
    if target.is_file():
        findings = scan_file(target)
    else:
        findings = scan_directory(target)

    if not findings:
        print("✓ Secret scan passed: No exposed credentials or unmasked secrets found.")
        sys.exit(0)
    else:
        print(f"🚨 ALERT: Found {len(findings)} potential security exposure(s):")
        for file_path, line_no, desc, masked in findings:
            loc = f":{line_no}" if line_no > 0 else ""
            print(f"  {file_path}{loc} -> [{desc}] {masked}")
        sys.exit(1)

if __name__ == "__main__":
    main()
