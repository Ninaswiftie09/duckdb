import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import CLEAN, RESULTS, ROOT, connect, files, sql, views

CARDS = [
    ("Viajes mensuales", "monthly", "trips", "Cantidad de viajes por mes y tipo de taxi. Permite observar cambios en la demanda."),
    ("Pago promedio", "monthly", "mean_total", "Pago total registrado promedio en USD. Incluye recargos y no incluye las propinas en efectivo."),
    ("Distancia promedio", "monthly", "mean_distance", "Distancia promedio en millas. Permite comparar el tamaño de los recorridos."),
    ("Duración promedio", "monthly", "mean_duration", "Duración promedio en minutos. Permite comparar el tiempo de cada recorrido."),
    ("Viajes por hora", "hourly", "trips", "Cantidad de viajes según la hora de inicio. Permite identificar horarios de mayor actividad."),
    ("Formas de pago", "payments", "trips", "Cantidad de viajes por forma de pago. Flex Fare es el código 0; tarjeta es 1 y efectivo es 2. Las propinas en efectivo no se registran."),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025, 2026])
    args = parser.parse_args()
    path = ROOT / "data" / "processed" / "taxi.duckdb"
    con = connect(path)
    views(con, files(args.years))
    print("Materializing dashboard database", flush=True)
    con.execute("CREATE OR REPLACE TABLE trips_materialized AS SELECT * FROM trips_raw")
    con.execute("CREATE OR REPLACE VIEW trips_raw AS SELECT * FROM trips_materialized")
    print("Building indicator tables", flush=True)
    con.execute("CREATE OR REPLACE VIEW trips_clean AS SELECT * FROM trips_materialized WHERE " + CLEAN)
    datasets = {}
    for name in ["monthly", "hourly", "payments", "quality", "comparable"]:
        con.execute(f"CREATE OR REPLACE TABLE dashboard_{name} AS " + sql(name))
        datasets[name] = con.execute(f"SELECT * FROM dashboard_{name}").fetchdf()
        print(f"Indicator ready: {name}", flush=True)
    con.execute("DROP VIEW trips_raw")
    con.close()
    evidence = ROOT / "docs" / "dashboard"
    evidence.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 2, figsize=(15, 13), constrained_layout=True)
    definitions = []
    for index, (title, name, metric, interpretation) in enumerate(CARDS):
        frame = datasets[name].copy()
        axis = axes.flat[index]
        if name == "monthly":
            frame["period"] = pd.to_datetime(dict(year=frame.source_year, month=frame.source_month, day=1))
            for taxi, group in frame.groupby("taxi"):
                axis.plot(group.period, group[metric], label=taxi)
            axis.tick_params(axis="x", rotation=30)
        else:
            x = "hour" if name == "hourly" else "payment_type"
            if name == "payments":
                frame[x] = frame[x].map({0: "Flex Fare", 1: "Tarjeta", 2: "Efectivo", 3: "Sin cargo", 4: "Disputa", 5: "Desconocido", 6: "Anulado"}).fillna("Sin identificar")
            grouped = frame.groupby([x, "taxi"])[metric].sum().unstack()
            grouped.plot(kind="bar" if name == "payments" else "line", ax=axis)
        axis.set_title(title)
        axis.set_ylabel({"trips": "Viajes", "mean_total": "USD", "mean_distance": "Millas", "mean_duration": "Minutos"}[metric])
        axis.legend()
        query = f"SELECT " + ("CAST(make_date(source_year, source_month, 1) AS DATE) AS period, taxi, " + metric if name == "monthly" else ("hour, taxi, trips" if name == "hourly" else "payment_type, taxi, sum(trips) AS trips")) + f" FROM dashboard_{name}" + (" GROUP BY payment_type, taxi" if name == "payments" else "") + " ORDER BY 1, 2"
        if name == "payments":
            query = query.replace("SELECT payment_type,", "SELECT CASE payment_type WHEN 0 THEN 'Flex Fare' WHEN 1 THEN 'Tarjeta' WHEN 2 THEN 'Efectivo' WHEN 3 THEN 'Sin cargo' WHEN 4 THEN 'Disputa' WHEN 5 THEN 'Desconocido' WHEN 6 THEN 'Anulado' ELSE 'Sin identificar' END AS payment_type,")
        definitions.append({"name": title, "sql": query, "metric": metric, "x": "period" if name == "monthly" else ("hour" if name == "hourly" else "payment_type"), "display": "bar" if name == "payments" else "line", "description": interpretation})
    fig.suptitle("Taxis NYC: 2024, 2025 y meses publicados de 2026", fontsize=18)
    fig.savefig(evidence / "dashboard.png", dpi=150)
    plt.close(fig)
    (evidence / "cards.json").write_text(json.dumps(definitions, ensure_ascii=False, indent=2), encoding="utf-8")
    for index, card in enumerate(definitions, 1):
        (ROOT / "sql" / f"indicator_{index:02d}.sql").write_text(card["sql"] + ";\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
