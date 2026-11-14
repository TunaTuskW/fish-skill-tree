#!/usr/bin/env python3
"""
Reference Implementation of AST Security & Malware Scanner for fish-skill-tree
Implements: Python AST visitor, Shell script analyzer, SSRF / Webhook detection, and JSON report generator.
"""

import sys
import os
import ast
import json
import re
from pathlib import Path

SUSPICIOUS_SINKS = ["discord.com/api/webhooks", "api.telegram.org", "webhook.site", "pipedream.net", "169.254.169.254", "evil-analytics-collector.dev", "attacker-webhook"]

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.findings = []

    def visit_Call(self, node):
        # 1. Dynamic Execution
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "compile"):
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "rule": "DYNAMIC_CODE_EXECUTION",
                    "severity": "CRITICAL",
                    "snippet": f"{node.func.id}(...)"
                })
        elif isinstance(node.func, ast.Attribute):
            # 2. Shell Execution (os.system, os.popen)
            val_id = getattr(node.func.value, "id", None)
            if val_id == "os" and node.func.attr in ("system", "popen"):
                self.findings.append({
                    "file": str(self.file_path),
                    "line": node.lineno,
                    "rule": "SHELL_EXECUTION",
                    "severity": "HIGH",
                    "snippet": f"os.{node.func.attr}(...)"
                })
            # 3. Subprocess shell=True
            elif node.func.attr in ("run", "Popen", "call", "check_call", "check_output"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.findings.append({
                            "file": str(self.file_path),
                            "line": node.lineno,
                            "rule": "SHELL_INJECTION_RISK",
                            "severity": "HIGH",
                            "snippet": f"subprocess.{node.func.attr}(shell=True)"
                        })

        # 4. Outbound SSRF / Webhook sinks
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                for s in SUSPICIOUS_SINKS:
                    if s in child.value:
                        self.findings.append({
                            "file": str(self.file_path),
                            "line": getattr(node, "lineno", 1),
                            "rule": "OUTBOUND_EXFILTRATION_SINK",
                            "severity": "HIGH",
                            "snippet": f"Sink: {child.value}"
                        })

        # 5. Obfuscated base64 eval
        func_id = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if func_id in ("eval", "exec") and any("b64decode" in ast.dump(arg) for arg in node.args):
            self.findings.append({
                "file": str(self.file_path),
                "line": getattr(node, "lineno", 1),
                "rule": "OBFUSCATED_DYNAMIC_EXEC",
                "severity": "CRITICAL",
                "snippet": "base64.b64decode inside execution sink"
            })

        self.generic_visit(node)

def analyze_shell_script(file_path: Path):
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for lnum, line in enumerate(f, 1):
                if re.search(r'curl\s+.*\|\s*(sh|bash)', line):
                    findings.append({
                        "file": str(file_path),
                        "line": lnum,
                        "rule": "UNCHECKSUMMED_REMOTE_EXEC",
                        "severity": "CRITICAL",
                        "snippet": line.strip()
                    })
                elif re.search(r'curl\s+.*-o\s+/tmp/.*&&\s*chmod\s+\+x', line):
                    findings.append({
                        "file": str(file_path),
                        "line": lnum,
                        "rule": "UNPINNED_BINARY_EXECUTION",
                        "severity": "HIGH",
                        "snippet": line.strip()
                    })
    except Exception:
        pass
    return findings

def scan_path(target_path: Path):
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path does not exist: {target_path}\n")
        return None, 0

    all_findings = []
    scanned_count = 0

    files_to_scan = []
    if target_path.is_file():
        files_to_scan.append(target_path)
    else:
        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__")]
            for f in files:
                files_to_scan.append(Path(root) / f)

    for fp in files_to_scan:
        if fp.suffix == ".py":
            scanned_count += 1
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(fp))
                visitor = ASTVisitor(fp)
                visitor.visit(tree)
                all_findings.extend(visitor.findings)
            except SyntaxError as e:
                sys.stderr.write(f"Syntax Error in {fp} at line {e.lineno}: {e.msg}\n")
                all_findings.append({
                    "file": str(fp),
                    "line": e.lineno or 1,
                    "rule": "PYTHON_SYNTAX_ERROR",
                    "severity": "CRITICAL",
                    "snippet": e.msg or "syntax error"
                })
        elif fp.suffix in (".sh", ".bash"):
            scanned_count += 1
            sh_findings = analyze_shell_script(fp)
            all_findings.extend(sh_findings)

    return all_findings, scanned_count

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
        import subprocess
        try:
            diff_res = subprocess.run(["git", "diff", "--cached", "--name-only"], stdout=subprocess.PIPE, text=True, check=True)
            files = [Path(f) for f in diff_res.stdout.splitlines() if f.endswith((".py", ".sh"))]
            findings = []
            scanned = 0
            for fp in files:
                if fp.exists():
                    res, c = scan_path(fp)
                    if res:
                        findings.extend(res)
                    scanned += c
        except Exception as e:
            sys.stderr.write(f"Error checking staged files: {e}\n")
            sys.exit(1)
    else:
        findings, scanned = scan_path(Path(target))
        if findings is None:
            sys.exit(1)

    is_clean = len(findings) == 0

    report = {
        "scanned_files": scanned,
        "clean": is_clean,
        "findings": findings
    }

    if json_path:
        with open(json_path, "w", encoding="utf-8") as jf:
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
