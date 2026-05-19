"""Accés i gestió de la llista d'alumnes (data/alumnes.json)."""

import hashlib
import json
from pathlib import Path
from typing import Optional

ALUMNES_FILE = Path(__file__).parent.parent / "data" / "alumnes.json"


def load_alumnes() -> list[dict]:
    if not ALUMNES_FILE.exists():
        return []
    with open(ALUMNES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_alumnes(alumnes: list[dict]) -> None:
    ALUMNES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALUMNES_FILE, "w", encoding="utf-8") as f:
        json.dump(alumnes, f, ensure_ascii=False, indent=2)


def get_alumnes_per_grup(grup: str) -> list[dict]:
    return sorted(
        [a for a in load_alumnes() if a["grup"] == grup and a.get("actiu", True)],
        key=lambda a: a["nom"],
    )


def get_alumne_per_expedient(expedient: str) -> Optional[dict]:
    return next((a for a in load_alumnes() if a["expedient"] == expedient), None)


def get_alumne_per_correu(correu: str) -> Optional[dict]:
    correu = correu.strip().lower()
    return next((a for a in load_alumnes() if a["correu"].lower() == correu), None)


def verificar_alumne(correu: str, password: str) -> Optional[dict]:
    """Retorna les dades de l'alumne si el correu i la contrasenya són correctes."""
    alumne = get_alumne_per_correu(correu)
    if alumne is None:
        return None
    hash_introduit = hashlib.sha256(password.encode()).hexdigest()
    if alumne.get("password_hash") == hash_introduit:
        return alumne
    return None
