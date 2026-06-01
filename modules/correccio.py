"""Orquestrador del motor de correcció automàtica."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from modules.alumnes_data import get_alumnes_per_grup
from modules.auth import get_data_inici_fact_recapitulativa
from modules.fitxers import get_llistats_alumne
from modules.referencia_data import load_referencia
from modules.utils import PENALITZACIONS_DEFAULT
from modules.correccio_compres import corregir_compres
from modules.correccio_vendes import corregir_vendes
from modules.correccio_magatzem import corregir_magatzem
from modules.neteja import netejar_llistats

TASQUES_DIR = Path(__file__).parent.parent / "data" / "tasques"


def _carregar_llistat(num_tasca: str, grup: str, expedient: str, codi: str) -> Optional[pd.DataFrame]:
    """Carrega un llistat xlsx d'un alumne com a DataFrame."""
    llistats = get_llistats_alumne(num_tasca, grup, str(expedient))
    if codi not in llistats:
        return None
    nom_fitxer = llistats[codi]["nom_fitxer"]
    path = TASQUES_DIR / num_tasca / grup / "entregues" / str(expedient) / nom_fitxer
    if not path.exists():
        return None
    try:
        df = pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how="all").reset_index(drop=True)
    except Exception:
        return None


def _calcular_nota(errors: list[dict], ambigus: list[dict]) -> float:
    """Calcula la nota a partir dels errors i els casos ambigus resolts."""
    penalitzacio = sum(abs(e["penalitzacio"]) for e in errors)
    # Casos ambigus rebutjats compten com a error
    for a in ambigus:
        if a.get("resolucio") == "rebutjat":
            penalitzacio += abs(a.get("penalitzacio_si_rebutjat", 0.5))
    return max(0.0, round(10.0 - penalitzacio, 2))


def _resultats_path(num_tasca: str, grup: str) -> Path:
    return TASQUES_DIR / num_tasca / grup / "correccions" / "resultats.json"


def load_resultats(num_tasca: str, grup: str) -> Optional[dict]:
    """Carrega els resultats de correcció guardats."""
    path = _resultats_path(num_tasca, grup)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_resultats(num_tasca: str, grup: str, resultats: dict) -> None:
    path = _resultats_path(num_tasca, grup)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)


def executar_correccio(
    num_tasca: str,
    grup: str,
    penalitzacions: Optional[dict] = None,
) -> dict:
    """
    Executa la correcció completa per a tots els alumnes d'un grup i una tasca.
    Conserva les resolucions de casos ambigus ja existents.
    Retorna el dict de resultats i el guarda a disc.
    """
    p = {**PENALITZACIONS_DEFAULT, **(penalitzacions or {})}
    alumnes = get_alumnes_per_grup(grup)
    ref_grup = load_referencia(num_tasca, grup)
    data_inici_recap = get_data_inici_fact_recapitulativa(grup)

    # Carregar resultats anteriors per conservar resolucions d'ambigus
    resultats_anteriors = load_resultats(num_tasca, grup) or {}
    alumnes_anteriors = resultats_anteriors.get("alumnes", {})

    resultats_alumnes: dict = {}

    for alumne in alumnes:
        exp = str(alumne["expedient"])
        ref_alumne = ref_grup.get(exp, {})
        compres_ref = ref_alumne.get("compres", [])
        vendes_ref = ref_alumne.get("vendes", [])

        # Carregar DataFrames
        df01 = _carregar_llistat(num_tasca, grup, exp, "01")
        df02 = _carregar_llistat(num_tasca, grup, exp, "02")
        df03 = _carregar_llistat(num_tasca, grup, exp, "03")
        df04 = _carregar_llistat(num_tasca, grup, exp, "04")
        df05 = _carregar_llistat(num_tasca, grup, exp, "05")
        df06 = _carregar_llistat(num_tasca, grup, exp, "06")
        df07 = _carregar_llistat(num_tasca, grup, exp, "07")
        df08 = _carregar_llistat(num_tasca, grup, exp, "08")

        # Neteja pre-correcció (devolucions, factures no-proveïdors, recepcions buides,
        # files de vendes amb client fora de l'empresa simulada)
        df02, df03, df04, df05, df06, accions_neteja = netejar_llistats(
            df02, df03, df05, df04, df06
        )

        # Executar correccions per blocs
        errors: list[dict] = []
        ambigus: list[dict] = []

        if compres_ref:
            e, a = corregir_compres(df01, df02, df03, compres_ref, p)
            errors.extend(e)
            ambigus.extend(a)
        elif any(df is not None for df in [df01, df02, df03]):
            errors.append({
                "llistat": "COMPRES", "tipus": "operacio_falta", "gravetat": "molt_greu",
                "penalitzacio": 0,
                "descripcio": "No hi ha dades de referència de compres per a aquest alumne",
            })

        if vendes_ref:
            e, a = corregir_vendes(df04, df05, df06, vendes_ref, data_inici_recap, p)
            errors.extend(e)
            ambigus.extend(a)
        elif any(df is not None for df in [df04, df05, df06]):
            errors.append({
                "llistat": "VENDES", "tipus": "operacio_falta", "gravetat": "molt_greu",
                "penalitzacio": 0,
                "descripcio": "No hi ha dades de referència de vendes per a aquest alumne",
            })

        e, _ = corregir_magatzem(df07, df08, p)
        errors.extend(e)

        # Conservar resolucions de casos ambigus anteriors (pel mateix id)
        resolucions_anteriors = {
            a["id"]: a.get("resolucio")
            for a in alumnes_anteriors.get(exp, {}).get("casos_ambigus", [])
            if a.get("resolucio") is not None
        }
        for a in ambigus:
            if a["id"] in resolucions_anteriors:
                a["resolucio"] = resolucions_anteriors[a["id"]]

        llistats_entregats = get_llistats_alumne(num_tasca, grup, exp)
        llistats_faltants = [c for c in ["01","02","03","04","05","06","07","08"]
                             if c not in llistats_entregats]

        nota = _calcular_nota(errors, ambigus)
        resultats_alumnes[exp] = {
            "nom": alumne["nom"],
            "nota": nota,
            "penalitzacio_total": round(10.0 - nota, 2),
            "errors": errors,
            "casos_ambigus": ambigus,
            "llistats_faltants": llistats_faltants,
            "ref_disponible": bool(ref_alumne),
            "neteja_aplicada": accions_neteja,
        }

    resultats = {
        "data_correccio": datetime.now().isoformat(timespec="seconds"),
        "num_tasca": num_tasca,
        "grup": grup,
        "alumnes": resultats_alumnes,
    }
    save_resultats(num_tasca, grup, resultats)
    return resultats


def resoldre_ambigu(
    num_tasca: str,
    grup: str,
    expedient: str,
    ambigu_id: str,
    resolucio: Optional[str],  # "acceptat" | "rebutjat" | None (desfer)
) -> dict:
    """
    Resol un cas ambigu i recalcula la nota de l'alumne.
    Retorna el dict de resultats actualitzat.
    """
    resultats = load_resultats(num_tasca, grup)
    if not resultats:
        raise ValueError("No hi ha resultats de correcció per a aquesta tasca")

    alumne_res = resultats["alumnes"].get(str(expedient))
    if not alumne_res:
        raise ValueError(f"Alumne {expedient} no trobat als resultats")

    for a in alumne_res["casos_ambigus"]:
        if a["id"] == ambigu_id:
            a["resolucio"] = resolucio
            break

    # Recalcular nota
    alumne_res["nota"] = _calcular_nota(alumne_res["errors"], alumne_res["casos_ambigus"])
    alumne_res["penalitzacio_total"] = round(10.0 - alumne_res["nota"], 2)

    save_resultats(num_tasca, grup, resultats)
    return resultats


def te_ambigus_pendents(resultats: dict) -> bool:
    """Retorna True si hi ha algun cas ambigu sense resoldre."""
    for alumne in resultats.get("alumnes", {}).values():
        for a in alumne.get("casos_ambigus", []):
            if a.get("resolucio") is None:
                return True
    return False
