SELECT taxi, source_year,
    quantile_cont(trip_distance, [0.25, 0.5, 0.75, 0.95, 0.99]) AS distance_quantiles,
    quantile_cont(total_amount, [0.25, 0.5, 0.75, 0.95, 0.99]) AS total_quantiles,
    quantile_cont(duration_minutes, [0.25, 0.5, 0.75, 0.95, 0.99]) AS duration_quantiles
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year
