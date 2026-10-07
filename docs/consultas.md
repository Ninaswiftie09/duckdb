# Consultas

Fuente: Parquet de taxis amarillos y verdes de 2024, 2025 y los meses publicados de 2026. trips_raw contiene los registros originales y trips_clean aplica los filtros del informe.

## Cantidad de archivos y registros

Fuente: trips_raw. Resultado: 64 archivos y 121,184,384 registros. Criterio: Cobertura por tipo y año.

```sql
SELECT taxi, source_year, count(DISTINCT source_file) AS files,
    count(*) AS rows, min(pickup) AS first_pickup, max(pickup) AS last_pickup
FROM trips_raw GROUP BY ALL ORDER BY taxi, source_year
```

## Datos inconsistentes

Fuente: trips_raw. Resultado: 1,290 fechas fuera del mes y 23,542,797 pasajeros faltantes. Criterio: Filtros de fecha, distancia, duración y pago.

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

## Cambios mensuales

Fuente: trips_clean. Resultado: Máximos en mayo de 2025 para amarillos y mayo de 2024 para verdes. Criterio: Serie mensual para comparar volumen y promedios.

```sql
SELECT taxi, source_year, source_month, count(*) AS trips,
    avg(total_amount) AS mean_total, median(total_amount) AS median_total,
    avg(trip_distance) AS mean_distance, avg(duration_minutes) AS mean_duration,
    sum(total_amount) AS revenue
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, source_month
```

## Actividad por hora

Fuente: trips_clean. Resultado: Máximos a las 18:00 en amarillos y 17:00 en verdes. Criterio: Indicador de horarios.

```sql
SELECT taxi, hour(pickup) AS hour, count(*) AS trips
FROM trips_clean GROUP BY ALL ORDER BY taxi, hour
```

## Formas de pago y propinas

Fuente: trips_clean. Resultado: La tarjeta es el pago más frecuente en ambos tipos. Criterio: Propinas respecto a tarifas positivas con tarjeta.

```sql
SELECT taxi, source_year, payment_type, count(*) AS trips,
    avg(total_amount) AS mean_total,
    avg(CASE WHEN payment_type = 1 AND fare_amount > 0 THEN 100.0 * tip_amount / fare_amount END) AS card_tip_percent
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year, payment_type
```

## Distribución de distancia, pago y duración

Fuente: trips_clean. Resultado: En amarillos de 2026, distancia mediana de 1.93 millas y percentil 95 de 12.56. Criterio: Mediana y percentiles para describir valores habituales y altos.

```sql
SELECT taxi, source_year,
    quantile_cont(trip_distance, [0.25, 0.5, 0.75, 0.95, 0.99]) AS distance_quantiles,
    quantile_cont(total_amount, [0.25, 0.5, 0.75, 0.95, 0.99]) AS total_quantiles,
    quantile_cont(duration_minutes, [0.25, 0.5, 0.75, 0.95, 0.99]) AS duration_quantiles
FROM trips_clean GROUP BY ALL ORDER BY taxi, source_year
```

## Zonas con más salidas

Fuente: trips_clean. Resultado: Zona 237 para amarillos y 74 para verdes. Criterio: Diez zonas principales por tipo.

```sql
SELECT taxi, pickup_zone, count(*) AS trips
FROM trips_clean GROUP BY taxi, pickup_zone QUALIFY row_number() OVER (PARTITION BY taxi ORDER BY count(*) DESC, pickup_zone) <= 10
ORDER BY taxi, trips DESC
```

## Evolución entre años

Fuente: trips_clean. Resultado: De 2024 a 2026, viajes amarillos +10.41% y verdes -22.64%. Criterio: Comparación de los mismos meses.

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

## Columnas y tipos

Fuente: Parquet originales. Resultado: 25 columnas. Las fechas de amarillos y verdes tienen nombres distintos y el recargo de congestión no aparece en 2024. La unión por nombre conserva esas diferencias.

```sql
DESCRIBE SELECT * FROM read_parquet({files}, union_by_name = true)
```

| Columna | Tipo |
| --- | --- |
| VendorID | INTEGER |
| lpep_pickup_datetime | TIMESTAMP |
| lpep_dropoff_datetime | TIMESTAMP |
| store_and_fwd_flag | VARCHAR |
| RatecodeID | BIGINT |
| PULocationID | INTEGER |
| DOLocationID | INTEGER |
| passenger_count | BIGINT |
| trip_distance | DOUBLE |
| fare_amount | DOUBLE |
| extra | DOUBLE |
| mta_tax | DOUBLE |
| tip_amount | DOUBLE |
| tolls_amount | DOUBLE |
| ehail_fee | DOUBLE |
| improvement_surcharge | DOUBLE |
| total_amount | DOUBLE |
| payment_type | BIGINT |
| trip_type | BIGINT |
| congestion_surcharge | DOUBLE |
| cbd_congestion_fee | DOUBLE |
| request_source | VARCHAR |
| tpep_pickup_datetime | TIMESTAMP |
| tpep_dropoff_datetime | TIMESTAMP |
| Airport_fee | DOUBLE |

## Muestra

Fuente: registros originales. Resultado: diez viajes, incluyendo fechas fuera del periodo. El filtro de fecha excluye esos valores de los indicadores.

```sql
SELECT * FROM trips_raw ORDER BY source_file, pickup LIMIT 10
```

## Transformaciones

Fechas de inicio y fin comunes para ambos tipos. Año y mes tomados del nombre del archivo. Duración calculada en minutos. Los filtros están en el informe.

## Benchmark e indicadores

El benchmark compara las consultas mensuales, de horarios y de pagos sobre Parquet y una tabla DuckDB. Los seis indicadores del tablero corresponden a las consultas numeradas de la carpeta sql.
