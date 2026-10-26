---
name: sensitive-data-guard
description: Scan repositories, staged git commits, and codebases for exposed API keys, private credentials, tokens, PII, and uncommitted .env files. Enforce pre-commit zero-leak invariants and git history purging.
metadata:
  origin: fish-coding-agent
---

# Sensitive Data Guard: Secret Leak Prevention & Security Audit

Use this skill whenever you are preparing to commit code to git, onboarding to a repository with environment variables, auditing code for credential exposure, or purging accidentally committed secrets from git history.

---

## 1. Quick Audit Protocol

Before running any git commit or push, run the built-in secret scanner script or inspect staged changes:

```bash
# 1. Audit staged diff for credentials
git diff --cached | python3 ~/.gemini/config/plugins/sensitive-data-guard/skills/sensitive-data-guard/scripts/scan_secrets.py --stdin

# 2. Or audit the entire working directory
python3 ~/.gemini/config/plugins/sensitive-data-guard/skills/sensitive-data-guard/scripts/scan_secrets.py .
```

---

## 2. Pre-Commit Hygiene Checklist

Always verify these 4 checkpoints before concluding git workflows:

1. **Verify `.gitignore` Coverage**:
   Ensure `.env`, `*.key`, `*.pem`, and `*credential*` are ignored. Test with:
   ```bash
   git check-ignore -v .env
   ```
2. **Review Staged Files by Name**:
   ```bash
   git status --short
   ```
   Ensure no `.env`, `.pem`, config with plaintext passwords, or secret files are marked as `A` (added) or `M` (modified).
3. **Explicit File Staging**:
   Stage files individually:
   ```bash
   git add src/main.py tests/test_main.py
   ```
   **NEVER** run `git add .` or `git add -A` blindly.
4. **Inspect Outgoing Commit Diffs**:
   ```bash
   git log -n 1 -p
   ```

---

## 3. Safe Environment Variable Pattern

### Python Setup
```python
import os
from dotenv import load_dotenv

# Load .env locally (never committed)
load_dotenv()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("Missing required environment variable: API_KEY")
```

### TypeScript / Node Setup
```typescript
import dotenv from "dotenv";
dotenv.config();

const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error("Missing required environment variable: API_KEY");
}
```

---

## 4. Emergency Remediation (Leaked Secret in Git History)

If a sensitive token was accidentally committed to git history:

1. **Rotate Credential Immediately**: Revoke the key at the provider dashboard (AWS, OpenAI, GitHub, etc.). Do not wait for git cleansing.
2. **Purge from Git History using `git-filter-repo`**:
   ```bash
   # Install if needed: pip install git-filter-repo
   git filter-repo --invert-paths --path <path-to-leaked-file>
   ```
3. **Force Push Clean Branches**:
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```
