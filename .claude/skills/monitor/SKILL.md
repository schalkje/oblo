---
name: monitor
description: Monitoring phase — re-check references of published posts and flag drift; propose updates or deprecation. Run periodically (manually for now).
---

# Monitor

For every post with `status: published`:

1. Launch the **reference-checker** agent on the post folder (monitoring mode): re-verify all `references` in `meta.yaml`.
2. If references are dead or their content drifted (especially vendor documentation), assess impact on the post's claims.
3. Propose, per affected post — never act without approval:
   - minor drift → a concrete update (which sections, what changes), keep `published.state: relevant`
   - significant drift → set `published.state: outdated` in `meta.yaml` and propose an update plan
   - topic passed by → set `published.state: passed-by` and propose deprecation
4. Comment handling is part of this phase once WordPress API access is configured (see `architecture.md`) — retrieve comments, classify (spam/unrelated/real), and draft replies for approval.

Later this becomes a scheduled job; for now the author runs `/monitor` manually.
