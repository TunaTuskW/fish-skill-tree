---
name: security-guard
description: >-
  Automated Python AST, Shell, and JavaScript static security and malware scanner
  for auditing repositories, third-party skills, and plugins against dynamic code
  execution (eval/exec/compile), obfuscated Base64 payloads, shell injection,
  unchecksummed binary downloads, unpinned npx @latest packages, insecure
  pickle/YAML deserialization, SSRF/webhook exfiltration, and sensitive path
  traversal. Use whenever auditing codebases, skills, extensions, or staged Git
  changes for malware, backdoors, or token drainers.
---

# Security Guard — AST & Malware Scanner

Use this skill to deterministically scan repositories, skills, plugins, or staged Git changes for malware, embedded payloads, supply-chain risks, and credential exfiltration sinks in a single command—replacing ad-hoc manual `grep` loops.

## Quick Start Commands

### 1. Full Directory or Repository Audit
```bash
python3 scripts/scan_security_ast.py --target <path_to_repo_or_skill>
```

### 2. Audit with Structured JSON Report
```bash
python3 scripts/scan_security_ast.py --target <path> --json reports/ast_audit.json
```

### 3. Pre-Commit Staged Changes Scan
```bash
python3 scripts/scan_security_ast.py --staged
```

### 4. Combined Dual-Pass Audit (AST Malware + High-Entropy Secrets)
Always pair AST scanning with `sensitive-data-guard` secret scanning when auditing new skills or before pushing commits:
```bash
python3 scripts/scan_security_ast.py --target <path> && \
python3 "[skill]/sensitive-data-guard/scripts/scan_secrets.py" <path>
```

## Detection Rules & Threat Coverage

| Rule ID | Target | Threat Class |
| :--- | :--- | :--- |
| `DYNAMIC_CODE_EXECUTION` | Python AST | `eval()`, `exec()`, `compile()`, `__import__()`, `importlib.import_module()`, including `builtins` aliases |
| `OBFUSCATED_DYNAMIC_EXEC` | Python AST | Composite `base64.b64decode` / `unhexlify` / `decompress` routed into dynamic execution sinks |
| `SHELL_INJECTION_RISK` | Python AST | `subprocess.Popen` / `run` / `call` with `shell=True` (including wildcard imports) |
| `SHELL_EXECUTION` | Python AST | `os.system()`, `os.popen()`, `pty.spawn()` |
| `INSECURE_DESERIALIZATION_PICKLE` | Python AST | `pickle.load()`, `pickle.loads()`, `_pickle` deserialization |
| `INSECURE_DESERIALIZATION_YAML` | Python AST | `yaml.unsafe_load()`, `yaml.full_load()`, or `yaml.load()` without `SafeLoader` |
| `OUTBOUND_EXFILTRATION_SINK` | Python AST | Webhook collectors (`webhook.site`, Discord/Telegram webhooks, `pipedream.net`) & cloud IMDS (`169.254.169.254`) |
| `CREDENTIAL_EXFILTRATION_FLOW` | Python AST | Reading `os.environ` / `os.getenv` and transmitting over outbound HTTP/socket calls |
| `SENSITIVE_PATH_TRAVERSAL` | Python / Shell / JS | Accessing `~/.ssh/id_rsa`, `~/.aws/credentials`, `~/.gemini/config/auth.json`, `/etc/shadow` |
| `UNCHECKSUMMED_REMOTE_EXEC` | Shell | `curl` / `wget` piped directly into `sh`, `bash`, `zsh`, `/bin/bash`, or `env bash` |
| `UNPINNED_BINARY_EXECUTION` | Shell | Downloading remote binaries and granting `chmod +x` without `sha256sum` / `shasum` / `verify_sha256` |
| `SUPPLY_CHAIN_UNPINNED_PACKAGE` | Shell / Markdown | Unpinned dynamic execution (`npx ...@latest`, `pnpx ...@latest`, `bunx ...@latest`) |
| `JS_DYNAMIC_EVAL` / `JS_VM_DYNAMIC_EXECUTION` | JS / TS | `eval()`, `new Function()`, `vm.runInContext()`, remote `import('https://...')` |

## Exit Codes
- `0`: Clean — zero vulnerabilities detected.
- `1`: Malware or high/critical security risk detected (blocks commit in `.git/hooks/pre-commit`).
