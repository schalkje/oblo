---
name: new-post
description: Start a new post from a seed idea — creates the post folder and grills the idea (ideation phase). Args - the seed idea in a couple of sentences, or a topic from blog-ideas.md.
---

# New post (ideation)

1. Derive a short kebab-case slug from the idea.
2. Create `posts/<slug>/` by copying `posts/_template/` (idea.md, research.md, post.md, meta.yaml); create `images/`, `poc/`, and `versions/` as needed later, not now. Fill `meta.yaml`: title, slug, type (`blog` unless the author says `professional`), `status: ideation`, `created:` today.
3. Launch the **idea-grinder** agent with the seed idea and the post folder path.
4. Report the grilled idea back to the author, including the open questions the grinder raised. Ask the author to answer them — do not proceed to research until the definition of done is agreed.
5. If the idea came from `blog-ideas.md`, mark it there with a link to the post folder.
