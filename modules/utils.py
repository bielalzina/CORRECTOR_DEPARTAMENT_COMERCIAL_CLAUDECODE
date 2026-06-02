"""Utilitats generals compartides entre mòduls i vistes."""

import re
from datetime import date
from typing import Optional

_DATE_ISO_RE = re.compile(r'(\d{4})-(\d{2})-(\d{2})(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?')


def fmt_data(s: str) -> str:
    """Converteix dates ISO (yyyy-mm-dd[Thh:mm:ss]) a dd/mm/yyyy.
    Funciona fins i tot dins de strings com '<= 2025-11-14' o '>= 2025-05-11 00:00:00'."""
    if not s:
        return "—"
    return _DATE_ISO_RE.sub(lambda m: f"{m.group(3)}/{m.group(2)}/{m.group(1)}", s)


# ── Utilitats per al motor de correcció ──────────────────────────────────────

def parse_data(val) -> Optional[date]:
    """Converteix qualsevol format de data a datetime.date. Retorna None si falla.
    Usa formats explícits per evitar l'ambigüitat de dayfirst en pandas modern."""
    import pandas as pd
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date() if hasattr(val, "hour") else val
    s = str(val).strip()
    if s in ("nan", "None", "NaT", ""):
        return None
    # Format ISO yyyy-mm-dd (referència JSON i dates Excel via dtype=str)
    try:
        return pd.to_datetime(s[:10], format="%Y-%m-%d").date()
    except Exception:
        pass
    # Format dd/mm/yyyy (text cells)
    try:
        return pd.to_datetime(s, format="%d/%m/%Y").date()
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


def imports_iguals(val_alumne, val_ref, tolerancia: float = 0.03) -> bool:
    """Compara dos imports amb tolerància de 3 cèntims (arrodoniments acumulats d'ODOO)."""
    f1 = to_float(val_alumne)
    f2 = to_float(val_ref)
    if f1 is None or f2 is None:
        return False
    return abs(abs(f1) - abs(f2)) <= tolerancia


def norm_str(val) -> str:
    """Normalitza un string per a comparació (strip + lower, sense valors nuls).
    - "1.0" → "1": enters representats com a float (pandas dtype=str sobre cel·les numèriques).
    - "0008" → "8": zeros inicials (cel·les de text amb format numèric al xlsx de l'alumne)."""
    if val is None or str(val).strip() in ("nan", "None", ""):
        return ""
    s = str(val).strip().lower()
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        s = s[:-2]
    if s.isdigit():
        s = str(int(s))
    return s


def _fmt_display(val) -> Optional[str]:
    """Formata un valor per mostrar-lo a l'informe d'errors.
    - "1.0" → "1": enters com a float.
    - "0008" → "8": zeros inicials."""
    if val is None:
        return None
    s = str(val)
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        s = s[:-2]
    if s.isdigit():
        s = str(int(s))
    return s


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
    document: Optional[str] = None,
) -> dict:
    """Construeix un dict d'error estàndard."""
    return {
        "llistat": llistat,
        "tipus": tipus,
        "gravetat": gravetat,
        "penalitzacio": -abs(penalitzacio),
        "descripcio": descripcio,
        "camp": camp,
        "valor_alumne": _fmt_display(valor_alumne),
        "valor_esperat": _fmt_display(valor_esperat),
        "operacio": operacio,
        "document": document,
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


def detectar_duplicats(
    df: "pd.DataFrame",
    nom_llistat: str,
    camps_clau: list[str],
    p: dict,
) -> list[dict]:
    """Detecta files amb la clau primària repetida al llistat de l'alumne.
    Ignora files on la clau sigui buida per evitar falsos positius."""
    errors = []
    vistos: set = set()
    for _, row in df.iterrows():
        clau = tuple(norm_str(row.get(c, "")) for c in camps_clau)
        if any(v in ("", "nan", "none") for v in clau):
            continue
        if clau in vistos:
            vals = {c: row.get(c, "") for c in camps_clau}
            errors.append(fer_error(
                nom_llistat, "operacio_falta", "molt_greu", p["operacio_falta"],
                f"Fila duplicada detectada: {vals}",
            ))
        else:
            vistos.add(clau)
    return errors


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
