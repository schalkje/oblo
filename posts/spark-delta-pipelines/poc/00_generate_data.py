# Databricks notebook source
# MAGIC %md
# MAGIC # Finance PoC — source data generator
# MAGIC
# MAGIC This notebook generates the source data **and** the incremental updates for the
# MAGIC declarative-pipeline PoC. It writes newline-delimited JSON files into a Unity
# MAGIC Catalog **Volume**, so the pipeline can ingest them with Auto Loader (`read_files`).
# MAGIC
# MAGIC It writes deliberately bad records so the data-quality expectations (warn / drop /
# MAGIC fail) have something real to act on.
# MAGIC
# MAGIC **Run order:**
# MAGIC 1. Set the widgets (catalog / schema / volume) at the top.
# MAGIC 2. Run **Cell: initial load** once. This writes clients, loans, payment *history*
# MAGIC    (for the backfill flow), and the first *incoming* payments batch.
# MAGIC 3. Create + run the pipeline (see `transformations/` and `README.md`).
# MAGIC 4. Run **Cell: incremental batch** to drop new/updated records, then re-run the
# MAGIC    pipeline to see incremental processing.
# MAGIC 5. Optional: run **Cell: inject FAIL record** to see an `ON VIOLATION FAIL UPDATE`
# MAGIC    expectation stop the pipeline. Then run **Cell: reset** and full-refresh.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Target catalog")
dbutils.widgets.text("schema", "finance_poc", "Target schema")
dbutils.widgets.text("volume", "landing", "Volume name")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
VOLUME = dbutils.widgets.get("volume")

# Base path for all source files. The pipeline SQL reads from these same folders,
# so if you change anything here, update the placeholder in transformations/01_bronze.sql too.
BASE = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

CLIENTS_DIR   = f"{BASE}/clients"
LOANS_DIR     = f"{BASE}/loans"
PAY_INCOMING  = f"{BASE}/payments/incoming"   # ongoing streaming flow reads this
PAY_HISTORY   = f"{BASE}/payments/history"    # one-time backfill flow reads this

print("Writing source files under:", BASE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## One-time setup: create the catalog / schema / volume
# MAGIC Comment these out if they already exist. Requires privileges to create them.

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}")

for d in (CLIENTS_DIR, LOANS_DIR, PAY_INCOMING, PAY_HISTORY):
    dbutils.fs.mkdirs(d)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helpers

# COMMAND ----------

import json, os, time

def write_jsonl(directory, filename, records):
    """Write a list of dicts as one newline-delimited JSON file into a Volume folder.
    Auto Loader picks up each new file as it appears."""
    path = f"{directory}/{filename}"
    payload = "\n".join(json.dumps(r) for r in records)
    # Standard Python file IO works against /Volumes paths in Databricks.
    with open(path, "w") as f:
        f.write(payload)
    print(f"  wrote {len(records):>3} records -> {path}")
    return path

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell: initial load  (run once)
# MAGIC
# MAGIC Writes:
# MAGIC - **clients** — includes a deliberate duplicate (client C001 appears twice with a
# MAGIC   changed segment) so the `clients_clean` materialized view has something to dedup.
# MAGIC - **loans** — one loan per client, plus a second loan for one client.
# MAGIC - **payments/history** — older payments (2023–2024) for the **backfill** flow.
# MAGIC - **payments/incoming** — current payments (2025), including two bad records:
# MAGIC   - a payment with `client_id = null`  → **dropped** by the silver drop expectation.
# MAGIC   - a payment of 5,000,000            → **warned** (kept, flagged) by the warn expectation.

# COMMAND ----------

# ---- clients (note the duplicate C001) ----
clients = [
    {"client_id": "C001", "name": "Aera Holdings",   "segment": "SME",        "country": "NL", "signup_date": "2021-03-01"},
    {"client_id": "C001", "name": "Aera Holdings",   "segment": "Corporate",  "country": "NL", "signup_date": "2024-11-15"},  # updated dup
    {"client_id": "C002", "name": "Borent BV",       "segment": "SME",        "country": "NL", "signup_date": "2022-07-19"},
    {"client_id": "C003", "name": "Cygnus Retail",   "segment": "Retail",     "country": "BE", "signup_date": "2020-01-30"},
    {"client_id": "C004", "name": "Delta Freight",   "segment": "Corporate",  "country": "DE", "signup_date": "2023-05-05"},
    {"client_id": "C005", "name": "Estel Marine",    "segment": "SME",        "country": "NL", "signup_date": "2024-02-11"},
]
write_jsonl(CLIENTS_DIR, "clients_0001.json", clients)

# ---- loans ----
loans = [
    {"loan_id": "L100", "client_id": "C001", "principal": 250000.0, "rate": 0.041, "origination_date": "2023-04-01", "status": "active"},
    {"loan_id": "L101", "client_id": "C002", "principal": 80000.0,  "rate": 0.052, "origination_date": "2023-09-12", "status": "active"},
    {"loan_id": "L102", "client_id": "C003", "principal": 15000.0,  "rate": 0.061, "origination_date": "2024-01-05", "status": "active"},
    {"loan_id": "L103", "client_id": "C004", "principal": 500000.0, "rate": 0.038, "origination_date": "2023-06-20", "status": "active"},
    {"loan_id": "L104", "client_id": "C004", "principal": 120000.0, "rate": 0.045, "origination_date": "2024-08-01", "status": "active"},
    {"loan_id": "L105", "client_id": "C005", "principal": 60000.0,  "rate": 0.049, "origination_date": "2024-03-15", "status": "active"},
]
write_jsonl(LOANS_DIR, "loans_0001.json", loans)

# ---- payment history (backfill source: older payments) ----
history = [
    {"payment_id": "PH001", "client_id": "C001", "loan_id": "L100", "amount": 5000.0, "currency": "EUR", "payment_date": "2023-05-01"},
    {"payment_id": "PH002", "client_id": "C001", "loan_id": "L100", "amount": 5000.0, "currency": "EUR", "payment_date": "2023-06-01"},
    {"payment_id": "PH003", "client_id": "C002", "loan_id": "L101", "amount": 2000.0, "currency": "EUR", "payment_date": "2023-10-01"},
    {"payment_id": "PH004", "client_id": "C003", "loan_id": "L102", "amount": 500.0,  "currency": "EUR", "payment_date": "2024-02-01"},
    {"payment_id": "PH005", "client_id": "C004", "loan_id": "L103", "amount": 12000.0,"currency": "EUR", "payment_date": "2023-07-01"},
]
write_jsonl(PAY_HISTORY, "history_0001.json", history)

# ---- first incoming batch (current payments + 2 bad records) ----
incoming_1 = [
    {"payment_id": "P001", "client_id": "C001", "loan_id": "L100", "amount": 5200.0,  "currency": "EUR", "payment_date": "2025-01-05"},
    {"payment_id": "P002", "client_id": "C002", "loan_id": "L101", "amount": 2100.0,  "currency": "EUR", "payment_date": "2025-01-06"},
    {"payment_id": "P003", "client_id": "C003", "loan_id": "L102", "amount": 550.0,   "currency": "EUR", "payment_date": "2025-01-07"},
    {"payment_id": "P004", "client_id": "C004", "loan_id": "L103", "amount": 15000.0, "currency": "EUR", "payment_date": "2025-01-08"},
    # --- deliberately bad #1: null client_id -> DROPPED by the drop expectation ---
    {"payment_id": "P005", "client_id": None,   "loan_id": "L104", "amount": 900.0,   "currency": "EUR", "payment_date": "2025-01-09"},
    # --- deliberately bad #2: implausibly large amount -> WARNED (kept + flagged) ---
    {"payment_id": "P006", "client_id": "C005", "loan_id": "L105", "amount": 5000000.0,"currency": "EUR", "payment_date": "2025-01-10"},
]
write_jsonl(PAY_INCOMING, "incoming_0001.json", incoming_1)

print("\nInitial load complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell: incremental batch  (run after the first pipeline run)
# MAGIC
# MAGIC Drops a second file into `payments/incoming/`. Re-run the pipeline afterwards:
# MAGIC the streaming table should append **only these new rows** (proof of incremental
# MAGIC processing). Includes one more null-client record so the drop metric ticks up.

# COMMAND ----------

incoming_2 = [
    {"payment_id": "P007", "client_id": "C001", "loan_id": "L100", "amount": 5200.0, "currency": "EUR", "payment_date": "2025-02-05"},
    {"payment_id": "P008", "client_id": "C002", "loan_id": "L101", "amount": 2100.0, "currency": "EUR", "payment_date": "2025-02-06"},
    {"payment_id": "P009", "client_id": "C004", "loan_id": "L104", "amount": 3000.0, "currency": "EUR", "payment_date": "2025-02-07"},
    {"payment_id": "P010", "client_id": "C005", "loan_id": "L105", "amount": 1500.0, "currency": "EUR", "payment_date": "2025-02-08"},
    # another null-client record -> dropped again
    {"payment_id": "P011", "client_id": None,   "loan_id": "L102", "amount": 400.0,  "currency": "EUR", "payment_date": "2025-02-09"},
]
write_jsonl(PAY_INCOMING, f"incoming_{int(time.time())}.json", incoming_2)
print("\nIncremental batch written. Re-run the pipeline.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell: inject FAIL record  (optional — to see ON VIOLATION FAIL UPDATE)
# MAGIC
# MAGIC Writes one payment with a **negative amount**. `payments_critical` has a
# MAGIC `CONSTRAINT ... EXPECT (amount >= 0) ON VIOLATION FAIL UPDATE`, so the next
# MAGIC pipeline run will **fail** on that flow with an `EXPECTATION_VIOLATION` error.
# MAGIC Screenshot the failed flow + the error message, then run **Cell: reset**.

# COMMAND ----------

bad = [
    {"payment_id": "P999", "client_id": "C003", "loan_id": "L102", "amount": -250.0, "currency": "EUR", "payment_date": "2025-03-01"},
]
write_jsonl(PAY_INCOMING, "incoming_fail_inject.json", bad)
print("\nFAIL-triggering record written. Re-run the pipeline to see it stop.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell: reset  (delete all generated files and start clean)
# MAGIC
# MAGIC Removes every generated file so you can re-run from a clean slate. After this,
# MAGIC re-run **Cell: initial load** and do a **full refresh** of the pipeline.

# COMMAND ----------

for d in (CLIENTS_DIR, LOANS_DIR, PAY_INCOMING, PAY_HISTORY):
    try:
        dbutils.fs.rm(d, recurse=True)
        dbutils.fs.mkdirs(d)
        print("cleared", d)
    except Exception as e:
        print("skip", d, e)
print("\nReset complete. Re-run 'initial load' and full-refresh the pipeline.")
</content>
