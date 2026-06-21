import os
import asyncio
import httpx
from datetime import datetime, timezone
from database.db import get_db

POLL_INTERVAL = 10  # secondes


async def fetch_p1_data(ip: str) -> dict:
    url = f"http://{ip}/api/v1/data"
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def store_reading(watts: float, kwh: float, is_charging: bool = False):
    ts = datetime.now(timezone.utc).isoformat()
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO consumption (timestamp, watts_total, kwh_cumulative, is_charging) VALUES (?, ?, ?, ?)",
            (ts, watts, kwh, int(is_charging)),
        )
        await db.commit()


async def get_latest() -> dict | None:
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT * FROM consumption ORDER BY id DESC LIMIT 1"
        ) as cur:
            return await cur.fetchone()


async def run_collector(state: dict):
    ip = os.getenv("P1_METER_IP", "")
    if not ip:
        print("[P1] P1_METER_IP non configuré, collecteur désactivé.")
        return

    print(f"[P1] Démarrage collecte sur {ip}")
    while True:
        try:
            data = await fetch_p1_data(ip)
            # HomeWizard P1 retourne active_power_w et total_power_import_kwh
            watts = data.get("active_power_w", 0.0)
            kwh = data.get("total_power_import_kwh", 0.0)
            state["watts_total"] = watts
            state["kwh_cumulative"] = kwh
            await store_reading(watts, kwh, state.get("session_recharge", False))
        except Exception as e:
            print(f"[P1] Erreur: {e}")
        await asyncio.sleep(POLL_INTERVAL)
