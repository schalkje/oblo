# Idea: Declarative pipelines on Databricks — the whole thing in SQL

## Seed (author's own words, a couple of sentences)

From the backlog (`blog-ideas.md`, Databricks Data Engineering):

> ### Spark Delta Pipelins
> #databricks #sdp #dataengineering
>
> How do Spark delta pipelines work?

Subject confirmed by the author: **Databricks Spark Declarative Pipelines** (the
Databricks product). The post is about **how they work and how easy the SQL
notation makes it**. The old DLT name and the rebrand history are *not* the
subject — a tag aside, we don't explain that history.

## Goal

Show a knowledgeable data engineer how declarative pipelines work on Databricks
and why the **SQL notation** makes them easy: you write `CREATE STREAMING TABLE`
/ `CREATE MATERIALIZED VIEW` statements that declare *what* you want, and the
engine works out the dependency DAG, the execution order, and the incremental
state — no hand-rolled orchestration. Grounded in one small finance pipeline the
author builds and runs on Databricks.

One post, one message: *"You describe the tables in SQL; Databricks builds and
runs the pipeline for you."* Not a docs re-tread, not a feature tour.

## Definition of done

- [ ] Opens with the recognizable ease-of-use hook — a short, generic sketch of
      the hand-rolled imperative pipeline everyone has written (managing order,
      dependencies, incremental loads, glue code), presented as *shared* pain,
      **not** as the author's own project. No naming history.
- [ ] Explains the declarative model in plain terms: you declare tables + their
      queries, the engine derives the DAG, execution order, and incremental
      state.
- [ ] Covers the core building blocks with **SQL examples**: streaming tables vs.
      materialized views, and how dependencies are expressed just by referencing
      other tables/views.
- [ ] Explains **when to use what** — streaming table vs. materialized view vs.
      plain view — not just what they are.
- [ ] Shows how to set **table properties and descriptions** (table properties,
      comments/descriptions on tables and columns).
- [ ] Shows **data quality expectations** with the three behaviours: warn / drop
      / fail.
- [ ] Shows **backloading** — how to backfill/reload historical data in a
      declarative pipeline.
- [ ] Grounded in **one runnable PoC the author executed on Databricks** — real
      SQL, real pipeline run, real output/screenshot (the DAG the engine built).
      The PoC also **generates the source data and the updates** itself, so the
      demo shows incremental changes arriving, not just a one-shot load.
- [ ] Names at least one "big bad": a limitation, gotcha, or thing the author
      still doesn't fully understand.
- [ ] Gives an honest **problems / disadvantages** picture — a "when NOT to use
      this / what you give up vs a hand-rolled Spark job" read. Lead with the
      serverless-only materialized-view incremental refresh, the streaming-table
      lock-down (no hand DML/ALTER), full-refresh reprocessing + data-loss risk,
      and the one-pipeline-owns-the-table model; sweep the smaller limits
      (pivot, MV time travel, file/concurrency limits) as a footnote line.
- [ ] Says something useful about **pipeline code organization** — split into
      multiple files (recommended `transformations/` layout) vs. keep together,
      and the ease-of-use point that the engine resolves dependencies **by name
      across files**, so file boundaries and order don't matter. Applied in the
      PoC (one file per medallion layer).
- [ ] Notes the relevant **preview / coming features** (clearly labelled as
      preview and date-checked) so the reader can factor them into current or
      future implementations — kept to a short, dated box, not a feature tour.
- [ ] Open-source Spark Declarative Pipelines mentioned only where it actually
      differs from the Databricks product — a footnote at most, not a theme.
- [ ] Length and register match the "wrestling" posts: scannable, code and
      screenshots do the heavy lifting, ends with a pragmatic close or an open
      question.

## The PoC

A **finance-based** example — clients, payments, and investments or loans. 2–3
pipeline steps over a real (simulated) source. Crucially, **generating the data
and the updates is part of the PoC**: the demo covers incremental changes
arriving over time (new payments, updated balances), so streaming tables,
expectations, and backloading all have something real to act on. A rough shape
to validate in research: raw ingest of clients/payments → cleaned/validated
silver with expectations → an aggregated gold view (e.g. exposure or balance per
client).

## Audience & angle

**Audience:** knowledgeable peers — data engineers and architects who know Spark
and SQL, have probably wired up their own pipelines/orchestration before, and
want to judge whether the declarative SQL approach actually saves them work.

**Angle (proposed):** ease of use through the SQL. Open on the *shared*,
recognizable pain of building a multi-step pipeline the imperative way — the
ordering, the dependency wiring, the incremental-load bookkeeping, the pile of
glue code we've all written. Keep it short and generic (not framed as the
author's own war story — nothing about his past is fabricated). Then show the
same result declared in a handful of SQL statements and let the engine-built DAG
be the "aha". The message the reader should feel: *"Wait, that's all of it?"*

## What the reader takes away

- A working intuition for the declarative model: declare tables in SQL, the
  engine handles order, dependencies, and incremental state.
- Concrete SQL patterns: streaming table vs. materialized view vs. plain view,
  when to reach for each, and how referencing another table *is* the dependency.
- The practical extras that make it production-usable: properties/descriptions,
  data-quality expectations (warn/drop/fail), and backloading.
- An honest read on where the ease breaks down — one real gotcha to expect.

## Scope watch (core vs. trimmable)

The DoD covers a lot for one post. To avoid bloat, treat it in layers:

- **Core (must land):** the declarative model + SQL notation, streaming table vs.
  materialized view vs. view (and when to use what), and the PoC showing
  incremental updates arriving. This is the "how it works / how easy" spine.
- **Supporting (keep, but tight):** properties/descriptions, data-quality
  expectations (warn/drop/fail), backloading. Show each with one crisp SQL
  snippet against the finance PoC rather than exhaustive coverage.
- **Supporting (added at the author's request — keep, but disciplined):**
  code-organization (cheap: one paragraph + the 3-file DAG screenshot), a
  problems/disadvantages section (land the top 3 drawbacks + a footnote sweep),
  and a short dated preview/coming box.
- **If the draft bloats:** with the added sections this is now a long read. The
  most natural split-offs, in order: (1) a **problems / "when NOT to use
  declarative pipelines"** follow-up (the disadvantages section can carry a whole
  post); (2) a **data-quality expectations** deep-dive (warn/drop/fail), leaving
  the first post a taste. Backloading, properties, and code-organization are
  cheap to keep. The preview box dates fastest — keep it short and re-check
  before publishing. Flag the split to the author at draft time rather than
  pre-emptively cutting — all additions stay in the DoD for now as requested.

## Open questions (from grilling)

_None blocking — the subject, angle, PoC, and scope are settled. Remaining
choices (exact table names, split-vs-single-post) are resolved during research
and drafting._
