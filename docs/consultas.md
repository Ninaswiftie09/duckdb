# Documentación de consultas

Las consultas se ejecutan sobre todos los archivos yellow y green de los años seleccionados. Cada salida se guarda en docs/results/<años>/<consulta>.csv. Los resultados por etapa permiten revisar 2026, 2024 con 2026 y los tres años. El informe explica los resultados y decisiones.

## monthly: ¿Cómo cambia la cantidad de viajes por mes?

Se usa el volumen mensual para observar la demanda.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/monthly.csv.

```sql
SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
```

## coverage: ¿Qué tipo de taxi registra más viajes?

Se compara el tamaño de ambos servicios con el mismo periodo.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/coverage.csv.

```sql
SELECT taxi, source_year, count(DISTINCT source_file) AS files,
    count(*) AS rows, min(pickup) AS first_pickup, max(pickup) AS last_pickup
FROM trips_raw GROUP BY ALL ORDER BY taxi, source_year
```

## hourly: ¿En qué horas se concentra la actividad?

Se agrupa por hora de inicio para identificar horarios de mayor actividad.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/hourly.csv.

```sql
SELECT taxi, hour(pickup) AS hour, count(*) AS trips
FROM trips_clean GROUP BY ALL ORDER BY taxi, hour
```

## monthly: ¿Cuánto se paga por viaje?

Se usa el promedio y la mediana del pago total en USD.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/monthly.csv.

```sql
SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
```

## monthly: ¿Qué distancias se recorren?

Se compara la distancia en millas entre tipos de taxi.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/monthly.csv.

```sql
SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
```

## monthly: ¿Cuánto dura un viaje?

Se calcula la diferencia entre las horas de inicio y fin en minutos.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/monthly.csv.

```sql
SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
```

## payments: ¿Qué formas de pago se usan?

Se cuentan los viajes por código de pago.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/payments.csv.

```sql
SELECT taxi, source_year, payment_type, count(*) AS trips,
    avg(total_amount) AS mean_total,
    avg(CASE WHEN payment_type = 1 AND fare_amount > 0 THEN 100.0 * tip_amount / fare_amount END) AS card_tip_percent
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, payment_type
```

## payments: ¿Qué porcentaje de la tarifa representa la propina registrada con tarjeta?

Se limita a tarjeta porque las propinas en efectivo no quedan registradas.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/payments.csv.

```sql
SELECT taxi, source_year, payment_type, count(*) AS trips,
    avg(total_amount) AS mean_total,
    avg(CASE WHEN payment_type = 1 AND fare_amount > 0 THEN 100.0 * tip_amount / fare_amount END) AS card_tip_percent
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, payment_type
```

## zones: ¿Cuáles son las zonas de inicio más frecuentes?

Se seleccionan las diez zonas con más viajes por tipo de taxi.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/zones.csv.

```sql
SELECT taxi, pickup_zone, count(*) AS trips
FROM trips_clean GROUP BY taxi, pickup_zone QUALIFY row_number() OVER (PARTITION BY taxi ORDER BY count(*) DESC, pickup_zone) <= 10
ORDER BY taxi, trips DESC
```

## distribution: ¿Qué valores extremos aparecen en las distancias y pagos?

Se usan percentiles para observar la distribución y reducir la dependencia del promedio.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/distribution.csv.

```sql
SELECT taxi, source_year,
    quantile_cont(trip_distance, [0.25, 0.5, 0.75, 0.95, 0.99]) AS distance_quantiles,
    quantile_cont(total_amount, [0.25, 0.5, 0.75, 0.95, 0.99]) AS total_quantiles,
    quantile_cont(duration_minutes, [0.25, 0.5, 0.75, 0.95, 0.99]) AS duration_quantiles
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year
```

## quality: ¿Cuántos registros presentan problemas de calidad?

Se cuentan problemas por separado antes de filtrar los datos.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/quality.csv.

```sql
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
```

## comparable: ¿Cómo cambian los viajes entre 2024, 2025 y 2026?

Se comparan únicamente los meses presentes en los tres años.

Fuente: trips_raw para coverage y quality. trips_clean para las demás. Resultado: docs/results/2024_2025_2026/comparable.csv.

```sql
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
```

## Columnas, tipos y muestra

schema.csv proviene de DESCRIBE SELECT * FROM read_parquet(lista_archivos, union_by_name=true). sample.csv proviene de SELECT * FROM trips_raw ORDER BY source_file, pickup LIMIT 10. Se obtienen los tipos originales y diez registros ordenados. La muestra no es aleatoria ni representativa.

## Transformaciones

sql/normalize.sql contiene la lectura, extracción del tipo y periodo de origen, unificación de fechas y cálculo de duración. scripts/common.py registra el filtro de trips_clean. No se modifican los archivos originales.

## Benchmark

Se reutilizan monthly.sql, hourly.sql y payments.sql. Solo cambia la fuente de trips_clean entre trips_raw y trips_materialized. Los filtros y agregaciones se mantienen. benchmark_runs.csv contiene todas las repeticiones. benchmark_summary.csv contiene mediana, mínimo y máximo. materialization.csv contiene el costo de crear cada tabla.
