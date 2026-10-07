SELECT taxi, hour(pickup) AS hour, count(*) AS trips
FROM trips_clean GROUP BY ALL ORDER BY taxi, hour
