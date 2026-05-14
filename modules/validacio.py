"""Pas 1: validació d'estructura dels fitxers xlsx pujats pels alumnes."""

import io
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

CAPCALERES_REQUERIDES: dict[str, list[str]] = {
    "01_COMANDES_COMPRES": [
        "Referencia del pedido", "Fecha límite del pedido", "Referencia de proveedor",
        "Data comanda", "Proveedor", "Base imponible", "Total",
        "Estado", "Estado de facturación",
    ],
    "02_RECEPCIONS": [
        "Referencia", "Fecha de traslado", "Numero albarà", "Data albarà",
        "Contacto", "Documento de origen", "Pedidos de compra/Total", "Estado",
    ],
    "03_FACTURES_COMPRA": [
        "Número", "Nombre de la empresa a mostrar en la factura", "Referencia",
        "Fecha de factura", "Fecha de vencimiento", "Origen",
        "Base imponible en la moneda firmada", "Impuesto firmado",
        "Total con signo en moneda", "Estado en pago",
    ],
    "04_COMANDES_VENDES": [
        "Referencia del pedido", "Fecha de creación", "Data comanda", "Numero comanda",
        "Cliente", "Base imponible", "Impuestos", "Total",
        "Estado", "Estado de la factura",
    ],
    "05_ENTREGUES": [
        "Referencia", "Fecha de traslado", "Contacto", "Documento de origen",
        "Pedido de venta/Total", "Estado",
    ],
    "06_FACTURES_VENDA": [
        "Número", "Fecha de factura", "Fecha de vencimiento",
        "Nombre de la empresa a mostrar en la factura", "Origen",
        "Base imponible en la moneda firmada", "Impuesto firmado",
        "Total con signo en moneda", "Estado en pago", "Enviado",
    ],
    "07_STOCK": [
        "Nombre para mostrar", "Coste promedio", "Valor total",
        "Cantidad real", "Cantidad disponible", "Entrante", "Saliente",
    ],
    "08_HISTORIAL_ENTRADES_SORTIDES": [
        "Producto", "Fecha", "Referencia", "Desde", "A", "Cantidad", "Estado",
    ],
}

# Mínim de files de dades (sense la capçalera) esperades per tipus
MIN_FILES: dict[str, int] = {
    "01_COMANDES_COMPRES": 2,
    "02_RECEPCIONS": 2,
    "03_FACTURES_COMPRA": 2,
    "04_COMANDES_VENDES": 3,
    "05_ENTREGUES": 3,
    "06_FACTURES_VENDA": 3,
    "07_STOCK": 1,
    "08_HISTORIAL_ENTRADES_SORTIDES": 1,
}

NOMS_LLISTATS: dict[str, str] = {
    "01_COMANDES_COMPRES": "01 — Comandes de compres",
    "02_RECEPCIONS": "02 — Recepcions (albarans de compra)",
    "03_FACTURES_COMPRA": "03 — Factures de compra",
    "04_COMANDES_VENDES": "04 — Comandes de vendes",
    "05_ENTREGUES": "05 — Entregues (albarans de venda)",
    "06_FACTURES_VENDA": "06 — Factures de venda",
    "07_STOCK": "07 — Stock",
    "08_HISTORIAL_ENTRADES_SORTIDES": "08 — Historial d'entrades i sortides",
}


@dataclass
class ResultatValidacio:
    valid: bool
    tipus: Optional[str]
    errors: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    df: Optional[pd.DataFrame] = None


def validar_estructura(contingut: bytes, nom_fitxer: str) -> ResultatValidacio:
    """Valida l'estructura d'un fitxer xlsx. Retorna errors concrets."""
    try:
        df = pd.read_excel(io.BytesIO(contingut), dtype=str)
    except Exception as e:
        return ResultatValidacio(
            valid=False,
            tipus=None,
            errors=[f"No s'ha pogut llegir el fitxer Excel: {e}"],
        )

    df.columns = [str(c).strip() for c in df.columns]

    tipus = _detectar_tipus(df)
    if tipus is None:
        parcial = _millor_coincidencia_parcial(df)
        msg = "No s'ha pogut identificar el tipus de llistat per les capçaleres del fitxer."
        if parcial:
            tipus_prob, manquen = parcial
            msg += (
                f" Sembla un {NOMS_LLISTATS[tipus_prob]}, "
                f"però manquen les columnes: {', '.join(repr(c) for c in manquen)}."
            )
        return ResultatValidacio(valid=False, tipus=None, errors=[msg])

    errors: list[str] = []
    avisos: list[str] = []
    requerides = CAPCALERES_REQUERIDES[tipus]

    # Eliminar files completament buides i detectar si n'hi ha al mig
    idx_primera_buida_intermedia = _primera_fila_buida_intermedia(df)
    df = df.dropna(how="all").reset_index(drop=True)
    if idx_primera_buida_intermedia is not None:
        errors.append(
            f"Hi ha files buides intercalades entre les dades "
            f"(primera a la fila {idx_primera_buida_intermedia + 2}, comptant des de la capçalera)."
        )

    # Columnes obligatòries completament buides
    for col in requerides:
        if col in df.columns and df[col].isna().all():
            errors.append(f"La columna '{col}' està completament buida.")

    # Mínim de files
    min_f = MIN_FILES.get(tipus, 1)
    if len(df) < min_f:
        errors.append(
            f"El llistat té {len(df)} fila(es) de dades, però el mínim esperat és {min_f}."
        )

    # Detecció d'esborranys
    if "Estado" in df.columns:
        n_esborrany = df["Estado"].isin(["Borrador", "Presupuesto"]).sum()
        if n_esborrany > 0:
            avisos.append(
                f"Atenció: {n_esborrany} fila(es) amb estat 'Borrador' o 'Presupuesto'. "
                "Confirma tots els documents a ODOO abans de lliurar."
            )

    valid = len(errors) == 0
    return ResultatValidacio(
        valid=valid,
        tipus=tipus,
        errors=errors,
        avisos=avisos,
        df=df if valid else None,
    )


def _detectar_tipus(df: pd.DataFrame) -> Optional[str]:
    """Retorna el tipus del llistat si TOTES les capçaleres requerides hi són."""
    cols = set(df.columns.tolist())
    millor_tipus = None
    millor_score = -1
    for tipus, requerides in CAPCALERES_REQUERIDES.items():
        if all(c in cols for c in requerides):
            score = len(requerides)
            if score > millor_score:
                millor_score = score
                millor_tipus = tipus
    return millor_tipus


def _millor_coincidencia_parcial(df: pd.DataFrame) -> Optional[tuple[str, list[str]]]:
    """Per a fitxers no identificables, retorna el tipus més probable i les columnes que manquen."""
    cols = set(df.columns.tolist())
    millor = None
    millor_score = -1
    for tipus, requerides in CAPCALERES_REQUERIDES.items():
        score = sum(1 for c in requerides if c in cols)
        if score > millor_score:
            millor_score = score
            millor = (tipus, [c for c in requerides if c not in cols])
    return millor if millor and millor_score > 0 else None


def _primera_fila_buida_intermedia(df: pd.DataFrame) -> Optional[int]:
    """Índex de la primera fila buida que no és al final del DataFrame."""
    last_data = next(
        (i for i in range(len(df) - 1, -1, -1) if not df.iloc[i].isna().all()),
        None,
    )
    if last_data is None:
        return None
    return next(
        (i for i in range(last_data) if df.iloc[i].isna().all()),
        None,
    )
