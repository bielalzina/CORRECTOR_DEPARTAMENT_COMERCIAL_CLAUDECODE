"""Gestió dels fitxers xlsx lliurats pels alumnes i de les metadades d'entrega."""

import json
from datetime import datetime
from pathlib import Path

TASQUES_DIR = Path(__file__).parent.parent / "data" / "tasques"

ORDRE_CODIS = ["01", "02", "03", "04", "05", "06", "07", "08"]


def _entregues_dir(num_tasca: str, grup: str, expedient: str) -> Path:
    return TASQUES_DIR / num_tasca / grup / "entregues" / expedient


def _metadata_path(num_tasca: str, grup: str, expedient: str) -> Path:
    return _entregues_dir(num_tasca, grup, expedient) / "metadata.json"


def load_metadata(num_tasca: str, grup: str, expedient: str) -> dict:
    path = _metadata_path(num_tasca, grup, expedient)
    if not path.exists():
        return {"llistats": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_metadata(num_tasca: str, grup: str, expedient: str, metadata: dict) -> None:
    path = _metadata_path(num_tasca, grup, expedient)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def guardar_llistat(
    contingut: bytes,
    num_tasca: str,
    grup: str,
    expedient: str,
    tipus_llistat: str,
    fora_termini: bool,
) -> str:
    """
    Guarda el fitxer xlsx amb la nomenclatura correcta i actualitza les metadades.
    Retorna el nom del fitxer guardat.
    """
    nom_fitxer = f"{num_tasca}-{expedient}-{tipus_llistat}.xlsx"
    directori = _entregues_dir(num_tasca, grup, expedient)
    directori.mkdir(parents=True, exist_ok=True)
    (directori / nom_fitxer).write_bytes(contingut)

    metadata = load_metadata(num_tasca, grup, expedient)
    codi = tipus_llistat.split("_")[0]
    metadata["llistats"][codi] = {
        "nom_fitxer": nom_fitxer,
        "tipus": tipus_llistat,
        "data_pujada": datetime.now().isoformat(timespec="seconds"),
        "fora_termini": fora_termini,
    }
    _save_metadata(num_tasca, grup, expedient, metadata)
    return nom_fitxer


def get_llistats_alumne(num_tasca: str, grup: str, expedient: str) -> dict:
    """Retorna el dict {codi: info} dels llistats lliurats per un alumne."""
    return load_metadata(num_tasca, grup, expedient).get("llistats", {})


def get_resum_entregues(num_tasca: str, grup: str, alumnes: list[dict]) -> list[dict]:
    """Resum per a la vista del professor: quins llistats ha entregat cada alumne."""
    resum = []
    for alumne in alumnes:
        exp = alumne["expedient"]
        llistats = get_llistats_alumne(num_tasca, grup, exp)
        fora = any(v.get("fora_termini") for v in llistats.values())
        resum.append({
            "expedient": exp,
            "nom": alumne["nom"],
            **{c: "✅" if c in llistats else "—" for c in ORDRE_CODIS},
            "fora_termini": "⚠️ Sí" if fora else "No",
            "total": f"{len(llistats)}/8",
        })
    return resum
