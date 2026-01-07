"""Generic HTML table parser for mortgage rates."""
import logging
import re
from typing import List, Dict, Any, Optional
from html.parser import HTMLParser

logger = logging.getLogger("mortgage_tracker.parsers.generic_table")


class SimpleHTMLTableParser(HTMLParser):
    """Generic HTML table parser."""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
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


def parse_percentage(value: str) -> Optional[float]:
    """Extract float from percentage string like '5.750%' or '5.750'."""
    if not value:
        return None
    try:
        # Remove %, $, commas and any whitespace
        clean = value.replace('%', '').replace('$', '').replace(',', '').strip()
        if not clean or clean == '—' or clean == '-' or clean.lower() == 'n/a':
            return None
        return float(clean)
    except (ValueError, AttributeError):
        return None


def identify_category(product_text: str) -> Optional[str]:
    """Identify loan category from product text."""
    product = product_text.lower()
    
    # Check for loan type
    if 'fha' in product:
        if '30' in product:
            return "FHA 30Y"
    elif 'va' in product:
        if '30' in product:
            return "VA 30Y"
    elif 'arm' in product or '/1' in product or '/6' in product:
        if '5' in product:
            return "5/6 ARM"
        elif '7' in product:
            return "7/6 ARM"
        elif '10' in product:
            return "10/6 ARM"
    elif 'fixed' in product or 'fix' in product:
        if '30' in product:
            return "30Y fixed"
        elif '15' in product:
            return "15Y fixed"
        elif '20' in product:
            return "20Y fixed"
        elif '10' in product:
            return "10Y fixed"
    
    # Fallback: just look for year mentions
    if '30' in product and 'year' in product:
        return "30Y fixed"
    elif '15' in product and 'year' in product:
        return "15Y fixed"
    elif '20' in product and 'year' in product:
        return "20Y fixed"
        
    return None


def extract_offers_from_html_table(
    html: str,
    lender_name: str,
    rate_col: int = 1,
    apr_col: int = 2,
    points_col: Optional[int] = None,
    product_col: int = 0,
    min_columns: int = 3
) -> List[Dict[str, Any]]:
    """
    Generic function to extract offers from HTML tables.
    
    Args:
        html: HTML content
        lender_name: Name of the lender
        rate_col: Column index for interest rate (0-indexed)
        apr_col: Column index for APR
        points_col: Column index for points (optional)
        product_col: Column index for product/term name
        min_columns: Minimum number of columns required
    """
    offers = []
    parser = SimpleHTMLTableParser()
    parser.feed(html)
    
    for row in parser.rows:
        if len(row) < min_columns:
            continue
            
        # Extract product/category
        if product_col >= len(row):
            continue
        category = identify_category(row[product_col])
        if not category:
            continue
            
        # Parse rate and APR
        rate = parse_percentage(row[rate_col]) if rate_col < len(row) else None
        apr = parse_percentage(row[apr_col]) if apr_col < len(row) else None
        points = parse_percentage(row[points_col]) if points_col is not None and points_col < len(row) else None
        
        # Validate
        if rate is None or apr is None:
            continue
        if rate <= 0 or rate > 20 or apr <= 0 or apr > 20:
            continue
            
        term_years = 30
        if '15' in category:
            term_years = 15
        elif '20' in category:
            term_years = 20
        elif '10' in category:
            term_years = 10
            
        offers.append({
            "lender_name": lender_name,
            "category": category,
            "rate": rate,
            "apr": apr,
            "points": points if points is not None else 0.0,
            "lender_fees": None,
            "term_months": term_years * 12,
        })
        
    return offers
