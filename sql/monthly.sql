SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
