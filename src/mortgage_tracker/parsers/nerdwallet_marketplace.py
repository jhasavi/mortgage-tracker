"""Parser for NerdWallet mortgage rates marketplace/aggregator page."""
import logging
import re
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.nerdwallet_marketplace")


class NerdWalletTableParser(HTMLParser):
    """Parse NerdWallet's mortgage rate tables."""
    
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


class NerdWalletMarketplaceParser(BaseParser):
    """
    Parser for NerdWallet mortgage rates aggregator.
    
    NerdWallet publishes daily mortgage rate data from multiple lenders
    in a clean table format with columns: Loan Type | Rate | APR
    
    This provides excellent data coverage across:
    - Fixed rate mortgages (30, 20, 15, 10 year)
    - ARMs (3/1, 5/1, 7/1, 10/1)
    - Government loans (FHA, VA)
    """
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers = []
        
        if not text:
            logger.warning("No text provided")
            return offers
        
        try:
            parser = NerdWalletTableParser()
            parser.feed(text)
            
            # NerdWallet typically has tables with format:
            # Loan Type | Rate | APR
            
            for row in parser.rows:
                if len(row) < 3:
                    continue
                
                product = row[0].lower()
                
                # Skip header rows
                if 'loan type' in product or 'product' in product or 'type' in product:
                    continue
                
                # Identify category
                category = self._identify_category(product)
                if not category:
                    continue
                
                # Extract rate and APR
                rate = self._parse_percentage(row[1])
                apr = self._parse_percentage(row[2])
                
                if rate is None or apr is None:
                    continue
                
                # Sanity check
                if rate < 2.0 or rate > 15.0 or apr < 2.0 or apr > 20.0:
                    logger.warning(f"Rate out of range: {product} {rate}% / {apr}%")
                    continue
                
                # Check if APR is reasonably >= rate (allow small tolerance for rounding)
                if apr < rate - 0.2:
                    logger.warning(f"APR < rate: {product} rate={rate}% apr={apr}%")
                    continue
                
                offers.append({
                    "lender_name": "NerdWallet National Average",
                    "category": category,
                    "rate": rate,
                    "apr": apr,
                    "points": None,
                    "lender_fees": None,
                    "term_months": self._term_for_category(category),
                    "source_type": "aggregator",
                    "source_name": "NerdWallet",
                })
                
                logger.info(f"Parsed NerdWallet: {category} @ {rate}% (APR {apr}%)")
            
            if not offers:
                logger.warning("No rates found in NerdWallet tables")
            else:
                logger.info(f"NerdWallet parser extracted {len(offers)} offers")
                
        except Exception as e:
            logger.error(f"NerdWallet parse error: {str(e)}")
        
        return offers
    
    def _identify_category(self, product: str) -> Optional[str]:
        """Map NerdWallet product names to our categories."""
        product = product.lower()
        
        if 'fha' in product:
            if '30' in product or 'year' not in product:
                return "FHA 30Y"
        elif 'va' in product:
            if '30' in product or 'year' not in product:
                return "VA 30Y"
        elif 'arm' in product or '/1' in product or '/6' in product:
            if '5' in product or '5/1' in product or '5/6' in product:
                return "5/6 ARM"
            elif '7' in product:
                return "7/6 ARM"
            elif '10' in product:
                return "10/6 ARM"
            elif '3' in product:
                return "3/1 ARM"
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
        """Extract float from percentage string like '6.03%' or '6.03'."""
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
