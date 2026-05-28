"""Correcció dels llistats 04_COMANDES_VENDES, 05_ENTREGUES i 06_FACTURES_VENDA."""

import re
from datetime import timedelta
from typing import Optional

import pandas as pd

from modules.utils import (
    dates_iguals, imports_iguals, norm_str, parse_data, to_float,
    fer_error, fer_ambigu, detectar_duplicats, PENALITZACIONS_DEFAULT,
)


def corregir_vendes(
    df04: Optional[pd.DataFrame],
    df05: Optional[pd.DataFrame],
    df06: Optional[pd.DataFrame],
    vendes_ref: list[dict],
    data_inici_recap: Optional[str],
    penalitzacions: Optional[dict] = None,
) -> tuple[list[dict], list[dict]]:
    """
    Corregeix els llistats 04, 05 i 06 d'un alumne.
    data_inici_recap: data ISO a partir de la qual s'aplica facturació recapitulativa (o None).
    Retorna (errors, casos_ambigus).
    """
    p = {**PENALITZACIONS_DEFAULT, **(penalitzacions or {})}
    errors: list[dict] = []
    ambigus: list[dict] = []

    # Separar operacions per mode de facturació
    vendes_indiv = [
        v for v in vendes_ref
        if not data_inici_recap or v["R_FECHA_EMISION_VP"] < data_inici_recap
    ]
    vendes_recap = [
        v for v in vendes_ref
        if data_inici_recap and v["R_FECHA_EMISION_VP"] >= data_inici_recap
    ]

    # Detectar files duplicades als llistats de l'alumne per clau primària real
    if df04 is not None:
        errors.extend(detectar_duplicats(df04, "04_COMANDES_VENDES",
                                         ["Referencia del pedido"], p))
    if df05 is not None:
        errors.extend(detectar_duplicats(df05, "05_ENTREGUES",
                                         ["Referencia"], p))
    if df06 is not None:
        errors.extend(detectar_duplicats(df06, "06_FACTURES_VENDA",
                                         ["Número"], p))

    # ── Llistats absents ──────────────────────────────────────────────────────
    if df04 is None:
        errors.append(fer_error(
            "04_COMANDES_VENDES", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(vendes_ref),
            f"Llistat 04 no entregat — {len(vendes_ref)} operació(ons) sense corregir",
        ))
    if df05 is None:
        errors.append(fer_error(
            "05_ENTREGUES", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(vendes_ref),
            f"Llistat 05 no entregat — {len(vendes_ref)} operació(ons) sense corregir",
        ))
    if df06 is None:
        errors.append(fer_error(
            "06_FACTURES_VENDA", "operacio_falta", "molt_greu",
            p["operacio_falta"] * len(vendes_ref),
            f"Llistat 06 no entregat — {len(vendes_ref)} operació(ons) sense corregir",
        ))
    if df04 is None or df05 is None or df06 is None:
        return errors, ambigus

    # ── Facturació individual ─────────────────────────────────────────────────
    for ref in vendes_indiv:
        desc_op = f"{ref['R_CLIENTE_V']} — {ref.get('R_FECHA_EMISION_VP', '')}"

        fila04, num_inferable = _match_04(df04, ref)

        if fila04 is None:
            errors.append(fer_error(
                "04_COMANDES_VENDES", "operacio_falta", "molt_greu", p["operacio_falta"],
                f"Operació que falta: comanda de {ref['R_CLIENTE_V']} "
                f"del {ref.get('R_FECHA_EMISION_VP', '')}",
                operacio=desc_op,
            ))
        else:
            doc04 = str(fila04.get("Referencia del pedido") or "")
            if num_inferable:
                ambigus.append(fer_ambigu(
                    "04_COMANDES_VENDES", "numero_inferable",
                    f"Número de comanda diferent del registre ({ref['R_CLIENTE_V']}, "
                    f"{ref.get('R_FECHA_EMISION_VP', '')}), però l'operació és identificable",
                    fila04.get("Numero comanda", ""), ref["R_NUMERO_VP"],
                    p["numero_incorrecte"],
                ))
            else:
                if norm_str(fila04.get("Numero comanda")) != norm_str(ref["R_NUMERO_VP"]):
                    errors.append(fer_error(
                        "04_COMANDES_VENDES", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                        f"Número de comanda incorrecte ({ref['R_CLIENTE_V']})",
                        "Numero comanda",
                        fila04.get("Numero comanda"), ref["R_NUMERO_VP"], desc_op,
                        document=doc04,
                    ))

            if not dates_iguals(fila04.get("Data comanda"), ref["R_FECHA_EMISION_VP"]):
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Data de comanda incorrecta ({ref['R_CLIENTE_V']})",
                    "Data comanda",
                    fila04.get("Data comanda"), ref["R_FECHA_EMISION_VP"], desc_op,
                    document=doc04,
                ))

            if norm_str(fila04.get("Cliente")) != norm_str(ref["R_CLIENTE_V"]):
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "proveidor_client_incorrecte", "greu",
                    p["proveidor_client_incorrecte"],
                    "Client incorrecte a la comanda de venda",
                    "Cliente",
                    fila04.get("Cliente"), ref["R_CLIENTE_V"], desc_op,
                    document=doc04,
                ))

            if not imports_iguals(fila04.get("Total"), ref["R_IMPORTE_V"]):
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "import_incorrecte", "greu", p["import_incorrecte"],
                    f"Import incorrecte ({ref['R_CLIENTE_V']})",
                    "Total",
                    fila04.get("Total"), ref["R_IMPORTE_V"], desc_op,
                    document=doc04,
                ))

            if norm_str(fila04.get("Estado")) != "pedido de venta":
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Estat incorrecte ({ref['R_CLIENTE_V']}). Ha de ser 'Pedido de venta'",
                    "Estado",
                    fila04.get("Estado"), "Pedido de venta", desc_op,
                    document=doc04,
                ))

            if norm_str(fila04.get("Estado de la factura")) != "completamente facturado":
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Estat de factura incorrecte ({ref['R_CLIENTE_V']})",
                    "Estado de la factura",
                    fila04.get("Estado de la factura"), "Completamente facturado", desc_op,
                    document=doc04,
                ))

        # Llistat 05
        ref_pedido_04 = fila04.get("Referencia del pedido") if fila04 else None
        fila05 = _match_05(df05, ref, ref_pedido_04)

        if fila05 is None:
            errors.append(fer_error(
                "05_ENTREGUES", "operacio_falta", "molt_greu", p["operacio_falta"],
                f"Operació que falta: entrega a {ref['R_CLIENTE_V']} "
                f"del {ref.get('R_FECHA_EMISION_VP', '')}",
                operacio=desc_op,
            ))
        else:
            doc05 = str(fila05.get("Referencia") or "")
            if norm_str(fila05.get("Contacto")) != norm_str(ref["R_CLIENTE_V"]):
                errors.append(fer_error(
                    "05_ENTREGUES", "proveidor_client_incorrecte", "greu",
                    p["proveidor_client_incorrecte"],
                    "Client incorrecte a l'entrega",
                    "Contacto", fila05.get("Contacto"), ref["R_CLIENTE_V"], desc_op,
                    document=doc05,
                ))

            if not imports_iguals(fila05.get("Pedido de venta/Total"), ref["R_IMPORTE_V"]):
                errors.append(fer_error(
                    "05_ENTREGUES", "import_incorrecte", "greu", p["import_incorrecte"],
                    f"Import incorrecte a l'entrega ({ref['R_CLIENTE_V']})",
                    "Pedido de venta/Total",
                    fila05.get("Pedido de venta/Total"), ref["R_IMPORTE_V"], desc_op,
                    document=doc05,
                ))

            if norm_str(fila05.get("Estado")) != "hecho":
                errors.append(fer_error(
                    "05_ENTREGUES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                    f"Entrega no realitzada ({ref['R_CLIENTE_V']}). Ha de ser 'Hecho'",
                    "Estado", fila05.get("Estado"), "Hecho", desc_op,
                    document=doc05,
                ))

            # Traçabilitat 04→05
            if ref_pedido_04:
                doc_origen = norm_str(fila05.get("Documento de origen"))
                if doc_origen and doc_origen != norm_str(ref_pedido_04):
                    errors.append(fer_error(
                        "05_ENTREGUES", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                        f"Document d'origen no correspon a la comanda ({ref['R_CLIENTE_V']})",
                        "Documento de origen",
                        fila05.get("Documento de origen"), ref_pedido_04, desc_op,
                        document=doc05,
                    ))

        # Llistat 06 — facturació individual
        ref_pedido_04_val = fila04.get("Referencia del pedido") if fila04 else None
        fila06 = _match_06_individual(df06, ref, ref_pedido_04_val)

        if fila06 is None:
            errors.append(fer_error(
                "06_FACTURES_VENDA", "operacio_falta", "molt_greu", p["operacio_falta"],
                f"Operació que falta: factura de venda a {ref['R_CLIENTE_V']}",
                operacio=desc_op,
            ))
        else:
            doc06 = str(fila06.get("Número") or "")
            _verificar_factura_venda(fila06, ref, p, errors, desc_op, recap=False,
                                     document=doc06)

        # Seqüència dates 04→05→06
        if fila04 and fila05 and fila06:
            doc04_seq = str(fila04.get("Referencia del pedido") or "")
            doc05_seq = str(fila05.get("Referencia") or "")
            doc06_seq = str(fila06.get("Número") or "")
            d_creacio = parse_data(fila04.get("Fecha de creación"))
            d_traslado = parse_data(fila05.get("Fecha de traslado"))
            d_factura = parse_data(fila06.get("Fecha de factura"))
            if d_creacio and d_traslado and d_traslado < d_creacio:
                errors.append(fer_error(
                    "05_ENTREGUES", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Fecha de traslado anterior a Fecha de creación ({ref['R_CLIENTE_V']})",
                    "Fecha de traslado", fila05.get("Fecha de traslado"),
                    f">= {fila04.get('Fecha de creación', '')}", desc_op,
                    document=doc05_seq,
                ))
            if d_traslado and d_factura and d_factura < d_traslado:
                errors.append(fer_error(
                    "06_FACTURES_VENDA", "data_incorrecta", "lleu", p["data_incorrecta"],
                    f"Fecha de factura anterior a Fecha de traslado ({ref['R_CLIENTE_V']})",
                    "Fecha de factura", fila06.get("Fecha de factura"),
                    f">= {fila05.get('Fecha de traslado', '')}", desc_op,
                    document=doc06_seq,
                ))

    # ── Facturació recapitulativa ─────────────────────────────────────────────
    if vendes_recap:
        e, a = _corregir_recap(df04, df05, df06, vendes_recap, p)
        errors.extend(e)
        ambigus.extend(a)

    # ── Seqüència numeració FV (llistat 06 sencer) ───────────────────────────
    if df06 is not None and not df06.empty:
        errors.extend(_verificar_sequencia_fv(df06, p))

    return errors, ambigus


def _corregir_recap(
    df04: pd.DataFrame,
    df05: pd.DataFrame,
    df06: pd.DataFrame,
    vendes_recap: list[dict],
    p: dict,
) -> tuple[list[dict], list[dict]]:
    """Corregeix la part recapitulativa: agrupa per client+setmana."""
    errors: list[dict] = []
    ambigus: list[dict] = []

    # Agrupar vendes de referència per client + data màxima facturació (divendres setmana)
    grups: dict[tuple, list[dict]] = {}
    for ref in vendes_recap:
        clau = (ref["R_CLIENTE_V"], ref["R_FECHA_MAX_FACTURACION_V"])
        grups.setdefault(clau, []).append(ref)

    for (client, data_max), refs_grup in grups.items():
        desc_op = f"{client} — setmana fins {data_max}"
        import_total_esp = sum(r["R_IMPORTE_V"] for r in refs_grup if r["R_IMPORTE_V"])

        # Verificar llistat 04: cada operació individual
        # Recollim les Referencia del pedido reals trobades a df04 per usar-les a _match_06_recap
        refs_pedido_04: list[str] = []
        for ref in refs_grup:
            fila04, num_inferable = _match_04(df04, ref)
            sub_desc = f"{client} — {ref.get('R_FECHA_EMISION_VP', '')}"

            if fila04 is None:
                errors.append(fer_error(
                    "04_COMANDES_VENDES", "operacio_falta", "molt_greu", p["operacio_falta"],
                    f"Operació que falta: comanda de {client} del {ref.get('R_FECHA_EMISION_VP', '')}",
                    operacio=sub_desc,
                ))
            else:
                doc04 = str(fila04.get("Referencia del pedido") or "")
                rp = fila04.get("Referencia del pedido")
                if rp:
                    refs_pedido_04.append(str(rp))
                if num_inferable:
                    ambigus.append(fer_ambigu(
                        "04_COMANDES_VENDES", "numero_inferable",
                        f"Número de comanda inferable ({client}, {ref.get('R_FECHA_EMISION_VP', '')})",
                        fila04.get("Numero comanda", ""), ref["R_NUMERO_VP"],
                        p["numero_incorrecte"],
                    ))
                if not imports_iguals(fila04.get("Total"), ref["R_IMPORTE_V"]):
                    errors.append(fer_error(
                        "04_COMANDES_VENDES", "import_incorrecte", "greu", p["import_incorrecte"],
                        f"Import incorrecte ({client})",
                        "Total", fila04.get("Total"), ref["R_IMPORTE_V"], sub_desc,
                        document=doc04,
                    ))
                if not dates_iguals(fila04.get("Data comanda"), ref["R_FECHA_EMISION_VP"]):
                    errors.append(fer_error(
                        "04_COMANDES_VENDES", "data_incorrecta", "lleu", p["data_incorrecta"],
                        f"Data incorrecta ({client})",
                        "Data comanda", fila04.get("Data comanda"),
                        ref["R_FECHA_EMISION_VP"], sub_desc,
                        document=doc04,
                    ))

            # Llistat 05: un albarà per comanda
            ref_pedido_04 = fila04.get("Referencia del pedido") if fila04 else None
            fila05 = _match_05(df05, ref, ref_pedido_04)
            if fila05 is None:
                errors.append(fer_error(
                    "05_ENTREGUES", "operacio_falta", "molt_greu", p["operacio_falta"],
                    f"Entrega que falta: {client} del {ref.get('R_FECHA_EMISION_VP', '')}",
                    operacio=sub_desc,
                ))
            else:
                doc05 = str(fila05.get("Referencia") or "")
                if norm_str(fila05.get("Estado")) != "hecho":
                    errors.append(fer_error(
                        "05_ENTREGUES", "estat_incorrecte", "lleu", p["estat_incorrecte"],
                        f"Entrega no realitzada ({client})",
                        "Estado", fila05.get("Estado"), "Hecho", sub_desc,
                        document=doc05,
                    ))
                if not imports_iguals(fila05.get("Pedido de venta/Total"), ref["R_IMPORTE_V"]):
                    errors.append(fer_error(
                        "05_ENTREGUES", "import_incorrecte", "greu", p["import_incorrecte"],
                        f"Import incorrecte a l'entrega ({client})",
                        "Pedido de venta/Total",
                        fila05.get("Pedido de venta/Total"), ref["R_IMPORTE_V"], sub_desc,
                        document=doc05,
                    ))

        # Llistat 06: una factura per grup (client + setmana) amb import total
        fila06 = _match_06_recap(df06, client, data_max, refs_pedido_04)
        if fila06 is None:
            errors.append(fer_error(
                "06_FACTURES_VENDA", "operacio_falta", "molt_greu", p["operacio_falta"],
                f"Factura recapitulativa que falta: {client} setmana fins {data_max}",
                operacio=desc_op,
            ))
        else:
            doc06 = str(fila06.get("Número") or "")
            # Verificar import total
            if not imports_iguals(fila06.get("Total con signo en moneda"), import_total_esp):
                errors.append(fer_error(
                    "06_FACTURES_VENDA", "import_incorrecte", "greu", p["import_incorrecte"],
                    f"Import total incorrecte a la factura recapitulativa ({client})",
                    "Total con signo en moneda",
                    fila06.get("Total con signo en moneda"), import_total_esp, desc_op,
                    document=doc06,
                ))
            # Verificar que l'Origen conté totes les Referencia del pedido del grup
            if refs_pedido_04:
                origen = str(fila06.get("Origen", ""))
                manquen = [rp for rp in refs_pedido_04
                           if norm_str(rp) not in norm_str(origen)]
                if manquen:
                    errors.append(fer_error(
                        "06_FACTURES_VENDA", "numero_incorrecte", "lleu", p["numero_incorrecte"],
                        f"Origen de la factura recapitulativa no inclou totes les comandes ({client})",
                        "Origen", origen, ", ".join(refs_pedido_04), desc_op,
                        document=doc06,
                    ))
            _verificar_factura_venda(fila06, refs_grup[0], p, errors, desc_op,
                                     recap=True, import_total=import_total_esp,
                                     document=doc06)

    return errors, ambigus


def _verificar_factura_venda(
    fila06: dict,
    ref: dict,
    p: dict,
    errors: list,
    desc_op: str,
    recap: bool = False,
    import_total: Optional[float] = None,
    document: Optional[str] = None,
) -> None:
    """Verifica els camps d'una factura de venda."""
    client = ref["R_CLIENTE_V"]

    if norm_str(fila06.get("Nombre de la empresa a mostrar en la factura")) != norm_str(client):
        errors.append(fer_error(
            "06_FACTURES_VENDA", "proveidor_client_incorrecte", "greu",
            p["proveidor_client_incorrecte"],
            f"Nom de client incorrecte a la factura de venda",
            "Nombre de la empresa a mostrar en la factura",
            fila06.get("Nombre de la empresa a mostrar en la factura"), client, desc_op,
            document=document,
        ))

    if not recap:
        importe_esp = ref["R_IMPORTE_V"]
        if not imports_iguals(fila06.get("Total con signo en moneda"), importe_esp):
            errors.append(fer_error(
                "06_FACTURES_VENDA", "import_incorrecte", "greu", p["import_incorrecte"],
                f"Import incorrecte a la factura de venda ({client})",
                "Total con signo en moneda",
                fila06.get("Total con signo en moneda"), importe_esp, desc_op,
                document=document,
            ))

    # Fecha factura <= data màxima facturació
    d_fact = parse_data(fila06.get("Fecha de factura"))
    d_max = parse_data(ref["R_FECHA_MAX_FACTURACION_V"])
    if d_fact and d_max and d_fact > d_max:
        errors.append(fer_error(
            "06_FACTURES_VENDA", "data_incorrecta", "lleu", p["data_incorrecta"],
            f"Fecha de factura posterior al termini ({client})",
            "Fecha de factura",
            fila06.get("Fecha de factura"), f"<= {ref['R_FECHA_MAX_FACTURACION_V']}", desc_op,
            document=document,
        ))

    # Venciment = data factura + 7 dies
    if d_fact:
        d_venc_esp = d_fact + timedelta(days=7)
        if not dates_iguals(fila06.get("Fecha de vencimiento"), d_venc_esp.isoformat()):
            errors.append(fer_error(
                "06_FACTURES_VENDA", "data_incorrecta", "lleu", p["data_incorrecta"],
                f"Data de venciment incorrecta ({client})",
                "Fecha de vencimiento",
                fila06.get("Fecha de vencimiento"), d_venc_esp.isoformat(), desc_op,
                document=document,
            ))

    estat = norm_str(fila06.get("Estado en pago", ""))
    if estat not in ("publicado", "pagada"):
        errors.append(fer_error(
            "06_FACTURES_VENDA", "estat_incorrecte", "lleu", p["estat_incorrecte"],
            f"Estat de pagament incorrecte ({client})",
            "Estado en pago", fila06.get("Estado en pago"), "Publicado / Pagada", desc_op,
            document=document,
        ))


def _verificar_sequencia_fv(df06: pd.DataFrame, p: dict) -> list[dict]:
    """Comprova la seqüència correlativa de números FV i la coherència de dates."""
    errors = []
    pattern = re.compile(r"FV-\d+/(\d{4})/(\d+)")

    files_fv = []
    for _, row in df06.iterrows():
        num = str(row.get("Número", ""))
        m = pattern.match(num.strip())
        if m:
            any_fv = int(m.group(1))
            ordre = int(m.group(2))
            d_fact = parse_data(row.get("Fecha de factura"))
            files_fv.append((any_fv, ordre, d_fact, num))

    if not files_fv:
        return errors

    files_fv.sort(key=lambda x: (x[0], x[1]))

    # Verificar seqüència sense salts
    for i in range(1, len(files_fv)):
        prev_any, prev_ord, _, prev_num = files_fv[i - 1]
        cur_any, cur_ord, cur_date, cur_num = files_fv[i]
        if cur_any == prev_any and cur_ord != prev_ord + 1:
            errors.append(fer_error(
                "06_FACTURES_VENDA", "numero_incorrecte", "greu", p["numero_incorrecte"],
                f"Salt en la numeració de factures: de {prev_num} a {cur_num}",
                "Número", cur_num, f"{prev_num[:-len(str(prev_ord))]}{prev_ord + 1:05d}",
                document=cur_num,
            ))

    # Verificar que dates segueixen l'ordre de números
    for i in range(1, len(files_fv)):
        _, _, prev_date, prev_num = files_fv[i - 1]
        _, _, cur_date, cur_num = files_fv[i]
        if prev_date and cur_date and cur_date < prev_date:
            errors.append(fer_error(
                "06_FACTURES_VENDA", "data_incorrecta", "greu", p["data_incorrecta"],
                f"Factura {cur_num} té data anterior a {prev_num} (ordre invers)",
                "Fecha de factura", str(cur_date), f">= {prev_date}",
                document=cur_num,
            ))

    return errors


# ── Funcions de matching ──────────────────────────────────────────────────────

def _match_04(df: pd.DataFrame, ref: dict) -> tuple[Optional[dict], bool]:
    """Cerca la fila de llistat 04 per l'operació ref."""
    # Intent 1: per número comanda
    for _, row in df.iterrows():
        if norm_str(row.get("Numero comanda")) == norm_str(ref["R_NUMERO_VP"]):
            return row.to_dict(), False

    # Intent 2: per client + data
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Cliente")) == norm_str(ref["R_CLIENTE_V"])
            and dates_iguals(row.get("Data comanda"), ref["R_FECHA_EMISION_VP"]))
    ]
    if len(candidates) == 1:
        return candidates[0].to_dict(), True

    # Intent 3: per client + import
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Cliente")) == norm_str(ref["R_CLIENTE_V"])
            and imports_iguals(row.get("Total"), ref["R_IMPORTE_V"]))
    ]
    if len(candidates) == 1:
        return candidates[0].to_dict(), True

    return None, False


def _match_05(
    df: pd.DataFrame,
    ref: dict,
    ref_pedido_04: Optional[str],
) -> Optional[dict]:
    """Cerca la fila de llistat 05 per l'operació ref."""
    # Intent 1: per Documento de origen = Referencia del pedido de llistat 04
    if ref_pedido_04:
        for _, row in df.iterrows():
            if norm_str(row.get("Documento de origen")) == norm_str(ref_pedido_04):
                return row.to_dict()

    # Intent 2: per client + import
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Contacto")) == norm_str(ref["R_CLIENTE_V"])
            and imports_iguals(row.get("Pedido de venta/Total"), ref["R_IMPORTE_V"]))
    ]
    if candidates:
        return candidates[0].to_dict()

    return None


def _match_06_individual(
    df: pd.DataFrame,
    ref: dict,
    ref_pedido_04: Optional[str],
) -> Optional[dict]:
    """Cerca la fila de llistat 06 per una factura individual."""
    # Intent 1: per Origen = ref_pedido_04
    if ref_pedido_04:
        for _, row in df.iterrows():
            origen = str(row.get("Origen", ""))
            if norm_str(origen) == norm_str(ref_pedido_04):
                return row.to_dict()

    # Intent 2: per client + import
    candidates = [
        row for _, row in df.iterrows()
        if (norm_str(row.get("Nombre de la empresa a mostrar en la factura"))
                == norm_str(ref["R_CLIENTE_V"])
            and imports_iguals(row.get("Total con signo en moneda"), ref["R_IMPORTE_V"]))
    ]
    if candidates:
        return candidates[0].to_dict()

    return None


def _match_06_recap(
    df: pd.DataFrame,
    client: str,
    data_max: str,
    refs_pedido_04: list[str],
) -> Optional[dict]:
    """Cerca la fila de llistat 06 per una factura recapitulativa (client + setmana).

    Matching: client + data factura <= data_max + Origen conté almenys una
    de les Referencia del pedido del grup.
    """
    d_max = parse_data(data_max)
    for _, row in df.iterrows():
        if norm_str(row.get("Nombre de la empresa a mostrar en la factura")) != norm_str(client):
            continue
        d_fact = parse_data(row.get("Fecha de factura"))
        if not (d_fact and d_max and d_fact <= d_max):
            continue
        if refs_pedido_04:
            origen = norm_str(str(row.get("Origen", "")))
            if any(norm_str(rp) in origen for rp in refs_pedido_04):
                return row.to_dict()
        else:
            # Sense referències a verificar (04 no pujat), fem matching per client+data
            return row.to_dict()
    return None
