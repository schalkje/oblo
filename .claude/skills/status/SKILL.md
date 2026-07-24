---
name: status
description: Overview of all posts and their lifecycle state, plus the suggested next action per post.
---

# Status

1. Read every `posts/*/meta.yaml` (skip `_template`).
2. Render a table: slug, title, type, status (+ published.state where published), created/published date.
3. For each post, suggest the next action based on status:
   - `ideation` → answer open questions, then `/research <slug>`
   - `writing` → `/draft <slug>`; check for unanswered `<!-- AUTHOR: -->` markers
   - `finalising` → `/finalise <slug>` or `/publish <slug>`
   - `published` → nothing, unless monitoring flagged it (`outdated` → propose update or deprecation)
4. Also surface: ideas in `blog-ideas.md` not yet started, and the weekly cadence — days since the last published post (the goal is one per week).
