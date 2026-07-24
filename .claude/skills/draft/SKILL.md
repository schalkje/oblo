---
name: draft
description: Write or revise the draft for a post (writing phase). Args - the post slug, optionally a named version or a specific revision instruction.
---

# Draft

Precondition: `status: writing` (or later, for revisions).

1. Launch the **writer** agent on the post folder. Default target is `post.md` (the main version); if the author asked for a named variant, target `versions/<name>.md` instead.
2. After the draft lands, list every `<!-- AUTHOR: ... -->` marker for the author to fill in with lived detail.
3. The author edits freely. After author edits, offer to run `/voice-lesson <slug>` so the edits improve `tone-of-voice.md`.
4. When the author says the draft is content-complete, set `status: finalising`.
