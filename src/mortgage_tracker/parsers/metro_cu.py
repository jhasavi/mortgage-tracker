"""
Parser for Metro Credit Union (MA) mortgage rates.

Note: Metro CU uses a quote flow rather than publishing static rates.
This parser attempts to extract any rate information found on the page,
but will typically return empty results.
"""
import logging
import re
from typing import List, Dict, Any, Optional

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.metro_cu")


class MetroCUParser(BaseParser):
    """Parser for Metro Credit Union mortgage rates."""
    
    def parse(
        self, 
        *, 
        text: Optional[str] = None, 
        js: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Attempt to parse Metro CU mortgage rates.
        
        Returns:
            List of offer dictionaries (typically empty for quote-flow pages)
        """
        offers: List[Dict[str, Any]] = []
        
        if not text:
            logger.warning("No text provided to Metro CU parser")
            return offers
        
        # Check if this is a quote flow page
        if "mortgage-rate-quote" in text.lower() or "personalized rate quote" in text.lower():
            logger.info("Metro CU page appears to be a quote flow, not a static rate table")
            # Return empty - this is expected
            return offers
        
        # Attempt best-effort parsing if rates are found
        # Look for patterns like "5.75% APR" or "30-year fixed: 5.875%"
        rate_patterns = [
            r'30[- ]?year.*?(\d+\.\d+)%',
            r'15[- ]?year.*?(\d+\.\d+)%',
            r'(\d+\.\d+)%\s+APR',
        ]
        
        for pattern in rate_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                logger.debug(f"Found potential rate match: {match.group(0)}")
                # TODO: Build offer dict if confident match found
                # For now, skip - needs manual verification
        
        logger.info(f"Metro CU parser found 0 offers (quote flow expected)")
        return offers
