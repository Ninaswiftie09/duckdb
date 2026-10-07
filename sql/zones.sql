SELECT taxi, pickup_zone, count(*) AS trips
FROM trips_clean GROUP BY ALL QUALIFY row_number() OVER (PARTITION BY taxi ORDER BY count(*) DESC) <= 10
ORDER BY taxi, trips DESC
