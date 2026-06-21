from datetime import datetime
from typing import Tuple

FORMULES_ENGIE = {
    "super_creuses": lambda epex: 1.2504 + (0.0840 * epex),
    "creuses":       lambda epex: 2.2304 + (0.1079 * epex),
    "pleines":       lambda epex: 2.8754 + (0.1395 * epex),
}

TARIFS_ORES = {
    "ECO":    5.09,
    "MEDIUM": 10.83,
    "PIC":    16.57,
}

SUPPLEMENTS = {
    "cotisation":   0.20417,
    "raccordement": 0.07500,
    "accise":       5.03288,
}

TVA = 1.06

PLAGES_FLEXTIME = {
    "semaine": {
        "pleines":       [(7, 11), (17, 22)],
        "creuses":       [(11, 17), (22, 1)],
        "super_creuses": [(1, 7)],
    },
    "weekend": {
        "creuses":       [(7, 11), (17, 1)],
        "super_creuses": [(1, 7), (11, 17)],
    },
}

PLAGES_ORES_IMPACT = {
    "PIC":    [(7, 11), (17, 22)],
    "MEDIUM": [(11, 17)],
    "ECO":    [(22, 7)],
}


def _heure_dans_plage(heure: int, plages: list) -> bool:
    for debut, fin in plages:
        if debut < fin:
            if debut <= heure < fin:
                return True
        else:
            if heure >= debut or heure < fin:
                return True
    return False


def get_plage_flextime(heure: int, jour_semaine: int) -> str:
    """jour_semaine: 0=lundi, 6=dimanche"""
    type_jour = "weekend" if jour_semaine >= 5 else "semaine"
    plages = PLAGES_FLEXTIME[type_jour]
    for plage, intervalles in plages.items():
        if _heure_dans_plage(heure, intervalles):
            return plage
    return "creuses"


def get_plage_ores(heure: int) -> str:
    for plage, intervalles in PLAGES_ORES_IMPACT.items():
        if _heure_dans_plage(heure, intervalles):
            return plage
    return "ECO"


def minutes_avant_changement(heure: int, minute: int, jour_semaine: int) -> int:
    """Retourne les minutes restantes avant le prochain changement de plage."""
    plage_actuelle = get_plage_flextime(heure, jour_semaine)
    for delta in range(1, 1441):
        total_minutes = heure * 60 + minute + delta
        h = (total_minutes // 60) % 24
        j = (jour_semaine + total_minutes // 1440) % 7
        if get_plage_flextime(h, j) != plage_actuelle:
            return delta
    return 0


def calcul_prix_total(epex_eur_mwh: float, heure: int, jour_semaine: int) -> float:
    """Retourne le prix total en c€/kWh (TVA incluse)."""
    epex_cents_kwh = epex_eur_mwh / 10

    plage_flex = get_plage_flextime(heure, jour_semaine)
    cout_engie = FORMULES_ENGIE[plage_flex](epex_cents_kwh)

    plage_ores = get_plage_ores(heure)
    cout_ores = TARIFS_ORES[plage_ores]

    supplements = sum(SUPPLEMENTS.values())
    total_htva = cout_engie + cout_ores + supplements
    return round(total_htva * TVA, 5)


def calcul_prix_eur_kwh(epex_eur_mwh: float, heure: int, jour_semaine: int) -> float:
    """Retourne le prix en €/kWh (TVA incluse)."""
    return round(calcul_prix_total(epex_eur_mwh, heure, jour_semaine) / 100, 5)
