SELECT taxi, source_year, count(DISTINCT source_file) AS files,
    count(*) AS rows, min(pickup) AS first_pickup, max(pickup) AS last_pickup
FROM trips_raw GROUP BY ALL ORDER BY taxi, source_year
