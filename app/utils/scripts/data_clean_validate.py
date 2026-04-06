from sqlalchemy import text
from app.core.database import engine


PHASE3_SQL = """
BEGIN;

-- =========================================================
-- DROP OLD OBJECTS
-- =========================================================
DROP VIEW IF EXISTS vw_spending_as_pct_gdp CASCADE;
DROP VIEW IF EXISTS vw_spending_volatility CASCADE;
DROP VIEW IF EXISTS vw_spending_trend_classification CASCADE;
DROP VIEW IF EXISTS vw_spending_share_global CASCADE;
DROP VIEW IF EXISTS vw_spending_cagr_windows CASCADE;
DROP VIEW IF EXISTS vw_spending_yoy_growth CASCADE;

DROP VIEW IF EXISTS vw_validation_duplicate_country_year CASCADE;
DROP VIEW IF EXISTS vw_validation_negative_values CASCADE;
DROP VIEW IF EXISTS vw_validation_missing_years CASCADE;
DROP VIEW IF EXISTS vw_validation_country_name_normalization CASCADE;

DROP TABLE IF EXISTS country_name_normalization CASCADE;
DROP TABLE IF EXISTS historical_spending_clean CASCADE;

-- =========================================================
-- 1) COUNTRY NAME NORMALIZATION MAP
-- Expand this as needed
-- =========================================================
CREATE TABLE country_name_normalization (
    raw_name TEXT PRIMARY KEY,
    normalized_name TEXT NOT NULL
);

INSERT INTO country_name_normalization (raw_name, normalized_name) VALUES
    ('United States of America', 'United States'),
    ('USA', 'United States'),
    ('U.S.', 'United States'),
    ('Russian Federation', 'Russia'),
    ('Republic of Korea', 'South Korea'),
    ('Korea, Republic of', 'South Korea'),
    ('Democratic People''s Republic of Korea', 'North Korea'),
    ('UK', 'United Kingdom'),
    ('U.K.', 'United Kingdom'),
    ('Viet Nam', 'Vietnam'),
    ('Türkiye', 'Turkey'),
    ('Czech Republic', 'Czechia')
ON CONFLICT (raw_name) DO NOTHING;

-- =========================================================
-- 2) VALIDATION: DUPLICATES
-- duplicate normalized country + year rows
-- =========================================================
CREATE VIEW vw_validation_duplicate_country_year AS
WITH base AS (
    SELECT
        hs.id,
        hs.year,
        hs.source,
        c.name AS raw_country_name,
        COALESCE(cnn.normalized_name, c.name) AS normalized_country_name
    FROM historical_spending hs
    JOIN countries c
      ON c.id = hs.country_id
    LEFT JOIN country_name_normalization cnn
      ON LOWER(TRIM(c.name)) = LOWER(TRIM(cnn.raw_name))
)
SELECT
    normalized_country_name,
    year,
    COUNT(*) AS row_count,
    STRING_AGG(source, ', ' ORDER BY source) AS sources
FROM base
GROUP BY normalized_country_name, year
HAVING COUNT(*) > 1
ORDER BY normalized_country_name, year;

-- =========================================================
-- 3) VALIDATION: NEGATIVE / IMPOSSIBLE VALUES
-- =========================================================
CREATE VIEW vw_validation_negative_values AS
SELECT
    hs.id,
    c.name AS country_name,
    hs.year,
    hs.spending_usd,
    hs.gdp_percent,
    hs.per_capita,
    hs.source
FROM historical_spending hs
JOIN countries c
  ON c.id = hs.country_id
WHERE hs.spending_usd < 0
   OR (hs.gdp_percent IS NOT NULL AND hs.gdp_percent < 0)
   OR (hs.per_capita IS NOT NULL AND hs.per_capita < 0)
ORDER BY c.name, hs.year;

-- =========================================================
-- 4) VALIDATION: COUNTRY NAME NORMALIZATION CHECK
-- shows raw -> normalized names
-- =========================================================
CREATE VIEW vw_validation_country_name_normalization AS
SELECT DISTINCT
    c.name AS raw_country_name,
    COALESCE(cnn.normalized_name, c.name) AS normalized_country_name
FROM countries c
LEFT JOIN country_name_normalization cnn
  ON LOWER(TRIM(c.name)) = LOWER(TRIM(cnn.raw_name))
ORDER BY normalized_country_name, raw_country_name;

-- =========================================================
-- 5) CLEAN TABLE
-- Rules:
-- - normalize country names
-- - remove impossible negatives
-- - dedupe country-year using source priority
-- =========================================================
CREATE TABLE historical_spending_clean AS
WITH base AS (
    SELECT
        hs.id,
        hs.country_id,
        hs.year::INT AS year,
        hs.spending_usd::NUMERIC(20,2) AS spending_usd,
        hs.gdp_percent::NUMERIC(10,4) AS gdp_percent,
        hs.per_capita::NUMERIC(20,2) AS per_capita,
        hs.source,
        hs.notes,
        c.name AS raw_country_name,
        COALESCE(cnn.normalized_name, c.name) AS country_name,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(cnn.normalized_name, c.name), hs.year
            ORDER BY
                CASE
                    WHEN LOWER(hs.source) LIKE '%sipri%' THEN 1
                    WHEN LOWER(hs.source) LIKE '%world bank%' THEN 2
                    WHEN LOWER(hs.source) LIKE '%nato%' THEN 3
                    ELSE 99
                END,
                hs.id DESC
        ) AS rn
    FROM historical_spending hs
    JOIN countries c
      ON c.id = hs.country_id
    LEFT JOIN country_name_normalization cnn
      ON LOWER(TRIM(c.name)) = LOWER(TRIM(cnn.raw_name))
    WHERE hs.spending_usd >= 0
      AND (hs.gdp_percent IS NULL OR hs.gdp_percent >= 0)
      AND (hs.per_capita IS NULL OR hs.per_capita >= 0)
)
SELECT
    id,
    country_id,
    country_name,
    raw_country_name,
    year,
    spending_usd,
    gdp_percent,
    per_capita,
    source,
    notes
FROM base
WHERE rn = 1;

CREATE INDEX idx_historical_spending_clean_country_year
    ON historical_spending_clean (country_name, year);

CREATE INDEX idx_historical_spending_clean_year
    ON historical_spending_clean (year);

-- =========================================================
-- 6) VALIDATION: MISSING YEARS
-- For each country, check gaps between min(year) and max(year)
-- =========================================================
CREATE VIEW vw_validation_missing_years AS
WITH country_ranges AS (
    SELECT
        country_name,
        MIN(year) AS min_year,
        MAX(year) AS max_year
    FROM historical_spending_clean
    GROUP BY country_name
),
expected_years AS (
    SELECT
        cr.country_name,
        gs.year::INT AS expected_year
    FROM country_ranges cr,
         LATERAL generate_series(cr.min_year, cr.max_year) AS gs(year)
),
actual_years AS (
    SELECT DISTINCT
        country_name,
        year
    FROM historical_spending_clean
)
SELECT
    ey.country_name,
    ey.expected_year AS missing_year
FROM expected_years ey
LEFT JOIN actual_years ay
  ON ay.country_name = ey.country_name
 AND ay.year = ey.expected_year
WHERE ay.year IS NULL
ORDER BY ey.country_name, ey.expected_year;

-- =========================================================
-- 7) YoY GROWTH
-- =========================================================
CREATE VIEW vw_spending_yoy_growth AS
WITH ordered AS (
    SELECT
        country_name,
        year,
        spending_usd,
        LAG(spending_usd) OVER (
            PARTITION BY country_name
            ORDER BY year
        ) AS prev_spending_usd
    FROM historical_spending_clean
)
SELECT
    country_name,
    year,
    spending_usd,
    prev_spending_usd,
    CASE
        WHEN prev_spending_usd IS NULL OR prev_spending_usd = 0 THEN NULL
        ELSE ROUND(((spending_usd - prev_spending_usd) / prev_spending_usd) * 100, 4)
    END AS yoy_growth_pct
FROM ordered
ORDER BY country_name, year;

-- =========================================================
-- 8) CAGR OVER WINDOWS
-- Computes trailing 3-year, 5-year, and 10-year CAGR
-- CAGR = (end/start)^(1/n) - 1
-- =========================================================
CREATE VIEW vw_spending_cagr_windows AS
WITH base AS (
    SELECT
        cur.country_name,
        cur.year,
        cur.spending_usd AS current_spending,

        lag3.spending_usd AS spending_3y_ago,
        lag5.spending_usd AS spending_5y_ago,
        lag10.spending_usd AS spending_10y_ago

    FROM historical_spending_clean cur
    LEFT JOIN historical_spending_clean lag3
      ON lag3.country_name = cur.country_name
     AND lag3.year = cur.year - 3
    LEFT JOIN historical_spending_clean lag5
      ON lag5.country_name = cur.country_name
     AND lag5.year = cur.year - 5
    LEFT JOIN historical_spending_clean lag10
      ON lag10.country_name = cur.country_name
     AND lag10.year = cur.year - 10
)
SELECT
    country_name,
    year,
    current_spending,

    CASE
        WHEN spending_3y_ago IS NULL OR spending_3y_ago <= 0 OR current_spending <= 0 THEN NULL
        ELSE ROUND((POWER((current_spending / spending_3y_ago), (1.0 / 3)) - 1) * 100, 4)
    END AS cagr_3y_pct,

    CASE
        WHEN spending_5y_ago IS NULL OR spending_5y_ago <= 0 OR current_spending <= 0 THEN NULL
        ELSE ROUND((POWER((current_spending / spending_5y_ago), (1.0 / 5)) - 1) * 100, 4)
    END AS cagr_5y_pct,

    CASE
        WHEN spending_10y_ago IS NULL OR spending_10y_ago <= 0 OR current_spending <= 0 THEN NULL
        ELSE ROUND((POWER((current_spending / spending_10y_ago), (1.0 / 10)) - 1) * 100, 4)
    END AS cagr_10y_pct

FROM base
ORDER BY country_name, year;

-- =========================================================
-- 9) SHARE OF GLOBAL SPENDING
-- =========================================================
CREATE VIEW vw_spending_share_global AS
WITH yearly_totals AS (
    SELECT
        year,
        SUM(spending_usd) AS global_spending_usd
    FROM historical_spending_clean
    GROUP BY year
)
SELECT
    hsc.country_name,
    hsc.year,
    hsc.spending_usd,
    yt.global_spending_usd,
    CASE
        WHEN yt.global_spending_usd = 0 THEN NULL
        ELSE ROUND((hsc.spending_usd / yt.global_spending_usd) * 100, 6)
    END AS global_spending_share_pct
FROM historical_spending_clean hsc
JOIN yearly_totals yt
  ON yt.year = hsc.year
ORDER BY hsc.year, global_spending_share_pct DESC NULLS LAST;

-- =========================================================
-- 10) VOLATILITY
-- trailing 5-year stddev of YoY growth
-- =========================================================
CREATE VIEW vw_spending_volatility AS
WITH yoy AS (
    SELECT
        country_name,
        year,
        yoy_growth_pct
    FROM vw_spending_yoy_growth
),
rolling AS (
    SELECT
        country_name,
        year,
        STDDEV_SAMP(yoy_growth_pct) OVER (
            PARTITION BY country_name
            ORDER BY year
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS yoy_volatility_5y
    FROM yoy
)
SELECT
    country_name,
    year,
    ROUND(yoy_volatility_5y::NUMERIC, 4) AS yoy_volatility_5y
FROM rolling
ORDER BY country_name, year;

-- =========================================================
-- 11) SPENDING AS % GDP
-- your schema already stores gdp_percent
-- we surface cleaned version as a derived analytics view
-- =========================================================
CREATE VIEW vw_spending_as_pct_gdp AS
SELECT
    country_name,
    year,
    spending_usd,
    gdp_percent AS spending_pct_gdp,
    per_capita
FROM historical_spending_clean
ORDER BY country_name, year;

-- =========================================================
-- 12) TREND CLASSIFICATION
-- based on 5y CAGR + volatility
-- =========================================================
CREATE VIEW vw_spending_trend_classification AS
WITH joined AS (
    SELECT
        c.country_name,
        c.year,
        c.cagr_5y_pct,
        v.yoy_volatility_5y
    FROM vw_spending_cagr_windows c
    LEFT JOIN vw_spending_volatility v
      ON v.country_name = c.country_name
     AND v.year = c.year
)
SELECT
    country_name,
    year,
    cagr_5y_pct,
    yoy_volatility_5y,
    CASE
        WHEN cagr_5y_pct IS NULL THEN 'insufficient_data'
        WHEN cagr_5y_pct >= 8 AND COALESCE(yoy_volatility_5y, 0) < 10 THEN 'strong_upward_stable'
        WHEN cagr_5y_pct >= 8 AND COALESCE(yoy_volatility_5y, 0) >= 10 THEN 'strong_upward_volatile'
        WHEN cagr_5y_pct >= 2 THEN 'moderate_upward'
        WHEN cagr_5y_pct > -2 AND cagr_5y_pct < 2 THEN 'flat'
        WHEN cagr_5y_pct <= -2 AND cagr_5y_pct > -8 THEN 'moderate_decline'
        WHEN cagr_5y_pct <= -8 THEN 'sharp_decline'
        ELSE 'unclassified'
    END AS trend_classification
FROM joined
ORDER BY country_name, year;

COMMIT;
"""


def clean_validate_data():
    with engine.begin() as conn:
        conn.execute(text(PHASE3_SQL))
    print("Phase 3 complete.")
    print("Created:")
    print("- historical_spending_clean")
    print("- vw_validation_duplicate_country_year")
    print("- vw_validation_negative_values")
    print("- vw_validation_missing_years")
    print("- vw_validation_country_name_normalization")
    print("- vw_spending_yoy_growth")
    print("- vw_spending_cagr_windows")
    print("- vw_spending_share_global")
    print("- vw_spending_trend_classification")
    print("- vw_spending_volatility")
    print("- vw_spending_as_pct_gdp")
