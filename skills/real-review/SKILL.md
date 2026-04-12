---
name: real-review
description: Fact-check written content (GitHub issues, docs, reports, posts) by verifying every claim, number, link, code reference, and conclusion against actual evidence. Use this skill when the user asks to "review", "fact-check", "verify", or "audit" written content for accuracy. Also use it when the user says things like "check this post", "is this correct", "review before publishing", or "make sure the claims are right". This skill is about factual accuracy of prose, not code review or style review.
---

# Real Review: Fact-Check Written Content

You are performing a rigorous factual audit of written content. The goal is to
catch every inaccurate claim before it gets published — wrong numbers, broken
links, misattributed sources, code references that don't match the actual code,
and conclusions that aren't supported by the evidence.

This matters because published content (issue posts, docs, reports) gets read by
others who trust it. A single wrong line number or fabricated section reference
undermines the credibility of everything else in the document.

## How the Review Works

### Phase 1: Extract Every Verifiable Claim

Read the content and build a checklist of every specific, verifiable assertion.
These fall into categories:

**Code references**: file paths, line numbers, function/class names, code snippets,
inline PTX/assembly, template signatures. These are the highest-value targets
because they're the most likely to be wrong and the easiest to check.

**Numbers and measurements**: section numbers, counts ("exactly two specializations"),
sizes, performance claims, ratios ("2x faster").

**Links and URLs**: do they resolve? Do they point where claimed?

**Cross-source consistency**: when the content cites multiple sources, do they
actually agree? Or does Source A say something subtly different from Source B?

**Causal claims and conclusions**: "X is true because Y" — does Y actually
support X? Are there unstated assumptions?

**Scope and attribution**: does the content claim a source says something the
source doesn't actually address? (e.g., citing a doc about instruction X as
evidence for instruction Y)

### Phase 2: Verify Each Claim Against Primary Sources

For each claim on the checklist, go to the actual source and check it. This means:

- **Read the actual file** at the cited line numbers. Don't trust your memory or
  prior context — re-read it fresh. Line numbers drift across edits.
- **Run the actual command** if a link or URL is cited. Check it resolves.
- **Grep for the actual pattern** if the content claims "zero matches" or
  "the only occurrence". Verify the absence, don't assume it.
- **Check exact strings** character by character for code snippets, instruction
  mnemonics, function signatures. A single wrong character matters — including
  struct names, dimension numbers (16x8 vs 16x32), and suffix variations.
- **Compare code descriptions to actual code literally.** If content says "the
  formula is `(head_dim) ** (-0.5)`" but the code actually says
  `(shape[-1] * 2) ** (-0.5)`, flag it — even if the result is mathematically
  equivalent. The reader expects the description to match what they'll see in
  the source. A "mathematically equivalent but literally different" description
  is misleading when someone goes to read the code.

Be efficient: once you have 2-3 corroborating sources for a claim, move on.
Don't search for a fourth just to be thorough — diminishing returns waste time.

For each claim, record one of:
- **Verified**: cite the exact evidence (file, line, content)
- **Incorrect**: state what was claimed vs what the source actually says
- **Unverifiable**: the source doesn't contain enough information to confirm or
  deny this claim. Be honest about this — saying "unverifiable" is better than
  guessing.
- **Misleading**: technically true but presents a distorted picture. Use this
  when the claim isn't outright wrong but would give a reader the wrong mental
  model. Examples: citing a correct number from the wrong column, describing a
  formula that's mathematically right but doesn't match the literal code, using
  a parent section number when the content lives three levels deeper. Don't
  over-flag — imprecision is only "misleading" if it would actually trip someone
  up.

### Phase 3: Report

Produce two things:

#### 1. Itemized Audit

For each claim, show:
- The claim as stated in the content
- The verdict (Verified / Incorrect / Unverifiable / Misleading)
- The evidence: file path + line number, or URL, or explanation
- For incorrect/misleading claims: what the correction should be

Group by severity: Incorrect first, then Misleading, then Unverifiable, then
Verified. The user's attention should go to problems first.

#### 2. Corrected Version

If there were any Incorrect or Misleading findings, produce a corrected version
of the content with problems fixed. For each fix, add a brief inline comment
explaining what changed and why so the user can review the diffs.

If everything checked out, say so clearly — don't invent problems.

## Common Traps to Watch For

These are failure modes that came up in real reviews. Keep them in mind:

**Names that are almost right.** Struct names, class names, and identifiers
often have similar-looking variants. `SM120_16x8x64_TN_VS` and
`SM120_16x32x64_TN_VS_NVFP4` differ by one dimension number and a suffix — but
they're completely different structs. Compare character by character: the
dimension, the prefix, the suffix, the underscores. If the content names a
specific identifier, search for it literally and verify the match.

**Descriptions that are right in spirit but wrong in code.** When content says
"the formula is X" and the code actually implements an equivalent expression Y,
that's worth flagging. Someone reading the doc and then looking at the code will
be confused when they don't match. The description should match what the reader
will see, not just what they'll compute.

**Conflating similar but different things.** Two instructions might target the
same hardware but have different PTX encodings, different section numbers, or
different constraints. A doc about `tcgen05.mma` is not a doc about `mma.sync`
even if the underlying tensor core is the same. Flag when a source is being used
outside its actual scope.

**Correct-but-incomplete lists.** If content says "supported types: A, B" and
the source actually says "supported types: A, B, C, D", the claim isn't wrong —
it's just incomplete. Mark this as Misleading only if the omission matters for
the reader's purpose (e.g., they might choose C if they knew about it). Don't
flag it as Incorrect.

**Line numbers that have drifted.** If the content was written against an older
version of a file, the line numbers may be off. Check the actual content at
those lines, not just whether the line number is in range.

**Grammar-based claims.** When the content says "X is the only valid value" for
some parameter, check whether this is because the spec literally hardcodes it
(like a literal in a grammar rule) vs. it being the only value that appears in
one implementation. These are very different levels of certainty.

**Overclaiming from absence.** "A grep returns zero matches" proves something
doesn't exist *in the searched scope*. It doesn't prove it can't exist or
isn't valid. Note the scope of the search.

**Web fetcher hallucinations.** If evidence was gathered via web fetching of
large documents, the fetcher may have summarized or fabricated content from
truncated pages. Treat web-fetched "quotes" with suspicion unless they can be
cross-referenced with local files.

## What NOT to Review

This skill is about factual accuracy. Don't:
- Rewrite for style, tone, or formatting (unless the user asks)
- Add new content or expand the scope
- Second-guess judgment calls that are clearly labeled as such
- Flag things as "unverifiable" when they're clearly common knowledge
