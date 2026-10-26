---
name: billion-context
description: Multi-generational incremental hierarchical context compression, active context pruning (acp-kernel), prefix-cache preservation, and lossless reversibility via decompress-to-file. Use for long-running marathon agent sessions, token budget management, and CLOUD_CODE_URL launcher integration.
metadata:
  origin: ranxianglei/billion-context
---

# Billion-Context: Incremental Hierarchical Compression & Active Context Pruning

Use this skill when managing long-lived agent sessions, marathon coding workflows, or massive context windows that risk token exhaustion, KV-cache degradation, or latency blowups.

Based on the Active Context Pruning engine (`acp-kernel`) from `ranxianglei/billion-context`.

---

## 1. Core Architectural Doctrines

### 1.1 The Fold Layout (Pagoda Tiering)
Never rely on destructive sliding-window truncation or whole-history re-summarization. Structure the attention window as **The Fold**:
- **Tier-1 Blocks**: Direct summaries of contiguous message increments (absorbing raw turn history).
- **Tier-2 Blocks**: Recursive summaries of older Tier-1 blocks once they accumulate.
- **Tier-3 Blocks**: Top-level meta-summaries of Tier-2 blocks.
- **Verbatim Recent Zone**: A rolling ~30,000 to 50,000 token active operational window kept completely untouched for syntactic precision, line numbering, and tool execution.

*Measured distribution in production*: Tier-1 holds ~92% of resident digest space, Tier-2 ~7%, Tier-3 <1%, while Tier-2+3 carry 37% of represented historical lineage. Resident context grows sublinearly ($\mathcal{O}(\log N)$) rather than linearly.

### 1.2 Increment-Only Compression
- **Growth-Gated Trigger**: Trigger compression only when newly consumed context exceeds the threshold floor ($\ge 22.5\text{K}$ tokens).
- **Delta-Only Invariant**: Compress *only* the new delta since the previous checkpoint. Never re-abstract existing summary blocks during standard turns.
- **Median Digest Size**: A single fold decision emits a compact digest of ~185 tokens.

### 1.3 KV-Cache Prefix Preservation
- Conversation history is strictly append-only.
- Folding deactivates compressible ranges into structured digest blocks without altering or invalidating the preceding conversation prefix.
- Preserves a **>94% active cache-read rate**, eliminating full-window prefill latency penalties.

### 1.4 Lossless Reversibility & `decompress-to-file`
- Every digest block maintains transitive pointers (`effectiveMessageIds`) mapping back to the exact original messages.
- **Zero In-Context Bloat**: When detailed historical source code or past outputs are needed, do NOT decompress them back into the active context window.
- **Disk Offloading**: Stream verbatim raw messages to disk (`/tmp/` or project `data/` via `decompress-to-file`), then inspect them programmatically using targeted Python or shell scripts (Section 5 "Think in Code").

### 1.5 Cryptographic Thinking Signature Integrity
- Gemini `thoughtSignature` parts and Anthropic `thinking` / `redacted_thinking` blocks are byte-for-byte signature verified by API endpoints.
- **Never modify, trim, re-layout, or filter thinking payloads**. Any alteration desynchronizes the signature and immediately invalidates/bricks the session.

---

## 2. Operational Tooling & Protocol

When `billion-context` / `acp-kernel` is integrated, the agent utilizes four core primitives:

### `acp_status`
Reports real-time context allocation:
- **Composition Breakdown**: Distribution across system instructions, user prompts, assistant text, thinking blocks, and tool results.
- **Compressible Units**: Identifies eligible ranges that satisfy the growth floor ($\ge 22.5\text{K}$ tokens).
- **Block Hierarchy**: Lists active Tier-1, Tier-2, and Tier-3 blocks.

### `compress`
Executes incremental folding over candidate ranges:
- **Input**: `range_start`, `range_end`, optional topic tag.
- **Output**: Compact summary block (median 185 tokens) carrying `effectiveMessageIds`.
- **Constraint**: Cannot fold into the protected root intent or the recent verbatim active zone.

### `decompress` / `decompress_to_file`
Restores historical context:
- `decompress(blockId)`: Re-activates source messages into context (reserved only for small, vital conversational turns).
- `decompress_to_file(blockId, target_path)`: **Preferred default**. Writes the verbatim uncompressed messages to disk for script-based inspection.

### `search_context`
Performs keyword and semantic retrieval across deactivated block summaries and recent history without forcing full decompression.

---

## 3. Antigravity CLI Integration (`bili antigravity`)

The Antigravity CLI (`agy`) runs a closed-source Go language server communicating via Google internal endpoints. `billion-context` connects without certificate MITM:

1. **Environment Override**:
   ```bash
   export CLOUD_CODE_URL="http://127.0.0.1:9090/bili/https://daily-cloudcode-pa.googleapis.com"
   ```
2. **Wire Interception**:
   The proxy intercepts Google-native `:streamGenerateContent` endpoints by URL path, applying incremental folding to streamed responses transparently.
3. **Fallback Route**:
   If `CLOUD_CODE_URL` is omitted, configure HTTPS proxy with MITM domain `daily-cloudcode-pa.googleapis.com` (note: `cloudcode-pa.googleapis.com` 400s on internal RPCs).

---

## 4. Best Practices for Marathon Agent Sessions

1. **Input Sandboxing First**: Follow Section 5 of `AGENTS.md`—intercept raw bulk data to disk before it reaches conversation context.
2. **Periodic Checkpoint Audits**: In sessions exceeding 20 turns or 50,000 tokens, run `check_acp_status.py` or inspect context metrics to verify that prior milestones are properly digested.
3. **Single Fold Invariant**: Ensure past milestones are folded once into Tier-1; do not re-summarize past summaries unless escalating to Tier-2 pagoda compaction.
