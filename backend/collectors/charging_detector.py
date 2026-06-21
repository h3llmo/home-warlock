import asyncio
from datetime import datetime, timezone
from database.db import get_db
from calculators.alerts import alerte_recharge_hors_fenetre, reset_session_alerte
from calculators.tariffs import calcul_prix_eur_kwh

SEUIL_DEBUT = 1800   # watts
SEUIL_FIN = 500      # watts
DUREE_MIN = 5 * 60   # 5 minutes en secondes

_session_id: str | None = None
_debut_session: datetime | None = None
_kwh_debut: float | None = None
_candidate_start: datetime | None = None


async def _get_avg_30j_sans_recharge() -> float:
    async with await get_db() as db:
        async with db.execute("""
            SELECT AVG(daily_kwh) FROM (
                SELECT DATE(timestamp) as day, MAX(kwh_cumulative) - MIN(kwh_cumulative) as daily_kwh
                FROM consumption
                WHERE is_charging = 0
                  AND timestamp >= datetime('now', '-30 days')
                GROUP BY day
            )
        """) as cur:
            row = await cur.fetchone()
            return row[0] or 0.0


async def _save_session(kwh: float, cout: float):
    global _session_id, _debut_session
    if not _session_id or not _debut_session:
        return
    end_time = datetime.now(timezone.utc).isoformat()
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO charging_sessions (start_time, end_time, kwh_total, cost_eur) VALUES (?, ?, ?, ?)",
            (_debut_session.isoformat(), end_time, kwh, cout),
        )
        await db.commit()


async def run_detector(state: dict):
    global _session_id, _debut_session, _kwh_debut, _candidate_start

    while True:
        watts = state.get("watts_total", 0)
        kwh_now = state.get("kwh_cumulative", 0)
        now = datetime.now(timezone.utc)

        if not state.get("session_recharge"):
            if watts > SEUIL_DEBUT:
                if _candidate_start is None:
                    _candidate_start = now
                elif (now - _candidate_start).total_seconds() >= DUREE_MIN:
                    _session_id = now.isoformat()
                    _debut_session = _candidate_start
                    _kwh_debut = kwh_now
                    state["session_recharge"] = True
                    state["session_id"] = _session_id
                    state["kwh_session"] = 0.0
                    state["cout_session"] = 0.0
                    alerte_recharge_hors_fenetre(_session_id, now.hour)
            else:
                _candidate_start = None
        else:
            if _kwh_debut is not None:
                kwh_session = kwh_now - _kwh_debut
                epex = state.get("epex_current", 100.0)
                prix = calcul_prix_eur_kwh(epex, now.hour, now.weekday())
                cout = kwh_session * prix
                state["kwh_session"] = round(kwh_session, 3)
                state["cout_session"] = round(cout, 4)

            if watts < SEUIL_FIN:
                await _save_session(
                    state.get("kwh_session", 0),
                    state.get("cout_session", 0),
                )
                reset_session_alerte(_session_id)
                state["session_recharge"] = False
                state["session_id"] = None
                _session_id = None
                _debut_session = None
                _kwh_debut = None
                _candidate_start = None

        await asyncio.sleep(10)
