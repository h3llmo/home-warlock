import os
import asyncio
from datetime import datetime, timezone
from database.db import get_db

POLL_INTERVAL_CHARGING = 300   # 5 min
POLL_INTERVAL_IDLE = 900       # 15 min


async def _fetch_bmw_status() -> dict:
    from bimmer_connected.account import MyBMWAccount
    from bimmer_connected.api.regions import get_region_from_name

    email = os.getenv("BMW_EMAIL", "")
    password = os.getenv("BMW_PASSWORD", "")
    if not email or not password:
        raise ValueError("BMW_EMAIL ou BMW_PASSWORD manquant")

    account = MyBMWAccount(email, password, get_region_from_name("rest_of_world"))
    await account.get_vehicles()

    vehicle = account.vehicles[0]
    status = vehicle.status

    return {
        "battery_percent": status.fuel_and_battery.remaining_battery_percent,
        "range_km": status.fuel_and_battery.remaining_range_electric[0],
        "charging_status": status.fuel_and_battery.charging_status.value,
    }


async def store_bmw(data: dict):
    ts = datetime.now(timezone.utc).isoformat()
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO bmw_status (timestamp, battery_percent, range_km, charging_status) VALUES (?, ?, ?, ?)",
            (ts, data["battery_percent"], data["range_km"], data["charging_status"]),
        )
        await db.commit()


async def get_latest() -> dict | None:
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT * FROM bmw_status ORDER BY id DESC LIMIT 1"
        ) as cur:
            return await cur.fetchone()


async def run_collector(state: dict):
    email = os.getenv("BMW_EMAIL", "")
    if not email:
        print("[BMW] BMW_EMAIL non configuré, collecteur désactivé.")
        return

    print("[BMW] Démarrage collecte statut véhicule")
    while True:
        try:
            data = await _fetch_bmw_status()
            state["bmw"] = data
            await store_bmw(data)
            is_charging = data["charging_status"] == "CHARGING"
            interval = POLL_INTERVAL_CHARGING if is_charging else POLL_INTERVAL_IDLE
        except Exception as e:
            print(f"[BMW] Erreur: {e}")
            interval = POLL_INTERVAL_IDLE
        await asyncio.sleep(interval)
