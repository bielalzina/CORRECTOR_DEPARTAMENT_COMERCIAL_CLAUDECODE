"""Correcció dels llistats 07_STOCK i 08_HISTORIAL_ENTRADES_SORTIDES."""

from typing import Optional

import pandas as pd

from modules.utils import (
    norm_str, to_float, fer_error, PENALITZACIONS_DEFAULT,
)

STOCK_MAX = 1000.0
MGZ_STOCK = "mgz01/stock"


def corregir_magatzem(
    df07: Optional[pd.DataFrame],
    df08: Optional[pd.DataFrame],
    penalitzacions: Optional[dict] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Corregeix els llistats 07 i 08 d'un alumne.
    Retorna (errors, casos_ambigus).
    """
    p = {**PENALITZACIONS_DEFAULT, **(penalitzacions or {})}
    errors: list[dict] = []
    ambigus: list[dict] = []  # magatzem no genera casos ambigus per ara

    # ── Llistat 07: STOCK ────────────────────────────────────────────────────
    if df07 is None:
        errors.append(fer_error(
            "07_STOCK", "operacio_falta", "molt_greu", p["operacio_falta"],
            "Llistat 07 (Stock) no entregat",
        ))
    else:
        errors.extend(_corregir_stock(df07, p))

    # ── Llistat 08: HISTORIAL ─────────────────────────────────────────────────
    if df08 is None:
        errors.append(fer_error(
            "08_HISTORIAL_ENTRADES_SORTIDES", "operacio_falta", "molt_greu",
            p["operacio_falta"],
            "Llistat 08 (Historial) no entregat",
        ))
    else:
        errors.extend(_corregir_historial(df08, p))

    return errors, ambigus


def _corregir_stock(df: pd.DataFrame, p: dict) -> list[dict]:
    errors = []

    # Valor total del magatzem <= 1000 €
    valors = [to_float(v) for v in df["Valor total"].dropna() if to_float(v) is not None]
    total_stock = sum(valors)
    if total_stock > STOCK_MAX:
        errors.append(fer_error(
            "07_STOCK", "import_incorrecte", "greu", p["import_incorrecte"],
            f"Valor total del magatzem supera els {STOCK_MAX:.0f} €",
            "Valor total",
            f"{total_stock:.2f} €", f"<= {STOCK_MAX:.0f} €",
        ))

    # Cantidad real = Cantidad disponible (no ha d'haver-hi moviments pendents)
    for _, row in df.iterrows():
        producte = str(row.get("Nombre para mostrar", ""))
        qty_real = to_float(row.get("Cantidad real"))
        qty_disp = to_float(row.get("Cantidad disponible"))
        entrante = to_float(row.get("Entrante")) or 0.0
        saliente = to_float(row.get("Saliente")) or 0.0

        if qty_real is not None and qty_disp is not None:
            if abs(qty_real - qty_disp) > 0.001:
                errors.append(fer_error(
                    "07_STOCK", "quantitat_incorrecta", "greu", p["quantitat_incorrecta"],
                    f"Moviments pendents al producte '{producte}': "
                    f"Cantidad real ({qty_real}) ≠ Cantidad disponible ({qty_disp})",
                    "Cantidad real / Cantidad disponible",
                    f"real={qty_real}, disp={qty_disp}",
                    "real = disponible (sense pendents)",
                    producte,
                ))

        if abs(entrante) > 0.001:
            errors.append(fer_error(
                "07_STOCK", "quantitat_incorrecta", "greu", p["quantitat_incorrecta"],
                f"Producte '{producte}' té entrades pendents (Entrante={entrante})",
                "Entrante", entrante, 0, producte,
            ))

        if abs(saliente) > 0.001:
            errors.append(fer_error(
                "07_STOCK", "quantitat_incorrecta", "greu", p["quantitat_incorrecta"],
                f"Producte '{producte}' té sortides pendents (Saliente={saliente})",
                "Saliente", saliente, 0, producte,
            ))

    return errors


def _corregir_historial(df: pd.DataFrame, p: dict) -> list[dict]:
    """
    Detecta estocs negatius en qualsevol moment de l'historial.
    Algoritme: ordena per empresa → producte → data; acumula quantitats.
    """
    errors = []

    # Filtrar únicament operacions confirmades
    df_fet = df[df["Estado"].apply(lambda v: norm_str(v) == "hecho")].copy()

    if df_fet.empty:
        return errors

    # Parsejar dates per ordenar
    import pandas as _pd
    df_fet = df_fet.copy()
    df_fet["_data_parsed"] = df_fet["Fecha"].apply(
        lambda v: _pd.to_datetime(str(v), dayfirst=True, errors="coerce")
    )
    df_fet = df_fet.sort_values(["Producto", "_data_parsed"]).reset_index(drop=True)

    # Acumular per producte
    estocs: dict[str, float] = {}

    for _, row in df_fet.iterrows():
        producte = str(row.get("Producto", "")).strip()
        if not producte or producte.lower() in ("nan", "none"):
            continue

        qty = to_float(row.get("Cantidad")) or 0.0
        desde = norm_str(row.get("Desde", ""))
        a = norm_str(row.get("A", ""))

        # Determinar signe: entrada si destí és MGZ, sortida si origen és MGZ
        if a and MGZ_STOCK in a:
            signe = 1  # entrada
        elif desde and MGZ_STOCK in desde:
            signe = -1  # sortida
        else:
            continue  # moviment intern que no afecta l'estoc de referència

        estocs[producte] = estocs.get(producte, 0.0) + signe * qty

        if estocs[producte] < -0.001:
            data_str = str(row.get("Fecha", ""))
            ref_str = str(row.get("Referencia", ""))
            errors.append(fer_error(
                "08_HISTORIAL_ENTRADES_SORTIDES", "estoc_negatiu", "greu",
                p["estoc_negatiu"],
                f"Estoc negatiu detectat al producte '{producte}' "
                f"(referència: {ref_str}, data: {data_str}). "
                f"Estoc acumulat: {estocs[producte]:.2f}",
                "Cantidad",
                f"{estocs[producte]:.2f}",
                ">= 0",
                producte,
            ))

    return errors
