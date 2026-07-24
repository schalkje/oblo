-- =============================================================================
-- GOLD — aggregate (materialized view) + a plain reporting view
-- =============================================================================
-- Reads clients_clean, loans_raw and payments_validated from the other files by
-- name. Same pipeline, same DAG.
-- =============================================================================

-- Outstanding exposure per client: joins + aggregation -> MATERIALIZED VIEW.
-- On SERVERLESS this can refresh incrementally (check the Incrementalization
-- column / the planning_information event, see README.md). On classic compute it
-- is always fully recomputed -- that is the "big bad" to write about.
CREATE OR REFRESH MATERIALIZED VIEW client_exposure (
  client_id       STRING COMMENT 'Client identifier',
  name            STRING COMMENT 'Client legal name',
  segment         STRING COMMENT 'Client segment',
  total_principal DOUBLE COMMENT 'Sum of outstanding loan principal for the client',
  total_paid      DOUBLE COMMENT 'Sum of validated payments received from the client',
  exposure        DOUBLE COMMENT 'Outstanding balance = principal - payments'
)
COMMENT 'Gold: outstanding exposure per client. Aggregation over joins, kept as an MV so downstream reads are cheap and correct.'
TBLPROPERTIES ('quality' = 'gold')
AS
WITH loan_totals AS (
  SELECT client_id, SUM(principal) AS total_principal
  FROM loans_raw
  GROUP BY client_id
),
pay_totals AS (
  SELECT client_id, SUM(amount) AS total_paid
  FROM payments_validated
  GROUP BY client_id
)
SELECT
  c.client_id,
  c.name,
  c.segment,
  COALESCE(l.total_principal, 0) AS total_principal,
  COALESCE(p.total_paid, 0)      AS total_paid,
  COALESCE(l.total_principal, 0) - COALESCE(p.total_paid, 0) AS exposure
FROM clients_clean c
LEFT JOIN loan_totals l ON c.client_id = l.client_id
LEFT JOIN pay_totals  p ON c.client_id = p.client_id;

-- A plain (temporary) VIEW: evaluated on demand, NOT persisted to the catalog.
-- Use for intermediate / reporting logic with no need to store results. It still
-- shows up as a node in the DAG, but you won't find it in Catalog Explorer.
CREATE TEMPORARY VIEW high_exposure_clients
COMMENT 'Reporting view: clients with exposure above 100k. Evaluated on demand, not stored.'
AS SELECT
  client_id,
  name,
  segment,
  exposure
FROM client_exposure
WHERE exposure > 100000;
</content>
