import logging
from typing import List, Dict, Any, Optional

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.html_table")


class ExampleHtmlTableParser(BaseParser):
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Minimal placeholder: in real usage, parse HTML table rows.
        # Here we simulate a single 30Y fixed record if text exists.
        offers: List[Dict[str, Any]] = []
        if text:
            offers.append({
                "lender_name": "Example Bank A",
                "category": "30Y fixed",
                "rate": 6.25,
                "apr": 6.35,
                "points": 0.0,
                "lender_fees": 1200.0,
                "term_months": 360,
            })
        else:
            logger.warning("no_text_provided")
        return offers
