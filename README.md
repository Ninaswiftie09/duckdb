# Lab 8 - DuckDB

Viajes de taxis amarillos y verdes de Nueva York en 2024, 2025 y enero a agosto de 2026.

[Resultados](docs/informe.md) · [Consultas](docs/consultas.md) · [Notebook](notebooks/lab8_duckdb.ipynb)

## Estructura

| Carpeta | Contenido |
| --- | --- |
| data/raw | Datos originales por tipo y año. |
| data/processed | Base DuckDB y datos derivados. |
| scripts | Descarga, análisis y tablero. |
| sql | Consultas. |
| notebooks | Exploración y resultados. |
| docs | Informe y evidencia. |

Los datos y las credenciales quedan fuera de Git.

## Ambiente

Requisitos: Git, Docker Desktop y Docker Compose.

```bash
git clone https://github.com/Ninaswiftie09/duckdb.git
cd duckdb
docker compose up --build -d
docker compose ps
```

JupyterLab: http://localhost:8888. Metabase: http://localhost:3000.

```bash
docker compose exec -T lab python -c "import requests; print(requests.get('http://localhost:8888/api/status').status_code); print(requests.get('http://metabase:3000/api/health').json())"
```

Respuestas esperadas: 200 y status: ok.

El ambiente incluye Python, DuckDB, Pandas, PyArrow, Matplotlib y Requests. Las versiones fijas permiten repetir los resultados con las mismas herramientas.

## Descarga y análisis por etapas

Los comandos van en este orden, uno después de otro.

```bash
docker compose exec -T lab python scripts/download_data.py --years 2026
docker compose exec -T lab python scripts/analyze.py --years 2026
docker compose exec -T lab python scripts/download_data.py --years 2024 2026
docker compose exec -T lab python scripts/analyze.py --years 2024 2026
```

La descarga incluye todos los meses publicados y omite archivos existentes. El registro de cada etapa contiene cantidad de archivos, registros y huellas SHA-256.

## Benchmark

```bash
docker compose exec -T lab python scripts/benchmark.py --years 2024 2026 --repeats 3
```

Comparación con 2, 12 y 40 archivos. Tres repeticiones por consulta sobre Parquet y tablas DuckDB.

## Análisis completo y tablero

```bash
docker compose exec -T lab python scripts/download_data.py --years 2024 2025 2026
docker compose exec -T lab python scripts/analyze.py --years 2024 2025 2026
docker compose stop metabase
docker compose exec -T lab python scripts/build_dashboard.py
docker compose start metabase
```

Con Metabase listo, continúa la configuración del tablero:

```bash
docker compose exec -T lab python scripts/setup_metabase.py
```

El tablero incluye viajes mensuales, pago promedio, distancia, duración, horarios y formas de pago. El acceso está en data/processed/metabase_credentials.json.

## Informe y notebook

```bash
docker compose exec -T lab python scripts/write_report.py
docker compose exec -T lab jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/lab8_duckdb.ipynb
docker compose exec -T lab python scripts/verify_lab.py
```

Resultados completos en docs/results y capturas en docs/dashboard.

## Ejecución completa

```bash
docker compose stop metabase
docker compose exec -T lab python scripts/run_lab.py
docker compose start metabase
```

Después, siguen la configuración de Metabase y la ejecución del notebook con los comandos anteriores.

## Fuente

[NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
