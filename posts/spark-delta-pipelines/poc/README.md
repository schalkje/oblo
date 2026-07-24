# Finance PoC — run instructions

A small **Lakeflow Spark Declarative Pipelines** demo: it generates its own
finance source data (clients, loans, payments) *and* the incremental updates,
then a SQL-only pipeline turns it into bronze -> silver -> gold and exercises
every item in the post's definition of done.

**You (the author) run this on Databricks.** Oblo only wrote the code. Paste
results and screenshot filenames back into `../research.md` -> "Results &
evidence", and drop screenshots into `../images/`.

## Files

| File | What it is |
|---|---|
| `00_generate_data.py` | Databricks notebook source. Writes source files to a UC Volume, plus incremental/updated/bad records on demand. |
| `transformations/01_bronze.sql` | Bronze ingest streaming tables + the backfill flow. |
| `transformations/02_silver.sql` | Silver validation (expectations) + the client dimension MV. |
| `transformations/03_gold.sql` | Gold exposure MV + the reporting view. |

### Why three files?

The pipeline SQL is split by medallion layer to match the Databricks-recommended
`transformations/` folder layout. This is purely for humans: the engine reads
**every** source file first, resolves dependencies **by name across files**, and
builds one DAG — file boundaries and statement order don't matter. `02_silver.sql`
references `payments_raw` from `01_bronze.sql` with nothing but the name. That's
a nice ease-of-use point for the post.

## Prerequisites

- A Databricks workspace with **Unity Catalog** enabled.
- Rights to create (or reuse) a **catalog**, **schema**, and **volume**, and to
  create a pipeline. The generator's first cells create them for you if allowed;
  otherwise create them yourself and point the widgets at existing ones.
- **Serverless compute strongly recommended.** It makes the materialized-view
  incremental-refresh behaviour observable (the "big bad"). On classic compute
  the gold MV will always report `Full recompute` — still a valid result to
  write about, just frame it correctly.

## Step 1 — generate the initial data

1. Import `00_generate_data.py` as a notebook (it's in Databricks `# COMMAND`
   source format).
2. Set the three widgets at the top: `catalog`, `schema`, `volume`
   (defaults: `main` / `finance_poc` / `landing`).
3. Run the setup cell and **Cell: initial load**. This writes:
   - `clients/` — 6 rows incl. one duplicated client (for the dedup MV),
   - `loans/` — 6 loans,
   - `payments/history/` — 5 old payments (the **backfill** source),
   - `payments/incoming/` — 6 current payments incl. **2 deliberately bad**
     (one null client_id, one 5,000,000 amount).

## Step 2 — align the pipeline SQL path

Open `transformations/01_bronze.sql` and **find-and-replace** the placeholder
`/Volumes/main/finance_poc/landing` with your actual volume path if you changed
the widgets. It appears only in this bronze file, in three `read_files(...)` calls.

## Step 3 — create and run the pipeline

1. **New -> ETL pipeline** (the Lakeflow Pipelines Editor). New pipelines default
   to Unity Catalog, the current channel, and serverless compute.
2. Add the three files in `transformations/` as the pipeline **source** — either
   point the pipeline root folder at this `poc/` folder (Git folder recommended),
   or create three transformation files and paste each layer in. All three files
   belong to the **one** pipeline; the engine stitches them together by name.
3. Set the pipeline's **default catalog and schema** to where you want the tables
   published (e.g. `main` / `finance_poc`). This is what lets the SQL reference
   tables by unqualified name.
4. Keep **Serverless** (recommended). Leave the rest at defaults (Advanced
   edition is the default and is required for expectations).
5. Click **Run pipeline**. (Use **Dry run** first if you want to validate without
   materializing anything.)

## Step 4 — capture the evidence (screenshots + numbers)

Save screenshots into `../images/` with the suggested names.

1. **The DAG the engine built** -> `images/dag-full-pipeline.png`.
   This is the centrepiece of the post. Note whether `payments_raw` shows **two
   flows** feeding it (incremental + backfill).
2. **Comments + properties** — open `payments_validated` in **Catalog Explorer**
   and screenshot the table comment, the per-column comments, and the
   `TBLPROPERTIES` -> `images/catalog-comments.png`.
3. **Expectations metrics** — click `payments_validated` in the pipeline, open
   the **Data quality** tab. Screenshot the warn (`plausible_amount`) and drop
   (`known_client`) counts -> `images/expectations-metrics.png`. Also paste the
   numbers into research.md.
4. **Backfill worked** — run and paste:
   ```sql
   SELECT count(*) AS total_payments FROM payments_raw;
   SELECT min(payment_date), max(payment_date) FROM payments_validated;
   ```
   You should see the historical (2023–2024) rows *and* the current (2025) rows.

## Step 5 — show incremental processing

1. Back in the generator, run **Cell: incremental batch** (writes a new file with
   4 new valid payments + 1 more null-client record).
2. Re-run the pipeline (a normal, non-full refresh).
3. Confirm only the new rows were appended:
   ```sql
   SELECT count(*) FROM payments_raw;          -- higher by the new rows
   SELECT count(*) FROM payments_validated;    -- higher, minus the dropped null-client row
   ```
   Paste before/after counts into research.md.

## Step 6 — see an expectation FAIL (optional but worth it)

1. Generator -> **Cell: inject FAIL record** (writes one negative-amount payment).
2. Re-run the pipeline.
3. The `payments_critical` flow should fail with an `EXPECTATION_VIOLATION`
   error. Screenshot the failed node + the error -> `images/expectation-fail.png`.
4. Clean up: generator -> **Cell: reset**, then re-run **Cell: initial load**,
   then **full-refresh** the pipeline to get back to green.

## Step 7 — the "big bad": incremental vs full recompute of the gold MV

1. In the pipeline **Tables** panel, look at the **Incrementalization** column for
   `client_exposure` (`Incremental` / `Full recompute` / `No change`).
2. Or query the event log (replace with the fully-qualified MV name):
   ```sql
   SELECT timestamp, message
   FROM event_log(TABLE(main.finance_poc.client_exposure))
   WHERE event_type = 'planning_information'
   ORDER BY timestamp DESC;
   ```
   Look for the technique: `GROUP_AGGREGATE`, `ROW_BASED`, `FULL_RECOMPUTE`, etc.
3. Note whether you ran serverless or classic — it changes the answer. Paste the
   result and your read on it into research.md. Optionally test
   `EXPLAIN CREATE MATERIALIZED VIEW ...` to see incrementalizability up front.

## Cleanup

- Delete the pipeline from the Pipelines UI (this drops its managed tables), or
  `DROP` the schema.
- Generator -> **Cell: reset** removes the generated source files.

## Notes / gotchas you may hit

- **Serverless vs classic** changes the MV refresh story (see Step 7).
- Streaming tables are locked down: no `ALTER TABLE` / `INSERT` / `MERGE` /
  `COPY INTO` by hand — change them through the pipeline definition only.
- If the workspace UI differs (Incrementalization column / Data quality tab not
  present), use the event-log queries above as the fallback evidence.
- If `read_files` infers an unexpected schema, check for a `_rescued_data` column
  in `payments_raw`; the silver SELECT projects explicit columns so it won't
  propagate downstream.
</content>
