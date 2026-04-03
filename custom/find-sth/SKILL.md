---
name: find-sth
description: Investigate a technical question by searching across multiple sources (source code, documentation, academic papers, existing findings) and produce a sourced findings document saved to disk. Use this skill whenever the user asks to "investigate", "find out", "research", "figure out", "what does X support", "how does X work", "why does X differ from Y", or any question that requires digging through code and docs to answer. Also use it when the user asks to compare implementations, trace a behavior through a codebase, or understand hardware/software constraints. This is for discovery work, not fact-checking existing documents (use real-review for that).
license: MIT
---

# Find Something — Technical Investigation Skill

You're investigating a technical question. Your job is to search multiple sources, cross-reference what you find, and produce a sourced findings document — not speculation, not summaries of what you already know, but verified claims with evidence trails.

## Why This Matters

Technical findings documents are only useful if they're trustworthy. The difference between "the accumulator is f32" and "the accumulator is f32 (confirmed at `mma_traits_sm100.hpp:247` and PTX ISA Section 9.7.14.5.14)" is the difference between a claim and evidence. Future readers — including future Claude sessions — need to verify your work without re-doing the investigation.

## Step 1: Clarify the Question

Restate the question in one sentence. If it's vague ("how does attention work"), narrow it to something investigatable ("what accumulator dtypes does the FP4 MMA instruction support on Blackwell?"). If you can't narrow it, ask.

## Step 2: Plan Your Sources

Before grepping anything, identify 2+ source categories to cross-reference. Common source types:

| Source Type | How to Search | Example |
|---|---|---|
| **Source code** | `grep -rn`, read specific files | CUTLASS headers, kernel implementations |
| **Documentation** | Read markdown/RST in the repo | README files, API docs, inline comments |
| **Academic papers** | Read LaTeX `.tex` source files | Method sections, experiment tables, appendices |
| **External docs** | WebFetch (with fallback — see below) | NVIDIA PTX ISA, hardware specs |
| **Existing findings** | Check `findings/`, `docs/`, `results/` directories | Prior investigation outputs |
| **Git history** | `git log`, `git blame` | When something changed, who changed it |

Pick at least 2 categories. A finding confirmed by only one source is a lead; confirmed by 2+ sources is a finding.

### Web Fetch Fallback Rule

If 3 web fetch attempts fail or return truncated content, stop trying. Fall back to local source code — grep through the relevant codebase (e.g., CUTLASS for NVIDIA hardware questions). This is almost always faster and more reliable than fighting with web fetches.

## Step 3: Investigate

Search your planned sources. For each finding:

1. **Record the exact location**: file path with line number, or command that produced the output
2. **Quote the relevant content**: don't paraphrase — include the actual text, code, or value
3. **Note what it means**: one sentence interpreting the finding in context of the question

When you find something surprising or contradictory, that's a signal to dig deeper, not to pick the more convenient answer. Cross-reference against another source.

## Step 4: Write the Findings Document

Save to `findings/YYYY-MM-DD-[descriptive-slug].md` (or `docs/findings/` if the project uses that convention). Create the directory if needed.

The format depends on what you found. Use the structure that fits:

### For comparisons across versions/implementations:

```markdown
# [What's Being Compared]

[One paragraph of context: what, why, methodology]

## Comparison Table

| Dimension | Variant A | Variant B | Variant C |
|-----------|-----------|-----------|-----------|
| [aspect]  | [value] — `file:line` | [value] — `file:line` | ... |

## Key Differences
1. **[Difference]** — [evidence]
2. **[Difference]** — [evidence]
```

Use `input × input → accumulator` notation for dtype/GEMM tables (e.g., `FP8 × FP8 → FP32`).

### For hardware/software constraint investigations:

```markdown
# [Component] — [Constraint Type] Reference

**Date:** YYYY-MM-DD
**Source:** [primary source files]

## Summary
[2-3 sentences: what the constraint is, why it matters]

## Evidence
1. **[Source 1]:** `file:line` — [what it shows]
2. **[Source 2]:** `file:line` — [what it confirms]

## Implications
[What this means for the project]
```

### For "why does X differ from Y" investigations:

```markdown
# [Question]

## Methodology
[What sources were checked, in what order]

## Findings
1. **[Root cause]** — [evidence with sources]

## Conclusion
[Direct answer to the original question]

## Open Questions
[What wasn't resolved]
```

### General rules for all formats:

- **Every factual claim needs a source.** `file:line`, command output, or document reference.
- **Skip sections that are empty.** Don't write "N/A" — just omit.
- **Include Open Questions** if anything remains unresolved. Future sessions need to know what's left.
- **Save to disk, not just stdout.** The whole point is producing a referenceable document.

## Step 5: Verify Before Finishing

Before declaring the investigation done, re-read your findings document and check:

- [ ] Does every claim cite a specific source?
- [ ] Did you cross-reference at least one key finding against a second source?
- [ ] Is the document saved to disk at a sensible path?
- [ ] Would someone reading this in 2 weeks know exactly where to look to verify each claim?

If any check fails, fix it.
