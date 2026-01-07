import logging
import re
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser

from .base import BaseParser

logger = logging.getLogger("mortgage_tracker.parsers.dcu")


class DCURateTableParser(HTMLParser):
    """HTML parser to extract DCU mortgage rate tables."""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_tag = None
        self.current_row = []
        self.rows = []
        self.table_depth = 0
        
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table_depth += 1
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.current_tag = tag
            
    def handle_endtag(self, tag):
        if tag == 'table':
            self.table_depth -= 1
            if self.table_depth == 0:
                self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ('td', 'th') and self.in_cell:
            self.in_cell = False
            
    def handle_data(self, data):
        if self.in_cell:
            self.current_row.append(data.strip())


class DCUParser(BaseParser):
    """Parser for DCU (Digital Federal Credit Union) mortgage rates from HTML tables."""
    
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers: List[Dict[str, Any]] = []
        
        if not text:
            logger.warning("no_text_provided")
            return offers
        
        try:
            parser = DCURateTableParser()
            parser.feed(text)
            
            # Find rows with mortgage rate data
            # Expected format: ["30 Years Fixed", "5.750%", "5.933%", "1.625%", "$5.84"]
            # Columns: Product, Rate, APR, Points, EMP
            for row in parser.rows:
                if len(row) < 4:
                    continue
                    
                product = row[0].lower()
                
                # Identify category
                category = None
                if '30' in product and 'year' in product:
                    if 'jumbo' in product:
                        category = "30Y fixed"  # Treat jumbo as 30Y for now
                    else:
                        category = "30Y fixed"
                elif '15' in product and 'year' in product:
                    category = "15Y fixed"
                elif '5' in product and ('arm' in product or '/' in product):
                    category = "5/6 ARM"
                    
                if not category:
                    continue
                    
                # Parse rate, APR, points
                rate = self._parse_percentage(row[1]) if len(row) > 1 else None
                apr = self._parse_percentage(row[2]) if len(row) > 2 else None
                points = self._parse_percentage(row[3]) if len(row) > 3 else None
                
                if rate is None or apr is None:
                    continue
                    
                term_years = 30 if '30' in category else (15 if '15' in category else 30)
                
                offers.append({
                    "lender_name": "DCU (Digital Federal Credit Union)",
                    "category": category,
                    "rate": rate,
                    "apr": apr,
                    "points": points if points is not None else 0.0,
                    "lender_fees": None,
                    "term_months": term_years * 12,
                })
                
                logger.info(f"parsed_offer: {category} @ {rate}% (APR {apr}%, points {points}%)")
            
            if not offers:
                logger.warning("no_rates_found_in_tables")
                
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
            if not clean:
                return None
            return float(clean)
        except (ValueError, AttributeError):
            return None
