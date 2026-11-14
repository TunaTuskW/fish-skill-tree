#!/usr/bin/env python3
"""
AST Security & Malware Scanner Engine for fish-skill-tree ecosystem.
Provides static AST analysis for Python, lexical pattern analysis for Shell & JavaScript,
supply-chain validation, outbound exfiltration/SSRF detection, and pre-commit Git index verification.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SUSPICIOUS_SINKS = [
    "discord.com/api/webhooks",
    "discordapp.com/api/webhooks",
    "api.telegram.org",
    "webhook.site",
    "pipedream.net",
    "requestbin.com",
    "hookbin.com",
    "beeceptor.com",
    "169.254.169.254",          # AWS / Cloud Metadata IP
    "metadata.google.internal",  # GCP Cloud Metadata DNS
    "evil-analytics-collector.dev",
    "attacker-webhook",
    "attacker.dev",
]

SENSITIVE_PATH_PATTERNS = [
    r"\.ssh/(?:id_rsa|id_ecdsa|id_ed25519|authorized_keys|known_hosts)",
    r"\.aws/(?:credentials|config)",
    r"\.gemini/config/(?:config\.json|auth\.json)",
    r"/etc/shadow",
    r"/etc/passwd",
]

IGNORE_DIRS = {
    ".git", ".agents", "node_modules", "venv", ".venv", "__pycache__",
    ".codegraph", "dist", "build", ".next", ".cache", "brain", "conversations"
}

DANGEROUS_WILDCARDS: Dict[str, Set[str]] = {
    "os": {"system", "popen", "open"},
    "subprocess": {"run", "Popen", "call", "check_call", "check_output"},
    "pickle": {"loads", "load"},
    "_pickle": {"loads", "load"},
    "pty": {"spawn", "fork"},
    "yaml": {
        "load", "load_all", "unsafe_load", "unsafe_load_all",
        "full_load", "full_load_all", "safe_load", "safe_load_all"
    },
    "io": {"open"},
    "pathlib": {"Path"},
    "builtins": {"eval", "exec", "compile", "open", "__import__"},
}

SHELL_PIPE_REGEX = re.compile(
    r"\b(?:curl|wget)\b.*\|"
    r"\s*(?:sudo\s+)?"
    r"(?:(?:/[a-zA-Z0-9_.-]+)+/|env\s+|/usr/bin/env\s+)?"
    r"(?:ba|z|da|k)?sh\b"
)

SHELL_BINARY_DL_SAME_LINE = re.compile(
    r"\b(?:curl|wget)\b.*?(?:-o|-O|>)\s*.*?(?:&&|;)\s*chmod\s+(?:-[a-zA-Z]+\s+)*(?:[ugoa]*\+x|[0-7]{3,4})\b"
)

DOWNLOAD_TARGET_REGEX = re.compile(
    r"\b(?:curl|wget)\b.*?(?:-o|-O|>)\s+([\"']?\S+[\"']?)"
)

CHMOD_CALL_REGEX = re.compile(
    r"\bchmod\s+(?:-[a-zA-Z]+\s+)*(?:[ugoa]*\+x|[0-7]{3,4})\b(?:\s+([\"']?\S+[\"']?))?"
)

CHECKSUM_VERIFY_REGEX = re.compile(
    r"\b(?:verify_sha256|sha256sum|shasum|sha1sum|md5sum|openssl\s+dgst|gpg\s+--verify)\b"
)


def parse_shell_logical_lines(lines: List[str]) -> List[Tuple[int, int, str]]:
    """Group lines ending with backslash continuations into single logical lines."""
    logical_lines: List[Tuple[int, int, str]] = []
    acc: List[str] = []
    start_line = 1
    for lnum, line in enumerate(lines, 1):
        stripped = line.strip()
        if not acc and stripped.startswith("#"):
            logical_lines.append((lnum, lnum, stripped))
            continue
        if not acc:
            start_line = lnum
        if stripped.endswith("\\"):
            acc.append(stripped[:-1].rstrip())
        else:
            if acc:
                acc.append(stripped)
                logical_lines.append((start_line, lnum, " ".join(acc)))
                acc = []
            else:
                logical_lines.append((lnum, lnum, stripped))
    if acc:
        logical_lines.append((start_line, len(lines), " ".join(acc)))
    return logical_lines


class SecurityASTVisitor(ast.NodeVisitor):
    """
    Python AST visitor detecting dynamic execution, process injection,
    insecure deserialization, exfiltration sinks, and sensitive file access.
    """

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.findings: List[Dict] = []
        self.aliases: Dict[str, str] = {}
        self.imported_symbols: Dict[str, str] = {}

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.aliases[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                if mod in DANGEROUS_WILDCARDS:
                    for sym in DANGEROUS_WILDCARDS[mod]:
                        self.imported_symbols[sym] = f"{mod}.{sym}"
            else:
                full = f"{mod}.{alias.name}" if mod else alias.name
                self.imported_symbols[alias.asname or alias.name] = full
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        rhs_name = self.resolve_call_name(node.value)
        if rhs_name:
            if any(rhs_name.startswith(p) for p in ("requests.", "http.client.", "aiohttp.", "urllib.", "socket.")):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.aliases[target.id] = rhs_name
            elif rhs_name in (
                "os.system", "os.popen", "pickle.loads", "pickle.load",
                "_pickle.loads", "_pickle.load", "eval", "exec", "compile"
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.imported_symbols[target.id] = rhs_name
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        for item in node.items:
            rhs_name = self.resolve_call_name(item.context_expr)
            if any(rhs_name.startswith(p) for p in ("requests.", "http.client.", "aiohttp.", "urllib.", "socket.")):
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    self.aliases[item.optional_vars.id] = rhs_name
        self.generic_visit(node)

    def resolve_call_name(self, node: ast.AST) -> str:
        """Resolve full canonical call or attribute path with import alias resolution."""
        res = ""
        if isinstance(node, ast.Name):
            res = self.imported_symbols.get(node.id, self.aliases.get(node.id, node.id))
        elif isinstance(node, ast.Attribute):
            receiver = self.resolve_call_name(node.value)
            receiver_resolved = self.aliases.get(receiver, receiver)
            res = f"{receiver_resolved}.{node.attr}" if receiver_resolved else node.attr
        elif isinstance(node, ast.Call):
            res = self.resolve_call_name(node.func)

        # Normalize builtin prefix
        if res.startswith("builtins."):
            res = res[len("builtins."):]
        elif res.startswith("__builtins__."):
            res = res[len("__builtins__."):]
        return res

    def visit_Call(self, node: ast.Call):
        func_name = self.resolve_call_name(node.func)
        end_lineno = getattr(node, "end_lineno", node.lineno)

        # 1. Dynamic Code Execution: eval, exec, compile
        if func_name in ("eval", "exec", "compile"):
            has_obfuscation = False
            for arg in node.args:
                for child in ast.walk(arg):
                    if isinstance(child, ast.Call):
                        child_fn = self.resolve_call_name(child.func)
                        if any(k in child_fn for k in ("b64decode", "unhexlify", "decompress")):
                            has_obfuscation = True
                            break
                        # Also check dynamic __import__ inside arguments
                        if child_fn in ("__import__", "importlib.import_module"):
                            has_obfuscation = True
                            break

            if has_obfuscation:
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "end_line": end_lineno,
                    "rule": "OBFUSCATED_DYNAMIC_EXEC",
                    "severity": "CRITICAL",
                    "snippet": f"{func_name}(b64decode(...)) inside execution sink"
                })
            else:
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "end_line": end_lineno,
                    "rule": "DYNAMIC_CODE_EXECUTION",
                    "severity": "CRITICAL",
                    "snippet": f"{func_name}(...)"
                })

        # 2. Dynamic __import__ & importlib.import_module
        elif func_name in ("__import__", "importlib.import_module"):
            if node.args and not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "end_line": end_lineno,
                    "rule": "DYNAMIC_CODE_EXECUTION",
                    "severity": "CRITICAL",
                    "snippet": f"{func_name}(<dynamic_expression>)"
                })

        # 3. Process Execution: os.system, os.popen
        elif func_name in ("os.system", "os.popen"):
            self.findings.append({
                "file": str(self.file_path),
                "line": node.lineno,
                "end_line": end_lineno,
                "rule": "SHELL_EXECUTION",
                "severity": "HIGH",
                "snippet": f"{func_name}(...)"
            })

        # 4. Interactive Pseudo-Terminal: pty.spawn, pty.fork
        elif func_name in ("pty.spawn", "pty.fork"):
            self.findings.append({
                "file": str(self.file_path),
                "line": node.lineno,
                "end_line": end_lineno,
                "rule": "SHELL_EXECUTION",
                "severity": "HIGH",
                "snippet": f"{func_name}(...)"
            })

        # 5. Subprocess shell=True
        elif func_name in ("subprocess.run", "subprocess.Popen", "subprocess.call",
                           "subprocess.check_call", "subprocess.check_output"):
            for kw in node.keywords:
                if kw.arg == "shell":
                    is_true = False
                    if isinstance(kw.value, ast.Constant) and bool(kw.value.value) is True:
                        is_true = True
                    elif not isinstance(kw.value, ast.Constant):
                        is_true = True
                    if is_true:
                        self.findings.append({
                            "file": str(self.file_path),
                            "line": node.lineno,
                            "end_line": end_lineno,
                            "rule": "SHELL_INJECTION_RISK",
                            "severity": "HIGH",
                            "snippet": f"{func_name}(shell=True)"
                        })

        # 6. Insecure Deserialization: pickle
        elif func_name in ("pickle.loads", "pickle.load", "_pickle.loads", "_pickle.load"):
            self.findings.append({
                "file": str(self.file_path),
                "line": node.lineno,
                "end_line": end_lineno,
                "rule": "INSECURE_DESERIALIZATION_PICKLE",
                "severity": "CRITICAL",
                "snippet": f"{func_name}(...)"
            })

        # 7. Insecure Deserialization: PyYAML unsafe load
        elif func_name in (
            "yaml.unsafe_load", "yaml.unsafe_load_all",
            "yaml.full_load", "yaml.full_load_all",
            "unsafe_load", "unsafe_load_all",
            "full_load", "full_load_all"
        ):
            self.findings.append({
                "file": str(self.file_path),
                "line": node.lineno,
                "end_line": end_lineno,
                "rule": "INSECURE_DESERIALIZATION_YAML",
                "severity": "CRITICAL",
                "snippet": f"{func_name}(...)"
            })

        elif func_name in ("yaml.load", "yaml.load_all"):
            safe = False
            for kw in node.keywords:
                if kw.arg == "Loader":
                    loader_name = self.resolve_call_name(kw.value)
                    if any(safe_ldr in loader_name for safe_ldr in ("SafeLoader", "CSafeLoader", "BaseLoader")):
                        safe = True
            if len(node.args) >= 2:
                loader_name = self.resolve_call_name(node.args[1])
                if any(safe_ldr in loader_name for safe_ldr in ("SafeLoader", "CSafeLoader", "BaseLoader")):
                    safe = True
            if not safe:
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "end_line": end_lineno,
                    "rule": "INSECURE_DESERIALIZATION_YAML",
                    "severity": "HIGH",
                    "snippet": f"{func_name}(...) without SafeLoader"
                })

        # 8. Path Traversal & Sensitive File Access
        elif func_name in ("open", "io.open", "os.open", "pathlib.Path",
                           "os.path.expanduser", "os.path.join"):
            for arg in node.args:
                checked_strs: List[str] = []
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    checked_strs.append(arg.value)
                elif isinstance(arg, ast.JoinedStr):
                    for part in arg.values:
                        if isinstance(part, ast.Constant) and isinstance(part.value, str):
                            checked_strs.append(part.value)
                for s_val in checked_strs:
                    for pat in SENSITIVE_PATH_PATTERNS:
                        if re.search(pat, s_val):
                            self.findings.append({
                                "file": str(self.file_path),
                                "line": node.lineno,
                                "end_line": end_lineno,
                                "rule": "SENSITIVE_PATH_TRAVERSAL",
                                "severity": "HIGH",
                                "snippet": f"{func_name}('{s_val}')"
                            })
                            break

        # 9. Credential exfiltration via network calls (e.g. os.environ exfiltration)
        if any(net in func_name for net in ("requests.", "urllib.", "http.client", "aiohttp.", "socket.")):
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and child.attr == "environ":
                    recv = self.resolve_call_name(child.value)
                    if recv == "os":
                        self.findings.append({
                            "file": str(self.file_path),
                            "line": node.lineno,
                            "end_line": end_lineno,
                            "rule": "CREDENTIAL_EXFILTRATION_FLOW",
                            "severity": "CRITICAL",
                            "snippet": f"{func_name}(... os.environ ...)"
                        })
                        break

        # 10. Outbound SSRF & Exfiltration Sinks
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                for s in SUSPICIOUS_SINKS:
                    if s in child.value:
                        self.findings.append({
                            "file": str(self.file_path),
                            "line": getattr(node, "lineno", 1),
                            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                            "rule": "OUTBOUND_EXFILTRATION_SINK",
                            "severity": "HIGH",
                            "snippet": f"Sink: {child.value}"
                        })

        self.generic_visit(node)


def analyze_shell_script(file_path: Path, content: Optional[str] = None) -> List[Dict]:
    """Scan shell script content for dangerous sinks, unpinned curl binaries, exfiltration, and sensitive paths."""
    findings: List[Dict] = []
    try:
        fp = Path(file_path)
        if content is None:
            content = fp.read_text(encoding="utf-8", errors="ignore")

        lines = content.splitlines()
        logical_lines = parse_shell_logical_lines(lines)

        has_global_checksum = bool(CHECKSUM_VERIFY_REGEX.search(content))
        pending_downloads: Dict[str, Tuple[int, str]] = {}

        for start_l, end_l, line in logical_lines:
            if line.startswith("#"):
                continue

            # 1. Remote pipe-to-shell (supports bare commands, absolute paths, env, sudo, multiline)
            if SHELL_PIPE_REGEX.search(line):
                findings.append({
                    "file": str(fp),
                    "line": start_l,
                    "end_line": end_l,
                    "line_span": (start_l, end_l),
                    "rule": "UNCHECKSUMMED_REMOTE_EXEC",
                    "severity": "CRITICAL",
                    "snippet": line
                })
                continue

            # 2. Binary download & chmod on same logical line (supports &&, ;, octal, wget)
            if SHELL_BINARY_DL_SAME_LINE.search(line):
                findings.append({
                    "file": str(fp),
                    "line": start_l,
                    "end_line": end_l,
                    "line_span": (start_l, end_l),
                    "rule": "UNPINNED_BINARY_EXECUTION",
                    "severity": "HIGH",
                    "snippet": line
                })
                continue

            # Check for download target for separate line tracking
            dm = DOWNLOAD_TARGET_REGEX.search(line)
            if dm:
                target = dm.group(1).strip("\"'")
                pending_downloads[target] = (start_l, line)

            # Check for checksum verification
            if CHECKSUM_VERIFY_REGEX.search(line):
                for t in list(pending_downloads.keys()):
                    if t in line or "$" in t or not t:
                        del pending_downloads[t]

            # Check for chmod on separate lines
            cm = CHMOD_CALL_REGEX.search(line)
            if cm:
                target = cm.group(1).strip("\"'") if cm.group(1) else None
                if target and target in pending_downloads:
                    findings.append({
                        "file": str(fp),
                        "line": start_l,
                        "end_line": end_l,
                        "line_span": (start_l, end_l),
                        "rule": "UNPINNED_BINARY_EXECUTION",
                        "severity": "HIGH",
                        "snippet": line
                    })
                    del pending_downloads[target]
                elif pending_downloads and not has_global_checksum:
                    findings.append({
                        "file": str(fp),
                        "line": start_l,
                        "end_line": end_l,
                        "line_span": (start_l, end_l),
                        "rule": "UNPINNED_BINARY_EXECUTION",
                        "severity": "HIGH",
                        "snippet": line
                    })
                    pending_downloads.clear()

            # 3. Supply chain unpinned package
            if re.search(r"\b(?:npx|pnpx|bunx)\s+(?:-y\s+)?[\w@/-]+@latest\b", line):
                findings.append({
                    "file": str(fp),
                    "line": start_l,
                    "end_line": end_l,
                    "line_span": (start_l, end_l),
                    "rule": "SUPPLY_CHAIN_UNPINNED_PACKAGE",
                    "severity": "HIGH",
                    "snippet": line
                })

            # 4. Outbound exfiltration sinks
            for s in SUSPICIOUS_SINKS:
                if s in line:
                    findings.append({
                        "file": str(fp),
                        "line": start_l,
                        "end_line": end_l,
                        "line_span": (start_l, end_l),
                        "rule": "OUTBOUND_EXFILTRATION_SINK",
                        "severity": "HIGH",
                        "snippet": line
                    })

            # 5. Sensitive path traversal
            for pat in SENSITIVE_PATH_PATTERNS:
                if re.search(pat, line):
                    findings.append({
                        "file": str(fp),
                        "line": start_l,
                        "end_line": end_l,
                        "line_span": (start_l, end_l),
                        "rule": "SENSITIVE_PATH_TRAVERSAL",
                        "severity": "HIGH",
                        "snippet": line
                    })
                    break
    except Exception:
        pass
    return findings


def analyze_js_script(file_path: Path, content: Optional[str] = None) -> List[Dict]:
    """Scan JavaScript/TypeScript content for eval, Function constructor, vm execution, sinks, and sensitive paths."""
    findings: List[Dict] = []
    try:
        fp = Path(file_path)
        if content is None:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        for lnum, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # 1. JS eval
            if re.search(r"\beval\s*\(", line):
                findings.append({
                    "file": str(fp),
                    "line": lnum,
                    "end_line": lnum,
                    "rule": "JS_DYNAMIC_EVAL",
                    "severity": "CRITICAL",
                    "snippet": stripped
                })

            # 2. Function constructor
            elif re.search(r"\bnew\s+Function\s*\(|\bFunction\s*\([^)]*\)\s*\(", line):
                findings.append({
                    "file": str(fp),
                    "line": lnum,
                    "end_line": lnum,
                    "rule": "JS_FUNCTION_CONSTRUCTOR",
                    "severity": "CRITICAL",
                    "snippet": stripped
                })

            # 3. Node VM execution
            elif re.search(r"\bvm\.(?:runInContext|runInNewContext|runInThisContext|compileFunction|Script)\s*\(", line):
                findings.append({
                    "file": str(fp),
                    "line": lnum,
                    "end_line": lnum,
                    "rule": "JS_VM_DYNAMIC_EXECUTION",
                    "severity": "HIGH",
                    "snippet": stripped
                })

            # 4. Dynamic unpinned remote import
            elif re.search(r"\bimport\s*\(\s*[\"']https?://", line):
                findings.append({
                    "file": str(fp),
                    "line": lnum,
                    "end_line": lnum,
                    "rule": "JS_UNPINNED_DYNAMIC_IMPORT",
                    "severity": "HIGH",
                    "snippet": stripped
                })

            # 5. Exfiltration sinks
            for s in SUSPICIOUS_SINKS:
                if s in line:
                    findings.append({
                        "file": str(fp),
                        "line": lnum,
                        "end_line": lnum,
                        "rule": "OUTBOUND_EXFILTRATION_SINK",
                        "severity": "HIGH",
                        "snippet": stripped
                    })

            # 6. Sensitive path traversal
            for pat in SENSITIVE_PATH_PATTERNS:
                if re.search(pat, line):
                    findings.append({
                        "file": str(fp),
                        "line": lnum,
                        "end_line": lnum,
                        "rule": "SENSITIVE_PATH_TRAVERSAL",
                        "severity": "HIGH",
                        "snippet": stripped
                    })
                    break
    except Exception:
        pass
    return findings


def is_script_file(fp: Path) -> Optional[str]:
    """Determine script kind ('py', 'sh', 'js') for a file, checking extensions and shebangs."""
    if fp.suffix == ".py":
        return "py"
    if fp.suffix in (".sh", ".bash"):
        return "sh"
    if fp.suffix in (".js", ".mjs", ".ts", ".tsx"):
        return "js"
    if fp.suffix == "":
        name = fp.name
        if name in ("gdocs", "gsheets"):
            return "sh"
        if fp.is_file():
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    first_line = f.readline()
                if first_line.startswith("#!"):
                    if "python" in first_line:
                        return "py"
                    if "sh" in first_line or "bash" in first_line:
                        return "sh"
                    if "node" in first_line:
                        return "js"
            except Exception:
                pass
    return None


def scan_path(target_path: Path) -> Tuple[Optional[List[Dict]], int]:
    """
    Scan a file or directory recursively.
    Returns (findings, scanned_count), or (None, 0) if the target path does not exist.
    """
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path does not exist: {target_path}\n")
        return None, 0

    all_findings: List[Dict] = []
    scanned_count = 0
    files_to_scan: List[Path] = []

    if target_path.is_file():
        files_to_scan.append(target_path)
    else:
        visited_dirs: Set[str] = set()
        skip_tests = "tests" not in str(target_path)

        for root, dirs, files in os.walk(target_path, followlinks=True):
            real_root = os.path.realpath(root)
            if real_root in visited_dirs:
                dirs[:] = []
                continue
            visited_dirs.add(real_root)

            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs
                if d not in IGNORE_DIRS and not (skip_tests and d == "tests")
            ]

            for f in files:
                fp = Path(root) / f
                if is_script_file(fp):
                    files_to_scan.append(fp)

    for fp in files_to_scan:
        kind = is_script_file(fp)
        if kind == "py":
            scanned_count += 1
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(fp))
                visitor = SecurityASTVisitor(fp)
                visitor.visit(tree)
                all_findings.extend(visitor.findings)
            except SyntaxError as e:
                err_line = e.lineno or 1
                sys.stderr.write(f"Syntax Error in {fp} at line {err_line}: {e.msg}\n")
                all_findings.append({
                    "file": str(fp),
                    "line": err_line,
                    "end_line": err_line,
                    "rule": "PYTHON_SYNTAX_ERROR",
                    "severity": "CRITICAL",
                    "snippet": e.msg or "syntax error"
                })
        elif kind == "sh":
            scanned_count += 1
            all_findings.extend(analyze_shell_script(fp))
        elif kind == "js":
            scanned_count += 1
            all_findings.extend(analyze_js_script(fp))

    return all_findings, scanned_count


def scan_staged_changes() -> Tuple[List[Dict], int]:
    """Inspect staged Git modifications via git diff --cached and git show."""
    try:
        status_proc = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
    except Exception as e:
        sys.stderr.write(f"Error checking git staged files: {e}\n")
        return [], 0

    staged_findings: List[Dict] = []
    scanned_count = 0

    for line in status_proc.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        status, rel_path = parts[0], parts[1].strip('"')
        if status.startswith("D"):
            continue

        fp = Path(rel_path)
        if fp.parts and fp.parts[0] == "tests":
            continue
        kind = is_script_file(fp)
        if not kind:
            continue

        scanned_count += 1

        try:
            show_proc = subprocess.run(
                ["git", "show", f":{rel_path}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            staged_content = show_proc.stdout
        except subprocess.CalledProcessError:
            if fp.exists():
                staged_content = fp.read_text(encoding="utf-8", errors="replace")
            else:
                continue

        # Extract added line numbers from unified diff hunks
        added_lines: Set[int] = set()
        diff_proc = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", rel_path],
            stdout=subprocess.PIPE, text=True, check=False
        )
        cur_line = 0
        in_hunk = False
        for dline in diff_proc.stdout.splitlines():
            hm = re.match(r"^@@\s+-[0-9]+(?:,[0-9]+)?\s+\+([0-9]+)(?:,([0-9]+))?\s+@@", dline)
            if hm:
                cur_line = int(hm.group(1))
                in_hunk = True
                continue
            if in_hunk:
                if dline.startswith("+") and not dline.startswith("+++"):
                    added_lines.add(cur_line)
                    cur_line += 1
                elif dline.startswith(" "):
                    cur_line += 1

        is_new_file = status.startswith("A")

        if kind == "py":
            try:
                tree = ast.parse(staged_content, filename=str(fp))
                visitor = SecurityASTVisitor(fp)
                visitor.visit(tree)
                for finding in visitor.findings:
                    f_start = finding.get("line", 1)
                    f_end = finding.get("end_line", f_start)
                    if is_new_file or any(l in added_lines for l in range(f_start, f_end + 1)):
                        staged_findings.append(finding)
            except SyntaxError as e:
                err_line = e.lineno or 1
                if is_new_file or err_line in added_lines:
                    sys.stderr.write(f"Syntax Error in {fp} at line {err_line}: {e.msg}\n")
                    staged_findings.append({
                        "file": str(fp),
                        "line": err_line,
                        "end_line": err_line,
                        "rule": "PYTHON_SYNTAX_ERROR",
                        "severity": "CRITICAL",
                        "snippet": e.msg or "syntax error"
                    })
        elif kind == "sh":
            sh_findings = analyze_shell_script(fp, content=staged_content)
            for f in sh_findings:
                f_start = f.get("line", 1)
                f_end = f.get("end_line", f.get("line_span", (f_start, f_start))[1])
                if is_new_file or any(l in added_lines for l in range(f_start, f_end + 1)):
                    staged_findings.append(f)
        elif kind == "js":
            js_findings = analyze_js_script(fp, content=staged_content)
            for f in js_findings:
                f_start = f.get("line", 1)
                f_end = f.get("end_line", f_start)
                if is_new_file or any(l in added_lines for l in range(f_start, f_end + 1)):
                    staged_findings.append(f)

    return staged_findings, scanned_count


def main():
    target = None
    json_path = None
    staged = False

    args = sys.argv[1:]
    idx = 0
    while idx < len(args):
        a = args[idx]
        if a == "--target" and idx + 1 < len(args):
            target = args[idx + 1]
            idx += 2
        elif a == "--json" and idx + 1 < len(args):
            json_path = args[idx + 1]
            idx += 2
        elif a == "--staged":
            staged = True
            idx += 1
        elif not a.startswith("--") and target is None:
            target = a
            idx += 1
        else:
            idx += 1

    if target is None and not staged:
        target = "."

    if staged:
        findings, scanned = scan_staged_changes()
    else:
        target_path = Path(target)
        findings, scanned = scan_path(target_path)
        if findings is None:
            sys.exit(1)

    is_clean = len(findings) == 0
    crit_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in findings if f.get("severity") == "HIGH")

    report = {
        "scanned_files": scanned,
        "clean": is_clean,
        "critical_count": crit_count,
        "high_count": high_count,
        "findings": findings
    }

    if json_path:
        p = Path(json_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as jf:
            json.dump(report, jf, indent=2)

    if not is_clean:
        print("MALWARE_DETECTED / AST security check failed! Violations found:")
        for f in findings:
            print(f"  {f['file']}:{f['line']} -> [{f['rule']}] {f['snippet']}")
        sys.exit(1)
    else:
        print("✓ AST security scan passed: 0 vulnerabilities found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
