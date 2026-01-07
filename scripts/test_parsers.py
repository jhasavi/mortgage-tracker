#!/usr/bin/env python3
"""Quick test script to check which lender parsers work."""

import sys
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mortgage_tracker.parsers.dcu import DCUParser

# Test sources with their rate URLs
TEST_SOURCES = [
    ("DCU", "https://www.dcu.org/about/rates.html", DCUParser),
    # Add more as we implement them
]

def test_parser(name, url, parser_class):
    """Test a parser against its source."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        parser = parser_class()
        offers = parser.parse(text=resp.text)
        
        if not offers:
            print(f"❌ No offers found")
            return False
            
        print(f"✅ Found {len(offers)} offers:")
        for i, offer in enumerate(offers[:5], 1):  # Show first 5
            print(f"  {i}. {offer['category']}: {offer['rate']}% APR {offer['apr']}% "
                  f"Points {offer.get('points', 'N/A')}")
            
            # Data quality checks
            if offer['rate'] is None or offer['rate'] <= 0 or offer['rate'] > 20:
                print(f"    ⚠️  Invalid rate: {offer['rate']}")
            if offer['apr'] is None or offer['apr'] <= 0 or offer['apr'] > 20:
                print(f"    ⚠️  Invalid APR: {offer['apr']}")
            if offer.get('points') is not None and (offer['points'] < 0 or offer['points'] > 10):
                print(f"    ⚠️  Invalid points: {offer['points']}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    results = {}
    for name, url, parser_class in TEST_SOURCES:
        results[name] = test_parser(name, url, parser_class)
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
