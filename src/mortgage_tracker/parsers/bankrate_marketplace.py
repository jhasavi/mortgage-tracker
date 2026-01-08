"""Parser for Bankrate mortgage rates marketplace/aggregator page."""
import logging
import re
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.bankrate_marketplace")


class BankrateTableParser(HTMLParser):
    """Parse Bankrate's mortgage rate tables."""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.current_text = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.current_text = []
            
    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ('td', 'th') and self.in_cell:
            self.in_cell = False
            cell_text = ' '.join(self.current_text).strip()
            self.current_row.append(cell_text)
            
    def handle_data(self, data):
        if self.in_cell:
            text = data.strip()
            if text:
                self.current_text.append(text)


class BankrateMarketplaceParser(BaseParser):
    """
    Parser for Bankrate mortgage rates aggregator.
    
    Bankrate publishes daily mortgage rate averages from multiple lenders
    in a clean HTML table format. This parser extracts rate data for:
    - 30-year fixed
    - 20-year fixed  
    - 15-year fixed
    - 10-year fixed
    - FHA 30-year
    - VA 30-year
    - Jumbo 30-year
    - Various ARMs
    """
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers = []
        
        if not text:
            logger.warning("No text provided")
            return offers
        
        try:
            parser = BankrateTableParser()
            parser.feed(text)
            
            # Bankrate typically has tables with format:
            # Product | Today's Rate | Last Week | Change
            # Or: Product | Purchase Rate | Refinance Rate
            
            for row in parser.rows:
                if len(row) < 2:
                    continue
                
                product = row[0].lower()
                
                # Skip header rows
                if 'product' in product or 'loan type' in product or 'today' in product:
                    continue
                
                # Identify category
                category = self._identify_category(product)
                if not category:
                    continue
                
                # Try to extract rate from second column
                rate_text = row[1] if len(row) > 1 else None
                rate = self._parse_percentage(rate_text)
                
                # Try third column for APR or refinance rate
                apr_text = row[2] if len(row) > 2 else None
                apr = self._parse_percentage(apr_text)
                
                # If no APR in third column, assume second column is rate = APR
                if apr is None and rate is not None:
                    apr = rate
                
                if rate is None or apr is None:
                    continue
                
                # Sanity check
                if rate < 2.0 or rate > 15.0 or apr < 2.0 or apr > 20.0:
                    logger.warning(f"Rate out of range: {product} {rate}% / {apr}%")
                    continue
                
                offers.append({
                    "lender_name": "Bankrate National Average",
                    "category": category,
                    "rate": rate,
                    "apr": apr,
                    "points": None,
                    "lender_fees": None,
                    "term_months": self._term_for_category(category),
                    "source_type": "aggregator",
                    "source_name": "Bankrate",
                })
                
                logger.info(f"Parsed Bankrate: {category} @ {rate}% (APR {apr}%)")
            
            if not offers:
                logger.warning("No rates found in Bankrate tables")
            else:
                logger.info(f"Bankrate parser extracted {len(offers)} offers")
                
        except Exception as e:
            logger.error(f"Bankrate parse error: {str(e)}")
        
        return offers
    
    def _identify_category(self, product: str) -> Optional[str]:
        """Map Bankrate product names to our categories."""
        product = product.lower()
        
        if 'fha' in product:
            if '30' in product or 'year' not in product:  # FHA defaults to 30-year
                return "FHA 30Y"
        elif 'va' in product:
            if '30' in product or 'year' not in product:
                return "VA 30Y"
        elif 'jumbo' in product:
            # Treat jumbo as regular 30Y fixed for now
            if '30' in product or 'year' not in product:
                return "30Y fixed"
        elif 'arm' in product or '/1' in product or '/6' in product:
            if '5' in product or '5/1' in product or '5/6' in product:
                return "5/6 ARM"
            elif '7' in product:
                return "7/6 ARM"
            elif '10' in product:
                return "10/6 ARM"
        elif 'fixed' in product or 'year' in product:
            if '30' in product:
                return "30Y fixed"
            elif '20' in product:
                return "20Y fixed"
            elif '15' in product:
                return "15Y fixed"
            elif '10' in product:
                return "10Y fixed"
        
        return None
    
    def _parse_percentage(self, value: str) -> Optional[float]:
        """Extract float from percentage string like '6.16%' or '6.16'."""
        if not value:
            return None
        try:
            # Remove %, whitespace, and any non-numeric chars except decimal point
            clean = re.sub(r'[^\d.]', '', value)
            if not clean:
                return None
            return float(clean)
        except (ValueError, AttributeError):
            return None
    
    def _term_for_category(self, category: str) -> int:
        """Return term in months for a category."""
        if '15' in category:
            return 180
        elif '20' in category:
            return 240
        elif '10' in category:
            return 120
        return 360  # Default to 30 years
