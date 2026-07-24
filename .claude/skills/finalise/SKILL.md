---
name: finalise
description: Finalising phase — tone-of-voice pass, reference check, summary and teaser. Args - the post slug.
---

# Finalise

Precondition: `status: finalising`.

Run these, reporting each result to the author:

1. **tone-editor** agent: tone pass on the draft; present its change list for veto.
2. **reference-checker** agent: verify all links, fill gaps with official docs; present its checklist.
3. Write `teaser.md` in the post folder: a short LinkedIn teaser (2–4 sentences + link placeholder) and a one-paragraph excerpt for WordPress. Both must follow `tone-of-voice.md` — a teaser in corporate voice defeats the purpose.
4. Image check: every image referenced exists in `images/`; propose generation/tuning tasks for missing ones.
5. Present the finalised post for approval. Only the author moves it forward: on approval run `/publish <slug>`.
