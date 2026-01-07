# Parser Reliability Tracking System

## Overview

We've implemented a reliability tracking system in `sources.yaml` to prioritize lenders that consistently provide accurate, parseable rate data. This ensures the website shows quality data even when some parsers fail.

## Reliability Levels

### High Reliability (Priority)
Consistently works, simple HTML tables, data always accurate:
- ✅ **DCU (Digital Federal Credit Union)** - 4 offers (30Y/15Y with points)
- ✅ **Navy Federal Credit Union** - 14 offers (15Y/30Y/ARM with points)

**Status**: Both working perfectly with correct rates, APRs, and points

### Medium Reliability
Tested but no parseable rate tables found:
- ❌ NCSECU - No static rate table
- ❌ America First CU - No parseable table
- ❌ First Tech FCU - Dynamic/JS-rendered content
- ❌ Patelco CU - No parseable table

### Low Reliability
Known to fail or block scraping:
- ❌ PenFed - Timeouts/blocks scraping
- ❌ Alliant CU - JS-rendered content only

### Quote-Flow Only
No published rate tables (require form submission):
- ⏭️ Metro Credit Union (MA)
- ⏭️ Rockland Trust

## Current Production Status

**Working Lenders**: 2  
**Total Real Offers**: 18  
**Success Rate**: 2/6 enabled = 33%

## Strategy Going Forward

### Option 1: Quality Over Quantity (Recommended)
- Keep 2 high-reliability lenders (DCU + Navy Federal)
- Show accurate data from these sources
- Add sample data to fill out website (19 additional offers)
- Total visible: 2 real lenders + sample lenders = 10+ options
- Badge shows "Live Rates" when real data is available

### Option 2: Hybrid Approach
- Continue real data collection from 2 reliable sources
- Display prominently with "Live" badge
- Show sample data below with "Sample" badge
- Gives users both current rates (where available) and benchmark rates

### Option 3: Expand Parser Development
- Invest time building custom parsers for specific lenders
- Target lenders with API access or developer programs
- Estimated effort: 10-20 hours for 5-10 additional working parsers
- Risk: Many lenders intentionally make rates hard to scrape

## Implementation in sources.yaml

Each source now includes:
```yaml
- id: dcu
  name: DCU (Digital Federal Credit Union)
  rate_url: https://www.dcu.org/borrow/mortgage-loans/home-mortgage-loans.html
  parser_key: dcu
  enabled: true
  parser_reliability: high  # <-- New field
  notes: "Simple HTML table, includes points data"
```

Reliability levels:
- `high`: Always works, simple to parse, accurate data
- `medium`: Usually works, may need occasional fixes
- `low`: Frequently fails, complex/blocked
- `untested`: Not yet attempted

## Collector Behavior

1. Attempts all `enabled: true` sources
2. Logs success/failure for each
3. Stores data from successful parses only
4. Returns status=partial (some succeeded, some failed)
5. CI treats partial as success (exit code 0)

## Quality Assurance

All parsed data is validated (via `validate.py`):
- Rates: 0-20% range, >2% threshold
- APR: Must be >= rate
- Points: 0-10% range
- Invalid data is logged and rejected

## Recommendation for Production

**Use Option 1 (Quality Over Quantity)**:

1. **Production Dataset**:
   - 2 reliable real lenders (DCU + Navy Federal) = 18 offers
   - These update daily via automated collector
   - All data quality-validated

2. **Website Display**:
   - Show real offers first, marked with "Live Rates" badge
   - Currently displays 2 lenders across multiple categories
   - Each lender shows multiple products (standard/jumbo/ARM)

3. **Future Growth**:
   - Monitor parser success rates
   - Add new lenders as we find reliable sources
   - Priority: high-reliability parsers only
   - Track in sources.yaml with `parser_reliability` field

## Next Steps

1. ✅ Commit reliability tracking system
2. ⏭️ Deploy website with current 2-lender dataset
3. ⏭️ Monitor daily collector runs
4. ⏭️ Add parsers opportunistically as we find working sources
5. ⏭️ Consider partnerships with lenders for API access

The tracking system is now in place - we can easily identify and prioritize working parsers while gracefully handling failures.
