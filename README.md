# Lab 8 - DuckDB

Se analizan los viajes de taxis amarillos y verdes publicados por la NYC TLC para 2024, 2025 y 2026. Los datos se consultan directamente en Parquet y se comparan con tablas DuckDB. El informe está en [docs/informe.md](docs/informe.md), las consultas en [docs/consultas.md](docs/consultas.md) y el notebook en [notebooks/lab8_duckdb.ipynb](notebooks/lab8_duckdb.ipynb).

## Repositorio y estructura

El trabajo se desarrolla en el fork https://github.com/Ninaswiftie09/duckdb. El repositorio del docente es https://github.com/menene/duckdb. La entrega consiste en la URL del fork con los commits publicados.

| Directorio | Propósito |
| --- | --- |
| data/raw | Archivos originales organizados por tipo y año. |
| data/processed | Base DuckDB, resultados temporales y credenciales locales. |
| scripts | Descarga, análisis, benchmarks y generación del tablero. |
| sql | Consultas y transformaciones usadas. |
| notebooks | Exploración y revisión de resultados. |
| docs | Informe, tablas pequeñas y evidencia del tablero. |

Los Parquet, las bases de datos y las credenciales están excluidos de Git. Los resultados agregados y la evidencia sí se versionan.

## Cómo levantar el ambiente

Se necesita Git, Docker Desktop con contenedores Linux, Docker Compose y espacio libre suficiente para imágenes, Parquet y tablas. Se recomiendan al menos 10 GB libres.

```bash
git clone https://github.com/Ninaswiftie09/duckdb.git
cd duckdb
docker compose up --build -d
docker compose ps
```

JupyterLab está en http://localhost:8888 y Metabase en http://localhost:3000. La primera construcción y el primer inicio de Metabase pueden tardar varios minutos.

```bash
docker compose exec -T lab python -c "import requests; print(requests.get('http://localhost:8888/api/status').status_code); print(requests.get('http://metabase:3000/api/health').json())"
```

Se espera 200 para Jupyter y status: ok para Metabase. Para revisar un inicio pendiente se usa `docker compose logs --tail 50 metabase`. Para detener el ambiente se usa `docker compose down`; no se agrega `-v` si se desea conservar la configuración de Metabase.

El ambiente incluye Python, DuckDB, JupyterLab, Pandas, PyArrow, Matplotlib, Requests y Metabase con el driver DuckDB. Las versiones están fijadas en requirements.txt y los Dockerfiles. Se usa un ambiente reproducible para mantener las mismas herramientas y repetir el análisis con menos diferencias entre equipos.

## Cómo descargar los datos

Se ejecutan las etapas en este orden. Se espera a que termine cada comando antes de iniciar el siguiente.

```bash
docker compose exec -T lab python scripts/download_data.py --years 2026
docker compose exec -T lab python scripts/analyze.py --years 2026
docker compose exec -T lab python scripts/download_data.py --years 2024 2026
docker compose exec -T lab python scripts/analyze.py --years 2024 2026
```

El descargador consulta los enlaces oficiales, descarga todos los meses publicados y verifica la estructura Parquet. Para 2024 y 2025 exige doce meses por tipo; para 2026 registra los meses aún no publicados. Cada etapa genera un manifiesto en docs/download_*.json con URL, tamaño, registros, SHA-256 y estado downloaded o existing. Los errores de red no se confunden con archivos no publicados. `--taxi yellow` o `--taxi green` limita el tipo; `--workers` controla las descargas simultáneas. No se ejecutan dos descargadores a la vez.

Se conserva data/raw/<tipo>/<año>/<archivo>.parquet. Un archivo existente se valida y se omite. Si un archivo está corrupto, el comando falla y se debe revisar ese archivo antes de repetir la descarga. El script no elimina archivos originales existentes.

## Cómo reproducir los benchmarks

El benchmark del ejercicio 6 se ejecuta con 2024 y 2026 antes de agregar 2025.

```bash
docker compose exec -T lab python scripts/benchmark.py --years 2024 2026 --repeats 3
```

Se comparan 2, 12 y todos los archivos disponibles. Se verifica la igualdad de resultados de monthly.sql, hourly.sql y payments.sql. Se ejecuta un calentamiento y luego tres repeticiones alternando el orden entre Parquet y DuckDB. Se registra la mediana, mínimo, máximo y tiempo de materialización por separado. Se usan cuatro hilos y un límite de memoria de 2 GB. Los resultados se guardan en docs/results/benchmark_*.csv y materialization.csv. El entorno y los archivos exactos están en benchmark_environment.json.

No se vacía la caché del sistema operativo. Se evalúa el caso de consultas repetidas con caché caliente. Los tiempos dependen de la máquina.

## Cómo ejecutar el análisis completo

```bash
docker compose exec -T lab python scripts/download_data.py --years 2024 2025 2026
docker compose exec -T lab python scripts/analyze.py --years 2024 2025 2026
docker compose exec -T lab python scripts/build_dashboard.py --years 2024 2025 2026
```

El análisis crea tablas pequeñas en docs/results/<años>/, incluyendo cobertura, calidad, columnas y tipos, muestra, viajes mensuales, horarios, pagos, percentiles, zonas y comparación temporal. Se conserva el año y mes del archivo para detectar fechas inconsistentes. Las columnas que cambian entre años se unen por nombre. Se registran todos los filtros en scripts/common.py y se explican en docs/informe.md.

El tablero usa seis indicadores: viajes mensuales, pago promedio, distancia promedio, duración promedio, viajes por hora y formas de pago. La imagen se genera en docs/dashboard/dashboard.png. Cada tarjeta tiene SQL en sql/indicator_*.sql. La base completa se genera en data/processed/taxi.duckdb.

## Cómo generar el tablero en Metabase

Antes de actualizar la base se detiene Metabase para evitar conflictos de acceso al archivo DuckDB. Después se vuelve a iniciar.

```bash
docker compose stop metabase
docker compose exec -T lab python scripts/build_dashboard.py --years 2024 2025 2026
docker compose start metabase
docker compose exec -T lab python scripts/setup_metabase.py
```

Se espera a que /api/health devuelva status: ok antes del último comando. El script configura una instalación nueva de Metabase, conecta la base, crea las seis tarjetas y verifica que sus consultas respondan. Si ya existe la configuración del laboratorio, se actualizan las tarjetas. El usuario local y su contraseña aleatoria se guardan en data/processed/metabase_credentials.json, que no se incluye en Git. Si se usa una instalación ya configurada por otra persona, se deben proporcionar MB_EMAIL y MB_PASSWORD al contenedor.

La conexión usa /workspace/data/processed/taxi.duckdb en modo de solo lectura. El tablero y la validación de sus tarjetas están registrados en docs/dashboard/metabase_validation.json. No se debe escribir en la base mientras Metabase la usa; se detiene el servicio antes de actualizarla.

## Cómo generar el informe y ejecutar el notebook

```bash
docker compose exec -T lab python scripts/write_report.py
docker compose exec -T lab jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/lab8_duckdb.ipynb
```

El informe requiere las salidas de las tres etapas y del benchmark. El notebook se puede abrir en JupyterLab y ejecutar de principio a fin. Se incluye una copia ejecutada con resultados. El informe contiene doce preguntas, los hallazgos, la comparación de años, la interpretación de indicadores y las ocho respuestas de discusión.

Para repetir todo el flujo se usan los comandos anteriores en orden. Se conserva la configuración de Metabase entre ejecuciones y se revisan los manifiestos para verificar que las descargas anteriores quedaron como existing. El año 2026 es parcial; la comparación temporal usa únicamente los meses presentes en los tres años.

También se puede ejecutar la descarga, análisis por etapas, benchmark, imagen del tablero e informe con un solo comando, después de detener Metabase:

```bash
docker compose stop metabase
docker compose exec -T lab python scripts/run_lab.py
docker compose start metabase
```

Después de verificar que Metabase inició, se ejecuta scripts/setup_metabase.py y el notebook con los comandos anteriores. El procesamiento completo puede tardar varios minutos por el volumen de datos.

## Fuente

[NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). La TLC advierte que los registros pueden contener errores y que la publicación tiene atraso. Los resultados describen los archivos disponibles, no una garantía de completitud de todos los viajes de Nueva York.
