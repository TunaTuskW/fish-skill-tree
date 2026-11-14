#!/usr/bin/env python3
"""
Unit and Verification Test Suite for Sensitive Data & Secret Scanner
Covers:
- Shannon entropy calculations & threshold behavior
- JSON OAuth key and token detection
- Token-level placeholder filtering and anti-bypass resilience
- Safe masking formatting
- Staged git diff scanning
- Pre-commit hook blocking behavior
"""

import os
import sys
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

# Add scanner path to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER_DIR = REPO_ROOT / "[skill]" / "sensitive-data-guard" / "scripts"
sys.path.insert(0, str(SCANNER_DIR))

import scan_secrets


class TestShannonEntropy(unittest.TestCase):
    """Verifies Shannon entropy calculation, mathematical properties, and thresholds."""

    def test_entropy_empty_and_repetition(self):
        self.assertEqual(scan_secrets.shannon_entropy(""), 0.0)
        self.assertEqual(scan_secrets.shannon_entropy("aaaaaaaaaaaaaaaaaaaa"), 0.0)
        self.assertEqual(scan_secrets.shannon_entropy("11111111111111111111"), 0.0)

    def test_entropy_natural_language_and_code_identifiers(self):
        # English dictionary words have low entropy (< 4.5)
        h_word = scan_secrets.shannon_entropy("internationalization")
        self.assertLess(h_word, 4.5)
        self.assertAlmostEqual(h_word, 2.95, delta=0.2)

        # CamelCase code identifiers have low entropy (< 4.5)
        h_ident = scan_secrets.shannon_entropy("getAuthenticationTokenManager")
        self.assertLess(h_ident, 4.5)
        self.assertAlmostEqual(h_ident, 3.66, delta=0.2)

    def test_entropy_hexadecimal_strings(self):
        # Pure hex alphabet (16 chars) has mathematical maximum entropy log2(16) = 4.0 <= 4.0 < 4.5
        git_sha = "e4d909c290d0fb1ca068ffaddf22cbd0adddefb2"
        h_sha = scan_secrets.shannon_entropy(git_sha)
        self.assertLessEqual(h_sha, 4.0)
        self.assertLess(h_sha, 4.5)

        sha256_hash = "79bb73447814f8d7142a5452187132408ac7cfcc1d1d72e317fe0f792a54a545"
        h_sha256 = scan_secrets.shannon_entropy(sha256_hash)
        self.assertLessEqual(h_sha256, 4.0)
        self.assertLess(h_sha256, 4.5)

    def test_entropy_high_randomness_tokens(self):
        # Cryptographic high-entropy random secrets exceed 4.5
        high_entropy_token = "-".join(("dGhpcy1pcy1h", "LXJhbmRvbS1zZWNyZXQ", "ta2V5LTEyMzQ1Njc=")).replace("-", "")
        h_token = scan_secrets.shannon_entropy(high_entropy_token)
        self.assertGreater(h_token, 4.5)

    def test_is_high_entropy_secret_filtering(self):
        # Short token (< 20 chars) should not be treated as high-entropy secret
        self.assertFalse(scan_secrets.is_high_entropy_secret("shortToken123"))

        # Pure hex hashes should be excluded
        self.assertFalse(scan_secrets.is_high_entropy_secret("e4d909c290d0fb1ca068ffaddf22cbd0adddefb2"))

        # URLs should be excluded
        self.assertFalse(scan_secrets.is_high_entropy_secret("https://example.com/api/v1/auth/tokens/authenticate"))

        # Genuine random secret should return True
        self.assertTrue(scan_secrets.is_high_entropy_secret("xK9#mQ2$vL8*pZ5!wN3^rT7@yB4"))


class TestJSONOAuthKeyDetection(unittest.TestCase):
    """Verifies detection of JSON OAuth keys and tokens in configuration payloads."""

    def test_json_client_secret_detection(self):
        tok_goc = "GOC" + "SPX-" + "aBcDeFgHiJkLmNoPq" + "RsTuVwXyZ12"
        camel_line = '{"client' + 'Secret": "' + tok_goc + '"}'
        findings = scan_secrets.scan_line(camel_line)
        self.assertTrue(any("Client Secret" in desc or "OAuth" in desc for desc, _ in findings))

        tok_custom = "myCustom" + "LiveSecret" + "Token12345678"
        snake_line = '{"client_' + 'secret": "' + tok_custom + '"}'
        findings = scan_secrets.scan_line(snake_line)
        self.assertTrue(any("OAuth" in desc or "Secret" in desc for desc, _ in findings))

    def test_json_private_key_detection(self):
        pk_val = "MIIEvgIBADANBg" + "kqhkiG9w0BAQEFAAS" + "CBKgwggSkAgEAAoIBAQD"
        line = '{"private' + 'Key": "' + pk_val + '"}'
        findings = scan_secrets.scan_line(line)
        self.assertTrue(any("Private" in desc or "OAuth" in desc for desc, _ in findings))

        line_snake = '{"private_' + 'key": "' + pk_val + '"}'
        findings = scan_secrets.scan_line(line_snake)
        self.assertTrue(any("Private" in desc or "OAuth" in desc for desc, _ in findings))

    def test_json_access_and_refresh_tokens(self):
        acc_val = "ya29." + "a0AWY7Ckm_12345" + "67890abcdefghijk" + "lmnopqrstuvwxyz"
        access_line = '{"access_' + 'token": "' + acc_val + '"}'
        findings = scan_secrets.scan_line(access_line)
        self.assertTrue(any("Access Token" in desc or "OAuth" in desc for desc, _ in findings))

        ref_val = "1//" + "04abcdef1234567" + "890abcdefghijklm" + "nopqrstuvwxyz"
        refresh_line = '{"refresh_' + 'token": "' + ref_val + '"}'
        findings = scan_secrets.scan_line(refresh_line)
        self.assertTrue(any("Refresh Token" in desc or "OAuth" in desc for desc, _ in findings))


class TestPlaceholderDiscrimination(unittest.TestCase):
    """Verifies token-level placeholder discrimination and ensures comments cannot bypass detection."""

    def test_bracketed_and_template_placeholders(self):
        self.assertTrue(scan_secrets.is_placeholder_token("<your_api_key>"))
        self.assertTrue(scan_secrets.is_placeholder_token("[REDACTED_API_KEY]"))
        self.assertTrue(scan_secrets.is_placeholder_token("${OPENAI_API_KEY}"))
        self.assertTrue(scan_secrets.is_placeholder_token("{{SECRET_KEY}}"))
        self.assertTrue(scan_secrets.is_placeholder_token("%CLIENT_SECRET%"))
        self.assertTrue(scan_secrets.is_placeholder_token("process.env.SECRET_KEY"))

    def test_known_exact_and_keyword_mocks(self):
        self.assertFalse(scan_secrets.is_placeholder_token("AKIA" + "IOSFODNN7EXAMPLE"))
        self.assertTrue(scan_secrets.is_placeholder_token("ghp_" + ("0" * 36)))
        self.assertTrue(scan_secrets.is_placeholder_token("your-client-secret"))
        self.assertTrue(scan_secrets.is_placeholder_token("dummy_secret_key"))
        self.assertTrue(scan_secrets.is_placeholder_token("test-secret-key"))

    def test_real_secret_with_inline_comment_not_bypassed(self):
        # Critical test: Line contains "example" in comment, but token is a real secret
        gem_tok = "AIza" + "SyB1c2D3e4F5g6H7" + "i8J9k0L1m2N3o4P5q6R"
        line = f'API_{"KEY"} = "{gem_tok}" # example for production'
        findings = scan_secrets.scan_line(line)
        self.assertEqual(len(findings), 1)
        self.assertIn("Google / Gemini API Key", findings[0][0])
        self.assertEqual(findings[0][1], "AIza...5q6R")

        # Line contains "placeholder" in comment, but token is real OpenAI key
        oai_tok = "sk-proj-" + "realRandomKey12" + "345678901234567" + "89012345"
        line2 = f'OPENAI_{"KEY"} = "{oai_tok}" # placeholder key'
        findings2 = scan_secrets.scan_line(line2)
        self.assertEqual(len(findings2), 1)
        self.assertIn("OpenAI / Model API Key", findings2[0][0])

        # Production database URI with comment "placeholder"
        db_scheme = "post" + "gres://"
        db_creds = "adm" + "in:P@ssw" + "0rd99!@prod-db.rds.amazonaws.com:5432/main"
        line3 = f'DB_URL = "{db_scheme}{db_creds}" # placeholder for now'
        findings3 = scan_secrets.scan_line(line3)
        self.assertEqual(len(findings3), 1)
        self.assertIn("Database Connection URI", findings3[0][0])

    def test_safe_mock_db_uri(self):
        # Safe local development URI is ignored
        mock_uri = 'DB_URL = "postgres://postgres:postgres@localhost:5432/testdb"'
        findings = scan_secrets.scan_line(mock_uri)
        self.assertEqual(len(findings), 0)


class TestMaskingOutput(unittest.TestCase):
    """Verifies that detected tokens are safely masked and never printed in plaintext."""

    def test_mask_token_format(self):
        token = "AIza" + "SyDummyUnitTest" + "Key000000000000" + "0xyz"
        masked = scan_secrets.mask_token(token)
        self.assertEqual(masked, "AIza...0xyz")
        self.assertNotIn("DummyUnitTest", masked)

    def test_mask_short_token(self):
        self.assertEqual(scan_secrets.mask_token("secret"), "***")


class TestStagedScan(unittest.TestCase):
    """Verifies `scan_staged_changes()` using temporary Git repositories."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=self.test_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_clean_staged_file(self):
        clean_file = Path(self.test_dir) / "app.py"
        clean_file.write_text("print('Hello world!')\n")
        subprocess.run(["git", "add", "app.py"], cwd=self.test_dir, check=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            findings = scan_secrets.scan_staged_changes()
            self.assertEqual(len(findings), 0)
        finally:
            os.chdir(old_cwd)

    def test_dirty_staged_file_with_secret(self):
        dirty_file = Path(self.test_dir) / "config.py"
        gem_tok = "AIza" + "SyB1c2D3e4F5g6H7" + "i8J9k0L1m2N3o4P5q6R"
        dirty_file.write_text(f'GEMINI_VAL = "{gem_tok}"\n')
        subprocess.run(["git", "add", "config.py"], cwd=self.test_dir, check=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            findings = scan_secrets.scan_staged_changes()
            self.assertEqual(len(findings), 1)
            file_path, line_no, desc, masked = findings[0]
            self.assertEqual(file_path, "config.py")
            self.assertEqual(line_no, 1)
            self.assertIn("Google / Gemini API Key", desc)
            self.assertEqual(masked, "AIza...5q6R")
        finally:
            os.chdir(old_cwd)

    def test_deleted_secret_not_flagged(self):
        # First commit with a secret
        secret_file = Path(self.test_dir) / "keys.py"
        gem_tok = "AIza" + "SyB1c2D3e4F5g6H7" + "i8J9k0L1m2N3o4P5q6R"
        secret_file.write_text(f'API_VAL = "{gem_tok}"\n')
        subprocess.run(["git", "add", "keys.py"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "add secret", "--no-verify"], cwd=self.test_dir, check=True, stdout=subprocess.DEVNULL)

        # Now remove the secret
        secret_file.write_text('API_KEY = "clean_value"\n')
        subprocess.run(["git", "add", "keys.py"], cwd=self.test_dir, check=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            findings = scan_secrets.scan_staged_changes()
            # Deletion must not be flagged
            self.assertEqual(len(findings), 0)
        finally:
            os.chdir(old_cwd)

    def test_sensitive_file_staged(self):
        env_file = Path(self.test_dir) / ".env"
        env_file.write_text("SOME_VAR=123\n")
        subprocess.run(["git", "add", ".env"], cwd=self.test_dir, check=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            findings = scan_secrets.scan_staged_changes()
            self.assertTrue(any("Sensitive File Staged" in desc for _, _, desc, _ in findings))
        finally:
            os.chdir(old_cwd)


class TestPreCommitHook(unittest.TestCase):
    """Verifies pre-commit hook execution and blocking behavior in a temporary repository."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=self.test_dir, check=True)

        # Copy pre-commit hook into temporary repo
        hooks_dir = Path(self.test_dir) / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_target = hooks_dir / "pre-commit"

        # Point SCANNER in hook to the real scanner script
        scanner_script = str((SCANNER_DIR / "scan_secrets.py").resolve())
        hook_content = f"""#!/bin/sh
SCANNER="{scanner_script}"
python3 "$SCANNER" --staged
SCAN_STATUS=$?
if [ $SCAN_STATUS -ne 0 ]; then
    echo "COMMIT REJECTED" >&2
    exit 1
fi
exit 0
"""
        hook_target.write_text(hook_content)
        hook_target.chmod(0o755)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_hook_allows_clean_commit(self):
        f = Path(self.test_dir) / "hello.py"
        f.write_text("print('All clean')\n")
        subprocess.run(["git", "add", "hello.py"], cwd=self.test_dir, check=True)

        proc = subprocess.run(["git", "commit", "-m", "clean commit"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_hook_blocks_commit_with_secret(self):
        f = Path(self.test_dir) / "leaked.py"
        gem_tok = "AIza" + "SyB1c2D3e4F5g6H7" + "i8J9k0L1m2N3o4P5q6R"
        f.write_text(f'API_VAL = "{gem_tok}" # example comment\n')
        subprocess.run(["git", "add", "leaked.py"], cwd=self.test_dir, check=True)

        proc = subprocess.run(["git", "commit", "-m", "bad commit"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("COMMIT REJECTED", proc.stderr)


if __name__ == "__main__":
    unittest.main()
