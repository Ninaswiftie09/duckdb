WITH common_months AS (
    SELECT source_month FROM trips_raw GROUP BY source_month
    HAVING count(DISTINCT source_year) = 3
)
SELECT taxi, source_year, count(*) AS trips, avg(total_amount) AS mean_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    avg(cbd_congestion_fee) AS mean_cbd_fee
FROM trips_clean WHERE source_month IN (SELECT source_month FROM common_months)
GROUP BY ALL ORDER BY taxi, source_year
