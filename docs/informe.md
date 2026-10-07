# Informe del laboratorio 8 - DuckDB

## Ejercicio 1: ambiente

Se trabajó sobre el fork configurado en origin: https://github.com/Ninaswiftie09/duckdb. El repositorio del docente está configurado como upstream. Se levantaron JupyterLab y Metabase con Docker Compose y se comprobó que ambos respondieran por HTTP. Las versiones del ambiente están fijadas en requirements.txt y en los Dockerfiles.

Un ambiente reproducible permite repetir el análisis con las mismas herramientas y versiones. Se reduce el riesgo de obtener resultados distintos por cambios en las dependencias. data/raw conserva los archivos originales. data/processed contiene las tablas y archivos derivados. Scripts contiene los procesos ejecutables. sql contiene las consultas. notebooks permite explorar los resultados. docs contiene la documentación y evidencia.

## Ejercicio 2: descarga inicial

Se reemplazó el año fijo del script por el argumento --years, cuyo valor inicial es 2026. Se obtiene el inventario desde los enlaces oficiales de la TLC. Se agregó un encabezado User-Agent porque el sitio rechazó inicialmente las solicitudes. Se conservaron las descargas por bloques y archivos temporales, y se agregaron reintentos, validación Parquet, cantidad de registros, tamaño y SHA-256. Los errores HTTP producen un fallo. No se clasifican como meses no publicados. Los meses no publicados se determinan usando el inventario oficial.

La integridad estructural se verifica con PyArrow. La huella SHA-256 permite detectar cambios posteriores, pero no demuestra por sí sola que la TLC publicó datos completos. La completitud de la descarga significa que cada enlace publicado tiene un archivo local válido. Los manifiestos download_*.json registran la cobertura por etapa. Una segunda ejecución registra existing y conserva las huellas.

## Ejercicio 3: consulta directa y calidad

Se consultó read_parquet con union_by_name=true. Las columnas de inicio y fin de yellow y green se unificaron con COALESCE. El año y mes de origen se extraen del nombre del archivo para detectar fechas fuera del periodo. cbd_congestion_fee no aparece en 2024. union_by_name conserva esa diferencia como NULL.

| taxi | source_year | files | rows | first_pickup | last_pickup |
| --- | --- | --- | --- | --- | --- |
| green | 2024 | 12 | 660,218 | 2008-12-31 00:00:00 | 2025-01-01 22:21:15 |
| green | 2025 | 12 | 591,375 | 2008-12-31 15:13:04 | 2026-01-01 21:09:39 |
| green | 2026 | 8 | 337,114 | 2008-12-31 17:35:31 | 2026-08-31 23:58:28 |
| yellow | 2024 | 12 | 41,169,720 | 2002-12-31 16:46:07 | 2026-06-26 23:53:12 |
| yellow | 2025 | 12 | 48,722,602 | 2007-12-05 18:45:00 | 2025-12-31 23:59:59 |
| yellow | 2026 | 8 | 29,703,355 | 2001-01-01 09:23:58 | 2026-08-31 23:59:59 |

Los tipos y columnas originales aparecen en results/2024_2025_2026/schema.csv y la muestra en sample.csv. Las consultas originales se ejecutaron sin importar los archivos a una tabla. DuckDB lee las columnas necesarias y puede evitar bloques que no cumplen algunos filtros. Esto permite trabajar con datos grandes sin cargar todos los registros en un DataFrame.

| taxi | source_year | rows | missing_pickup | wrong_period | invalid_distance | invalid_duration | invalid_total | missing_passengers | zero_passengers | extreme_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| green | 2024 | 660,218 | 0 | 164 | 34,574 | 3,641 | 2,574 | 24,328 | 6,793 | 270 |
| green | 2025 | 591,375 | 0 | 248 | 24,438 | 4,617 | 2,706 | 49,880 | 8,255 | 231 |
| green | 2026 | 337,114 | 0 | 98 | 12,212 | 1,521 | 1,566 | 48,775 | 4,527 | 92 |
| yellow | 2024 | 41,169,720 | 0 | 420 | 776,305 | 38,859 | 614,406 | 4,091,232 | 401,354 | 2,219 |
| yellow | 2025 | 48,722,602 | 0 | 214 | 1,402,958 | 564,705 | 980,522 | 11,611,894 | 260,062 | 3,854 |
| yellow | 2026 | 29,703,355 | 0 | 146 | 952,231 | 381,810 | 167,093 | 7,716,688 | 91,359 | 1,822 |

Se conservaron todos los archivos originales. Para los indicadores se usó trips_clean: fecha dentro del año y mes del archivo, distancia mayor que 0 y hasta 100 millas, duración mayor que 0 y hasta 180 minutos y pago total mayor que 0 y hasta 500 USD. Los límites son decisiones de análisis y pueden excluir viajes reales largos o caros. No se presentan como reglas oficiales. No se imputaron pasajeros ni propinas. Los problemas de calidad se cuentan por separado y pueden superponerse, por lo que no deben sumarse para calcular registros excluidos. Un pago de cero o negativo puede corresponder a un viaje sin cargo, una disputa o un reembolso. Se excluye del indicador de viajes pagados, sin afirmar que todos esos registros sean errores. No se eliminaron duplicados porque no existe una identificación única de viaje.

## Ejercicio 4: preguntas y hallazgos

1. ¿Cómo cambia la cantidad de viajes por mes? Se usa el volumen mensual para observar la demanda. Consulta: sql/monthly.sql. Resultado: results/2024_2025_2026/monthly.csv.

2. ¿Qué tipo de taxi registra más viajes? Se compara el tamaño de ambos servicios con el mismo periodo. Consulta: sql/coverage.sql. Resultado: results/2024_2025_2026/coverage.csv.

3. ¿En qué horas se concentra la actividad? Se agrupa por hora de inicio para identificar horarios de mayor actividad. Consulta: sql/hourly.sql. Resultado: results/2024_2025_2026/hourly.csv.

4. ¿Cuánto se paga por viaje? Se usa el promedio y la mediana del pago total en USD. Consulta: sql/monthly.sql. Resultado: results/2024_2025_2026/monthly.csv.

5. ¿Qué distancias se recorren? Se compara la distancia en millas entre tipos de taxi. Consulta: sql/monthly.sql. Resultado: results/2024_2025_2026/monthly.csv.

6. ¿Cuánto dura un viaje? Se calcula la diferencia entre las horas de inicio y fin en minutos. Consulta: sql/monthly.sql. Resultado: results/2024_2025_2026/monthly.csv.

7. ¿Qué formas de pago se usan? Se cuentan los viajes por código de pago. Consulta: sql/payments.sql. Resultado: results/2024_2025_2026/payments.csv.

8. ¿Qué porcentaje de la tarifa representa la propina registrada con tarjeta? Se limita a tarjeta porque las propinas en efectivo no quedan registradas. Consulta: sql/payments.sql. Resultado: results/2024_2025_2026/payments.csv.

9. ¿Cuáles son las zonas de inicio más frecuentes? Se seleccionan las diez zonas con más viajes por tipo de taxi. Consulta: sql/zones.sql. Resultado: results/2024_2025_2026/zones.csv.

10. ¿Qué valores extremos aparecen en las distancias y pagos? Se usan percentiles para observar la distribución y reducir la dependencia del promedio. Consulta: sql/distribution.sql. Resultado: results/2024_2025_2026/distribution.csv.

11. ¿Cuántos registros presentan problemas de calidad? Se cuentan problemas por separado antes de filtrar los datos. Consulta: sql/quality.sql. Resultado: results/2024_2025_2026/quality.csv.

12. ¿Cómo cambian los viajes entre 2024, 2025 y 2026? Se comparan únicamente los meses presentes en los tres años. Consulta: sql/comparable.sql. Resultado: results/2024_2025_2026/comparable.csv.

En yellow, la hora con más viajes es 18:00, con 7,725,998 viajes. Esto permite identificar la hora de mayor actividad dentro de los registros analizados, sin afirmar una causa.

En green, la hora con más viajes es 17:00, con 121,523 viajes. Esto permite identificar la hora de mayor actividad dentro de los registros analizados, sin afirmar una causa.

Los archivos amarillos contienen 119,595,677 registros y los verdes 1,588,707. El volumen amarillo es 75.28 veces el verde. Esto describe estos archivos y no toda la movilidad de Nueva York.

En yellow, el mes con más viajes filtrados fue 2025-05, con 4,283,501 viajes. Se mantiene la serie mensual para observar si el máximo es parte de un patrón repetido.

En yellow, se encontraron 780 fechas fuera del periodo del archivo y 23,419,814 valores de pasajeros faltantes. Se filtran las fechas inconsistentes y se conserva el dato de pasajeros sin imputación.

La zona de inicio más frecuente en yellow tiene ID 237, con 5,153,451 viajes filtrados. Se mantiene el ID oficial. No se asigna un nombre de barrio sin una tabla de referencia.

En yellow 2024, la mediana de distancia fue 1.80 millas y el percentil 95 fue 14.44. La mediana del pago fue 21.10 USD y el percentil 95 fue 82.64 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

En yellow 2025, la mediana de distancia fue 1.90 millas y el percentil 95 fue 12.93. La mediana del pago fue 21.54 USD y el percentil 95 fue 77.50 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

En yellow 2026, la mediana de distancia fue 1.93 millas y el percentil 95 fue 12.56. La mediana del pago fue 23.58 USD y el percentil 95 fue 77.25 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

En green, el mes con más viajes filtrados fue 2024-05, con 57,428 viajes. Se mantiene la serie mensual para observar si el máximo es parte de un patrón repetido.

En green, se encontraron 510 fechas fuera del periodo del archivo y 122,983 valores de pasajeros faltantes. Se filtran las fechas inconsistentes y se conserva el dato de pasajeros sin imputación.

La zona de inicio más frecuente en green tiene ID 74, con 376,372 viajes filtrados. Se mantiene el ID oficial. No se asigna un nombre de barrio sin una tabla de referencia.

En green 2024, la mediana de distancia fue 1.97 millas y el percentil 95 fue 8.62. La mediana del pago fue 19.25 USD y el percentil 95 fue 55.24 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

En green 2025, la mediana de distancia fue 2.06 millas y el percentil 95 fue 9.90. La mediana del pago fue 20.05 USD y el percentil 95 fue 57.64 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

En green 2026, la mediana de distancia fue 2.14 millas y el percentil 95 fue 10.62. La mediana del pago fue 20.52 USD y el percentil 95 fue 56.60 USD. La separación entre mediana y percentil 95 muestra que los valores altos no describen el viaje habitual.

## Ejercicio 5: incorporación de 2024

Se ejecutó --years 2024 2026 después de la descarga inicial y se confirmó la cobertura conjunta con coverage.sql. Los 24 archivos de 2024 se incorporaron sin eliminar los de 2026. Se ejecutaron las mismas consultas sobre el conjunto ampliado. Sus resultados están en results/2024_2026. La selección de archivos y union_by_name permiten agregar años sin reescribir las consultas. comparable.sql produce una tabla vacía hasta que estén presentes los tres años. Esa consulta fue diseñada para la comparación final.

## Ejercicio 6: benchmark

Se usaron los datos de 2024 y 2026. Se evaluaron 2, 12 y todos los archivos de esos años. Los prefijos se ordenan por año, mes y tipo para incluir ambos tipos de taxi. No son muestras aleatorias. Para cada tamaño se creó una tabla con todas las columnas normalizadas. Se midieron monthly.sql, hourly.sql y payments.sql con los mismos filtros y se comprobó que sus resultados coincidieran dentro de una tolerancia numérica.

Se ejecutó una consulta de calentamiento por modo y luego tres repeticiones, alternando el orden. Se midió ejecución y recuperación de resultados. Se excluyó la creación de vistas de cada medición. Se fijaron cuatro hilos y un límite de memoria de 2 GB. La caché del sistema operativo no se vació. Los resultados representan consultas repetidas con caché caliente, no lecturas en frío. El tiempo de materialización se registró por separado.

| files | rows | query | mode | median | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 3,021,175 | hourly | duckdb | 0.102 | 0.069 | 0.106 |
| 2 | 3,021,175 | hourly | parquet | 0.253 | 0.252 | 0.300 |
| 2 | 3,021,175 | monthly | duckdb | 0.212 | 0.176 | 0.215 |
| 2 | 3,021,175 | monthly | parquet | 0.347 | 0.306 | 0.378 |
| 2 | 3,021,175 | payments | duckdb | 0.100 | 0.094 | 0.122 |
| 2 | 3,021,175 | payments | parquet | 0.315 | 0.279 | 0.337 |
| 12 | 20,671,900 | hourly | duckdb | 0.588 | 0.578 | 0.781 |
| 12 | 20,671,900 | hourly | parquet | 1.698 | 1.563 | 2.116 |
| 12 | 20,671,900 | monthly | duckdb | 1.255 | 1.021 | 1.509 |
| 12 | 20,671,900 | monthly | parquet | 2.178 | 2.045 | 2.445 |
| 12 | 20,671,900 | payments | duckdb | 0.777 | 0.752 | 0.877 |
| 12 | 20,671,900 | payments | parquet | 2.080 | 2.058 | 2.083 |
| 40 | 71,870,407 | hourly | duckdb | 2.127 | 1.995 | 2.827 |
| 40 | 71,870,407 | hourly | parquet | 5.433 | 5.425 | 7.252 |
| 40 | 71,870,407 | monthly | duckdb | 3.196 | 3.066 | 4.062 |
| 40 | 71,870,407 | monthly | parquet | 8.325 | 7.907 | 24.463 |
| 40 | 71,870,407 | payments | duckdb | 2.903 | 2.715 | 3.045 |
| 40 | 71,870,407 | payments | parquet | 7.048 | 6.931 | 7.585 |

Con 2 archivos, hourly tardó 0.2531 s en Parquet y 0.1024 s en la tabla. La relación Parquet/tabla fue 2.47.

Con 2 archivos, monthly tardó 0.3474 s en Parquet y 0.2120 s en la tabla. La relación Parquet/tabla fue 1.64.

Con 2 archivos, payments tardó 0.3148 s en Parquet y 0.1002 s en la tabla. La relación Parquet/tabla fue 3.14.

Con 12 archivos, hourly tardó 1.6981 s en Parquet y 0.5877 s en la tabla. La relación Parquet/tabla fue 2.89.

Con 12 archivos, monthly tardó 2.1779 s en Parquet y 1.2549 s en la tabla. La relación Parquet/tabla fue 1.74.

Con 12 archivos, payments tardó 2.0804 s en Parquet y 0.7773 s en la tabla. La relación Parquet/tabla fue 2.68.

Con 40 archivos, hourly tardó 5.4333 s en Parquet y 2.1274 s en la tabla. La relación Parquet/tabla fue 2.55.

Con 40 archivos, monthly tardó 8.3249 s en Parquet y 3.1963 s en la tabla. La relación Parquet/tabla fue 2.60.

Con 40 archivos, payments tardó 7.0484 s en Parquet y 2.9033 s en la tabla. La relación Parquet/tabla fue 2.43.

Con 40 archivos, el costo de materialización se compensaría después de aproximadamente 6.0 rondas de las tres consultas, si se mantienen estas medianas. Esta estimación no incluye actualizaciones ni operaciones adicionales.

Los tiempos sobre Parquet incluyen la unificación de fechas y el cálculo de duración. La tabla conserva esos campos precalculados. Se separó el costo de crear la tabla para evaluar ese trabajo inicial.

El costo de crear las tablas se registró por separado:

| files | rows | materialization_seconds |
| --- | --- | --- |
| 2 | 3,021,175 | 9.247 |
| 12 | 20,671,900 | 26.017 |
| 40 | 71,870,407 | 75.205 |

Se repitió el benchmark de forma aislada después de observar presión de memoria con otros procesos. El informe usa únicamente esa repetición completa. Aun así, se observa variación entre mínimos y máximos, por lo que la mediana describe mejor estas mediciones que un solo tiempo.

Los tiempos cambian con el volumen, la compresión, el tipo de consulta y la caché. No se asume que una estrategia sea siempre mejor. Parquet permite explorar archivos nuevos sin una carga previa ni una segunda copia de los datos. Una tabla puede servir para consultas repetidas y para Metabase, pero requiere tiempo de creación, espacio adicional y actualización al incorporar datos nuevos.

## Ejercicio 7: indicadores y tablero

Se definieron doce preguntas y seis indicadores: cantidad mensual de viajes, pago promedio, distancia promedio, duración promedio, viajes por hora y formas de pago. Cada tarjeta usa una consulta en sql/indicator_*.sql. El tablero se creó en Metabase y su verificación está en dashboard/metabase_validation.json. dashboard/dashboard.png permite revisar los seis indicadores sin abrir el servicio. Los indicadores se calculan con datos filtrados. Las cifras de coverage corresponden a datos originales.

Para yellow, se analizaron 113,898,370 viajes después de los filtros. El pago promedio ponderado fue 28.71 USD, la distancia promedio 3.47 millas y la duración promedio 17.23 minutos. La ponderación usa la cantidad de viajes de cada mes.

En yellow, el código de pago más frecuente es 1, con 78,948,755 viajes (69.32% del total filtrado). Los códigos deben interpretarse usando el diccionario correspondiente a cada tipo y año. El código 1 identifica tarjeta.

En yellow 2024, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 25.17%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

En yellow 2025, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 25.48%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

En yellow 2026, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 25.10%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

Para green, se analizaron 1,503,848 viajes después de los filtros. El pago promedio ponderado fue 24.76 USD, la distancia promedio 3.12 millas y la duración promedio 15.62 minutos. La ponderación usa la cantidad de viajes de cada mes.

En green, el código de pago más frecuente es 1, con 1,025,479 viajes (68.19% del total filtrado). Los códigos deben interpretarse usando el diccionario correspondiente a cada tipo y año. El código 1 identifica tarjeta.

En green 2024, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 22.37%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

En green 2025, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 22.50%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

En green 2026, el promedio del porcentaje de propina registrada con tarjeta respecto a la tarifa fue 22.95%. Se consideran únicamente tarifas positivas. No se extiende a propinas en efectivo.

## Ejercicio 8: tres años y comparación temporal

Se incorporaron los 24 archivos de 2025 después de validar 2024 y 2026. Se ejecutaron nuevamente las consultas y se actualizó el tablero. Para la comparación entre años se seleccionaron únicamente los meses presentes en 2024, 2025 y 2026. El año 2026 está incompleto y no se compara su total parcial contra doce meses de otro año.

| taxi | source_year | trips | mean_total | mean_distance | mean_duration | mean_cbd_fee |
| --- | --- | --- | --- | --- | --- | --- |
| green | 2024 | 416,816 | 23.731 | 2.912 | 14.417 | nan |
| green | 2025 | 374,777 | 24.835 | 3.101 | 15.277 | 0.074 |
| green | 2026 | 322,429 | 25.402 | 3.345 | 17.099 | 0.064 |
| yellow | 2024 | 25,569,452 | 28.243 | 3.418 | 16.379 | nan |
| yellow | 2025 | 29,792,621 | 27.438 | 3.454 | 16.491 | 0.548 |
| yellow | 2026 | 28,230,818 | 30.234 | 3.516 | 17.665 | 0.543 |

En yellow, la cantidad de viajes fue 25,569,452.00 en 2024, 29,792,621.00 en 2025 y 28,230,818.00 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue 10.41%. Se describe un patrón observado, sin atribuirlo a una causa específica.

En yellow, la pago promedio fue 28.24 en 2024, 27.44 en 2025 y 30.23 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue 7.05%. Se describe un patrón observado, sin atribuirlo a una causa específica.

En yellow, la distancia promedio fue 3.42 en 2024, 3.45 en 2025 y 3.52 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue 2.86%. Se describe un patrón observado, sin atribuirlo a una causa específica.

En green, la cantidad de viajes fue 416,816.00 en 2024, 374,777.00 en 2025 y 322,429.00 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue -22.64%. Se describe un patrón observado, sin atribuirlo a una causa específica.

En green, la pago promedio fue 23.73 en 2024, 24.84 en 2025 y 25.40 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue 7.04%. Se describe un patrón observado, sin atribuirlo a una causa específica.

En green, la distancia promedio fue 2.91 en 2024, 3.10 en 2025 y 3.35 en 2026 para los mismos meses. El cambio de 2024 a 2026 fue 14.87%. Se describe un patrón observado, sin atribuirlo a una causa específica.

El recargo cbd_congestion_fee se incorporó desde 2025 según la TLC. Su ausencia en 2024 se conserva como NULL y no se interpreta como una medición de cero. Los cambios en pago pueden incluir cambios en recargos, composición de viajes y otras variables, por lo que no se atribuyen automáticamente a una tarifa más alta.

## Ejercicio 9: discusión

### 9.1 Características útiles

Se usaron SQL, lectura directa de Parquet, unión de esquemas por nombre y procesamiento de agregaciones con memoria limitada. Se pudieron consultar varios años sin crear primero una tabla.

### 9.2 Parquet

Se evita una importación previa y se conservan los archivos originales. Como limitación, hay que controlar diferencias de esquema, cantidad de archivos y calidad. Las consultas repetidas pueden volver a leer y descomprimir información.

### 9.3 Tablas materializadas

Se dispone de una fuente estable para Metabase y consultas repetidas. Se requiere espacio extra, tiempo de materialización y una estrategia para actualizar la tabla. Los tiempos medidos permiten evaluar si el costo inicial se compensa.

### 9.4 Comparación con Pandas

DuckDB puede filtrar y agregar antes de llevar resultados pequeños a Pandas. Se evita concatenar todos los viajes en memoria. Pandas se usó para tablas de resultados y gráficos, donde el volumen ya es reducido.

### 9.5 Nuevos datos

Los años son parámetros, los archivos mantienen un nombre predecible y las consultas usan vistas normalizadas. Los archivos existentes se omiten y los manifiestos registran la cobertura.

### 9.6 Automatización en producción

Se debería programar la revisión de nuevas publicaciones, validar esquemas e integridad, controlar fallos de descarga, actualizar tablas y tablero y alertar cuando cambie la cobertura o la calidad.

### 9.7 Reproducibilidad

Se fijaron versiones, se versionaron scripts y SQL, se conservaron los originales y se registraron filtros, fuentes y metodología de medición. Los datos grandes y las credenciales se excluyeron de Git.

### 9.8 Aprendizajes

Con varios años se hacen visibles los costos de memoria, lectura y copias adicionales. También se observa que los archivos pueden tener cambios de columnas y fechas fuera de su periodo. Comparar años requiere controlar la cobertura temporal.

## Fuentes

TLC: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

DuckDB: https://duckdb.org/docs/stable/data/parquet/overview

Metabase: https://www.metabase.com/docs/latest/api

Los resultados corresponden a los archivos publicados y descargados durante esta ejecución. Los tiempos dependen de la máquina y no son garantías de desempeño.
