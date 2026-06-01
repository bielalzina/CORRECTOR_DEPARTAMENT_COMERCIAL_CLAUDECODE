"""Neteja de llistats dels alumnes abans de la correcció automàtica.

Cinc operacions aplicades sobre els DataFrames carregats:
  1. Eliminació de devolucions de recepcions (ENTRA retornades via SURT a df05 + df02)
  2. Eliminació de devolucions d'entregues  (SURT retornades via ENTRA a df02 + df05)
  3. Eliminació de factures de compra que no son de ALUBIX SL ni ROCALLA SA (df03)
  4. Eliminació de recepcions sense import (nul o zero) de df02
  5. Eliminació de files de vendes on el client no és BIGCORP SL ni COMERCIAL CALCO SA
     (df04 columna Cliente, df05 columna Contacto, df06 columna Nombre empresa)
"""

import re
from typing import Optional

import pandas as pd

PROVEÏDORS_MERCADERIES = {"ALUBIX SL", "ROCALLA SA"}


def _extreure_ref_normalitzada(doc_origen: str) -> str:
    """
    De 'Devolución de MGZ01/ENTRA/00002' retorna 'MGZ01/ENTRA/00002'.
    De 'Devolución de MGZ01/SURT/12'    retorna 'MGZ01/SURT/00012'.
    Normalitza sempre a 5 dígits.
    """
    match = re.search(r"MGZ01/(ENTRA|SURT)/(\d+)", str(doc_origen), re.IGNORECASE)
    if match:
        tipus = match.group(1).upper()
        num = int(match.group(2))
        return f"MGZ01/{tipus}/{num:05d}"
    return ""


CLIENTS_VENDES = {"BIGCORP SL", "COMERCIAL CALCO SA"}


def netejar_llistats(
    df02: Optional[pd.DataFrame],
    df03: Optional[pd.DataFrame],
    df05: Optional[pd.DataFrame],
    df04: Optional[pd.DataFrame] = None,
    df06: Optional[pd.DataFrame] = None,
) -> tuple[
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    list[str],
]:
    """
    Aplica les 4 operacions de neteja als llistats 02, 03 i 05.
    No modifica els DataFrames originals (treballa amb còpies).
    Retorna (df02_net, df03_net, df05_net, accions) on accions és un log de la neteja.
    """
    df02 = df02.copy() if df02 is not None else None
    df03 = df03.copy() if df03 is not None else None
    df04 = df04.copy() if df04 is not None else None
    df05 = df05.copy() if df05 is not None else None
    df06 = df06.copy() if df06 is not None else None
    accions: list[str] = []

    # ── 1. Devolucions de recepcions ──────────────────────────────────────────
    # df05: files on Documento de origen = "Devolución de MGZ01/ENTRA/XXXXX"
    # → eliminar d'df05 + eliminar la ENTRA corresponent de df02
    if df05 is not None and "Documento de origen" in df05.columns:
        mascara = df05["Documento de origen"].str.contains(
            r"Devolución de MGZ01/ENTRA/", na=False, case=False
        )
        if mascara.any():
            refs_entra = (
                df05.loc[mascara, "Documento de origen"]
                .apply(_extreure_ref_normalitzada)
                .tolist()
            )
            refs_entra = [r for r in refs_entra if r]
            n = mascara.sum()
            df05 = df05[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} devolució/ns de recepcions de 05_ENTREGUES "
                f"({', '.join(refs_entra)})"
            )
            if df02 is not None and "Referencia" in df02.columns and refs_entra:
                mascara2 = df02["Referencia"].isin(refs_entra)
                n2 = mascara2.sum()
                if n2:
                    df02 = df02[~mascara2].reset_index(drop=True)
                    accions.append(
                        f"Eliminades {n2} recepcions de 02_RECEPCIONS "
                        f"(ENTRA retornades: {', '.join(refs_entra)})"
                    )

    # ── 2. Devolucions d'entregues ────────────────────────────────────────────
    # df02: files on Documento de origen = "Devolución de MGZ01/SURT/XX"
    # → eliminar d'df02 + eliminar la SURT corresponent de df05
    if df02 is not None and "Documento de origen" in df02.columns:
        mascara = df02["Documento de origen"].str.contains(
            r"Devolución de MGZ01/SURT/", na=False, case=False
        )
        if mascara.any():
            refs_surt = (
                df02.loc[mascara, "Documento de origen"]
                .apply(_extreure_ref_normalitzada)
                .tolist()
            )
            refs_surt = [r for r in refs_surt if r]
            n = mascara.sum()
            df02 = df02[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} recepció/ns de devolució de venda de 02_RECEPCIONS "
                f"({', '.join(refs_surt)})"
            )
            if df05 is not None and "Referencia" in df05.columns and refs_surt:
                mascara2 = df05["Referencia"].isin(refs_surt)
                n2 = mascara2.sum()
                if n2:
                    df05 = df05[~mascara2].reset_index(drop=True)
                    accions.append(
                        f"Eliminades {n2} entregues de 05_ENTREGUES "
                        f"(SURT retornades: {', '.join(refs_surt)})"
                    )

    # ── 3. Factures compra de no-proveïdors ───────────────────────────────────
    # df03: eliminar files on Nombre empresa ≠ ALUBIX SL ni ROCALLA SA
    if df03 is not None and "Nombre de la empresa a mostrar en la factura" in df03.columns:
        col = df03["Nombre de la empresa a mostrar en la factura"].str.strip().str.upper()
        provs_upper = {p.upper() for p in PROVEÏDORS_MERCADERIES}
        mascara = ~col.isin(provs_upper)
        n = mascara.sum()
        if n:
            eliminades = col[mascara].unique().tolist()
            df03 = df03[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} factures de compra de 03_FACTURES_COMPRA "
                f"(no-proveïdors: {', '.join(eliminades)})"
            )

    # ── 4. Recepcions sense import ────────────────────────────────────────────
    # df02: eliminar files on Pedidos de compra/Total és nul o zero
    if df02 is not None and "Pedidos de compra/Total" in df02.columns:
        col_num = pd.to_numeric(df02["Pedidos de compra/Total"], errors="coerce")
        mascara = col_num.isna() | (col_num == 0)
        n = mascara.sum()
        if n:
            refs = df02.loc[mascara, "Referencia"].tolist() if "Referencia" in df02.columns else []
            df02 = df02[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} recepció/ns sense import de 02_RECEPCIONS "
                f"({', '.join(refs)})"
            )

    # ── 5. Files de vendes amb client fora de l'empresa simulada ─────────────
    # Elimina files on el client no és BIGCORP SL ni COMERCIAL CALCO SA.
    clients_upper = {c.upper() for c in CLIENTS_VENDES}

    if df04 is not None and "Cliente" in df04.columns:
        col = df04["Cliente"].str.strip().str.upper()
        mascara = ~col.isin(clients_upper)
        n = mascara.sum()
        if n:
            eliminats = df04.loc[mascara, "Cliente"].unique().tolist()
            df04 = df04[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} comanda/es de 04_COMANDES_VENDES "
                f"(clients no esperats: {', '.join(eliminats)})"
            )

    if df05 is not None and "Contacto" in df05.columns:
        col = df05["Contacto"].str.strip().str.upper()
        mascara = ~col.isin(clients_upper)
        n = mascara.sum()
        if n:
            eliminats = df05.loc[mascara, "Contacto"].unique().tolist()
            df05 = df05[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} entrega/es de 05_ENTREGUES "
                f"(clients no esperats: {', '.join(eliminats)})"
            )

    if df06 is not None and "Nombre de la empresa a mostrar en la factura" in df06.columns:
        col = df06["Nombre de la empresa a mostrar en la factura"].str.strip().str.upper()
        mascara = ~col.isin(clients_upper)
        n = mascara.sum()
        if n:
            eliminats = df06.loc[mascara, "Nombre de la empresa a mostrar en la factura"].unique().tolist()
            df06 = df06[~mascara].reset_index(drop=True)
            accions.append(
                f"Eliminades {n} factura/es de 06_FACTURES_VENDA "
                f"(clients no esperats: {', '.join(eliminats)})"
            )

    return df02, df03, df04, df05, df06, accions
