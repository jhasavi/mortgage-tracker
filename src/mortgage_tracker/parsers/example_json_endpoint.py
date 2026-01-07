import logging
from typing import List, Dict, Any, Optional

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.json_endpoint")


class ExampleJsonEndpointParser(BaseParser):
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers: List[Dict[str, Any]] = []
        if js and isinstance(js, dict):
            # Expect a schema like { offers: [ { ... } ] }
            for item in js.get("offers", []):
                offers.append({
                    "lender_name": item.get("lender") or "Example CU B",
                    "category": item.get("category") or "15Y fixed",
                    "rate": item.get("rate"),
                    "apr": item.get("apr"),
                    "points": item.get("points", 0.0),
                    "lender_fees": item.get("fees", 0.0),
                    "term_months": item.get("term_months"),
                })
        else:
            logger.warning("no_json_provided")
        return offers
