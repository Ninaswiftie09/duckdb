WITH monthly AS (
    SELECT taxi, source_year, source_month, count(*) AS trips,
        sum(total_amount) AS total, sum(trip_distance) AS distance,
        sum(duration_minutes) AS duration, sum(cbd_congestion_fee) AS cbd_fee,
        count(cbd_congestion_fee) AS cbd_observations
    FROM trips_clean GROUP BY taxi, source_year, source_month
), common_months AS (
    SELECT source_month FROM monthly GROUP BY source_month
    HAVING count(DISTINCT source_year) = 3
)
SELECT taxi, source_year, sum(trips) AS trips, sum(total) / sum(trips) AS mean_total,
    sum(distance) / sum(trips) AS mean_distance, sum(duration) / sum(trips) AS mean_duration,
    sum(cbd_fee) / nullif(sum(cbd_observations), 0) AS mean_cbd_fee
FROM monthly WHERE source_month IN (SELECT source_month FROM common_months)
GROUP BY ALL ORDER BY taxi, source_year
