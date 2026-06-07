"""Correcció dels llistats 01_COMANDES_COMPRES, 02_RECEPCIONS i 03_FACTURES_COMPRA."""

from datetime import timedelta
from typing import Optional

import pandas as pd

from modules.utils import (
    dates_iguals, imports_iguals, norm_str, parse_data, to_float,
    fer_error, fer_ambigu, detectar_duplicats, PENALITZACIONS_DEFAULT,
)


def corregir_compres(
    df01: Optional[pd.DataFrame],
    df02: Optional[pd.DataFrame],
    df03: Optional[pd.DataFrame],
    compres_ref: list[dict],
    penalitzacions: Optional[dict] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Corregeix els llistats 01, 02 i 03 d'un alumne.
    Rep els DataFrames ja carregats i les operacions de referència.
    Retorna (errors, casos_ambigus).
    """
    p = {**PENALITZACIONS_DEFAULT, **(penalitzacions or {})}
    errors: list[dict] = []
    ambigus: list[dict] = []

    # Detectar files duplicades als llistats de l'alumne per clau primària real
    if df01 is not None:
        errors.extend(detectar_duplicats(df01, "01_COMANDES_COMPRES",
                                         ["Referencia de proveedor"], p))
    if df02 is not None:
        errors.extend(detectar_duplicats(df02, "02_RECEPCIONS",
                                         ["Documento de origen"], p))
    if df03 is not None:
        errors.extend(detectar_duplicats(df03, "03_FACTURES_COMPRA",
                                         ["Número"], p))

    # Rastrejar claus primàries emparellades per detectar sobrants
    matched_cp: set[str] = set()           # Referencia de proveedor (01)
    matched_ca: set[str] = set()           # Documento de origen (02)
    matched_num03: set[str] = set()        # Número (03)

    for ref in compres_ref:
        desc_op = f"{ref['R_PROVEEDOR_C']} — {ref.get('R_FECHA_EMISION_C', '')}"

        # ── Llistat 01 ────────────────────────────────────────────────────────
        fila01, num_inferable = _match_01(df01, ref)
        if fila01 is not None:
            matched_cp.add(norm_str(fila01.get("Referencia de proveedor", "")))

        if fila01 is None:
            if df01 is not None:  # llistat pujat però operació no trobada
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "operacio_falta", "molt_greu",
                    p["operacio_falta"],
                    f"Operació que falta: comanda a {ref['R_PROVEEDOR_C']} "
                    f"del {ref.get('R_FECHA_EMISION_C', '')}",
                    operacio=desc_op,
                ))
        else:
            doc01 = str(fila01.get("Referencia del pedido") or "")
            if num_inferable:
                ambigus.append(fer_ambigu(
                    "01_COMANDES_COMPRES", "numero_inferable",
                    f"Número de comanda a proveïdor diferent del registre "
                    f"({ref['R_PROVEEDOR_C']}, {ref.get('R_FECHA_EMISION_C', '')}), "
                    "però l'operació és identificable per proveïdor i data",
                    fila01.get("Referencia de proveedor", ""),
                    ref["R_NUMERO_CP"],
                    p["numero_incorrecte"],
                ))
            else:
                if norm_str(fila01.get("Referencia de proveedor")) != norm_str(ref["R_NUMERO_CP"]):
                    errors.append(fer_error(
                        "01_COMANDES_COMPRES", "numero_incorrecte", "lleu",
                        p["numero_incorrecte"],
                        f"Número de comanda incorrecte ({ref['R_PROVEEDOR_C']})",
                        "Referencia de proveedor",
                        fila01.get("Referencia de proveedor"), ref["R_NUMERO_CP"], desc_op,
                        document=doc01,
                    ))

            # Data comanda
            if not dates_iguals(fila01.get("Data comanda"), ref["R_FECHA_EMISION_C"]):
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Data de comanda incorrecta ({ref['R_PROVEEDOR_C']})",
                    "Data comanda",
                    fila01.get("Data comanda"), ref["R_FECHA_EMISION_C"], desc_op,
                    document=doc01,
                ))

            # Proveïdor
            if norm_str(fila01.get("Proveedor")) != norm_str(ref["R_PROVEEDOR_C"]):
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "proveidor_client_incorrecte", "greu",
                    p["proveidor_client_incorrecte"],
                    "Proveïdor incorrecte a la comanda",
                    "Proveedor",
                    fila01.get("Proveedor"), ref["R_PROVEEDOR_C"], desc_op,
                    document=doc01,
                ))

            # Import
            if not imports_iguals(fila01.get("Total"), ref["R_IMPORTE_C"]):
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "import_incorrecte", "greu", p["import_incorrecte"],
                    f"Import incorrecte ({ref['R_PROVEEDOR_C']})",
                    "Total",
                    fila01.get("Total"), ref["R_IMPORTE_C"], desc_op,
                    document=doc01,
                ))

            # Estat
            if norm_str(fila01.get("Estado")) != "pedido de compra":
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Estat incorrecte ({ref['R_PROVEEDOR_C']}). Ha de ser 'Pedido de compra'",
                    "Estado",
                    fila01.get("Estado"), "Pedido de compra", desc_op,
                    document=doc01,
                ))

            # Estat de facturació (si tenim R_DATA_ENTREGA_TASCA)
            data_entrega = ref.get("R_DATA_ENTREGA_TASCA")
            if data_entrega:
                estat_fact_esp = (
                    "Totalmente facturado"
                    if data_entrega > ref["R_FECHA_EMISION_C"]
                    else "Facturas en espera"
                )
                if norm_str(fila01.get("Estado de facturación")) != norm_str(estat_fact_esp):
                    errors.append(fer_error(
                        "01_COMANDES_COMPRES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                        f"Estat de facturació incorrecte ({ref['R_PROVEEDOR_C']})",
                        "Estado de facturación",
                        fila01.get("Estado de facturación"), estat_fact_esp, desc_op,
                        document=doc01,
                    ))

            # Fecha límite >= Data comanda
            d_limit = parse_data(fila01.get("Fecha límite del pedido"))
            d_comanda = parse_data(fila01.get("Data comanda"))
            if d_limit and d_comanda and d_limit < d_comanda:
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Fecha límite anterior a la Data comanda ({ref['R_PROVEEDOR_C']})",
                    "Fecha límite del pedido",
                    fila01.get("Fecha límite del pedido"),
                    f">= {fila01.get('Data comanda', '')}",
                    desc_op,
                    document=doc01,
                ))

        # ── Llistat 02 ────────────────────────────────────────────────────────
        ref_pedido_01 = fila01.get("Referencia del pedido") if fila01 is not None else None
        fila02 = _match_02(df02, ref, ref_pedido_01)
        if fila02 is not None:
            matched_ca.add(norm_str(fila02.get("Documento de origen", "")))

        if fila02 is None:
            if df02 is not None:
                errors.append(fer_error(
                    "02_RECEPCIONS", "operacio_falta", "molt_greu", p["operacio_falta"],
                    f"Operació que falta: recepció de {ref['R_PROVEEDOR_C']} "
                    f"del {ref.get('R_FECHA_EMISION_C', '')}",
                    operacio=desc_op,
                ))
        else:
            doc02 = str(fila02.get("Referencia") or "")
            if norm_str(fila02.get("Numero albarà")) != norm_str(ref["R_NUMERO_CA"]):
                errors.append(fer_error(
                    "02_RECEPCIONS", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                    f"Número d'albarà incorrecte ({ref['R_PROVEEDOR_C']})",
                    "Numero albarà",
                    fila02.get("Numero albarà"), ref["R_NUMERO_CA"], desc_op,
                    document=doc02,
                ))

            if not dates_iguals(fila02.get("Data albarà"), ref["R_FECHA_EMISION_C"]):
                errors.append(fer_error(
                    "02_RECEPCIONS", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Data d'albarà incorrecta ({ref['R_PROVEEDOR_C']})",
                    "Data albarà",
                    fila02.get("Data albarà"), ref["R_FECHA_EMISION_C"], desc_op,
                    document=doc02,
                ))

            if norm_str(fila02.get("Contacto")) != norm_str(ref["R_PROVEEDOR_C"]):
                errors.append(fer_error(
                    "02_RECEPCIONS", "proveidor_client_incorrecte", "greu",
                    p["proveidor_client_incorrecte"],
                    "Contacte incorrecte a la recepció",
                    "Contacto",
                    fila02.get("Contacto"), ref["R_PROVEEDOR_C"], desc_op,
                    document=doc02,
                ))

            if not imports_iguals(fila02.get("Pedidos de compra/Total"), ref["R_IMPORTE_C"]):
                errors.append(fer_error(
                    "02_RECEPCIONS", "import_incorrecte", "greu", p["import_incorrecte"],
                    f"Import incorrecte a la recepció ({ref['R_PROVEEDOR_C']})",
                    "Pedidos de compra/Total",
                    fila02.get("Pedidos de compra/Total"), ref["R_IMPORTE_C"], desc_op,
                    document=doc02,
                ))

            estat02 = norm_str(fila02.get("Estado", ""))
            if estat02 == "listo":
                errors.append(fer_error(
                    "02_RECEPCIONS", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Recepció no realitzada (Listo) — {ref['R_PROVEEDOR_C']}",
                    "Estado", fila02.get("Estado"), "Hecho", desc_op,
                    document=doc02,
                ))
            elif estat02 not in ("hecho", "cancelado"):
                errors.append(fer_error(
                    "02_RECEPCIONS", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Estat de recepció incorrecte ({ref['R_PROVEEDOR_C']})",
                    "Estado", fila02.get("Estado"), "Hecho", desc_op,
                    document=doc02,
                ))

            # Traçabilitat 01→02
            if ref_pedido_01 and fila02 is not None:
                doc_origen = norm_str(fila02.get("Documento de origen"))
                if doc_origen and doc_origen != norm_str(ref_pedido_01):
                    errors.append(fer_error(
                        "02_RECEPCIONS", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                        f"Document d'origen no correspon a la comanda ({ref['R_PROVEEDOR_C']})",
                        "Documento de origen",
                        fila02.get("Documento de origen"), ref_pedido_01, desc_op,
                        document=doc02,
                    ))

            # Fecha de traslado >= Data albarà
            d_traslado = parse_data(fila02.get("Fecha de traslado"))
            d_albara = parse_data(fila02.get("Data albarà"))
            if d_traslado and d_albara and d_traslado < d_albara:
                errors.append(fer_error(
                    "02_RECEPCIONS", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Fecha de traslado anterior a Data albarà ({ref['R_PROVEEDOR_C']})",
                    "Fecha de traslado",
                    fila02.get("Fecha de traslado"),
                    f">= {fila02.get('Data albarà', '')}",
                    desc_op,
                    document=doc02,
                ))

        # ── Llistat 03 ────────────────────────────────────────────────────────
        fila03 = _match_03(df03, ref, ref_pedido_01)
        if fila03 is not None:
            matched_num03.add(norm_str(fila03.get("Número", "")))

        if fila03 is None:
            if df03 is not None:
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "operacio_falta", "molt_greu", p["operacio_falta"],
                    f"Operació que falta: factura de {ref['R_PROVEEDOR_C']} "
                    f"ref. {ref.get('R_NUMERO_CF', '')}",
                    operacio=desc_op,
                ))
        else:
            doc03 = str(fila03.get("Número") or "")
            # Error greu: factura registrada el dia de la comanda (no disponible)
            data_entrega = ref.get("R_DATA_ENTREGA_TASCA")
            if data_entrega and data_entrega <= ref["R_FECHA_EMISION_C"]:
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "factura_anticipada", "greu", p["factura_anticipada"],
                    f"Factura de {ref['R_PROVEEDOR_C']} registrada el dia de la comanda "
                    "(no disponible fins l'endemà)",
                    "Fecha de factura",
                    fila03.get("Fecha de factura"),
                    f"> {ref['R_FECHA_EMISION_C']}",
                    desc_op,
                    document=doc03,
                ))

            if norm_str(fila03.get("Nombre de la empresa a mostrar en la factura")) \
                    != norm_str(ref["R_PROVEEDOR_C"]):
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "proveidor_client_incorrecte", "greu",
                    p["proveidor_client_incorrecte"],
                    "Nom d'empresa incorrecte a la factura de compra",
                    "Nombre de la empresa a mostrar en la factura",
                    fila03.get("Nombre de la empresa a mostrar en la factura"),
                    ref["R_PROVEEDOR_C"], desc_op,
                    document=doc03,
                ))

            if norm_str(fila03.get("Referencia")) != norm_str(ref["R_NUMERO_CF"]):
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                    f"Referència de factura incorrecta ({ref['R_PROVEEDOR_C']})",
                    "Referencia",
                    fila03.get("Referencia"), ref["R_NUMERO_CF"], desc_op,
                    document=doc03,
                ))

            if not dates_iguals(fila03.get("Fecha de factura"), ref["R_FECHA_EMISION_C"]):
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Data de factura incorrecta ({ref['R_PROVEEDOR_C']})",
                    "Fecha de factura",
                    fila03.get("Fecha de factura"), ref["R_FECHA_EMISION_C"], desc_op,
                    document=doc03,
                ))

            # Venciment = data factura + 7 dies
            d_fact = parse_data(fila03.get("Fecha de factura"))
            if d_fact:
                d_venc_esp = d_fact + timedelta(days=7)
                if not dates_iguals(fila03.get("Fecha de vencimiento"), d_venc_esp.isoformat()):
                    errors.append(fer_error(
                        "03_FACTURES_COMPRA", "data_incorrecta", "lleu", p["data_incorrecta"],
                        f"Data de venciment incorrecta ({ref['R_PROVEEDOR_C']})",
                        "Fecha de vencimiento",
                        fila03.get("Fecha de vencimiento"), d_venc_esp.isoformat(), desc_op,
                        document=doc03,
                    ))

            # Import (ODOO dóna negatiu → convertir a positiu)
            import_f03 = to_float(fila03.get("Total con signo en moneda"))
            if import_f03 is not None:
                if not imports_iguals(abs(import_f03), ref["R_IMPORTE_C"]):
                    errors.append(fer_error(
                        "03_FACTURES_COMPRA", "import_incorrecte", "greu", p["import_incorrecte"],
                        f"Import incorrecte a la factura de {ref['R_PROVEEDOR_C']}",
                        "Total con signo en moneda",
                        import_f03, ref["R_IMPORTE_C"], desc_op,
                        document=doc03,
                    ))

            estat03 = norm_str(fila03.get("Estado en pago", ""))
            if estat03 not in ("publicado", "pagada"):
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Estat de pagament incorrecte ({ref['R_PROVEEDOR_C']})",
                    "Estado en pago",
                    fila03.get("Estado en pago"), "Publicado / Pagada", desc_op,
                    document=doc03,
                ))

    # Detectar operacions sobrants (registrades per l'alumne però no esperades)
    if df01 is not None and compres_ref:
        for _, row in df01.iterrows():
            cp = norm_str(row.get("Referencia de proveedor", ""))
            if cp in ("", "nan", "none"):
                continue
            if cp not in matched_cp:
                errors.append(fer_error(
                    "01_COMANDES_COMPRES", "operacio_sobrant", "molt_greu",
                    p.get("operacio_sobrant", p["operacio_falta"]),
                    f"Operació no esperada: comanda {cp} "
                    f"({row.get('Proveedor', '')}) no figura a les dades de referència",
                    document=str(row.get("Referencia del pedido", "")),
                ))
    if df02 is not None and compres_ref:
        for _, row in df02.iterrows():
            doc_origen = norm_str(row.get("Documento de origen", ""))
            if doc_origen in ("", "nan", "none"):
                continue
            if doc_origen not in matched_ca:
                errors.append(fer_error(
                    "02_RECEPCIONS", "operacio_sobrant", "molt_greu",
                    p.get("operacio_sobrant", p["operacio_falta"]),
                    f"Operació no esperada: recepció amb origen {doc_origen} "
                    "no figura a les dades de referència",
                    document=str(row.get("Referencia", "")),
                ))
    if df03 is not None and compres_ref:
        for _, row in df03.iterrows():
            num3 = norm_str(row.get("Número", ""))
            if num3 in ("", "nan", "none"):
                continue
            if num3 not in matched_num03:
                errors.append(fer_error(
                    "03_FACTURES_COMPRA", "operacio_sobrant", "molt_greu",
                    p.get("operacio_sobrant", p["operacio_falta"]),
                    f"Operació no esperada: factura {row.get('Número', '')} "
                    f"({row.get('Nombre de la empresa a mostrar en la factura', '')}) "
                    "no figura a les dades de referència",
                    document=str(row.get("Número", "")),
                ))

    # Llistats completament absents
    if df01 is None:
        errors.append(fer_error(
            "01_COMANDES_COMPRES", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(compres_ref),
            f"Llistat 01 no entregat — {len(compres_ref)} operació(ons) sense corregir",
        ))
    if df02 is None:
        errors.append(fer_error(
            "02_RECEPCIONS", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(compres_ref),
            f"Llistat 02 no entregat — {len(compres_ref)} operació(ons) sense corregir",
        ))
    if df03 is None:
        errors.append(fer_error(
            "03_FACTURES_COMPRA", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(compres_ref),
            f"Llistat 03 no entregat — {len(compres_ref)} operació(ons) sense corregir",
        ))

    return errors, ambigus


# ── Funcions de matching ──────────────────────────────────────────────────────

def _match_01(df: Optional[pd.DataFrame], ref: dict) -> tuple[Optional[dict], bool]:
    """
    Cerca la fila de llistat 01 que correspon a l'operació ref.
    Retorna (fila, num_inferable): fila=None si no trobada.
    num_inferable=True si s'ha trobat per proveïdor+data però no per número.
    """
    if df is None or df.empty:
        return None, False

    # Intent 1: per número CP + proveïdor (exacte)
    for _, row in df.iterrows():
        if (norm_str(row.get("Referencia de proveedor")) == norm_str(ref["R_NUMERO_CP"])
                and norm_str(row.get("Proveedor")) == norm_str(ref["R_PROVEEDOR_C"])):
            return row.to_dict(), False

    # Intent 2: per proveïdor + data (número potencialment erroni → ambigu)
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Proveedor")) == norm_str(ref["R_PROVEEDOR_C"])
            and dates_iguals(row.get("Data comanda"), ref["R_FECHA_EMISION_C"]))
    ]
    if len(candidates) == 1:
        return candidates[0].to_dict(), True  # inferable
    if len(candidates) > 1:
        return candidates[0].to_dict(), True  # multiple → agafem el primer, cas ambigu

    # Intent 3: proveïdor + import (data incorrecta)
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Proveedor")) == norm_str(ref["R_PROVEEDOR_C"])
            and imports_iguals(row.get("Total"), ref["R_IMPORTE_C"]))
    ]
    if len(candidates) == 1:
        return candidates[0].to_dict(), True

    return None, False


def _match_02(
    df: Optional[pd.DataFrame],
    ref: dict,
    ref_pedido_01: Optional[str],
) -> Optional[dict]:
    """Cerca la fila de llistat 02 que correspon a l'operació ref."""
    if df is None or df.empty:
        return None

    # Intent 1: per Documento de origen = Referencia del pedido de llistat 01
    if ref_pedido_01:
        for _, row in df.iterrows():
            if norm_str(row.get("Documento de origen")) == norm_str(ref_pedido_01):
                return row.to_dict()

    # Intent 2: per proveïdor + data
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Contacto")) == norm_str(ref["R_PROVEEDOR_C"])
            and dates_iguals(row.get("Data albarà"), ref["R_FECHA_EMISION_C"]))
    ]
    if candidates:
        return candidates[0].to_dict()

    # Intent 3: proveïdor + import
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Contacto")) == norm_str(ref["R_PROVEEDOR_C"])
            and imports_iguals(row.get("Pedidos de compra/Total"), ref["R_IMPORTE_C"]))
    ]
    if candidates:
        return candidates[0].to_dict()

    return None


def _match_03(
    df: Optional[pd.DataFrame],
    ref: dict,
    ref_pedido_01: Optional[str],
) -> Optional[dict]:
    """Cerca la fila de llistat 03 que correspon a l'operació ref.

    Traçabilitat única: factura.Origen == ref_pedido_01 (referència interna ODOO de la comanda).
    Si no hi ha coincidència, la factura no existeix (operació que falta).
    No s'usen fallbacks: qualsevol intent addicional pot generar falsos positius.
    """
    if df is None or df.empty or not ref_pedido_01:
        return None

    for _, row in df.iterrows():
        if norm_str(row.get("Origen")) == norm_str(ref_pedido_01):
            return row.to_dict()

    return None


