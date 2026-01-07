"""Parser for Navy Federal Credit Union mortgage rates."""
import logging
from typing import List, Dict, Any, Optional

from .base import BaseParser
from .generic_table import extract_offers_from_html_table

logger = logging.getLogger("mortgage_tracker.parsers.navy_federal")


class NavyFederalParser(BaseParser):
    """Parser for Navy Federal Credit Union mortgage rates."""
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not text:
            logger.warning("no_text_provided")
            return []
        
        try:
            # Navy Federal uses tables with columns: Term, Rate, Points, APR
            offers = extract_offers_from_html_table(
                html=text,
                lender_name="Navy Federal Credit Union",
                product_col=0,
                rate_col=1,
                apr_col=3,  # APR is in column 3
                points_col=2,  # Points in column 2
                min_columns=4
            )
            
            # Deduplicate exact duplicates (same rate, APR, points for same category)
            seen = set()
            unique_offers = []
            for offer in offers:
                key = (offer['category'], offer['rate'], offer['apr'], offer['points'])
                if key not in seen:
                    seen.add(key)
                    unique_offers.append(offer)
                    logger.info(f"parsed_offer: {offer['category']} @ {offer['rate']}% (APR {offer['apr']}%, points {offer['points']}%)")
            
            if len(unique_offers) < len(offers):
                logger.info(f"Removed {len(offers) - len(unique_offers)} duplicate offers")
            
            if not unique_offers:
                logger.warning("no_rates_found_in_tables")
                
            return unique_offers
            
        except Exception as e:
            logger.error(f"parse_error: {str(e)}")
            return []
