from typing import List, Dict, Any, Optional

from .config import Defaults


ALLOWED_CATEGORIES = {"30Y fixed", "15Y fixed", "5/6 ARM", "FHA 30Y", "VA 30Y"}


def normalize_offers(raw_offers: List[Dict[str, Any]], defaults: Defaults) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    for ro in raw_offers:
        cat = ro.get("category") or "30Y fixed"
        if cat not in ALLOWED_CATEGORIES:
            # Skip unknown categories for MVP
            continue
        entry = {
            "lender_name": ro.get("lender_name"),
            "category": cat,
            "rate": _to_float(ro.get("rate")),
            "apr": _to_float(ro.get("apr")),
            "points": _to_float(ro.get("points")),
            "lender_fees": _to_float(ro.get("lender_fees")),
            "loan_amount": _to_float(ro.get("loan_amount")) or defaults.loan_amount,
            "ltv": _to_float(ro.get("ltv")) or defaults.ltv,
            "fico": _to_int(ro.get("fico")) or defaults.fico,
            "state": ro.get("state") or defaults.state,
            "term_months": _to_int(ro.get("term_months")) or _term_for_category(cat),
            "lock_days": _to_int(ro.get("lock_days")) or defaults.lock_days,
            "details_json": ro,
        }
        norm.append(entry)
    return norm


def _term_for_category(cat: str) -> int:
    if cat == "15Y fixed":
        return 180
    return 360


def _to_float(v) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _to_int(v) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None
