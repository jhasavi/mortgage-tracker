import logging
from typing import List, Dict, Any, Optional

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.sample_rates")


class SampleRatesParser(BaseParser):
    """
    Sample parser that returns mock data for demonstration.
    Replace this with real parsers for each lender.
    """
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # In production, you would parse the actual HTML/JSON from the lender's website
        # This is just sample data to demonstrate the system
        offers: List[Dict[str, Any]] = []
        
        if not text:
            return offers
        
        # Extract lender name from HTML if possible (or use a configured name)
        # For now, just log that we attempted to parse
        logger.info("sample_parser_executed")
        
        # Return empty for now - real parsers will extract actual data
        return offers
