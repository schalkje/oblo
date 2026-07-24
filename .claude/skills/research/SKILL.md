---
name: research
description: Run the research phase for a post — desk research, content plan, PoC code for the author to run. Args - the post slug.
---

# Research

Precondition: `posts/<slug>/idea.md` exists and its open questions are answered (`status: ideation`).

1. Launch the **researcher** agent on the post folder.
2. Present to the author: the content plan, the source list, and — if any — the PoC code with run instructions. Remind the author to run the PoCs and paste outputs/screenshots into `research.md` → "Results & evidence" (screenshots into `images/`).
3. When the author confirms the evidence is sufficient (no blocking entries under "Gaps / still needed"), set `status: writing` in `meta.yaml`.
