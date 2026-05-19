"""Utilitats generals compartides entre mòduls i vistes."""


def fmt_data(s: str) -> str:
    """Converteix una data ISO (yyyy-mm-dd o yyyy-mm-ddTHH:MM:SS) a dd/mm/yyyy."""
    if not s or len(s) < 10:
        return s or "—"
    try:
        y, m, d = s[:10].split("-")
        return f"{d}/{m}/{y}"
    except (ValueError, AttributeError):
        return s
