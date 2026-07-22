# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

**Oblo** is an AI writing companion that helps the author (Jeroen, an Enterprise Data Architect) go from a seed idea to a published blog post — and longer professional pieces — about data governance, Databricks, and Microsoft Azure. The project is in the **design phase**: the architecture is decided (see below) but there is no code, build system, or test suite yet. Do not look for commands to build, lint, or test; they don't exist.

## Documents

- `architecture.md` — **the authoritative design.** Decisions table, lifecycle (with mermaid state diagram), agent roster with model choices, autonomy rules, publishing, comment handling, and open questions. Read this first.
- `tone-of-voice.md` — the living style guide every writing agent must follow; grows via voice lessons from author edits.
- `README.md` — original project goal and audience statement.
- `name.md` — the product name **Oblo** ("Organize Blog") and branding rationale.
- `blog-ideas.md` — running list of blog post ideas, organized by topic with hashtags.
- `assets/` — images (e.g., the Oblo logo).

## Key design decisions (summary — details in architecture.md)

- **Hybrid foundation**: CLI agent engine (Claude Code / Claude Agent SDK, multi-agent) + thin local web UI for markdown/mermaid rendering, diffing, and review (MarkRead-based).
- **Publishing**: WordPress at schalken.net via REST API (as drafts) + LinkedIn teasers. **Always propose, author approves** — no outward-facing action (publish, teaser, comment reply/delete) executes without explicit approval.
- **Co-writing model**: the author seeds an idea in a couple of sentences; Oblo expands, restructures, checks references, guards tone, and suggests improvements. The author's edits are captured as voice lessons that update `tone-of-voice.md`.
- **Storage**: markdown + PNG in git; multiple named versions of a post can coexist alongside a main version.
- **Full lifecycle** including monitoring (reference drift, comments) and deprecation.
- **PoC experiments**: Oblo writes the code/notebooks; the author runs them in Databricks/Azure. Oblo executing experiments itself is a documented future step, not current scope.

## Working in this repo

- `architecture.md` is maintained; `README.md` and `name.md` are the author's original writing — preserve voice and intent when editing rather than rewriting wholesale.
- Any writing produced for the blog must follow `tone-of-voice.md`. The audience is knowledgeable — avoid oversimplifying, except when explaining something the author is just learning.
