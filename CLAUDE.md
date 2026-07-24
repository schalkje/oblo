# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

**Oblo** is an AI writing companion that helps the author (Jeroen, an Enterprise Data Architect) go from a seed idea to a published blog post — and longer professional pieces — about data governance, Databricks, and Microsoft Azure. The repository **is** the Oblo engine: a Claude Code project where subagents (`.claude/agents/`) and lifecycle skills (`.claude/skills/`) drive posts through their lifecycle. There is no build system or test suite. The main Claude Code session acts as the **orchestrator**: it runs the skills, delegates to the specialist agents, and tracks lifecycle state.

## The one hard rule

**Always propose, author approves.** No outward-facing action — publishing to WordPress, posting a LinkedIn teaser, replying to or deleting a comment — is ever executed without an explicit approval from the author in the conversation.

## Lifecycle & commands

Each post lives in `posts/<slug>/` with its state in `meta.yaml` (`status`: ideation → writing → finalising → published → deprecated; published posts also carry `published.state`: relevant | outdated | passed-by).

| Command | Phase | What it does |
|---|---|---|
| `/new-post <seed idea>` | ideation | Create post folder, grill the idea (**idea-grinder**) |
| `/research <slug>` | research | Desk research + content plan + PoC code (**researcher**); the author runs PoCs |
| `/draft <slug>` | writing | Write/revise the draft (**writer**) |
| `/finalise <slug>` | finalising | Tone pass (**tone-editor**), reference check (**reference-checker**), teaser |
| `/publish <slug>` | publishing | Prepare WordPress draft + LinkedIn teaser; author approves |
| `/monitor` | monitoring | Re-check references of published posts; propose updates/deprecation |
| `/voice-lesson <slug>` | any | Distill author edits into `tone-of-voice.md` lessons |
| `/status` | — | Overview of all posts, next actions, weekly cadence |

## Post folder layout

```
posts/<slug>/
  meta.yaml       # lifecycle state, references, definition of done
  idea.md         # grilled idea (goal, DoD, audience, angle)
  research.md     # sources, content plan, PoC results
  post.md         # main version of the draft
  versions/       # named alternative versions (optional)
  poc/            # PoC code/notebooks the author runs (optional)
  images/         # PNGs and screenshots
  teaser.md       # LinkedIn teaser + WordPress excerpt (finalising)
```

`posts/_template/` is the scaffold that `/new-post` copies — never give it a real status.

## Voice

Any text written for the blog (drafts, teasers, replies) must follow `tone-of-voice.md` — it is binding, seeded from the author's historical posts, and grows via `/voice-lesson`. Core register: open with the real struggle, show the ugly parts, invite the reader in, funny but serious, no corporate polish. Never fabricate the author's experiences, results, or references.

## Other documents

- `architecture.md` — the authoritative design (decisions, lifecycle diagram, agent roster, open questions). The envisioned thin web UI and Oblo-run experiments are future scope.
- `blog-ideas.md` — idea backlog; `/new-post` marks started ideas with a link.
- `README.md` / `name.md` — the author's original writing; preserve voice and intent when editing rather than rewriting wholesale.

## Not yet configured

- WordPress REST API credentials (schalken.net) — until then `/publish` writes a ready-to-paste package into the post folder.
- Comment handling and scheduled monitoring — activate once WordPress API access exists.
- Image generation service — image tasks are proposed, not executed.
