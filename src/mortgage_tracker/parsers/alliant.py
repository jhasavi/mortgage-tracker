"""Parser for Alliant Credit Union mortgage rates."""
import logging
from typing import List, Dict, Any, Optional

from .base import BaseParser
from .generic_table import extract_offers_from_html_table

logger = logging.getLogger("mortgage_tracker.parsers.alliant")


class AlliantParser(BaseParser):
    """Parser for Alliant Credit Union mortgage rates."""
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not text:
            logger.warning("no_text_provided")
            return []
        
        try:
            # Alliant uses tables
            offers = extract_offers_from_html_table(
                html=text,
                lender_name="Alliant Credit Union",
                product_col=0,
                rate_col=1,
                apr_col=2,
                points_col=None,
                min_columns=3
            )
            
            for offer in offers:
                logger.info(f"parsed_offer: {offer['category']} @ {offer['rate']}% (APR {offer['apr']}%)")
                
            if not offers:
                logger.warning("no_rates_found_in_tables")
                
            return offers
            
        except Exception as e:
            logger.error(f"parse_error: {str(e)}")
            return []
