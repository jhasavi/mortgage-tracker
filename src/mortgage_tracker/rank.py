from typing import List, Dict


def top_n_per_category(rows: List[Dict], n: int = 10) -> dict:
    grouped: dict = {}
    for r in rows:
        cat = r.get("category")
        grouped.setdefault(cat, []).append(r)
    result: dict = {}
    for cat, items in grouped.items():
        items.sort(key=lambda x: (
            _safe_float(x.get("rate"), 9999.0),
            _safe_float(x.get("apr"), 9999.0),
        ))
        result[cat] = items[:n]
    return result


def _safe_float(v, default):
    try:
        return float(v) if v is not None else default
    except Exception:
        return default
