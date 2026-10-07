import pandas as pd

from common import RESULTS, ROOT, sql

QUESTIONS = [
    ('¿Cómo cambia la cantidad de viajes por mes?', 'Viajes mensuales', 'Cambios en la actividad.'),
    ('¿Qué tipo de taxi registra más viajes?', 'Cantidad por tipo', 'Diferencia de volumen.'),
    ('¿Cuál es la hora con más viajes?', 'Viajes por hora', 'Horarios de mayor actividad.'),
    ('¿Cuánto cuesta un viaje?', 'Pago promedio', 'Costo para el pasajero.'),
    ('¿Qué distancias recorren los taxis?', 'Distancia promedio', 'Tamaño de los recorridos.'),
    ('¿Cuánto dura un viaje?', 'Duración promedio', 'Tiempo de traslado.'),
    ('¿Qué forma de pago es más frecuente?', 'Viajes por forma de pago', 'Uso de formas de pago.'),
    ('¿Cuánto representa la propina con tarjeta?', 'Porcentaje de propina', 'Relación entre propina y tarifa.'),
    ('¿Qué zonas tienen más salidas?', 'Viajes por zona', 'Concentración de viajes.'),
    ('¿Qué tan altos son los pagos y distancias?', 'Mediana y percentil 95', 'Diferencia entre valores habituales y altos.'),
    ('¿Cuántos registros tienen datos inconsistentes?', 'Cantidad por problema', 'Calidad de los datos.'),
    ('¿Cómo cambian los indicadores entre años?', 'Comparación de los mismos meses', 'Evolución del servicio.'),
]


def table(frame):
    values = frame.copy()
    for column in values:
        if pd.api.types.is_numeric_dtype(values[column]):
            integer = not pd.api.types.is_float_dtype(values[column]) or column in ['Viajes', 'Registros', 'Archivos']
            values[column] = values[column].map(lambda v: '-' if pd.isna(v) else (str(int(v)) if column == 'Año' else f'{int(v):,}' if integer else f'{v:,.2f}'))
    return '| ' + ' | '.join(values.columns) + ' |\n| ' + ' | '.join('---' for _ in values.columns) + ' |\n' + '\n'.join('| ' + ' | '.join(str(v) for v in row) + ' |' for row in values.itertuples(index=False, name=None))


def main():
    output = RESULTS / '2024_2025_2026'
    frames = {p.stem: pd.read_csv(p) for p in output.glob('*.csv')}
    coverage, monthly, quality = [frames[name] for name in ['coverage', 'monthly', 'quality']]
    names = {'yellow': 'Amarillos', 'green': 'Verdes'}
    counts = coverage[['taxi', 'source_year', 'files', 'rows']].rename(columns={'taxi': 'Taxi', 'source_year': 'Año', 'files': 'Archivos', 'rows': 'Registros'})
    counts['Taxi'] = counts.Taxi.map(names)
    initial = coverage[coverage.source_year == 2026]
    added = coverage[coverage.source_year == 2024]
    parts = ['# Lab 8 - DuckDB', '## 1. Ambiente', 'Fork: https://github.com/Ninaswiftie09/duckdb. Repositorio de Erick: https://github.com/menene/duckdb.', 'JupyterLab y Metabase responden correctamente. El ambiente incluye Python, DuckDB, Pandas, PyArrow, Matplotlib y Requests. Las versiones fijas permiten repetir el análisis con las mismas herramientas.', '## 2. Descarga inicial', f'2026 contiene {int(initial.files.sum())} archivos y {int(initial.rows.sum()):,} registros de los meses publicados. Todos los enlaces publicados tienen un Parquet local válido. Los archivos existentes permanecen sin cambios.', 'El descargador acepta varios años, identifica los meses publicados y omite archivos existentes. Cada descarga incluye tamaño, cantidad de registros y una huella SHA-256.', '## 3. Exploración y calidad', f'El conjunto completo contiene {int(coverage.files.sum())} archivos y {int(coverage.rows.sum()):,} registros.', table(counts), 'Las 25 columnas incluyen fechas de inicio y fin, pasajeros, distancia, zonas, forma de pago, tarifa, propina y recargos. Las fechas son TIMESTAMP, los importes y distancias son DOUBLE, los códigos son INTEGER o BIGINT y las cadenas son VARCHAR.', 'La muestra contiene fechas fuera del periodo del archivo. También hay distancias y duraciones no positivas, pagos no positivos y pasajeros faltantes.', 'Los indicadores incluyen fechas dentro del mes de origen, distancias mayores que 0 y hasta 100 millas, duración mayor que 0 y hasta 180 minutos y pagos mayores que 0 y hasta 500 USD. Los pasajeros faltantes permanecen sin imputación.', 'Consultar Parquet directamente permite filtrar y agrupar datos sin importarlos primero a una tabla ni cargar todo el conjunto en memoria.', '## 4. Preguntas y hallazgos', table(pd.DataFrame(QUESTIONS, columns=['Pregunta', 'Indicador', 'Motivo']))]
    highlights = []
    for taxi, label in names.items():
        hours = frames['hourly'][frames['hourly'].taxi == taxi]
        peak_hour = hours.loc[hours.trips.idxmax()]
        months = monthly[monthly.taxi == taxi]
        peak_month = months.loc[months.trips.idxmax()]
        zone = frames['zones'][frames['zones'].taxi == taxi].iloc[0]
        highlights.append(f'{label}: mayor actividad a las {int(peak_hour["hour"]):02d}:00, con {int(peak_hour.trips):,} viajes. El mes con más viajes es {int(peak_month.source_year)}-{int(peak_month.source_month):02d}, con {int(peak_month.trips):,}. La zona de salida más frecuente es {int(zone.pickup_zone)}, con {int(zone.trips):,} viajes.')
    totals = coverage.groupby('taxi').rows.sum()
    parts.extend(highlights + [f'Los taxis amarillos acumulan {totals.yellow / totals.green:.2f} veces más registros que los verdes.', f'Las fechas fuera del mes del archivo suman {int(quality.wrong_period.sum()):,} registros. Los datos de pasajeros faltantes suman {int(quality.missing_passengers.sum()):,}.', '## 5. Incorporación de 2024', f'2024 aporta {int(added.files.sum())} archivos y {int(added.rows.sum()):,} registros. La cobertura conjunta de 2024 y 2026 es de {int(coverage[coverage.source_year.isin([2024, 2026])].files.sum())} archivos. Las huellas de los 16 archivos anteriores coinciden y las consultas funcionan con ambos años.', 'Los años como parámetros y la unión de columnas por nombre permiten agregar datos sin cambiar las consultas.', '## 6. Benchmark', 'Datos de 2024 y 2026. Tres repeticiones por consulta, después de un calentamiento, con cuatro hilos y 2 GB de memoria. Los tiempos corresponden a las medianas en segundos y los resultados coinciden entre ambas fuentes.'])
    benchmark = pd.read_csv(RESULTS / 'benchmark_summary.csv')
    pivot = benchmark.pivot(index=['files', 'query'], columns='mode', values='median').reset_index()
    pivot['query'] = pivot['query'].map({'monthly': 'Mensual', 'hourly': 'Horarios', 'payments': 'Pagos'})
    parts.append(table(pivot[['files', 'query', 'parquet', 'duckdb']].rename(columns={'files': 'Archivos', 'query': 'Consulta', 'parquet': 'Parquet (s)', 'duckdb': 'DuckDB (s)'})))
    builds = pd.read_csv(RESULTS / 'materialization.csv')
    parts.extend(['Tiempo de creación de las tablas:', table(builds[['files', 'materialization_seconds']].rename(columns={'files': 'Archivos', 'materialization_seconds': 'Segundos'})), 'La tabla responde más rápido en las nueve comparaciones. Los tiempos aumentan con el volumen. Parquet permite consultas ocasionales sin una carga previa. La tabla resulta útil para consultas repetidas, aunque requiere tiempo de creación y espacio adicional.', '## 7. Indicadores y tablero', 'El tablero contiene viajes mensuales, pago promedio, distancia promedio, duración promedio, viajes por hora y formas de pago. Estos indicadores resumen actividad, costo y características de los recorridos.'])
    indicator_rows = []
    for taxi, label in names.items():
        group = monthly[monthly.taxi == taxi]
        total = group.trips.sum()
        payments = frames['payments'][frames['payments'].taxi == taxi]
        card_count = payments[payments.payment_type == 1].trips.sum()
        indicator_rows.append([label, int(total), (group.mean_total * group.trips).sum() / total, (group.mean_distance * group.trips).sum() / total, (group.mean_duration * group.trips).sum() / total, 100 * card_count / total])
    parts.extend([table(pd.DataFrame(indicator_rows, columns=['Taxi', 'Viajes', 'Pago (USD)', 'Distancia (millas)', 'Duración (min)', 'Tarjeta (%)'])), 'Los amarillos tienen mayor volumen, pago y duración promedio. La tarjeta es la forma de pago más frecuente en ambos tipos. Las horas de mayor actividad son las 18:00 para amarillos y las 17:00 para verdes.', '![Tablero](dashboard/metabase.png)', '## 8. Comparación entre años', f'2025 aporta {int(coverage[coverage.source_year == 2025].files.sum())} archivos. La comparación corresponde a los meses presentes en los tres años.'])
    tips = frames['payments'][frames['payments'].payment_type == 1].pivot(index='source_year', columns='taxi', values='card_tip_percent').reset_index()
    tips = tips.rename(columns={'source_year': 'Año', 'yellow': 'Amarillos (%)', 'green': 'Verdes (%)'})
    insertion = parts.index('![Tablero](dashboard/metabase.png)')
    parts[insertion:insertion] = ['Propina con tarjeta como porcentaje de la tarifa:', table(tips[['Año', 'Amarillos (%)', 'Verdes (%)']])]
    comparable = frames['comparable']
    temporal = comparable[['taxi', 'source_year', 'trips', 'mean_total', 'mean_distance', 'mean_duration']].rename(columns={'taxi': 'Taxi', 'source_year': 'Año', 'trips': 'Viajes', 'mean_total': 'Pago (USD)', 'mean_distance': 'Distancia (millas)', 'mean_duration': 'Duración (min)'})
    temporal['Taxi'] = temporal.Taxi.map(names)
    parts.append(table(temporal))
    for taxi, label in names.items():
        values = comparable[comparable.taxi == taxi].set_index('source_year')
        changes = [100 * (values.loc[2026, metric] / values.loc[2024, metric] - 1) for metric in ['trips', 'mean_total', 'mean_distance']]
        parts.append(f'{label}, de 2024 a 2026: viajes {changes[0]:+.2f}%, pago promedio {changes[1]:+.2f}% y distancia promedio {changes[2]:+.2f}%.')
    parts.extend(['Los viajes verdes disminuyen en los tres años. Los amarillos alcanzan su mayor volumen en 2025. El pago y la distancia promedio de 2026 superan los de 2024 en ambos tipos. El recargo de congestión aparece desde 2025.', '## 9. Discusión', '### 9.1 Características útiles', 'Lectura directa de Parquet, SQL y unión de columnas por nombre permiten analizar varios años sin una importación previa.', '### 9.2 Parquet', 'Permite trabajar con los archivos originales sin otra copia. Las diferencias de columnas requieren una unión por nombre y las consultas repetidas vuelven a leer los datos.', '### 9.3 Tablas DuckDB', 'Las consultas repetidas tienen menores tiempos. La tabla requiere espacio adicional, tiempo de creación y actualización al agregar datos.', '### 9.4 Comparación con Pandas', 'DuckDB filtra y agrupa antes de pasar resultados a Pandas. Esto reduce la cantidad de datos en memoria.', '### 9.5 Incorporación de datos', 'Los años como parámetros, los nombres mensuales y las vistas comunes permiten incorporar archivos nuevos con pocos cambios.', '### 9.6 Automatización en producción', 'Descarga mensual, validación de datos y actualización de la base y el tablero.', '### 9.7 Reproducibilidad', 'Versiones fijas, código y SQL versionados, filtros documentados y datos originales separados de Git.', '### 9.8 Aprendizaje', 'El volumen hace visibles los costos de lectura, memoria y almacenamiento. Las diferencias de columnas y fechas requieren atención al combinar años.', '## Fuente', '[NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)'])
    (ROOT / 'docs/informe.md').write_text('\n\n'.join(parts) + '\n', encoding='utf-8')
    summaries = {
        'coverage': ('Cantidad de archivos y registros', f'{int(coverage.files.sum())} archivos y {int(coverage.rows.sum()):,} registros.', 'Cobertura por tipo y año.'),
        'quality': ('Datos inconsistentes', f'{int(quality.wrong_period.sum()):,} fechas fuera del mes y {int(quality.missing_passengers.sum()):,} pasajeros faltantes.', 'Filtros de fecha, distancia, duración y pago.'),
        'monthly': ('Cambios mensuales', 'Máximos en mayo de 2025 para amarillos y mayo de 2024 para verdes.', 'Serie mensual para comparar volumen y promedios.'),
        'hourly': ('Actividad por hora', 'Máximos a las 18:00 en amarillos y 17:00 en verdes.', 'Indicador de horarios.'),
        'payments': ('Formas de pago y propinas', 'La tarjeta es el pago más frecuente en ambos tipos.', 'Propinas respecto a tarifas positivas con tarjeta.'),
        'distribution': ('Distribución de distancia, pago y duración', 'En amarillos de 2026, distancia mediana de 1.93 millas y percentil 95 de 12.56.', 'Mediana y percentiles para describir valores habituales y altos.'),
        'zones': ('Zonas con más salidas', 'Zona 237 para amarillos y 74 para verdes.', 'Diez zonas principales por tipo.'),
        'comparable': ('Evolución entre años', 'De 2024 a 2026, viajes amarillos +10.41% y verdes -22.64%.', 'Comparación de los mismos meses.'),
    }
    queries = ['# Consultas', 'Fuente: Parquet de taxis amarillos y verdes de 2024, 2025 y los meses publicados de 2026. trips_raw contiene los registros originales y trips_clean aplica los filtros del informe.']
    for name, (purpose, result, decision) in summaries.items():
        source = 'trips_raw' if name in ['coverage', 'quality'] else 'trips_clean'
        queries.extend([f'## {purpose}', f'Fuente: {source}. Resultado: {result} Criterio: {decision}', '```sql\n' + sql(name).strip() + '\n```'])
    queries.extend(['## Columnas y tipos', 'Fuente: Parquet originales. Resultado: 25 columnas. Las fechas de amarillos y verdes tienen nombres distintos y el recargo de congestión no aparece en 2024. La unión por nombre conserva esas diferencias.', '```sql\n' + sql('schema').strip() + '\n```', table(frames['schema'][['column_name', 'column_type']].rename(columns={'column_name': 'Columna', 'column_type': 'Tipo'})), '## Muestra', 'Fuente: registros originales. Resultado: diez viajes, incluyendo fechas fuera del periodo. El filtro de fecha excluye esos valores de los indicadores.', '```sql\n' + sql('sample').strip() + '\n```', '## Transformaciones', 'Fechas de inicio y fin comunes para ambos tipos. Año y mes tomados del nombre del archivo. Duración calculada en minutos. Los filtros están en el informe.', '## Benchmark e indicadores', 'El benchmark compara las consultas mensuales, de horarios y de pagos sobre Parquet y una tabla DuckDB. Los seis indicadores del tablero corresponden a las consultas numeradas de la carpeta sql.'])
    (ROOT / 'docs/consultas.md').write_text('\n\n'.join(queries) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
