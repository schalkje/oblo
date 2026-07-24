-- =============================================================================
-- BRONZE — ingest with streaming tables (each row processed once)
-- =============================================================================
-- This is one of THREE source files in this pipeline (01_bronze / 02_silver /
-- 03_gold). Splitting by medallion layer is just for humans: the engine reads
-- every source file first, resolves dependencies BY NAME across files, and
-- builds one DAG. File boundaries and statement order do not matter.
--
-- BEFORE YOU RUN: find-and-replace the placeholder volume path below with YOUR
-- path (it only appears in this bronze file, in three read_files() calls):
--     /Volumes/main/finance_poc/landing
-- =============================================================================

-- Clients dimension, raw as it lands.
CREATE OR REFRESH STREAMING TABLE clients_raw
COMMENT 'Bronze: raw client records as they land in the volume.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT * FROM STREAM read_files(
  '/Volumes/main/finance_poc/landing/clients',
  format => 'json'
);

-- Loans, raw.
CREATE OR REFRESH STREAMING TABLE loans_raw
COMMENT 'Bronze: raw loan records.'
TBLPROPERTIES ('quality' = 'bronze')
AS SELECT * FROM STREAM read_files(
  '/Volumes/main/finance_poc/landing/loans',
  format => 'json'
);

-- Payments, raw. This table shows BACKLOADING: it has TWO flows writing into it,
-- an ongoing streaming flow (current payments) and a one-time backfill flow
-- (historical payments). The engine merges both into one streaming table.
CREATE OR REFRESH STREAMING TABLE payments_raw
COMMENT 'Bronze: raw payments. Fed by an ongoing streaming flow plus a one-time historical backfill flow.'
TBLPROPERTIES ('quality' = 'bronze');

-- Ongoing streaming flow: reads new files as they arrive in /incoming.
CREATE FLOW payments_raw_incremental
AS INSERT INTO payments_raw BY NAME
SELECT * FROM STREAM read_files(
  '/Volumes/main/finance_poc/landing/payments/incoming',
  format => 'json'
);

-- One-time backfill flow: reads the historical payments once (INSERT INTO ONCE).
-- It stays in the graph but goes idle after running; a full refresh re-runs it.
CREATE FLOW payments_raw_backfill
AS INSERT INTO ONCE payments_raw BY NAME
SELECT * FROM read_files(
  '/Volumes/main/finance_poc/landing/payments/history',
  format => 'json'
);
</content>
