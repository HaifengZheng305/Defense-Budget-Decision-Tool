-- Country signal latest and flags views built off historical_spending (SIPRI)

-- Helper: latest year per country for SIPRI source
CREATE OR REPLACE VIEW vw_country_latest_spending AS
WITH base AS (
    SELECT
        hs.country_id,
        hs.year,
        hs.spending_usd,
        hs.gdp_percent,
        hs.per_capita,
        ROW_NUMBER() OVER (PARTITION BY hs.country_id ORDER BY hs.year DESC) AS rn
    FROM historical_spending hs
    WHERE hs.source = 'SIPRI'
)
SELECT
    b.country_id,
    b.year,
    b.spending_usd,
    b.gdp_percent,
    b.per_capita
FROM base b
WHERE b.rn = 1;

-- Helper: previous (latest-1) spending per country
CREATE OR REPLACE VIEW vw_country_prev_spending AS
WITH latest AS (
    SELECT country_id, year
    FROM vw_country_latest_spending
),
prev AS (
    SELECT
        hs.country_id,
        hs.year,
        hs.spending_usd
    FROM historical_spending hs
    JOIN latest l
      ON l.country_id = hs.country_id
     AND hs.source = 'SIPRI'
     AND hs.year = l.year - 1
)
SELECT * FROM prev;

-- Helper: latest and 5y-ago values per country
CREATE OR REPLACE VIEW vw_country_5y_window AS
WITH latest AS (
    SELECT country_id, year, spending_usd
    FROM vw_country_latest_spending
),
ago5 AS (
    SELECT
        hs.country_id,
        hs.year AS year_5y,
        hs.spending_usd AS spending_usd_5y
    FROM historical_spending hs
    JOIN latest l
      ON l.country_id = hs.country_id
     AND hs.source = 'SIPRI'
     AND hs.year = l.year - 5
)
SELECT
    l.country_id,
    l.year AS latest_year,
    l.spending_usd AS latest_spending_usd,
    a5.year_5y,
    a5.spending_usd_5y
FROM latest l
LEFT JOIN ago5 a5 ON a5.country_id = l.country_id;

-- Helper: YoY percent series to compute 5y volatility (stddev of YoY% over last 5 intervals)
CREATE OR REPLACE VIEW vw_country_yoy_percent AS
WITH base AS (
    SELECT
        hs.country_id,
        hs.year,
        hs.spending_usd,
        LAG(hs.spending_usd) OVER (PARTITION BY hs.country_id ORDER BY hs.year) AS prev_spending_usd
    FROM historical_spending hs
    WHERE hs.source = 'SIPRI'
)
SELECT
    country_id,
    year,
    CASE
        WHEN prev_spending_usd IS NULL OR prev_spending_usd = 0 THEN NULL
        ELSE ((spending_usd - prev_spending_usd) / prev_spending_usd) * 100.0
    END AS yoy_percent
FROM base;

-- Helper: latest rank and 5y-ago rank
CREATE OR REPLACE VIEW vw_country_rank_tracks AS
WITH ranks AS (
    SELECT
        hs.year,
        hs.country_id,
        hs.spending_usd,
        RANK() OVER (PARTITION BY hs.year ORDER BY hs.spending_usd DESC) AS spending_rank
    FROM historical_spending hs
    WHERE hs.source = 'SIPRI'
),
latest AS (
    SELECT
        l.country_id,
        l.year AS latest_year,
        r.spending_rank AS latest_rank
    FROM (SELECT country_id, MAX(year) AS year FROM ranks GROUP BY country_id) l
    JOIN ranks r ON r.country_id = l.country_id AND r.year = l.year
),
ago5 AS (
    SELECT
        lt.country_id,
        r.spending_rank AS rank_5y,
        r.year AS year_5y
    FROM latest lt
    JOIN ranks r ON r.country_id = lt.country_id AND r.year = lt.latest_year - 5
)
SELECT
    lt.country_id,
    lt.latest_year,
    lt.latest_rank,
    a5.rank_5y,
    a5.year_5y
FROM latest lt
LEFT JOIN ago5 a5 ON a5.country_id = lt.country_id;

-- Main: country latest signal snapshot (single row per country)
CREATE OR REPLACE VIEW vw_country_signal_latest AS
WITH latest AS (
    SELECT cls.country_id,
           cls.year,
           cls.spending_usd,
           cls.gdp_percent,
           cls.per_capita
    FROM vw_country_latest_spending cls
),
prev AS (
    SELECT cps.country_id, cps.spending_usd AS prev_spending_usd
    FROM vw_country_prev_spending cps
),
five AS (
    SELECT cw.country_id,
           cw.latest_year,
           cw.latest_spending_usd,
           cw.spending_usd_5y
    FROM vw_country_5y_window cw
),
vol AS (
    WITH ly AS (
        SELECT country_id, MAX(year) AS latest_year
        FROM vw_country_yoy_percent
        GROUP BY country_id
    )
    SELECT
        vy.country_id,
        STDDEV_SAMP(vy.yoy_percent) AS volatility_5y
    FROM vw_country_yoy_percent vy
    JOIN ly ON ly.country_id = vy.country_id
    WHERE vy.year > ly.latest_year - 5
    GROUP BY vy.country_id
),
share AS (
    SELECT
        l.year,
        l.country_id,
        (l.spending_usd * 100.0) / NULLIF(SUM(l.spending_usd) OVER (PARTITION BY l.year), 0) AS share_global_pct
    FROM latest l
),
ranks AS (
    SELECT crt.country_id, crt.latest_year, crt.latest_rank, crt.rank_5y
    FROM vw_country_rank_tracks crt
)
SELECT
    c.id AS country_id,
    c.name AS country_name,
    c.iso3,
    c.region,
    c.subregion,
    l.year,
    l.spending_usd,
    CASE
        WHEN p.prev_spending_usd IS NULL OR p.prev_spending_usd = 0 THEN NULL
        ELSE ((l.spending_usd - p.prev_spending_usd) / p.prev_spending_usd) * 100.0
    END AS yoy_latest_pct,
    CASE
        WHEN f.spending_usd_5y IS NULL OR f.spending_usd_5y = 0 THEN NULL
        ELSE ((f.latest_spending_usd / f.spending_usd_5y) ^ (1.0 / 5) - 1.0) * 100.0
    END AS cagr_5y_pct,
    v.volatility_5y,
    s.share_global_pct,
    l.gdp_percent,
    r.latest_rank AS rank,
    CASE
        WHEN r.rank_5y IS NULL THEN NULL
        ELSE (r.rank_5y - r.latest_rank)
    END AS rank_change_5y
FROM latest l
JOIN countries c ON c.id = l.country_id
LEFT JOIN prev p ON p.country_id = l.country_id
LEFT JOIN five f ON f.country_id = l.country_id
LEFT JOIN vol v ON v.country_id = l.country_id
LEFT JOIN share s ON s.country_id = l.country_id AND s.year = l.year
LEFT JOIN ranks r ON r.country_id = l.country_id AND r.latest_year = l.year;

-- Heuristic flags on top of latest signals
CREATE OR REPLACE VIEW vw_country_signal_flags AS
SELECT
    country_id,
    country_name,
    iso3,
    region,
    subregion,
    year,
    spending_usd,
    yoy_latest_pct,
    cagr_5y_pct,
    COALESCE(volatility_5y, 0) AS volatility_5y,
    share_global_pct,
    gdp_percent,
    rank,
    rank_change_5y,
    CASE WHEN cagr_5y_pct IS NOT NULL AND cagr_5y_pct >= 8 THEN TRUE ELSE FALSE END AS rapid_growth_flag,
    CASE WHEN volatility_5y IS NOT NULL AND volatility_5y >= 10 THEN TRUE ELSE FALSE END AS high_volatility_flag,
    CASE WHEN gdp_percent IS NOT NULL AND gdp_percent >= 3 THEN TRUE ELSE FALSE END AS elevated_gdp_burden_flag,
    CASE WHEN rank_change_5y IS NOT NULL AND rank_change_5y <= -3 THEN TRUE ELSE FALSE END AS rising_rank_flag,
    CASE WHEN rank_change_5y IS NOT NULL AND rank_change_5y >= 3 THEN TRUE ELSE FALSE END AS declining_rank_flag,
    CASE WHEN share_global_pct IS NOT NULL AND share_global_pct >= 3 THEN TRUE ELSE FALSE END AS stable_major_spender_flag
FROM vw_country_signal_latest;