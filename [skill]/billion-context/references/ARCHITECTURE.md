# Architecture Specification: Active Context Pruning (`acp-kernel`)

## 1. Mathematical Foundations of The Fold

Standard sliding windows and naive auto-compaction suffer from zero asymptotic retention:
$$\lim_{k \to \infty} R_k = 0$$
where $R_k$ is the retention of early turn information at compaction round $k$.

In contrast, **The Fold** implements multi-generational tiered distillation (analogous to an LSM-tree):
- Raw messages are folded **once** into Tier-1 digest blocks.
- When Tier-1 mass reaches capacity, blocks are compacted into Tier-2 blocks with explicit block-lineage pointers (`directBlockIds`).
- Tier-2 blocks recursively compact into Tier-3 blocks.

Because the compression ratio at each tier is high ($\sim 10:1$ to $50:1$), total resident digest mass $M(N)$ for $N$ turns satisfies:
$$M(N) = \mathcal{O}(\log N)$$
while retaining non-zero asymptotic information via transitive message pointers:
$$R_\infty > 0$$

---

## 2. Block Lifecycle & State Schema

A `CompressionBlock` conforms to the following schema:

```typescript
interface CompressionBlock {
  blockId: string;               // Unique block identifier (e.g., "b00042")
  runId: string;                 // Active session run identifier
  tier: 1 | 2 | 3;               // Pagoda hierarchy level
  topic: string;                 // Concise topic descriptor
  summary: string;               // Verbatim digest text (median ~185 tokens)
  directMessageIds: string[];    // Immediate message IDs summarized
  effectiveMessageIds: string[]; // Transitive closure of all covered message IDs
  directBlockIds: string[];      // Source blocks if tier >= 2
  createdAt: number;             // Timestamp (ms)
  survivedCount: number;         // Number of compaction cycles survived
  generation: "young" | "old";   // Generational tag
  active: boolean;               // True if rendered in current prompt
}
```

---

## 3. Order-Centric Reconciliation Engine

When conversation histories are serialized, re-minted, or modified across turns, relying strictly on message ID equality or naive content hashes causes catastrophic unfolding:
- **Order First**: Position and sequential continuity are the primary carriers of identity across turns.
- **Content Hashes Second**: SHA-256 and SimHash word-shingle sketches serve as per-cell confirmation gates.
- **Soft Failure**: A single mismatched cell voids only that cell's claim; adjacent verified spans resync automatically.
- **Thinking Blocks**: Byte-for-byte immutability is enforced. Any modification to signature-bearing chunks invalidates backend crypto checks.
