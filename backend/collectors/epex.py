import os
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from database.db import get_db
from calculators.alerts import alerte_epex_bas

ENTSO_E_URL = "https://web-api.tp.entsoe.eu/api"
POLL_INTERVAL = 3600  # secondes


async def fetch_day_ahead_prices() -> list[tuple[str, float]]:
    token = os.getenv("ENTSO_E_TOKEN", "")
    now = datetime.now(timezone.utc)
    period_start = now.strftime("%Y%m%d0000")
    period_end = (now + timedelta(days=1)).strftime("%Y%m%d0000")

    params = {
        "securityToken": token,
        "documentType": "A44",
        "in_Domain": "10YBE----------2",
        "out_Domain": "10YBE----------2",
        "periodStart": period_start,
        "periodEnd": period_end,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(ENTSO_E_URL, params=params)
        resp.raise_for_status()
        return _parse_prices(resp.text)


def _parse_prices(xml_text: str) -> list[tuple[str, float]]:
    ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
    root = ET.fromstring(xml_text)
    results = []
    for ts in root.findall(".//ns:TimeSeries", ns):
        period = ts.find("ns:Period", ns)
        if period is None:
            continue
        start_elem = period.find("ns:timeInterval/ns:start", ns)
        if start_elem is None:
            continue
        start_str = start_elem.text  # format: 2024-01-15T23:00Z
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        for point in period.findall("ns:Point", ns):
            pos = int(point.find("ns:position", ns).text)
            price = float(point.find("ns:price.amount", ns).text)
            hour_dt = start_dt + timedelta(hours=pos - 1)
            results.append((hour_dt.isoformat(), price))
    return results


async def store_prices(prices: list[tuple[str, float]]):
    async with await get_db() as db:
        for hour_start, price in prices:
            await db.execute(
                "INSERT OR REPLACE INTO epex_prices (hour_start, price_eur_mwh) VALUES (?, ?)",
                (hour_start, price),
            )
        await db.commit()


async def get_current_price() -> float | None:
    now = datetime.now(timezone.utc)
    hour_start = now.replace(minute=0, second=0, microsecond=0).isoformat()
    async with await get_db() as db:
        async with db.execute(
            "SELECT price_eur_mwh FROM epex_prices WHERE hour_start <= ? ORDER BY hour_start DESC LIMIT 1",
            (now.isoformat(),),
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def run_collector(state: dict):
    token = os.getenv("ENTSO_E_TOKEN", "")
    if not token:
        print("[EPEX] ENTSO_E_TOKEN non configuré, collecteur désactivé.")
        return

    print("[EPEX] Démarrage collecte prix day-ahead")
    while True:
        try:
            prices = await fetch_day_ahead_prices()
            await store_prices(prices)
            print(f"[EPEX] {len(prices)} prix stockés")
            # Vérifier prix bas pour alerte
            price = await get_current_price()
            if price is not None:
                state["epex_current"] = price
                alerte_epex_bas(price)
        except Exception as e:
            print(f"[EPEX] Erreur: {e}")
        await asyncio.sleep(POLL_INTERVAL)
