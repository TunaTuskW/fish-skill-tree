#!/usr/bin/env python3
"""
Python Helper Utilities for fish-skill-tree E2E Test Harness
Provides robust YAML frontmatter parsing, Shannon entropy scoring, AST checks, and JSON validation.
Compatible with Python 3.9+ and macOS BSD environment.
"""

import sys
import os
import re
import math
import json
import ast
from pathlib import Path

def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy for a given string: H(X) = -sum(p_i * log2(p_i))."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    char_counts = {}
    for c in text:
        char_counts[c] = char_counts.get(c, 0) + 1
    for count in char_counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def validate_yaml_frontmatter(file_path: Path) -> dict:
    """
    Validate YAML frontmatter in SKILL.md and return parsed metadata dictionary.
    Exits with code 1 and error message on invalid frontmatter.
    """
    if not file_path.exists():
        sys.stderr.write(f"Error: SKILL.md file not found: {file_path}\n")
        sys.exit(1)

    if file_path.stat().st_size == 0:
        sys.stderr.write(f"Error: SKILL.md is empty (0 bytes): {file_path}\n")
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as e:
        sys.stderr.write(f"Error: Failed to decode UTF-8 content in {file_path}: {e}\n")
        sys.exit(1)

    # Frontmatter pattern: starts with --- at beginning of file, ends with --- on its own line
    pattern = r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        sys.stderr.write(f"Error: Missing YAML frontmatter boundary delimiters (---) in {file_path}\n")
        sys.exit(1)

    yaml_block = match.group(1)

    try:
        import yaml
        data = yaml.safe_load(yaml_block)
    except Exception as e:
        sys.stderr.write(f"YAML Parser Error at {file_path}: {e}\n")
        sys.exit(1)

    if not isinstance(data, dict):
        sys.stderr.write(f"Validation Error: Frontmatter is not a key-value mapping in {file_path}\n")
        sys.exit(1)

    # Mandatory field checks
    if "name" not in data:
        sys.stderr.write(f"Validation Error: Missing mandatory frontmatter field: name in {file_path}\n")
        sys.exit(1)
    name_val = str(data["name"]).strip()
    if not name_val:
        sys.stderr.write(f"Validation Error: Frontmatter 'name' is empty in {file_path}\n")
        sys.exit(1)

    if "description" not in data:
        sys.stderr.write(f"Validation Error: Missing mandatory frontmatter field: description in {file_path}\n")
        sys.exit(1)
    desc_val = str(data["description"]).strip()
    if not desc_val:
        sys.stderr.write(f"Validation Error: Frontmatter 'description' is empty in {file_path}\n")
        sys.exit(1)

    return data

def check_python_ast(file_path: Path) -> dict:
    """Parse python AST and detect dangerous sinks (eval, exec, shell=True, webhooks)."""
    if not file_path.exists():
        sys.stderr.write(f"Error: File does not exist: {file_path}\n")
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception as e:
        sys.stderr.write(f"Error reading {file_path}: {e}\n")
        sys.exit(1)

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        sys.stderr.write(f"Syntax Error in {file_path} at line {e.lineno}: {e.msg}\n")
        sys.exit(1)

    findings = []
    suspicious_urls = ["discord.com/api/webhooks", "api.telegram.org", "webhook.site", "pipedream.net", "169.254.169.254", "evil-analytics-collector.dev", "attacker-webhook"]

    class SecurityVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # Check eval(), exec(), compile()
            if isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec", "compile"):
                    findings.append({
                        "rule": "DYNAMIC_CODE_EXECUTION",
                        "severity": "CRITICAL",
                        "line": node.lineno,
                        "sink": node.func.id
                    })
            # Check subprocess shell=True or os.system/popen
            if isinstance(node.func, ast.Attribute):
                val_id = getattr(node.func.value, "id", None)
                if val_id == "os" and node.func.attr in ("system", "popen"):
                    findings.append({
                        "rule": "SHELL_EXECUTION",
                        "severity": "HIGH",
                        "line": node.lineno,
                        "sink": node.func.attr
                    })
                elif node.func.attr in ("run", "Popen", "call", "check_call", "check_output"):
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            findings.append({
                                "rule": "SHELL_INJECTION_RISK",
                                "severity": "HIGH",
                                "line": node.lineno,
                                "sink": "subprocess.shell=True"
                            })
            # Check string constants for suspicious exfiltration URLs
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    for s_url in suspicious_urls:
                        if s_url in child.value:
                            findings.append({
                                "rule": "OUTBOUND_EXFILTRATION_SINK",
                                "severity": "HIGH",
                                "line": getattr(node, "lineno", 1),
                                "sink": child.value
                            })
            self.generic_visit(node)

    visitor = SecurityVisitor()
    visitor.visit(tree)
    return {
        "file": str(file_path),
        "clean": len(findings) == 0,
        "findings": findings
    }

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python_helpers.py <validate-yaml|calc-entropy|check-ast|validate-json> [args...]\n")
        sys.exit(2)

    cmd = sys.argv[1]

    if cmd == "validate-yaml":
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: python_helpers.py validate-yaml <file_path>\n")
            sys.exit(2)
        meta = validate_yaml_frontmatter(Path(sys.argv[2]))
        print(json.dumps(meta, ensure_ascii=False))
        sys.exit(0)

    elif cmd == "calc-entropy":
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: python_helpers.py calc-entropy <text>\n")
            sys.exit(2)
        entropy = calculate_entropy(sys.argv[2])
        print(f"{entropy:.4f}")
        sys.exit(0)

    elif cmd == "check-ast":
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: python_helpers.py check-ast <file_path>\n")
            sys.exit(2)
        result = check_python_ast(Path(sys.argv[2]))
        print(json.dumps(result))
        sys.exit(0 if result["clean"] else 1)

    elif cmd == "validate-json":
        if len(sys.argv) < 3:
            sys.stderr.write("Usage: python_helpers.py validate-json <file_path_or_string>\n")
            sys.exit(2)
        target = sys.argv[2]
        try:
            if os.path.exists(target):
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = json.loads(target)
            print("VALID")
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"Invalid JSON: {e}\n")
            sys.exit(1)

    else:
        sys.stderr.write(f"Unknown command: {cmd}\n")
        sys.exit(2)

if __name__ == "__main__":
    main()
