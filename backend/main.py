import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from database.db import init_db, get_db
from collectors import p1_meter, epex, bmw, charging_detector
from calculators.tariffs import (
    get_plage_flextime,
    get_plage_ores,
    calcul_prix_eur_kwh,
    minutes_avant_changement,
)
from calculators.alerts import alerte_conso_anormale

# Shared state entre collecteurs et API
state: dict = {
    "watts_total": 0.0,
    "kwh_cumulative": 0.0,
    "epex_current": None,
    "bmw": None,
    "session_recharge": False,
    "session_id": None,
    "kwh_session": 0.0,
    "cout_session": 0.0,
}


async def _run_alert_scheduler():
    while True:
        try:
            now = datetime.now(timezone.utc)
            async with await get_db() as db:
                async with db.execute("""
                    SELECT SUM(kwh_cumulative) FROM consumption
                    WHERE DATE(timestamp) = DATE('now')
                      AND is_charging = 0
                """) as cur:
                    row = await cur.fetchone()
                    kwh_today = row[0] or 0.0

                async with db.execute("""
                    SELECT AVG(daily) FROM (
                        SELECT DATE(timestamp) as d, MAX(kwh_cumulative)-MIN(kwh_cumulative) as daily
                        FROM consumption WHERE is_charging=0
                          AND timestamp >= datetime('now', '-30 days')
                        GROUP BY d
                    )
                """) as cur:
                    row = await cur.fetchone()
                    avg_30j = row[0] or 0.0

            alerte_conso_anormale(kwh_today, avg_30j)
        except Exception as e:
            print(f"[AlertScheduler] Erreur: {e}")
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    tasks = [
        asyncio.create_task(p1_meter.run_collector(state)),
        asyncio.create_task(epex.run_collector(state)),
        asyncio.create_task(bmw.run_collector(state)),
        asyncio.create_task(charging_detector.run_detector(state)),
        asyncio.create_task(_run_alert_scheduler()),
    ]
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="Energy Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/realtime")
async def get_realtime():
    now = datetime.now(timezone.utc)
    heure = now.hour
    jour = now.weekday()
    epex = state.get("epex_current") or 100.0

    watts_total = state.get("watts_total", 0)
    watts_voiture = watts_total if state.get("session_recharge") else 0
    watts_maison = watts_total - watts_voiture

    plage = get_plage_flextime(heure, jour)
    plage_ores = get_plage_ores(heure)
    prix_kwh = calcul_prix_eur_kwh(epex, heure, jour)
    mins_restants = minutes_avant_changement(heure, now.minute, jour)

    return {
        "watts_total": watts_total,
        "watts_voiture": watts_voiture,
        "watts_maison": watts_maison,
        "prix_kwh_actuel": prix_kwh,
        "plage_active": plage,
        "plage_ores": plage_ores,
        "epex_eur_mwh": epex,
        "minutes_avant_changement": mins_restants,
        "session_recharge": state.get("session_recharge", False),
        "kwh_session": state.get("kwh_session", 0),
        "cout_session": state.get("cout_session", 0),
    }


@app.get("/api/bmw")
async def get_bmw():
    data = state.get("bmw")
    if data:
        return data
    saved = await bmw.get_latest()
    if saved:
        return {
            "battery_percent": saved["battery_percent"],
            "range_km": saved["range_km"],
            "charging_status": saved["charging_status"],
        }
    return {"battery_percent": None, "range_km": None, "charging_status": "UNKNOWN"}


@app.get("/api/projection")
async def get_projection():
    now = datetime.now(timezone.utc)
    jour_du_mois = now.day
    jours_dans_mois = 30

    async with await get_db() as db:
        # Coût mois en cours
        async with db.execute("""
            SELECT SUM(kwh) FROM (
                SELECT (MAX(kwh_cumulative) - MIN(kwh_cumulative)) as kwh
                FROM consumption
                WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
                GROUP BY DATE(timestamp)
            )
        """) as cur:
            row = await cur.fetchone()
            kwh_mois = row[0] or 0.0

        # Coût mois précédent
        async with db.execute("""
            SELECT SUM(kwh) FROM (
                SELECT (MAX(kwh_cumulative) - MIN(kwh_cumulative)) as kwh
                FROM consumption
                WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', datetime('now', '-1 month'))
                GROUP BY DATE(timestamp)
            )
        """) as cur:
            row = await cur.fetchone()
            kwh_mois_precedent = row[0] or 0.0

    epex = state.get("epex_current") or 100.0
    heure = now.hour
    jour = now.weekday()
    prix_moyen = calcul_prix_eur_kwh(epex, heure, jour)

    cout_mois_actuel = round(kwh_mois * prix_moyen, 2)
    cout_projete = round((kwh_mois / max(jour_du_mois, 1)) * jours_dans_mois * prix_moyen, 2)
    cout_mois_precedent = round(kwh_mois_precedent * prix_moyen, 2)

    variation = 0.0
    if cout_mois_precedent > 0:
        variation = round((cout_mois_actuel - cout_mois_precedent) / cout_mois_precedent * 100, 1)

    return {
        "cout_mois_actuel": cout_mois_actuel,
        "cout_projete": cout_projete,
        "cout_mois_precedent": cout_mois_precedent,
        "variation_pct": variation,
    }


@app.get("/api/history")
async def get_history(granularity: str = "15min", from_ts: str = None, to_ts: str = None):
    now = datetime.now(timezone.utc)
    if not from_ts:
        from_ts = (now - timedelta(days=1)).isoformat()
    if not to_ts:
        to_ts = now.isoformat()

    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("""
            SELECT timestamp, watts_total, kwh_cumulative, is_charging
            FROM consumption
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (from_ts, to_ts)) as cur:
            rows = await cur.fetchall()

    # Agréger par quart d'heure
    buckets: dict[str, dict] = {}
    for row in rows:
        ts = datetime.fromisoformat(row["timestamp"])
        if granularity == "15min":
            bucket_key = ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0).isoformat()
        elif granularity == "1h":
            bucket_key = ts.replace(minute=0, second=0, microsecond=0).isoformat()
        else:
            bucket_key = ts.replace(second=0, microsecond=0).isoformat()

        if bucket_key not in buckets:
            buckets[bucket_key] = {"watts_sum": 0, "count": 0, "is_charging": 0, "kwh_start": row["kwh_cumulative"]}
        b = buckets[bucket_key]
        b["watts_sum"] += row["watts_total"]
        b["count"] += 1
        b["is_charging"] = max(b["is_charging"], row["is_charging"])
        b["kwh_end"] = row["kwh_cumulative"]

    epex_current = state.get("epex_current") or 100.0
    result = []
    for ts_str, b in sorted(buckets.items()):
        ts = datetime.fromisoformat(ts_str)
        kwh = round(b.get("kwh_end", 0) - b.get("kwh_start", 0), 4)
        prix = calcul_prix_eur_kwh(epex_current, ts.hour, ts.weekday())
        plage = get_plage_flextime(ts.hour, ts.weekday())
        result.append({
            "timestamp": ts_str,
            "watts": round(b["watts_sum"] / max(b["count"], 1), 1),
            "kwh": kwh,
            "cout": round(kwh * prix, 4),
            "plage": plage,
            "est_recharge": bool(b["is_charging"]),
        })

    return result


@app.get("/api/analytics")
async def get_analytics():
    async with await get_db() as db:
        # Sessions recharge
        async with db.execute(
            "SELECT SUM(kwh_total), SUM(cost_eur), COUNT(*) FROM charging_sessions"
        ) as cur:
            row = await cur.fetchone()
            kwh_voiture = row[0] or 0.0
            cout_voiture = row[1] or 0.0
            nb_sessions = row[2] or 0

        # Conso totale
        async with db.execute(
            "SELECT MAX(kwh_cumulative) - MIN(kwh_cumulative) FROM consumption"
        ) as cur:
            row = await cur.fetchone()
            kwh_total = row[0] or 0.0

    kwh_maison = max(kwh_total - kwh_voiture, 0)

    epex = state.get("epex_current") or 100.0
    now = datetime.now(timezone.utc)
    prix_moyen = calcul_prix_eur_kwh(epex, now.hour, now.weekday())
    cout_maison = kwh_maison * prix_moyen

    cout_moyen_kwh = round((cout_voiture + cout_maison) / max(kwh_total, 0.001), 4)
    # BMW i4 : ~18 kWh/100km → cout par km
    CONSO_BMW_KWH_100KM = 18.0
    cout_par_km = round(cout_moyen_kwh * CONSO_BMW_KWH_100KM / 100, 4)

    # Économies vs tarif fixe 0.42 €/kWh
    TARIF_BASE = 0.42
    economies = round((TARIF_BASE - cout_moyen_kwh) * kwh_total, 2)

    return {
        "cout_moyen_kwh_reel": cout_moyen_kwh,
        "cout_par_km": cout_par_km,
        "kwh_voiture": round(kwh_voiture, 2),
        "kwh_maison": round(kwh_maison, 2),
        "kwh_total": round(kwh_total, 2),
        "cout_voiture": round(cout_voiture, 2),
        "cout_maison": round(cout_maison, 2),
        "economies_vs_fixe": economies,
        "nb_sessions_recharge": nb_sessions,
    }
