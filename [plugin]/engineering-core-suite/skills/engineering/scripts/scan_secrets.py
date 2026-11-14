#!/usr/bin/env python3
"""
Sensitive Data & Secret Scanner (Zero-Leak Hardened)
Scans files, directories, or staged git diffs for exposed credentials,
API keys, OAuth tokens, private keys, and high-entropy secrets.
"""

import sys
import os
import re
import math
import subprocess
from pathlib import Path
from collections import Counter
from typing import List, Tuple

# Comprehensive regex patterns for sensitive tokens
PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?:aws|amazon).{0,20}['\"][0-9a-zA-Z/+]{40}['\"]", "AWS Secret Key Candidate"),
    (r"ghp_[0-9a-zA-Z]{36}", "GitHub Personal Access Token (Classic)"),
    (r"github_pat_[0-9a-zA-Z_]{82}", "GitHub Fine-Grained Personal Access Token"),
    (r"sk-[a-zA-Z0-9-]{32,}", "OpenAI / Model API Key"),
    (r"sk-ant-[a-zA-Z0-9-]{32,}", "Anthropic API Key"),
    (r"AIzaSy[0-9a-zA-Z-_]{33,}", "Google / Gemini API Key"),
    (r"GOCSPX-[a-zA-Z0-9_-]{24,34}", "Google OAuth Client Secret"),
    (r"ya29\.[0-9a-zA-Z_-]{25,}", "Google OAuth Access Token"),
    (r"1\/\/[0-9a-zA-Z_-]{25,}", "Google OAuth Refresh Token"),
    (r"sk_live_[0-9a-zA-Z]{24}", "Stripe Live Secret Key"),
    (r"rk_live_[0-9a-zA-Z]{24}", "Stripe Live Restricted Key"),
    (r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}", "Slack Token"),
    (r"hf_[a-zA-Z0-9]{34}", "HuggingFace Access Token"),
    (r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "JSON Web Token (JWT)"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Cryptographic Key"),
    (r"(?:postgres|mysql|mongodb(?:\+srv)?|redis):\/\/[^:\s]+:[^@\s]+@[^\s\/]+", "Database Connection URI with Credentials"),
    (r"""(?i)["']?(?:client[_-]?secret|private[_-]?key|access[_-]?token|refresh[_-]?token)["']?\s*[:=]\s*["']([^"'\r\n]{10,})["']""", "JSON OAuth / Private Key Secret"),
    (r"""(?i)["']?(?:api[_-]?key|secret[_-]?key|auth[_-]?token)["']?\s*[:=]\s*["']([a-zA-Z0-9_\-\.\/+]{16,})["']""", "Generic Secret Assignment"),
]

COMPILED_PATTERNS = [(re.compile(p), desc) for p, desc in PATTERNS]

IGNORE_DIRS = {
    ".git", ".agents", "node_modules", "venv", ".venv", "__pycache__", ".codegraph",
    "dist", "build", ".next", ".cache", "brain", "conversations"
}

SENSITIVE_FILENAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ecdsa", "id_ed25519", "auth.json", "credentials.json"
}

DB_URI_RE = re.compile(
    r"(?:postgres|mysql|mongodb(?:\+srv)?|redis):\/\/([^:\s]+):([^@\s]+)@([^\s\/:]+)(?::\d+)?(?:\/[^\s]*)?",
    re.IGNORECASE
)

HUNK_RE = re.compile(r"^@@\s+-[0-9]+(?:,[0-9]+)?\s+\+([0-9]+)(?:,[0-9]+)?\s+@@")


def mask_token(token: str) -> str:
    """Mask secret token for terminal output to prevent leakage."""
    if len(token) > 8:
        return token[:4] + "..." + token[-4:]
    return "***"


def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def is_placeholder_token(token: str) -> bool:
    """
    Evaluate whether a candidate token itself is an intentional mock/placeholder.
    Never evaluates external comments or full lines.
    """
    if not token:
        return True
    lower = token.lower().strip()

    # Bracketed / Template placeholders: <...>, [...], ${...}, {{...}}, %...%
    if (lower.startswith("<") and lower.endswith(">")) or \
       (lower.startswith("[") and lower.endswith("]")) or \
       (lower.startswith("${") and lower.endswith("}")) or \
       (lower.startswith("{{") and lower.endswith("}}")) or \
       (lower.startswith("%") and lower.endswith("%")):
        return True

    if "process.env." in lower or "os.environ" in lower:
        return True

    # Exact known mock tokens
    EXACT_MOCKS = {
        "wjalrxutnfemi/k7mdeng/bpxrficyexamplekey",
        "ghp_000000000000000000000000000000000000",
        "00000000000000000000000000000000",
        "12345678901234567890123456789012",
        "placeholder", "your_key", "your_token", "your-api-key", "your_client_secret",
        "your_secret", "your-client-secret", "your-secret-key", "fake", "dummy", "test",
        "xxx", "todo", "change_me", "changeme", "none", "null", "undefined",
        "example_key", "example_secret", "example_token", "test-secret-key",
        "user:password", "user:pass", "postgres:postgres", "client_secret_here"
    }
    if lower in EXACT_MOCKS:
        return True

    # If it is a formatted AWS access key ID, do not treat as placeholder
    if lower.startswith("akia") and len(lower) == 20:
        return False

    # Obvious placeholder keywords inside the token itself
    KEYWORD_MOCKS = [
        "example", "placeholder", "fake", "dummy", "sample",
        "your_key", "your-key", "your_token", "your-token",
        "your-api-key", "your_api_key", "your-express-api-key",
        "your-client-secret", "your_client_secret",
        "test-secret-key", "test_secret_key", "changeme",
        "<password>", "<token>", "<api_key>", "<secret>"
    ]
    if any(k in lower for k in KEYWORD_MOCKS):
        return True

    # Prefixes indicating placeholders
    PLACEHOLDER_PREFIXES = ("your_", "your-", "insert_", "insert-", "my-", "test_")
    if any(lower.startswith(pfx) for pfx in PLACEHOLDER_PREFIXES):
        return True

    # Composed entirely of repetition / mask characters
    if set(lower) <= {"x", "-", "_", "*", ".", "0"}:
        return True

    # Low character diversity after stripping known fixed prefixes
    core = re.sub(
        r"^(sk-ant-[a-zA-Z0-9]+-|sk-proj-|sk-|ghp_|github_pat_|aizasy|akia|gocspx-|ya29\.|rk_live_|sk_live_)",
        "", lower
    )
    if len(core) >= 8 and len(set(core)) <= 2:
        return True

    return False


def is_mock_db_uri(uri: str) -> bool:
    """Determine if a database URI uses safe local development / placeholder credentials."""
    m = DB_URI_RE.search(uri)
    if not m:
        return False
    user, password, host = m.group(1).lower(), m.group(2).lower(), m.group(3).lower()
    mock_users = {"user", "username", "postgres", "root", "admin", "test", "myuser", "dbuser"}
    mock_passwords = {"password", "pass", "postgres", "root", "admin", "test", "secret", "<password>", "mypassword"}
    mock_hosts = {"localhost", "127.0.0.1", "db", "database", "postgres", "mysql", "redis", "mongo", "mongodb", "example.com"}

    if (user in mock_users and password in mock_passwords) or any(k in password for k in ["example", "placeholder", "dummy", "test"]):
        if host in mock_hosts or "example" in host:
            return True
    return False


def is_high_entropy_secret(token: str) -> bool:
    """Detect unlabelled high-entropy candidate tokens (Shannon H > 4.5)."""
    if len(token) < 20 or len(token) > 120:
        return False
    # Exclude URLs
    if token.startswith("http://") or token.startswith("https://") or token.startswith("//"):
        return False
    # Exclude pure hex commit SHAs and checksums (max entropy 4.0)
    if set(token.lower()).issubset(set("0123456789abcdef")):
        return False
    # Exclude paths
    if "/" in token and ("." in token or token.startswith("/")):
        return False
    # Exclude obvious single-case alpha words
    if token.isalpha() and (token.islower() or token.isupper()):
        return False
    if is_placeholder_token(token):
        return False

    return shannon_entropy(token) > 4.5


def scan_line(line: str) -> List[Tuple[str, str]]:
    """Scan a single line of text. Returns List[(description, masked_token)]."""
    findings = []
    seen_tokens = set()

    # 1. Regex Pattern Matches
    for regex, desc in COMPILED_PATTERNS:
        for match in regex.finditer(line):
            matched_str = match.group(1) if match.groups() else match.group(0)

            # Special case for DB URIs
            if "Database Connection URI" in desc:
                if is_mock_db_uri(matched_str):
                    continue
            elif is_placeholder_token(matched_str):
                continue

            if matched_str not in seen_tokens:
                seen_tokens.add(matched_str)
                findings.append((desc, mask_token(matched_str)))

    # 2. Shannon Entropy Inspection for continuous quoted strings or tokens
    quoted_tokens = re.findall(r"""['"]([a-zA-Z0-9_\-\.\/+]{20,})['"]""", line)
    assigned_tokens = re.findall(
        r"""(?i)(?:key|secret|token|password|auth|credential|api|private)[\w-]*\s*[:=]\s*['"]?([a-zA-Z0-9_\-\.\/+]{20,})['"]?""",
        line
    )
    for q in quoted_tokens + assigned_tokens:
        if is_high_entropy_secret(q):
            if q not in seen_tokens:
                seen_tokens.add(q)
                h = shannon_entropy(q)
                findings.append((f"High-Entropy Secret Candidate (Shannon H={h:.2f})", mask_token(q)))

    return findings


def scan_text(text: str, source_label: str = "") -> List[Tuple[int, str, str]]:
    """Scan arbitrary multi-line text and return findings with 1-based line numbers."""
    findings = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        line_findings = scan_line(line)
        for desc, masked in line_findings:
            findings.append((idx, desc, masked))
    return findings


def parse_diff(diff_text: str) -> List[Tuple[str, int, str]]:
    """
    Parse unified diff (e.g. git diff -U0).
    Returns List[(file_path, new_file_line_no, added_content_line)].
    """
    current_file = None
    current_line = 0
    in_hunk = False
    added_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            current_file = None
            in_hunk = False
            continue
        if line.startswith("+++ "):
            if line == "+++ /dev/null":
                current_file = None
            elif line.startswith("+++ b/"):
                current_file = line[6:].strip().strip("\"")
            else:
                current_file = line[4:].strip().strip("\"")
            in_hunk = False
            continue
        if line.startswith("--- "):
            continue

        hunk_match = HUNK_RE.match(line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            in_hunk = True
            continue

        if in_hunk and current_file:
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                line_num = current_line if current_line > 0 else 1
                added_lines.append((current_file, line_num, content))
                current_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                pass  # Deleted line: do not scan and do not increment new line counter
            elif line.startswith(" "):
                current_line += 1

    return added_lines


def scan_staged_changes() -> List[Tuple[str, int, str, str]]:
    """Execute `git diff --cached --no-color -U0` and inspect staged modifications."""
    findings = []

    # 1. Check staged filenames for sensitive files
    try:
        name_proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if name_proc.returncode == 0:
            for fname in name_proc.stdout.splitlines():
                fname_clean = fname.strip()
                if not fname_clean:
                    continue
                lower_name = os.path.basename(fname_clean).lower()
                if lower_name in SENSITIVE_FILENAMES or lower_name.endswith(".pem") or lower_name.endswith(".key") or "id_rsa" in lower_name:
                    findings.append((fname_clean, 0, "Sensitive File Staged for Commit", lower_name))
        elif name_proc.returncode != 0:
            print(f"Error executing git diff: {name_proc.stderr.strip()}", file=sys.stderr)
            sys.exit(name_proc.returncode)
    except Exception as e:
        print(f"Failed to run git diff: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Check staged content diff
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--no-color", "-U0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if proc.returncode != 0:
            print(f"Error executing git diff: {proc.stderr.strip()}", file=sys.stderr)
            sys.exit(proc.returncode)
        diff_text = proc.stdout
    except Exception as e:
        print(f"Failed to run git diff: {e}", file=sys.stderr)
        sys.exit(1)

    added_items = parse_diff(diff_text)
    for file_path, line_no, content in added_items:
        line_findings = scan_line(content)
        for desc, masked in line_findings:
            findings.append((file_path, line_no, desc, masked))

    return findings


def scan_file(file_path: Path) -> List[Tuple[str, int, str, str]]:
    """Scan an individual file on disk."""
    results = []
    try:
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
    """Recursively scan directory tree for sensitive files and secret tokens."""
    all_findings = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            p = Path(root) / f
            lower_name = f.lower()
            if lower_name in SENSITIVE_FILENAMES or lower_name.endswith(".pem") or lower_name.endswith(".key") or "id_rsa" in lower_name:
                all_findings.append((str(p), 0, "Sensitive File Stored Plaintext on Disk", f))
            all_findings.extend(scan_file(p))
    return all_findings


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("Usage: scan_secrets.py [--staged | --stdin | --help | <target_path>]")
        print("  --staged      Scan staged Git modifications (via git diff --cached)")
        print("  --stdin       Scan unified diff or text piped via stdin")
        print("  <target_path> Scan specified file or directory (default: current directory)")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "--staged":
        findings = scan_staged_changes()
        if not findings:
            print("✓ Secret scan passed: Zero sensitive tokens detected in staged changes.")
            sys.exit(0)
        else:
            print(f"🚨 ALERT: Found {len(findings)} potential security exposure(s) in staged changes:")
            for file_path, line_no, desc, masked in findings:
                loc = f":{line_no}" if line_no > 0 else ""
                print(f"  {file_path}{loc} -> [{desc}] {masked}")
            print("\nAborting: Scrub sensitive tokens before proceeding.")
            sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--stdin":
        diff_text = sys.stdin.read()
        if "diff --git " in diff_text or "--- " in diff_text:
            added_items = parse_diff(diff_text)
            findings = []
            for file_path, line_no, content in added_items:
                for desc, masked in scan_line(content):
                    findings.append((file_path, line_no, desc, masked))
        else:
            raw_findings = scan_text(diff_text, "stdin")
            findings = [("stdin", line_no, desc, masked) for line_no, desc, masked in raw_findings]

        if not findings:
            print("✓ Secret scan passed: Zero sensitive tokens detected in diff.")
            sys.exit(0)
        else:
            print(f"🚨 ALERT: Found {len(findings)} potential security exposure(s) in diff:")
            for file_path, line_no, desc, masked in findings:
                loc = f":{line_no}" if line_no > 0 else ""
                print(f"  {file_path}{loc} -> [{desc}] {masked}")
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
