# Research: Declarative pipelines on Databricks — the whole thing in SQL

## Naming guidance for the writer (read this first)

The docs moved. As of July 2026 the Databricks product is called **Lakeflow Spark
Declarative Pipelines** — often shortened in the docs to **Lakeflow pipelines**.
It is built on the open-source **Apache Spark Declarative Pipelines (SDP)** engine.
The old name (DLT / Delta Live Tables) still shows up in URLs (`/dlt/`) and the
Python module name (`dlt`), but the docs themselves have moved to `/ldp/` and to
"Lakeflow pipelines".

Recommendation for the post:
- First mention: "Databricks **Lakeflow Spark Declarative Pipelines**" and note
  in a single aside/footnote that this is what used to be called Delta Live
  Tables (DLT). Do **not** narrate the rebrand history — one line, done.
- After that, use "Lakeflow pipelines" or just "declarative pipelines".
- Keep the blog's working title/tag "Spark Declarative Pipelines" if you like —
  it reads fine and matches the `#sdp` tag. Just make the product name explicit
  once so a reader searching the docs lands in the right place.
- SDP (the open-source engine) is only a footnote where it differs from the
  Databricks product — see the difference table under Sources.

## Content plan

**One message:** *You describe the tables in SQL; Databricks builds and runs the
pipeline for you.* The engine-built DAG screenshot is the "aha".

**Register:** wrestling-post. Open on shared pain, let code + the DAG screenshot
do the heavy lifting, name at least one honest "big bad", close pragmatically /
with an open question. Audience knows Spark and SQL — don't oversimplify.

### Storyline (problem → takeaway)

1. **The hook — shared, generic pain (no personal war story).**
   The imperative multi-step pipeline everyone has hand-rolled: bronze → silver →
   gold, and the glue around it — figuring out execution order, wiring
   dependencies by hand, tracking which rows you've already processed
   (incremental bookkeeping), the checkpoint plumbing, the "did step 2 finish
   before step 3 started?" orchestration. "Wouldn't it be nice if you just
   described the tables and something else worked out the order?"

2. **The declarative model in plain terms.**
   You write a set of `CREATE ... TABLE / VIEW` statements that each declare
   *what* a dataset is (a query). You reference other datasets by name. The
   engine reads *all* the definitions first, builds a dataflow graph (the DAG),
   figures out execution order and maximum parallelism, and manages the
   incremental state — before any query runs. Load-bearing quote to paraphrase:
   *"Lakeflow pipelines evaluate all dataset definitions across all source code
   files configured in a pipeline and build a dataflow graph before any queries
   are run. The order of queries appearing in the source files defines the order
   of code evaluation, but not the order of query execution."* (sql-dev doc)
   → **Evidence needed:** the DAG the engine builds for the finance PoC
   (screenshot). This is the centrepiece.

3. **The three building blocks, SQL-first, and when to use what.**
   - **Streaming table** (`CREATE OR REFRESH STREAMING TABLE ... AS SELECT * FROM
     STREAM ...`): append-only / incremental ingest, each row processed once.
   - **Materialized view** (`CREATE OR REFRESH MATERIALIZED VIEW ... AS SELECT
     ...`): result cached and kept correct; good for joins/aggregations and
     anything multiple downstreams read.
   - **(Temporary) view** (`CREATE TEMPORARY VIEW ... AS SELECT ...`): evaluated
     on demand, not persisted; intermediate logic.
   - Dependencies are expressed *just by referencing the other table/view by
     name* — that reference **is** the edge in the DAG. No orchestration code.
   - "When to use what" table (paraphrase the docs decision table):
     ingest / append-only / high volume → streaming table; joins, aggregations,
     multiple readers, correctness on updates → materialized view; intermediate
     step with no downstream reader / no need to persist → view.
   → **Evidence needed:** the PoC uses all three; show the SQL and the DAG.

4. **The production extras (keep tight — one crisp snippet each).**
   - **Properties + descriptions:** table `COMMENT`, per-column `COMMENT`,
     `TBLPROPERTIES ('quality' = 'silver', ...)`. Show these land in Catalog
     Explorer. → **Evidence:** screenshot of the comments/properties in Catalog
     Explorer.
   - **Data-quality expectations (warn / drop / fail):** `CONSTRAINT name EXPECT
     (expr)` = warn (row kept + flagged in metrics); `... ON VIOLATION DROP ROW`
     = dropped; `... ON VIOLATION FAIL UPDATE` = pipeline stops and rolls back.
     → **Evidence:** the Data quality tab metrics (warn count, drop count) plus
     one deliberately triggered FAIL and its error message.
   - **Backloading / backfill:** a streaming table can have **multiple flows** —
     one ongoing streaming flow plus a one-time `INSERT INTO ONCE` backfill flow
     that loads history. → **Evidence:** DAG showing two flows into the bronze
     payments table, and row counts before/after.

4b. **Code organization — split or keep together? (ease-of-use beat.)**
   Short section: the docs' recommended layout is a pipeline root folder with a
   `transformations/` folder holding the source files (plus `explorations/` for
   ad-hoc notebooks and `utilities/` for importable Python). You can split SQL
   across as many files as you like — the punchline is that **the engine doesn't
   care about file boundaries**: *"the pipeline analyzes dataset dependencies
   across all of its source files"* and *"you can organize source code across
   files in any order"*, referencing tables by name. Recommendation for the post
   (and applied to the PoC): **one file per medallion layer** (bronze/silver/gold)
   for a small pipeline; group by domain/subject once it grows. Note the practical
   limits (100 source files per pipeline unless you use folders, then up to 1000)
   and the "run a single file / single table" dev loop. → **Evidence:** the PoC is
   split into `transformations/01_bronze.sql`, `02_silver.sql`, `03_gold.sql` and
   still builds one DAG.

5. **Problems / disadvantages — the honest "when NOT to use this / what you give
   up" section.** Ranked list below; lead with the serverless-MV big bad, then
   the streaming-table lock-down and the "one pipeline owns the table" model, and
   be honest about the testing/dev-loop story.

5b. **What's in preview / coming (factor into your implementation).** Short,
   clearly-labelled, date-stamped. See the preview sweep below. Frame as "don't
   over-engineer around today's gaps — some are already closing."

6. **Pragmatic close / open question.** Something like: the SQL really is most of
   it, but the incremental magic has fine print (serverless + supported query
   shapes) and you hand the framework the keys to your tables — an honest "here's
   where I'd want to hear how you handle it".

### Problems / disadvantages — ranked (all doc-verified unless noted)

**Strong enough to earn space in the post (the "when NOT to use this" spine):**

1. **Incremental refresh of materialized views is serverless-only and not
   guaranteed.** *"Only materialized views updated using serverless pipelines can
   use incremental refresh. Materialized views that do not use serverless
   pipelines are always fully recomputed."* Even on serverless, only certain
   query shapes incrementalize; unsupported expressions silently fall back to a
   **full recompute** (cost surprise). Reported per-table in the
   **Incrementalization** column (`Incremental` / `Full recompute` / `No change`)
   and the event log (`planning_information` → `ROW_BASED`, `GROUP_AGGREGATE`,
   `FULL_RECOMPUTE`, …). *The headline big-bad; ties straight back to
   "declarative = easy".* → PoC checks the gold MV's status.
2. **Streaming tables are locked down — you give up hand DML.** `ALTER TABLE`,
   `INSERT INTO`/`MERGE`, `COPY INTO`, `TRUNCATE`, `RESTORE`, `CLONE` are
   disallowed; only the owner can refresh. This is the biggest "what you give up
   vs a hand-rolled Spark job / plain Delta table" point — the framework takes
   the wheel.
3. **Change the query and old rows don't retro-fix; the fix (full refresh) can
   lose data.** Streaming tables process each row once, so changing the logic
   only affects new rows; reprocessing old rows needs a **full refresh** — and
   *"a full refresh can also lead to data loss if the source does not retain
   historical data"* (e.g. Kafka retention, or a source you archive). Medallion
   with a raw bronze layer is the documented mitigation.
4. **A dataset can be defined only once, and one pipeline owns it.** *"Pipeline
   datasets can be defined only once… they can be the target of only a single
   operation across all pipelines"* (exception: append flows). *"Tables defined
   by a pipeline can't be changed or updated by any other pipeline."* Real
   coupling/lock-in: you can't split the writes to one table across pipelines,
   and the table's lifecycle is tied to its pipeline.
5. **The testing / dev-loop story is different from plain Spark.** Pipelines use
   **files, not notebooks** (*"cell-based execution of notebooks is not
   compatible with pipelines"*); `%pip install` isn't supported from source
   files (declare deps in settings instead); there's no true "run it locally as a
   unit test" path — you iterate in the editor with Run file / Run table / Dry
   run, or push to a bundle and a dev target. Worth an honest line: you trade
   arbitrary imperative testability for the declarative model. (Community posts —
   waitingforcode, Kanniappan — echo this and add micro-batch ≠ true
   event-by-event streaming.)

**Footnote / one-liner material (real, but not worth a paragraph each):**

- `pivot()` is not supported (eager schema evaluation).
- **Delta time-travel is not supported on materialized views** (only on
  streaming tables).
- **Concurrency / file limits:** 1000 concurrent pipeline updates per workspace;
  100 source files per pipeline unless you use folders (then up to 1000).
- **Identity columns** are recomputed on MV updates → recommended only on
  streaming tables; not supported on AUTO CDC targets.
- **External access:** MVs/STs are only reachable by Databricks clients by
  default; exposing them to outside systems needs extra setup.
- **Ops complexity (community, cross-checked):** three editions
  (Core/Pro/Advanced) on classic vs. serverless bundling everything; the runtime
  `channel` auto-upgrades (CURRENT vs PREVIEW).
- **Lock-in nuance for the SDP footnote:** the *transformation code* is portable
  to open-source SDP, but the production value-adds you'll actually lean on —
  AUTO CDC, expectations, the queryable event log, continuous mode — are
  **Lakeflow-only** and do **not** port. So "it's open source now" is only half
  true.

### Preview / coming features (sweep of the 2026 release notes + editor docs)

Clearly label these as preview and date-check at draft time — they drift fast and
they're in `meta.yaml` references for monitoring. As of the June 2026 release
notes (checked 2026-07-23): pipeline runtime channels are **CURRENT = Databricks
Runtime 17.3**, **PREVIEW = Databricks Runtime 18 / 18.1**.

- **Genie Code for pipeline development — Public Preview.** Agentic
  create/modify/debug of whole pipelines from natural language, inside the
  Lakeflow Pipelines Editor. Most relevant "developer tooling" preview.
- **`REPLACE WHERE` flows — Beta** (April 2026), and **now support incremental
  refresh** (June 2026). New declarative SQL for incremental batch processing of
  joins/aggregations, late-arriving data, and backfills — directly adjacent to
  this post's backfill section; worth a "watch this" line.
- **Standalone MVs/STs on serverless compute — Beta** (April 2026): create
  managed MV/ST objects without a full pipeline. Relevant to "do I even need a
  pipeline for one table?"
- **Pipeline `parameters` — Beta:** named-parameter (`:param`) reuse of SQL
  source across environments.
- **Updated pipeline monitoring experience — Preview** (toggle in the editor).
- **`AUTO CDC` inline `FLOW` syntax** requires DBR 17.3+ and the **PREVIEW**
  channel (per the CREATE STREAMING TABLE reference).
- Recently **GA** (mention as "already landed", not preview): AUTO CDC SCD Type 1
  materialization + bitemporal tracking; Delta **type widening** without a full
  reset; retain UC tables when deleting a pipeline; reuse clusters on retry;
  storing expectations/schedules in Unity Catalog table properties.

Out of scope for this post (note only if asked): the AUTO CDC / SCD deep-dive —
it's a big topic and Lakeflow-specific, and this post is deliberately about the
plain streaming-table / MV / view core.

### Claims that need PoC evidence (checklist for the author)

- [ ] The engine builds the DAG itself — **DAG screenshot** (centrepiece).
- [ ] All three dataset types work together — SQL + DAG.
- [ ] Comments + properties show up — **Catalog Explorer screenshot**.
- [ ] warn / drop / fail behave as documented — **Data quality tab** + the FAIL
      error message.
- [ ] Backfill flow + streaming flow both land in one table — DAG + row counts.
- [ ] Incremental vs full recompute of the gold MV — **Incrementalization column**
      or event-log `planning_information` output.
- [ ] Incremental arrival: re-running after new files appends only new rows.
- [ ] File boundaries don't matter — three per-layer files still build **one**
      DAG (the DAG screenshot already proves this; call it out).

## Sources

Official Databricks / Microsoft Learn docs (primary; the `/ldp/` tree is the
current product docs; all checked 2026-07-23). Databricks moves fast — these are
version/date sensitive, hence the `ms.date` noted where useful.

- [Spark Declarative Pipelines (landing)](https://learn.microsoft.com/en-us/azure/databricks/ldp/) — top of the current product tree; confirms "Lakeflow pipelines extend and are interoperable with Spark Declarative Pipelines". Naming anchor. (doc ms.date 2026-07-10) — checked 2026-07-23.
- [What are Lakeflow pipelines? (concepts)](https://learn.microsoft.com/en-us/azure/databricks/ldp/concepts/) — the declarative model, the three dataset types, and the **when-to-use-what** decision list. Core of sections 2–3. — checked 2026-07-23.
- [Develop Lakeflow pipelines code with SQL](https://learn.microsoft.com/en-us/azure/databricks/ldp/developer/sql-dev) — the load-bearing SQL: `CREATE OR REFRESH STREAMING TABLE / MATERIALIZED VIEW`, `STREAM`, `read_files`, the "graph built before any queries run" quote, the four-dataset example. Primary SQL reference for the post. — checked 2026-07-23.
- [CREATE STREAMING TABLE (pipelines) — SQL reference](https://learn.microsoft.com/en-us/azure/databricks/ldp/developer/ldp-sql-ref-create-streaming-table) — exact grammar: column `COMMENT`, table `COMMENT`, `TBLPROPERTIES`, `CONSTRAINT ... EXPECT`, `FLOW ... INSERT [ONCE] BY NAME`, and the streaming-table **limitations** list (no `ALTER`, no `MERGE`, etc.). — checked 2026-07-23.
- [Streaming tables (concept)](https://learn.microsoft.com/en-us/azure/databricks/ldp/concepts/streaming-tables) — append-only semantics, "row seen once", query-change/full-refresh gotcha, joins-don't-recompute. Feeds the big-bad. — checked 2026-07-23.
- [Materialized views (concept)](https://learn.microsoft.com/en-us/azure/databricks/ldp/concepts/materialized-views) — caching, "always correct on refresh", and the limitation that some input changes force a full (expensive) recompute. — checked 2026-07-23.
- [Incremental refresh for materialized views](https://learn.microsoft.com/en-us/azure/databricks/ldp/incremental-refresh) — the strongest gotcha: serverless-only incremental refresh, the supported-keyword table, `EXPLAIN CREATE MATERIALIZED VIEW`, `REFRESH POLICY`, the Incrementalization column and `planning_information` event. — checked 2026-07-23.
- [Manage data quality with pipeline expectations](https://learn.microsoft.com/en-us/azure/databricks/ldp/expectations) — the three actions table (warn/drop/fail), exact `CONSTRAINT ... EXPECT ... ON VIOLATION ...` syntax, multiple-constraint syntax, and the FAIL error-message example. Primary source for the expectations section. — checked 2026-07-23.
- [Backfilling historical data with pipelines](https://learn.microsoft.com/en-us/azure/databricks/ldp/flows-backfill) — exact `CREATE FLOW ... AS INSERT INTO [ONCE] target BY NAME SELECT ...` backfill pattern (one streaming flow + N one-time backfill flows into one bronze table). Primary source for the backloading section. — checked 2026-07-23.
- [Load data in pipelines](https://learn.microsoft.com/en-us/azure/databricks/ldp/load) — `read_files` / Auto Loader ingest patterns, loading from volumes, medallion mapping. Feeds the PoC ingest. — checked 2026-07-23.
- [Best practices for Lakeflow pipelines](https://learn.microsoft.com/en-us/azure/databricks/ldp/best-practices) — the clean warn/drop/fail SQL trio, dataset-type decision table, medallion mapping, and the "understand streaming state and full refresh" data-loss warning. — checked 2026-07-23.
- [Pipeline properties reference](https://learn.microsoft.com/en-us/azure/databricks/ldp/properties) — pipeline table properties (`pipelines.reset.allowed`, `pipelines.autoOptimize.*`), edition (Core/Pro/Advanced), channel, serverless flag. Source for the properties snippet + an ops gotcha. — checked 2026-07-23.
- [Apache Spark Declarative Pipelines (SDP vs Lakeflow)](https://learn.microsoft.com/en-us/azure/databricks/ldp/concepts/spark-declarative-pipelines) — the difference table: AUTO CDC, expectations, queryable event log, continuous mode are **Lakeflow-only, not in open-source SDP**. This is the whole basis for the SDP footnote — don't over-claim. — checked 2026-07-23.
- [CREATE TEMPORARY VIEW (pipelines)](https://learn.microsoft.com/en-us/azure/databricks/ldp/developer/ldp-sql-ref-create-temporary-view) — confirms the plain-view syntax in a pipeline is `CREATE TEMPORARY VIEW name AS query` (with optional column comments / `COMMENT` / `TBLPROPERTIES`); `CREATE LIVE VIEW` is the older syntax. — checked 2026-07-23.
- [Pipeline limitations](https://learn.microsoft.com/en-us/azure/databricks/ldp/limitations) — the canonical limitations list: dataset-defined-once / single-owner, `pivot()` unsupported, time-travel not on MVs, concurrency + source-file limits, identity-column limits, external-access caveat. Primary source for the "problems/disadvantages" section. (doc ms.date 2026-07-10) — checked 2026-07-23.
- [Develop and debug ETL pipelines with the Lakeflow Pipelines Editor (multi-file editor)](https://learn.microsoft.com/en-us/azure/databricks/ldp/multi-file-editor) — the recommended folder layout (`transformations/`, `explorations/`, `utilities/`), "dependencies resolved across all files / any order", Run file / Run table / Dry run dev loop, files-not-notebooks rationale, and Genie Code (Public Preview). Primary source for the code-organization section. — checked 2026-07-23.
- [Lakeflow pipelines release notes 2026](https://learn.microsoft.com/en-us/azure/databricks/release-notes/dlt/2026) — the preview/GA sweep: channel = CURRENT DBR 17.3 / PREVIEW DBR 18, REPLACE WHERE flows (Beta) + incremental refresh, standalone MV/ST on serverless (Beta), AUTO CDC SCD1/bitemporal (GA), type widening (GA). Primary source for the "preview / coming" section; monitor this one. (doc ms.date 2026-07-14) — checked 2026-07-23.

Community / engineering (secondary; used to sanity-check the gotchas, not as
primary claims):

- [Lakeflow Spark Declarative Pipelines: introduction and incremental refreshes — waitingforcode.com (Bartosz Konieczny, 2026-05-06)](https://www.waitingforcode.com/databricks/lakeflow-spark-declarative-pipelines-introduction-incremental-refreshes/read) — credible independent engineer; independently flags the serverless-only incremental-refresh constraint and the editions/channel operational complexity. Confirms the big-bad is real, not just doc small print. — checked 2026-07-23.
- [Data + AI Summit 2025 keynote demo — Lakeflow Spark Declarative Pipelines (Databricks)](https://www.databricks.com/resources/demos/videos/lakeflow-declarative-pipelines-dais-2025-keynote) — vendor video, useful for the "what it looks like live" framing and the naming; treat as marketing, not evidence. — checked 2026-07-23.
- [Pitfalls You Must Know Before Using Declarative Lakeflow Pipelines — Prabhakaran Kanniappan, Medium (2025-11-26)](https://medium.com/@prabhakarankanniappan/pitfalls-you-must-know-before-using-declarative-lakeflow-pipelines-in-databricks-658c6d8397cb) — practitioner "it isn't magic" piece flagging streaming-table constraints and full-refresh pain. Corroborates the disadvantages section; the copy I fetched was partly truncated, so lean on the docs for specifics. — checked 2026-07-23.

## PoC / experiments

A finance PoC the **author runs on Databricks** (Oblo only wrote the code). It
generates its own source data *and* incremental updates, then a single pipeline
turns it into bronze → silver → gold and exercises every DoD item.

Files (in `poc/`):
- `poc/README.md` — full step-by-step run instructions, prerequisites, what to
  screenshot, and where to paste results.
- `poc/00_generate_data.py` — Databricks notebook source. Writes initial data
  (clients, loans, payment **history** + first **incoming** batch) as JSON files
  to a Unity Catalog Volume, with deliberately bad records baked in. Has a cell
  to drop an **incremental** batch (new/updated records), and a gated cell to
  inject a FAIL-triggering record.
- `poc/transformations/01_bronze.sql`, `02_silver.sql`, `03_gold.sql` — the
  declarative pipeline, SQL-first, **split one file per medallion layer** to
  follow the docs' recommended `transformations/` layout and to demonstrate that
  the engine resolves dependencies by name across files (they still form one DAG).

### PoC shape (validated against the docs, improved from the idea's rough shape)

Medallion, finance domain:

- **Bronze (streaming tables, ingest):**
  - `clients_raw` — streaming table, Auto Loader from the clients folder.
  - `loans_raw` — streaming table, Auto Loader from the loans folder.
  - `payments_raw` — streaming table **with two flows**: an ongoing streaming
    flow over `payments/incoming/` **plus** a one-time `INSERT INTO ONCE`
    backfill flow over `payments/history/`. This is the **backloading** demo and
    proves multiple flows land in one table.
- **Silver (validation + a dimension MV):**
  - `payments_validated` — streaming table from `STREAM(payments_raw)` carrying
    the **warn** (suspiciously large amount) and **drop** (null `client_id`)
    expectations, plus column comments and `TBLPROPERTIES`.
  - `payments_critical` — streaming table from `STREAM(payments_validated)` with
    a **FAIL** expectation (`amount >= 0`). Passes on the normal run; fails only
    when the author injects the bad record — a controlled way to *see* FAIL.
  - `clients_clean` — **materialized view** that de-duplicates the client
    dimension (keeps latest row per `client_id`). Justifies an MV (multiple
    downstreams read it; source can change via updates).
- **Gold (aggregation):**
  - `client_exposure` — **materialized view** joining `clients_clean`, `loans_raw`
    and validated payments, aggregating **outstanding balance / exposure per
    client** (`sum(principal) - sum(payments)`). This is the MV whose
    Incrementalization status the author checks for the big-bad.
  - `high_exposure_clients` — **plain (temporary) view** filtering the gold MV to
    clients above a threshold: an intermediate/reporting view that shows the
    third dataset type and that a view is *not* persisted.

Why this shape hits every DoD item: three dataset types + when-to-use-what
(bronze ST, dimension MV, gold MV, reporting view); dependencies purely by name
(the DAG); properties + table/column comments; warn+drop+fail; backfill via a
second ONCE flow; incremental updates via a second dropped file batch; and the
MV incremental-refresh gotcha is directly observable.

### Results & evidence
<!-- AUTHOR: paste outputs, observations, and screenshot filenames here. -->

- [ ] **DAG screenshot** (the engine-built graph) → save to
      `images/dag-full-pipeline.png`. Note: does it show two flows into
      `payments_raw`?
- [ ] **Catalog Explorer** showing table comment + column comments +
      `TBLPROPERTIES` on `payments_validated` → `images/catalog-comments.png`.
- [ ] **Data quality tab** on `payments_validated` — warn count and drop count
      from the seeded bad records → `images/expectations-metrics.png`. Paste the
      numbers here too.
- [ ] **FAIL demo:** run the inject cell, re-run pipeline, screenshot the failed
      `payments_critical` flow + the `EXPECTATION_VIOLATION` error message →
      `images/expectation-fail.png`. Then remove the bad record / full refresh to
      get back to green.
- [ ] **Backfill:** row count of `payments_raw` after the first run (history +
      incoming) — paste `SELECT count(*)` and, if easy, a count split by a
      history vs current flag/date.
- [ ] **Incremental arrival:** run the incremental-batch cell, re-run the
      pipeline, and record how many rows were added to `payments_raw` /
      `payments_validated` (should be only the new ones).
- [ ] **MV incremental vs full recompute:** check the **Incrementalization**
      column for `client_exposure`, and/or run the `planning_information`
      event-log query from `README.md`. Paste the technique
      (`GROUP_AGGREGATE` / `FULL_RECOMPUTE` / …). Note whether the pipeline is
      serverless or classic — it changes the answer.
- [ ] Anything that surprised you / broke — raw notes for the "big bad".

## Gaps / still needed

- **Author must run the PoC on Databricks.** Nothing here is executed against a
  workspace. All screenshots and counts above are blanks for the author.
- **Serverless vs classic compute is a real fork.** The MV incremental-refresh
  gotcha only shows the "incremental" side on **serverless**. Decide before
  running: serverless is recommended by the docs and makes the demo cleaner.
  If the author runs classic, the gold MV will always say `Full recompute` —
  which is still a valid (and honest) result to write about, just frame it
  correctly.
- **Unity Catalog + a Volume are prerequisites.** The PoC writes source files to
  a UC Volume and the pipeline needs a target catalog/schema. Author must pick
  `catalog.schema` and a volume and find-replace the placeholder path (one place,
  flagged in the SQL and the generator).
- **Exact table/property screenshots depend on workspace UI version** — the
  Incrementalization column and the Data quality tab are current-UI features;
  if the author's workspace differs, fall back to the event-log queries in
  `README.md`.
- **Not verified by us:** whether `payments_critical`'s FAIL rolls back cleanly
  and leaves `payments_validated` intact on a triggered pipeline (docs say a
  single flow's failure doesn't fail parallel flows in triggered mode) — worth
  the author confirming, it's a nice detail for the post.
- **Open decision (for draft time, not blocking):** whether warn/drop/fail gets
  split into a follow-up post. The PoC covers all three so either choice is
  supported.
- **Scope/length warning (author-requested additions).** Three new beats were
  added to scope: a problems/disadvantages section, a preview/coming section, and
  a code-organization section. That is real length on top of an already-full DoD.
  Honest layering for the draft:
  - *Core (still the spine):* declarative model + SQL notation, ST vs MV vs view
    + when-to-use, incremental updates in the PoC.
  - *Keep, tight:* properties/descriptions, warn/drop/fail, backloading,
    code-organization (it's a cheap ease-of-use beat — one paragraph + the
    3-file screenshot).
  - *New, and the most likely split-off:* the **problems/disadvantages** section
    could carry a whole "when NOT to use declarative pipelines" follow-up post;
    for this post, land items 1–3 (serverless-MV, lock-down, full-refresh) plus a
    one-line footnote sweep. The **preview/coming** section should be a short,
    dated box, not a feature tour — it dates fastest.
  - Flag to the author at draft time: with all additions in, this is likely a
    long read; consider the problems section as the natural spin-off.
- **Preview features are volatile.** Everything in the preview sweep is
  date-stamped to 2026-07 and channel-dependent (CURRENT DBR 17.3 / PREVIEW DBR
  18). Re-check the 2026 release notes right before publishing — Beta→GA moves
  will happen (e.g. REPLACE WHERE, standalone serverless MV/ST).
- **Community disadvantages source was partly truncated** (Kanniappan Medium
  post); the disadvantages list leans on the docs (`ldp/limitations`, streaming/MV
  concept pages) for anything load-bearing. If the author wants more outside
  voices, that's a nice-to-have, not a blocker.
- **Not tested by us:** whether splitting the PoC across three source files
  builds cleanly as one pipeline (it should per the docs — dependencies resolve
  by name across files). Author confirms when running; the DAG screenshot is the
  proof and doubles as evidence for the code-organization beat.
</content>
</invoke>
