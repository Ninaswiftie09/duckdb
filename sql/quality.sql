SELECT taxi, source_year, count(*) AS rows,
    count(*) FILTER (WHERE pickup IS NULL) AS missing_pickup,
    count(*) FILTER (WHERE year(pickup) != source_year OR month(pickup) != source_month) AS wrong_period,
    count(*) FILTER (WHERE trip_distance <= 0 OR trip_distance IS NULL) AS invalid_distance,
    count(*) FILTER (WHERE duration_minutes <= 0 OR duration_minutes > 180 OR duration_minutes IS NULL) AS invalid_duration,
    count(*) FILTER (WHERE total_amount <= 0 OR total_amount IS NULL) AS invalid_total,
    count(*) FILTER (WHERE passenger_count IS NULL) AS missing_passengers,
    count(*) FILTER (WHERE passenger_count = 0) AS zero_passengers,
    count(*) FILTER (WHERE trip_distance > 100 OR total_amount > 500) AS extreme_values
FROM trips_raw GROUP BY ALL ORDER BY taxi, source_year
