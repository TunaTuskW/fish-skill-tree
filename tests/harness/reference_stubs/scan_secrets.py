#!/usr/bin/env python3
"""
Reference Implementation of Sensitive Data Scanner for fish-skill-tree
Implements: --staged, --stdin, Shannon entropy, JSON OAuth inspection, and token-level masking.
"""

import sys
import os
import re
import math
import json
import subprocess
from pathlib import Path

# Common high-severity credential patterns
SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r'\b(AKIA[0-9A-Z]{16})\b')),
    ("GitHub Personal Access Token", re.compile(r'\b(ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})\b')),
    ("OpenAI API Key", re.compile(r'\b(sk-[a-zA-Z0-9-]{32,})\b')),
    ("Anthropic API Key", re.compile(r'\b(sk-ant-[a-zA-Z0-9-]{32,})\b')),
    ("Google / Gemini API Key", re.compile(r'\b(AIzaSy[0-9a-zA-Z-_]{33})\b')),
    ("Stripe Live Secret Key", re.compile(r'\b([rs]k_live_[0-9a-zA-Z]{24})\b')),
    ("Slack Token", re.compile(r'\b(xox[baprs]-[0-9a-zA-Z-]{10,48})\b')),
    ("Private Key Header", re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ("Database Connection String", re.compile(r'(?:postgres|mysql|mongodb(?:\+srv)?|redis):\/\/[^:\s]+:[^@\s]+@[^\s\/]+')),
]

JSON_OAUTH_KEYS = {"clientsecret", "client_secret", "private_key", "accesstoken", "refreshtoken"}

PLACEHOLDERS = [
    "your_api_key_here", "your_token", "placeholder", "fake_key", "dummy_token"
]

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    counts = {}
    for c in text:
        counts[c] = counts.get(c, 0) + 1
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return secret[:4] + "..." + secret[-4:]

def scan_text_lines(lines, source_label: str):
    findings = []
    for line_num, line in enumerate(lines, 1):
        # Diff addition check
        if source_label.startswith("diff:"):
            if line.startswith("+++"):
                continue
            if not line.startswith("+"):
                continue
            line = line[1:]

        # Token-level placeholder filtering
        lower_line = line.lower()
        is_pure_placeholder = False
        for ph in PLACEHOLDERS:
            if ph in lower_line and not any(p[1].search(line) for p in SECRET_PATTERNS):
                is_pure_placeholder = True
                break
        if is_pure_placeholder:
            continue

        # 1. Regex patterns
        for rule_name, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                raw = match.group(0)
                findings.append((source_label, line_num, rule_name, mask_secret(raw)))

        # 2. JSON OAuth keys
        if "{" in line or ":" in line:
            for k in JSON_OAUTH_KEYS:
                json_pat = re.compile(rf'["\']{k}["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
                m = json_pat.search(line)
                if m:
                    val = m.group(1)
                    if not any(ph in val.lower() for ph in PLACEHOLDERS):
                        findings.append((source_label, line_num, f"JSON OAuth Key ({k})", mask_secret(val)))

        # 3. High entropy tokens (H > 4.5, length >= 20)
        candidate_tokens = re.findall(r'["\']([a-zA-Z0-9_\-\.\/+]{20,})["\']', line)
        for cand in candidate_tokens:
            if not set(cand.lower()).issubset(set("0123456789abcdef")):
                h = calculate_entropy(cand)
                if h > 4.5:
                    findings.append((source_label, line_num, f"High Entropy Secret (H={h:.2f} > 4.5)", mask_secret(cand)))

    return findings

def scan_file(file_path: Path):
    if not file_path.exists():
        sys.stderr.write(f"Error: Target path {file_path} does not exist.\n")
        return None
    if file_path.is_file():
        # Skip files > 5MB
        if file_path.stat().st_size > 5 * 1024 * 1024:
            return []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            return scan_text_lines(lines, str(file_path))
        except Exception:
            return []
    elif file_path.is_dir():
        all_findings = []
        for root, dirs, files in os.walk(file_path):
            # Skip ignored dirs
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__")]
            for file in files:
                fp = Path(root) / file
                res = scan_file(fp)
                if res:
                    all_findings.extend(res)
        return all_findings
    return []

def main():
    if len(sys.argv) < 2:
        target = "."
    else:
        target = sys.argv[1]

    findings = []

    if target == "--staged":
        try:
            res = subprocess.run(["git", "diff", "--cached"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            lines = res.stdout.splitlines()
            findings = scan_text_lines(lines, "diff:staged")
        except Exception as e:
            sys.stderr.write(f"Error running git diff --cached: {e}\n")
            sys.exit(1)

    elif target == "--stdin":
        lines = sys.stdin.read().splitlines()
        findings = scan_text_lines(lines, "diff:stdin")

    else:
        path = Path(target)
        if not path.exists():
            sys.stderr.write(f"Error: Target path {target} does not exist.\n")
            sys.exit(1)
        res = scan_file(path)
        if res is None:
            sys.exit(1)
        findings = res

    if findings:
        print("ALERT: Security exposure detected! Plaintext credentials found:")
        for src, lnum, rule, masked in findings:
            print(f"  {src}:{lnum} -> [{rule}] {masked}")
        sys.exit(1)
    else:
        print("✓ Secret scan passed: No exposed credentials found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
