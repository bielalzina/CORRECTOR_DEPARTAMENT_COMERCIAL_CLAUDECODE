"""Utilitats generals compartides entre mòduls i vistes."""

from datetime import date
from typing import Optional


def fmt_data(s: str) -> str:
    """Converteix una data ISO (yyyy-mm-dd o yyyy-mm-ddTHH:MM:SS) a dd/mm/yyyy."""
    if not s or len(s) < 10:
        return s or "—"
    try:
        y, m, d = s[:10].split("-")
        return f"{d}/{m}/{y}"
    except (ValueError, AttributeError):
        return s


# ── Utilitats per al motor de correcció ──────────────────────────────────────

def parse_data(val) -> Optional[date]:
    """Converteix qualsevol format de data a datetime.date. Retorna None si falla."""
    if val is None or str(val).strip() in ("nan", "None", "NaT", ""):
        return None
    import pandas as pd
    try:
        return pd.to_datetime(str(val).strip(), dayfirst=True).date()
    except Exception:
        return None


def dates_iguals(val_alumne, val_ref: str) -> bool:
    """Compara dues dates (val_alumne pot ser qualsevol format, val_ref és ISO yyyy-mm-dd)."""
    d1 = parse_data(val_alumne)
    d2 = parse_data(val_ref)
    if d1 is None or d2 is None:
        return False
    return d1 == d2


def to_float(val) -> Optional[float]:
    """Converteix un valor a float. Retorna None si no es pot."""
    if val is None or str(val).strip() in ("nan", "None", ""):
        return None
    try:
        return float(str(val).replace(",", ".").replace(" ", "").replace("\xa0", ""))
    except (ValueError, TypeError):
        return None


def imports_iguals(val_alumne, val_ref, tolerancia: float = 0.01) -> bool:
    """Compara dos imports amb tolerància d'1 cèntim."""
    f1 = to_float(val_alumne)
    f2 = to_float(val_ref)
    if f1 is None or f2 is None:
        return False
    return abs(abs(f1) - abs(f2)) <= tolerancia


def norm_str(val) -> str:
    """Normalitza un string per a comparació (strip + lower, sense valors nuls)."""
    if val is None or str(val).strip() in ("nan", "None", ""):
        return ""
    return str(val).strip().lower()


def fer_error(
    llistat: str,
    tipus: str,
    gravetat: str,
    penalitzacio: float,
    descripcio: str,
    camp: Optional[str] = None,
    valor_alumne=None,
    valor_esperat=None,
    operacio: Optional[str] = None,
) -> dict:
    """Construeix un dict d'error estàndard."""
    return {
        "llistat": llistat,
        "tipus": tipus,
        "gravetat": gravetat,
        "penalitzacio": -abs(penalitzacio),
        "descripcio": descripcio,
        "camp": camp,
        "valor_alumne": str(valor_alumne) if valor_alumne is not None else None,
        "valor_esperat": str(valor_esperat) if valor_esperat is not None else None,
        "operacio": operacio,
    }


def fer_ambigu(
    llistat: str,
    tipus: str,
    descripcio: str,
    valor_alumne,
    valor_esperat,
    penalitzacio_si_rebutjat: float = 0.5,
) -> dict:
    """Construeix un dict de cas ambigu estàndard."""
    import uuid
    return {
        "id": str(uuid.uuid4()),
        "llistat": llistat,
        "tipus": tipus,
        "descripcio": descripcio,
        "valor_alumne": str(valor_alumne),
        "valor_esperat": str(valor_esperat),
        "resolucio": None,  # None | "acceptat" | "rebutjat"
        "penalitzacio_si_rebutjat": penalitzacio_si_rebutjat,
    }


PENALITZACIONS_DEFAULT: dict = {
    "operacio_falta":           1.0,
    "proveidor_client_incorrecte": 1.0,
    "import_incorrecte":        1.0,
    "quantitat_incorrecta":     1.0,
    "factura_anticipada":       1.0,
    "estoc_negatiu":            1.0,
    "data_incorrecta":          0.5,
    "numero_incorrecte":        0.5,
    "estat_incorrecte":         0.5,
}
