-- =============================================================================
-- SILVER — validate (streaming table + expectations) and a dimension (MV)
-- =============================================================================
-- These tables reference the bronze tables (defined in 01_bronze.sql) purely by
-- name. No imports, no ordering, no glue: the reference IS the dependency.
-- =============================================================================

-- Validated payments. Demonstrates table + column descriptions, table
-- properties, and two of the three expectation behaviours:
--   warn  -> plausible_amount : large amounts are KEPT but flagged in metrics.
--   drop  -> known_client     : payments with no client_id are DROPPED.
CREATE OR REFRESH STREAMING TABLE payments_validated (
  payment_id   STRING COMMENT 'Unique payment identifier',
  client_id    STRING COMMENT 'Client that made the payment; must be present',
  loan_id      STRING COMMENT 'Loan the payment is applied to',
  amount       DOUBLE COMMENT 'Payment amount in the original currency',
  currency     STRING COMMENT 'ISO currency code',
  payment_date DATE   COMMENT 'Date the payment was booked',
  CONSTRAINT plausible_amount EXPECT (amount <= 1000000),
  CONSTRAINT known_client     EXPECT (client_id IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Silver: validated payments. Implausibly large amounts are flagged (warn); orphan payments with no client are dropped.'
TBLPROPERTIES ('quality' = 'silver', 'pipelines.reset.allowed' = 'true')
AS SELECT
  payment_id,
  client_id,
  loan_id,
  CAST(amount AS DOUBLE)     AS amount,
  currency,
  CAST(payment_date AS DATE) AS payment_date
FROM STREAM(payments_raw);

-- The third expectation behaviour: FAIL. Under a normal run every amount is >= 0
-- so this passes. Run 00_generate_data.py (Cell: inject FAIL record) to drop a
-- negative amount and watch this flow STOP the update with an EXPECTATION_VIOLATION.
CREATE OR REFRESH STREAMING TABLE payments_critical (
  CONSTRAINT non_negative_amount EXPECT (amount >= 0) ON VIOLATION FAIL UPDATE
)
COMMENT 'Silver+: payments that must never be negative. A single bad record here stops the pipeline update.'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT * FROM STREAM(payments_validated);

-- Client dimension, de-duplicated. This is a MATERIALIZED VIEW because it is a
-- small dimension read by multiple downstreams and its source can CHANGE (a
-- client row gets updated), so we want it recomputed to stay correct -- exactly
-- the case the docs say to prefer an MV over a streaming table.
CREATE OR REFRESH MATERIALIZED VIEW clients_clean (
  client_id   STRING COMMENT 'Unique client identifier',
  name        STRING COMMENT 'Client legal name',
  segment     STRING COMMENT 'Latest known client segment',
  country     STRING COMMENT 'Country code',
  signup_date DATE   COMMENT 'Date the client was onboarded'
)
COMMENT 'Silver dimension: one row per client, keeping the most recent record.'
TBLPROPERTIES ('quality' = 'silver')
AS SELECT
  client_id,
  name,
  segment,
  country,
  CAST(signup_date AS DATE) AS signup_date
FROM clients_raw
QUALIFY ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY signup_date DESC) = 1;
</content>
