import argparse
import json
import os
import secrets

import requests

from common import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://metabase:3000")
    args = parser.parse_args()
    client = requests.Session()
    base = args.url.rstrip("/") + "/api"

    def call(method, endpoint, payload=None):
        response = client.request(method, base + endpoint, json=payload, timeout=180)
        if not response.ok:
            raise RuntimeError(f"{method} {endpoint}: {response.status_code}: {response.text[:1500]}")
        return response.json()

    settings = call("GET", "/session/properties")
    credentials = ROOT / "data" / "processed" / "metabase_credentials.json"
    if settings.get("setup-token"):
        password = secrets.token_urlsafe(24) + "Aa1!"
        email = "lab8@example.com"
        result = call("POST", "/setup", {"token": settings["setup-token"], "user": {"first_name": "Lab", "last_name": "DuckDB", "email": email, "password": password}, "prefs": {"site_name": "Lab 8 DuckDB", "allow_tracking": False}})
        credentials.write_text(json.dumps({"email": email, "password": password}), encoding="utf-8")
        client.headers["X-Metabase-Session"] = result["id"]
    else:
        account = json.loads(credentials.read_text()) if credentials.exists() else {"email": os.environ["MB_EMAIL"], "password": os.environ["MB_PASSWORD"]}
        client.headers["X-Metabase-Session"] = call("POST", "/session", {"username": account["email"], "password": account["password"]})["id"]
    databases = call("GET", "/database")["data"]
    database = next((d for d in databases if d["name"] == "Taxis NYC"), None)
    if database is None:
        database = call("POST", "/database", {"name": "Taxis NYC", "engine": "duckdb", "details": {"database_file": "/workspace/data/processed/taxi.duckdb", "read_only": True, "memory_limit": "1GB"}})
    dashboards = call("GET", "/dashboard")
    dashboard = next((d for d in dashboards if d["name"] == "Lab 8 - Taxis NYC"), None)
    if dashboard is None:
        dashboard = call("POST", "/dashboard", {"name": "Lab 8 - Taxis NYC", "description": "2024, 2025 y meses publicados de 2026. Se excluyen valores inconsistentes. USD y millas.", "parameters": []})
    definitions = json.loads((ROOT / "docs" / "dashboard" / "cards.json").read_text(encoding="utf-8"))
    existing = call("GET", "/card")
    cards = []
    evidence = []
    for index, definition in enumerate(definitions):
        card = next((c for c in existing if c["name"] == definition["name"]), None)
        x_title = {"period": "Fecha", "hour": "Hora", "payment_type": "Forma de pago"}[definition["x"]]
        y_title = {"trips": "Viajes", "mean_total": "USD", "mean_distance": "Millas", "mean_duration": "Minutos"}[definition["metric"]]
        payload = {"name": definition["name"], "description": definition["description"], "display": definition["display"], "dataset_query": {"database": database["id"], "type": "native", "native": {"query": definition["sql"], "template-tags": {}}}, "visualization_settings": {"graph.dimensions": [definition["x"], "taxi"], "graph.metrics": [definition["metric"]], "graph.x_axis.title_text": x_title, "graph.y_axis.title_text": y_title}}
        card = call("PUT", f"/card/{card['id']}", payload) if card else call("POST", "/card", payload)
        result = call("POST", f"/card/{card['id']}/query", {})
        if result.get("status") != "completed":
            raise RuntimeError(str(result)[:2000])
        evidence.append({"name": definition["name"], "card_id": card["id"], "rows": len(result["data"]["rows"]), "status": result["status"]})
        cards.append({"id": -(index + 1), "card_id": card["id"], "row": (index // 2) * 5, "col": (index % 2) * 12, "size_x": 12, "size_y": 5, "parameter_mappings": [], "visualization_settings": {}})
    call("PUT", f"/dashboard/{dashboard['id']}", {"dashcards": cards})
    (ROOT / "docs" / "dashboard" / "metabase_validation.json").write_text(json.dumps({"dashboard_id": dashboard["id"], "url": f"http://localhost:3000/dashboard/{dashboard['id']}", "database_id": database["id"], "cards": evidence}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Dashboard verified: http://localhost:3000/dashboard/{dashboard['id']}")


if __name__ == "__main__":
    main()
