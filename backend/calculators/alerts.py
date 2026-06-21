import os
import asyncio
from datetime import datetime, date
from discord_webhook import DiscordWebhook

EPEX_LOW_THRESHOLD = 40.0  # €/MWh

_alerte_recharge_envoyee: dict[str, bool] = {}
_alerte_epex_derniere_heure: str | None = None
_alerte_conso_envoyee_aujourd_hui: str | None = None


def _send_discord(message: str):
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return
    webhook = DiscordWebhook(url=url, content=message)
    webhook.execute()


def alerte_recharge_hors_fenetre(session_id: str, heure: int):
    if _alerte_recharge_envoyee.get(session_id):
        return
    if not (1 <= heure < 7):
        heure_fmt = f"{heure:02d}h{datetime.now().minute:02d}"
        _send_discord(
            f"⚠️ Recharge démarrée à {heure_fmt} — hors fenêtre super-creuse !"
        )
        _alerte_recharge_envoyee[session_id] = True


def alerte_epex_bas(epex: float):
    global _alerte_epex_derniere_heure
    heure_actuelle = datetime.now().strftime("%Y-%m-%d-%H")
    if epex < EPEX_LOW_THRESHOLD and heure_actuelle != _alerte_epex_derniere_heure:
        _send_discord(
            f"💡 Prix EPEX : {epex:.1f} €/MWh — excellent moment pour consommer !"
        )
        _alerte_epex_derniere_heure = heure_actuelle


def alerte_conso_anormale(kwh_aujourd_hui: float, moyenne_30j: float):
    global _alerte_conso_envoyee_aujourd_hui
    aujourd_hui = date.today().isoformat()
    if (
        datetime.now().hour == 20
        and kwh_aujourd_hui > moyenne_30j * 1.5
        and _alerte_conso_envoyee_aujourd_hui != aujourd_hui
    ):
        _send_discord(
            f"📊 Conso élevée aujourd'hui : {kwh_aujourd_hui:.1f} kWh "
            f"vs moyenne {moyenne_30j:.1f} kWh"
        )
        _alerte_conso_envoyee_aujourd_hui = aujourd_hui


def reset_session_alerte(session_id: str):
    _alerte_recharge_envoyee.pop(session_id, None)
