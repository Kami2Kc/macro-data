-- US inflation: % change in CPI on the same month a year earlier
CREATE OR REPLACE VIEW cpi_yoy AS
SELECT
    obs_date,
    value AS cpi_index,
    ROUND(100 * (value / LAG(value, 12) OVER (ORDER BY obs_date) - 1), 2) AS yoy_pct
FROM observation
WHERE series_id = 'CPIAUCSL';

-- Yield curve slope: 10-year minus 2-year Treasury yield, in percentage points
CREATE OR REPLACE VIEW curve_slope AS
SELECT
    obs_date,
    MAX(value) FILTER (WHERE series_id = 'DGS10')
    - MAX(value) FILTER (WHERE series_id = 'DGS2') AS slope_10y_2y
FROM observation
WHERE series_id IN ('DGS2', 'DGS10')
GROUP BY obs_date;
