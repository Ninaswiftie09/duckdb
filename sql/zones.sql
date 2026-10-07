SELECT taxi, pickup_zone, count(*) AS trips
FROM trips_clean GROUP BY taxi, pickup_zone QUALIFY row_number() OVER (PARTITION BY taxi ORDER BY count(*) DESC, pickup_zone) <= 10
ORDER BY taxi, trips DESC
