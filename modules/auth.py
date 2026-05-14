"""Autenticació i gestió de contrasenyes dels professors."""

import hashlib
import json
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path(__file__).parent.parent / "data" / "config.json"


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"professors": {}}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_config(config: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def professor_configurat(grup: str) -> bool:
    """Retorna True si el professor del grup ja té contrasenya configurada."""
    config = _load_config()
    return bool(config.get("professors", {}).get(grup, {}).get("password_hash"))


def verificar_professor(grup: str, password: str) -> Optional[dict]:
    """Retorna les dades del professor si la contrasenya és correcta, None si no."""
    config = _load_config()
    prof = config.get("professors", {}).get(grup)
    if prof and prof.get("password_hash") == _hash(password):
        return {**prof, "grup": grup}
    return None


def configurar_password(grup: str, password_nova: str) -> None:
    """Estableix o canvia la contrasenya d'un professor."""
    config = _load_config()
    if grup not in config.get("professors", {}):
        config.setdefault("professors", {})[grup] = {}
    config["professors"][grup]["password_hash"] = _hash(password_nova)
    _save_config(config)
