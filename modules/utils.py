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


# ── Àlies de visualització dels camps ───────────────────────────────────────
# Estructura: { nom_intern: (alias, llistat) }
# Quan un mateix camp apareix a diversos llistats s'usa el llistat com a
# desambiguador. La funció `alias_camp` retorna l'àlies adequat.

ALIASES_CAMPS: dict[str, dict[str, str]] = {
    # ── 01_COMANDES_COMPRES ──────────────────────────────────────────────────
    "01_COMANDES_COMPRES": {
        "Referencia del pedido":   "CODI ODOO COMANDA COMPRA",
        "Fecha límite del pedido": "DATA REGISTRE COMANDA COMPRA",
        "Referencia de proveedor": "NÚMERO EMISSIO COMANDA COMPRA",
        "Data comanda":            "DATA EMISSIO COMANDA COMPRA",
        "Proveedor":               "PROVEÏDOR",
        "Base imponible":          "BASE IMPONIBLE COMPRA",
        "Total":                   "IMPORT TOTAL COMPRA",
        "Estado":                  "ESTAT COMANDA COMPRA",
        "Estado de facturación":   "ESTAT FACTURACIÓ COMANDA COMPRA",
    },
    # ── 02_RECEPCIONS ────────────────────────────────────────────────────────
    "02_RECEPCIONS": {
        "Referencia":              "CODI ODOO ALBARA COMPRA",
        "Fecha de traslado":       "DATA REGISTRE ALBARA COMPRA",
        "Numero albarà":           "NUMERO EMISSIO ALBARA COMPRA",
        "Data albarà":             "DATA EMISSIO ALBARA COMPRA",
        "Contacto":                "PROVEÏDOR",
        "Documento de origen":     "CODI ODOO COMANDA COMPRA",
        "Pedidos de compra/Total": "IMPORT TOTAL COMPRA",
        "Estado":                  "ESTAT RECEPCIÓ",
    },
    # ── 03_FACTURES_COMPRA ───────────────────────────────────────────────────
    "03_FACTURES_COMPRA": {
        "Número":                                       "CODI ODOO FACTURA COMPRA",
        "Nombre de la empresa a mostrar en la factura": "PROVEÏDOR",
        "Referencia":                                   "NUMERO EMISSIO FACTURA COMPRA",
        "Fecha de factura":                             "DATA EMISSIO FACTURA COMPRA",
        "Fecha de vencimiento":                         "DATA VENCIMENT FACTURA COMPRA",
        "Origen":                                       "CODI ODOO COMANDA COMPRA",
        "Base imponible en la moneda firmada":          "BASE IMPONIBLE COMPRA",
        "Impuesto firmado":                             "IMPORT IVA COMPRA",
        "Total con signo en moneda":                    "IMPORT TOTAL COMPRA",
        "Estado en pago":                               "ESTAT PAGAMENT FACTURA COMPRA",
    },
    # ── 04_COMANDES_VENDES ───────────────────────────────────────────────────
    "04_COMANDES_VENDES": {
        "Referencia del pedido":   "CODI ODOO COMANDA VENDA",
        "Fecha de creación":       "DATA REGISTRE COMANDA VENDA",
        "Data comanda":            "DATA EMISSIO COMANDA VENDA",
        "Numero comanda":          "NÚMERO EMISSIO COMANDA VENDA",
        "Cliente":                 "CLIENT",
        "Base imponible":          "BASE IMPONIBLE VENDA",
        "Impuestos":               "IMPORT IVA VENDA",
        "Total":                   "IMPORT TOTAL VENDA",
        "Estado":                  "ESTAT COMANDA VENDA",
        "Estado de la factura":    "ESTAT FACTURACIÓ COMANDA VENDA",
    },
    # ── 05_ENTREGUES ─────────────────────────────────────────────────────────
    "05_ENTREGUES": {
        "Referencia":              "CODI ODOO ALBARA VENDA",
        "Fecha de traslado":       "DATA EMISSIO ALBARA VENDA",
        "Contacto":                "CLIENT",
        "Documento de origen":     "CODI ODOO COMANDA VENDA",
        "Pedido de venta/Total":   "IMPORT TOTAL VENDA",
        "Estado":                  "ESTAT ENTREGA",
    },
    # ── 06_FACTURES_VENDA ────────────────────────────────────────────────────
    "06_FACTURES_VENDA": {
        "Número":                                       "NUMERO EMISSIO FACTURA VENDA",
        "Fecha de factura":                             "DATA EMISSIO FACTURA VENDA",
        "Fecha de vencimiento":                         "DATA VENCIMENT FACTURA VENDA",
        "Nombre de la empresa a mostrar en la factura": "CLIENT",
        "Origen":                                       "CODI ODOO COMANDA VENDA",
        "Base imponible en la moneda firmada":          "BASE IMPONIBLE VENDA",
        "Impuesto firmado":                             "IMPORT IVA VENDA",
        "Total con signo en moneda":                    "IMPORT TOTAL VENDA",
        "Estado en pago":                               "ESTAT PAGAMENT FACTURA VENDA",
        "Enviado":                                      "ESTAT ENVIAMENT FACTURA VENDA",
    },
    # ── 07_STOCK ─────────────────────────────────────────────────────────────
    "07_STOCK": {
        "Nombre para mostrar":     "CODI DESCRIPCIO ARTICLE",
        "Coste promedio":          "PREU COST UNITARI ARTICLE",
        "Valor total":             "VALOR TOTAL ARTICLE EN MAGATZEM",
        "Cantidad real":           "NUMERO REAL UNITATS ARTICLE",
        "Cantidad disponible":     "NUMERO DISPONIBLE UNITATS ARTICLE",
        "Entrante":                "NUMERO UNITATS ARTICLES PENDENTS ENTRADA",
        "Saliente":                "NUMERO UNITATS ARTICLES PENDENTS SORTIDA",
    },
    # ── 08_HISTORIAL_ENTRADES_SORTIDES ───────────────────────────────────────
    "08_HISTORIAL_ENTRADES_SORTIDES": {
        "Producto":                "CODI DESCRIPCIO ARTICLE",
        "Fecha":                   "DATA OPERACIO ENTRADA-SORTIDA",
        "Referencia":              "CODI ODOO RECEPCIO - ENTREGA",
        "Desde":                   "ORIGEN ARTICLES",
        "A":                       "DESTI ARTICLES",
        "Cantidad":                "NUMERO UNITATS OPERACIO",
        "Estado":                  "ESTAT OPERACIO",
    },
    # ── DADES_REFERENCIA_COMPRA ──────────────────────────────────────────────
    "DADES_REFERENCIA_COMPRA": {
        "Expedient":               "REF. EXPEDIENT COMPRA",
        "R_EMPRESA_C":             "REF. EMPRESA ALUMNE COMPRA",
        "R_PROVEEDOR_C":           "REF. PROVEÏDOR",
        "R_FECHA_EMISION_C":       "REF. DATA EMISSIÓ COMANDA COMPRA",
        "R_NUMERO_CP":             "REF. NUMERO EMISSIO COMANDA COMPRA",
        "R_NUMERO_CA":             "REF. NUMERO EMISSIO ALBARA COMPRA",
        "R_NUMERO_CF":             "REF. NUMERO EMISSIO FACTURA COMPRA",
        "R_IMPORTE_C":             "REF. IMPORT TOTAL COMPRA",
    },
    # ── DADES_REFERENCIA_VENDA ───────────────────────────────────────────────
    "DADES_REFERENCIA_VENDA": {
        "Expedient":               "REF. EXPEDIENT VENDA",
        "R_EMPRESA_V":             "REF. EMPRESA ALUMNE VENDA",
        "R_FECHA_EMISION_VP":      "REF. DATA EMISSIÓ COMANDA VENDA",
        "R_NUMERO_VP":             "REF. NUMERO EMISSIO COMANDA VENDA",
        "R_CLIENTE_V":             "REF. CLIENT",
        "R_IMPORTE_V":             "REF. IMPORT TOTAL VENDA",
        "R_FECHA_MAX_FACTURACION_V": "REF. DATA LIMIT FACTURACIO",
    },
}


def alias_camp(camp: str, llistat: str = "") -> str:
    """Retorna l'àlies de visualització d'un camp donat el seu nom intern.

    Si s'especifica `llistat`, cerca primer dins el llistat concret (desambigua
    camps homònims com 'Estado' o 'Referencia' que apareixen a múltiples llistats).
    Si no troba coincidència, retorna el nom original sense modificar.

    Exemples:
        alias_camp("Referencia del pedido", "01_COMANDES_COMPRES")
        → "CODI ODOO COMANDA COMPRA"

        alias_camp("Estado", "02_RECEPCIONS")
        → "ESTAT RECEPCIÓ"

        alias_camp("camp_desconegut")
        → "camp_desconegut"
    """
    if llistat and llistat in ALIASES_CAMPS:
        resultat = ALIASES_CAMPS[llistat].get(camp)
        if resultat:
            return resultat
    # Cerca global (sense llistat especificat o no trobat al llistat concret)
    for mapa in ALIASES_CAMPS.values():
        if camp in mapa:
            return mapa[camp]
    return camp


PENALITZACIONS_DEFAULT: dict = {
    "operacio_falta":           1.0,
    "operacio_sobrant":         1.0,
    "proveidor_client_incorrecte": 1.0,
    "import_incorrecte":        1.0,
    "quantitat_incorrecta":     1.0,
    "factura_anticipada":       1.0,
    "estoc_negatiu":            1.0,
    "data_incorrecta":          0.5,
    "numero_incorrecte":        0.5,
    "estat_incorrecte":         0.5,
}
