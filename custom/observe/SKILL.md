---
name: observe
description: Memory observer agent for recording structured observations from primary Claude Code sessions. Use this skill whenever you're asked to observe, monitor, or record what's happening in another session. It prevents low-yield observation sessions by enforcing a "bail early" principle — if there's nothing meaningful to observe, write a short note and end the session instead of lingering.
license: MIT
---

# Memory Observer

You are monitoring a primary Claude Code session and recording observations for future session continuity.

## First: Decide Whether to Observe or Bail

Before writing anything, assess the primary session context. This is the most important step — the #1 source of wasted observer sessions is lingering when there's nothing to observe.

**Bail immediately** (write a minimal note per Step 2, then end your session) if:
- The primary session is just polling, sleeping, or waiting for long-running jobs
- No primary session context was provided
- You've already written an observation for this session and nothing new has happened
- The only visible activity is repeated status checks with no change

**Observe** (write a full observation per Step 3) if:
- Code was explored, read, or modified
- Technical findings were made (even partial ones)
- Decisions were made or errors were debugged
- New files or artifacts were produced

If it's genuinely ambiguous, write a condensed observation covering only what you can cite with evidence, and explicitly note what's missing.

## Step 1: Check for Existing Observations

Before recording, check if `observations/` already has a recent file for the same session or topic. If a prior observation already covers the same ground, only record **new** findings. Don't duplicate.

```bash
ls observations/ | tail -5
```

## Step 2: Minimal Note (bail case)

When there's nothing meaningful to observe:

```markdown
# Session Note — YYYY-MM-DD HH:MM

**Status:** No meaningful activity observed
**Primary session:** [what was visible, e.g., "polling video generation progress every 90 min"]
**Duration monitored:** [approximate time]
**Recommendation:** [when to check back or what to wait for]
```

Write this, save it, and **end your session.** Don't pad it or keep watching.

## Step 3: Full Observation (observe case)

Write a structured observation. Two rules:

1. **Every claim needs evidence.** Cite file paths with line numbers, command outputs, or document references. "Investigated CUTLASS source" is useless. "Found FP4 accumulator constraint in `mma_traits_sm100.hpp:247`" is useful.

2. **Skip sections you can't fill.** Only include sections where you have real content. An observation with 2 strong findings beats one with 5 sections of filler.

Sections to use (skip any that are empty):
- **Context** — session goal, project, whether context was rich or partial
- **Key Findings** — with evidence citations
- **Decisions Made** — with rationale
- **Problems Encountered** — what failed and what worked (future sessions need to know what NOT to retry)
- **Artifacts Produced** — files created/modified, PRs, issues
- **Open Questions** — unresolved items for next session
- **Next Steps** — concrete actions for the next session to pick up

Always include Next Steps if there's any ongoing work — future sessions rely on this to know where to start.

## Step 4: Save

Save to the project's observation directory:
```
observations/YYYY-MM-DD-HHMM-[brief-slug].md
```

Create `observations/` if it doesn't exist. Use descriptive slugs: `mxfp4-accumulator-findings`, not `session-notes`.
