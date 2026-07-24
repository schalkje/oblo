---
name: publish
description: Publishing phase — prepare the WordPress draft and LinkedIn teaser for author approval. Nothing goes public without explicit approval. Args - the post slug.
---

# Publish

Precondition: `status: finalising` and the author approved the finalised post.

**Hard rule: always propose, author approves. Never publish, post, or schedule anything without an explicit go from the author in this conversation.**

1. Convert `post.md` to WordPress-ready content (HTML or block markup), including title, excerpt, categories, tags, and featured-image reference.
2. If WordPress REST API credentials are configured (see `architecture.md` open questions): create the post on schalken.net **as a draft**, and give the author the preview link. If not configured: write the ready-to-paste package to `publish/wordpress.html` in the post folder.
3. Present the LinkedIn teaser from `teaser.md` with the (future) post URL filled in, copy-paste ready.
4. After the author confirms the post is live: fill `published.url`, `published.date`, `published.state: relevant` in `meta.yaml` and set `status: published`.
