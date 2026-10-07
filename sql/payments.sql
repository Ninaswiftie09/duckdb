SELECT taxi, source_year, payment_type, count(*) AS trips,
    avg(total_amount) AS mean_total,
    avg(CASE WHEN payment_type = 1 AND fare_amount > 0 THEN 100.0 * tip_amount / fare_amount END) AS card_tip_percent
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, payment_type
