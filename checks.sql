-- 1. Freshness: the latest date with a value, per series
SELECT
    series_id,
    MAX(obs_date) AS latest_date,
    CURRENT_DATE - MAX(obs_date) AS days_old
FROM observation
WHERE value IS NOT NULL
GROUP BY series_id
ORDER BY series_id;

-- 2. Rows with no value (daily yields have one for each market holiday)
SELECT
    series_id,
    COUNT(*) AS rows_without_value
FROM observation
WHERE value IS NULL
GROUP BY series_id
ORDER BY series_id;

-- 3. Monthly series: months that exist but have no value
SELECT
    o.series_id,
    o.obs_date
FROM observation AS o
JOIN series AS s ON s.series_id = o.series_id
WHERE s.frequency = 'M'
  AND o.value IS NULL
ORDER BY o.series_id, o.obs_date;

-- 4. Monthly series: months with no row at all
WITH bounds AS (
    SELECT
        o.series_id,
        MIN(o.obs_date) AS first_month
    FROM observation AS o
    JOIN series AS s ON s.series_id = o.series_id
    WHERE s.frequency = 'M'
    GROUP BY o.series_id
),
expected AS (
    SELECT
        series_id,
        generate_series(
            first_month,
            DATE_TRUNC('month', CURRENT_DATE)::date - INTERVAL '2 months',
            INTERVAL '1 month'
        )::date AS obs_date
    FROM bounds
)
SELECT
    e.series_id,
    e.obs_date AS missing_month
FROM expected AS e
LEFT JOIN observation AS o
    ON o.series_id = e.series_id
   AND o.obs_date = e.obs_date
WHERE o.obs_date IS NULL
ORDER BY e.series_id, e.obs_date;
