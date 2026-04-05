CREATE OR REPLACE VIEW defense_spending_analysis AS
SELECT
    c.id AS country_id,
    c.name AS country,
    c.region,
    c.subregion,
    c.nato_member,
    d.year,
    d.spending_usd,
    d.spending_usd - LAG(d.spending_usd) OVER (
        PARTITION BY d.country_id ORDER BY d.year
    ) AS yoy_absolute_change,
    (
        (d.spending_usd - LAG(d.spending_usd) OVER (
            PARTITION BY d.country_id ORDER BY d.year
        )) /
        NULLIF(LAG(d.spending_usd) OVER (
            PARTITION BY d.country_id ORDER BY d.year
        ), 0)
    ) * 100 AS yoy_percent_change,
    (
        (d.spending_usd - LAG(d.spending_usd, 5) OVER (
            PARTITION BY d.country_id ORDER BY d.year
        )) /
        NULLIF(LAG(d.spending_usd, 5) OVER (
            PARTITION BY d.country_id ORDER BY d.year
        ), 0)
    ) * 100 AS growth_5yr_percent,
    ROUND(
        (
            d.spending_usd * 100.0 /
            SUM(d.spending_usd) OVER (PARTITION BY d.year)
        )::numeric,
        2
    ) AS global_share_percent,
    RANK() OVER (
        PARTITION BY d.year ORDER BY d.spending_usd DESC
    ) AS spending_rank
FROM defense_spending d
JOIN countries c ON d.country_id = c.id;