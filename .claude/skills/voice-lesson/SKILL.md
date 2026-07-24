---
name: voice-lesson
description: Distill the author's recent edits on a post into voice lessons that update tone-of-voice.md. Args - the post slug (or a file path).
---

# Voice lesson

Run after the author has hand-edited a draft that Oblo wrote.

1. Launch the **tone-editor** agent in voice-lesson mode: diff the author's edits against Oblo's previous version (use `git diff`/`git log` on the post file; the pre-edit version is the last commit authored by Oblo, or ask the author which revision to compare).
2. The agent appends distilled lessons to `tone-of-voice.md` → "Voice lessons (from edits)" and updates rules/phrasings where a lesson generalizes.
3. Report the new lessons to the author for confirmation; remove any the author rejects.
