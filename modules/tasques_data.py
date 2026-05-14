"""Gestió de les tasques setmanals (configuració, obertura, tancament)."""

import json
from datetime import date
from pathlib import Path
from typing import Optional

TASQUES_DIR = Path(__file__).parent.parent / "data" / "tasques"


def _config_path(num_tasca: str, grup: str) -> Path:
    return TASQUES_DIR / num_tasca / grup / "config.json"


def load_tasca(num_tasca: str, grup: str) -> Optional[dict]:
    path = _config_path(num_tasca, grup)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_tasca(config: dict) -> None:
    path = _config_path(config["num_tasca"], config["grup"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_tasques_obertes(grup: str) -> list[dict]:
    """Retorna les tasques marcades com actives per a un grup, ordenades per número."""
    return sorted(
        [t for t in _iter_tasques(grup) if t.get("activa", False)],
        key=lambda t: t["num_tasca"],
    )


def get_totes_tasques(grup: str) -> list[dict]:
    return sorted(_iter_tasques(grup), key=lambda t: t["num_tasca"])


def _iter_tasques(grup: str):
    if not TASQUES_DIR.exists():
        return
    for tasca_dir in sorted(TASQUES_DIR.iterdir()):
        config_path = tasca_dir / grup / "config.json"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                yield json.load(f)


def is_fora_termini(config: dict) -> bool:
    try:
        tancament = date.fromisoformat(config["data_tancament"])
        return date.today() > tancament
    except (KeyError, ValueError):
        return False


def get_nums_tasques_disponibles(grup: str) -> list[str]:
    usats = {t["num_tasca"] for t in get_totes_tasques(grup)}
    return [f"02.{i:02d}" for i in range(1, 100) if f"02.{i:02d}" not in usats]
