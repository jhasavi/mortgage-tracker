import json
import logging
import re
from typing import List, Dict, Any, Optional

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.dcu")


class DCUParser(BaseParser):
    """Parser for DCU (Digital Federal Credit Union) mortgage rates."""
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers: List[Dict[str, Any]] = []
        
        if not text:
            logger.warning("no_text_provided")
            return offers
        
        try:
            # DCU embeds rate data in schema.org JSON-LD
            # Look for <script type="application/ld+json"> containing MortgageLoan
            pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, dict) and data.get('@type') == 'MortgageLoan':
                        # Extract rate data
                        rate_str = data.get('interestRate', '')
                        apr_str = data.get('annualPercentageRate', '')
                        loan_term = data.get('loanTerm', {})
                        
                        # Parse rate percentages
                        rate = self._parse_percentage(rate_str)
                        apr = self._parse_percentage(apr_str)
                        
                        # Determine term
                        term_value = loan_term.get('value') if isinstance(loan_term, dict) else None
                        term_years = int(term_value) if term_value else 30
                        
                        # Determine category based on term
                        if term_years == 30:
                            category = "30Y fixed"
                        elif term_years == 15:
                            category = "15Y fixed"
                        else:
                            category = "30Y fixed"  # Default
                        
                        offers.append({
                            "lender_name": "DCU (Digital Federal Credit Union)",
                            "category": category,
                            "rate": rate,
                            "apr": apr,
                            "points": 0.0,
                            "lender_fees": None,
                            "term_months": term_years * 12,
                        })
                        
                        logger.info(f"parsed_offer: {category} @ {rate}%")
                        
                except json.JSONDecodeError:
                    continue
            
            if not offers:
                logger.warning("no_rates_found_in_schema")
                
        except Exception as e:
            logger.error(f"parse_error: {str(e)}")
        
        return offers
    
    def _parse_percentage(self, value: str) -> Optional[float]:
        """Extract float from percentage string like '5.750%'."""
        if not value:
            return None
        try:
            # Remove % and any whitespace
            clean = value.replace('%', '').strip()
            return float(clean)
        except (ValueError, AttributeError):
            return None
