SELECT
    regexp_extract(filename, '(yellow|green)_tripdata_', 1) AS taxi,
    CAST(regexp_extract(filename, 'tripdata_(\d{4})-', 1) AS INTEGER) AS source_year,
    CAST(regexp_extract(filename, 'tripdata_\d{4}-(\d{2})', 1) AS INTEGER) AS source_month,
    filename AS source_file,
    COALESCE(tpep_pickup_datetime, lpep_pickup_datetime) AS pickup,
    COALESCE(tpep_dropoff_datetime, lpep_dropoff_datetime) AS dropoff,
    passenger_count, trip_distance, fare_amount, total_amount,
    tip_amount, payment_type, PULocationID AS pickup_zone,
    DOLocationID AS dropoff_zone, cbd_congestion_fee,
    date_diff('second', COALESCE(tpep_pickup_datetime, lpep_pickup_datetime),
        COALESCE(tpep_dropoff_datetime, lpep_dropoff_datetime)) / 60.0 AS duration_minutes
FROM read_parquet({files}, union_by_name = true, filename = true)
