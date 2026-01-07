# Real vs Sample Data: Complete Guide

## 📊 Overview

The mortgage rate tracker system supports **two types of data**:

1. **REAL DATA** - Live rates scraped from actual lender websites
2. **SAMPLE DATA** - Realistic mock data for testing and fallback

## 🎯 Where Each Type is Used

### Real Data 🟢

**Source**: Live web scraping from lender websites
**Storage**: `offers_normalized` table with `data_source='real'`
**Runs**: `runs` table with `run_type='real'`

**Used When**:
- GitHub Actions daily collector runs (`--run-type real`)
- Manual collector execution for production
- Website displays "Live Rates" badge

**Command**:
```bash
python -m mortgage_tracker.main --run-type real
```

**Current Status** (Run 19):
- ✅ DCU: 1 offer @ 5.75% / 5.933% APR (30Y fixed)
- ⚠️ Metro CU: Quote flow (expected, not parseable)
- ⚠️ Rockland Trust: No static rates (expected)

**Parsers Collecting Real Data**:
- `DCUParser` - Schema.org JSON-LD scraping ✅ Working
- `MetroCUParser` - Gracefully detects quote flows (0 offers expected)
- `RocklandTrustParser` - Gracefully handles missing content (0 offers expected)

---

### Sample Data 🔵

**Source**: Manually curated realistic test data
**Storage**: `offers_normalized` table with `data_source='sample'`
**Runs**: `runs` table with `run_type='sample'`

**Used When**:
- Development and testing
- Website fallback when no real data exists
- Demonstrating UI before parsers are complete
- Quality assurance

**Command**:
```bash
python scripts/add_sample_data.py
```

**Current Status** (Run 15):
- 19 sample offers across 9 lenders
- Includes: DCU, Metro CU, Eastern Bank, Cambridge Savings, PenFed, Navy Federal, Rocket, Wells Fargo, Chase
- Categories: 30Y fixed, 15Y fixed, 5/6 ARM, FHA 30Y, VA 30Y

**Scripts**:
- `scripts/add_sample_data.py` - Add sample data to database
- `scripts/clear_sample_data.py` - Remove all sample data

---

## 🔄 Fallback System

### How It Works

The system uses the RPC function `get_latest_rates_with_fallback(include_sample boolean)` to intelligently serve data:

```sql
-- Returns real data if available, otherwise sample data
SELECT * FROM get_latest_rates_with_fallback(true);
```

**Logic Flow**:
1. Find latest successful real run (`run_type='real'`, status=`success` OR `partial`)
2. Count real offers from that run
3. **IF** real offers exist:
   - Return real data with `is_fallback=false`
   - Website shows **"Live Rates"** badge 🟢
4. **ELSE IF** `include_sample=true`:
   - Find latest successful sample run
   - Return sample data with `is_fallback=true`
   - Website shows **"Sample Data"** badge 🔵
5. **ELSE**:
   - Return empty result

### Website Implementation

**File**: `/Users/Sanjeev/nb/app/rates/page.tsx` (separate repo)

**Key Code**:
```typescript
// Call RPC with fallback enabled
const { data, error } = await supabase
  .rpc('get_latest_rates_with_fallback', { include_sample: true })

// Check fallback status
const isFallback = data[0]?.is_fallback || false

// Display badge
{isFallback ? (
  <Badge variant="secondary">Sample Data</Badge>
) : (
  <Badge variant="default">Live Rates</Badge>
)}
```

**User Experience**:
- Real data available → "Live Rates" badge (green)
- No real data → "Sample Data" badge (gray/secondary)
- User knows exactly what they're looking at

---

## 🗄️ Database Schema

### Tables

#### `runs`
```sql
id              bigint           -- Run ID
run_type        text             -- 'real' or 'sample'
status          text             -- 'started', 'success', 'partial', 'failed'
created_at      timestamptz
finished_at     timestamptz
stats_json      jsonb            -- Run statistics
error_text      text
```

#### `offers_normalized`
```sql
id              bigint           -- Offer ID
run_id          bigint           -- FK to runs.id
source_id       bigint           -- FK to sources.id
data_source     text             -- 'real' or 'sample'
lender_name     text
category        text             -- '30Y fixed', etc.
rate            numeric          -- Interest rate (e.g., 5.75)
apr             numeric          -- APR (e.g., 5.933)
points          numeric
lender_fees     numeric
state           text
loan_amount     numeric
ltv             integer
fico            integer
lock_days       integer
created_at      timestamptz
details_json    jsonb
```

### Views

#### `latest_rates_view`
```sql
-- Only shows REAL data (no sample)
-- Used for: Admin dashboard, monitoring, alerts
SELECT * FROM latest_rates_view WHERE category = '30Y fixed';
```

**Columns**: Same as offers_normalized plus `updated_at`
**Filter**: Only `data_source='real'` from latest successful real run

### Functions

#### `get_latest_rates_with_fallback(include_sample boolean)`
```sql
-- Intelligent fallback: real data preferred, sample as backup
-- Used by: Website
SELECT * FROM get_latest_rates_with_fallback(true);
```

**Returns**: 
- All columns from offers_normalized
- `is_fallback` boolean flag
- Real data when available (is_fallback=false)
- Sample data when not (is_fallback=true)

---

## 📝 Data Flow Examples

### Example 1: Fresh System Start

```
1. Run: python scripts/add_sample_data.py
   → Creates run_id=1, run_type='sample', 19 offers

2. Website loads
   → Calls get_latest_rates_with_fallback(true)
   → No real data exists
   → Returns 19 sample offers with is_fallback=true
   → Shows "Sample Data" badge 🔵

3. Run: python -m mortgage_tracker.main --run-type real
   → Creates run_id=2, run_type='real', 1 offer (DCU)

4. Website refreshes
   → Calls get_latest_rates_with_fallback(true)
   → Real data exists (1 DCU offer)
   → Returns 1 real offer with is_fallback=false
   → Shows "Live Rates" badge 🟢
```

### Example 2: Production Usage

```
1. GitHub Actions runs daily at 7:30 AM ET
   → python -m mortgage_tracker.main --run-type real
   → Creates run with run_type='real'
   → DCU parser succeeds: 1 offer
   → Metro CU parser: 0 offers (quote flow)
   → Rockland Trust parser: 0 offers (no content)
   → Run status: 'partial' (1/3 sources succeeded)

2. Website serves real DCU data all day
   → RPC returns 1 offer with is_fallback=false
   → "Live Rates" badge displayed

3. IF DCU website goes down tomorrow
   → Collector run creates run_id with status='failed'
   → No real offers inserted
   → RPC falls back to sample data
   → Website shows "Sample Data" badge
   → Users still see example rates
```

### Example 3: Development Workflow

```
1. Developer tests new parser locally
   → python -m mortgage_tracker.main --run-type real
   → See real data in terminal

2. Developer wants clean test data
   → python scripts/clear_sample_data.py
   → python scripts/add_sample_data.py
   → Fresh sample data loaded

3. Developer tests website integration
   → Website uses sample data (is_fallback=true)
   → No real collector runs interfere

4. Developer pushes changes
   → GitHub Actions runs with --run-type real
   → Production gets real data
   → Sample data untouched for dev use
```

---

## 🔍 Quality Checks

### Verify Real Data

```bash
# Run collector
python -m mortgage_tracker.main --run-type real

# Check database
SELECT r.id, r.run_type, r.status, COUNT(o.id) as offers
FROM runs r
LEFT JOIN offers_normalized o ON o.run_id = r.id AND o.data_source = 'real'
WHERE r.run_type = 'real'
GROUP BY r.id
ORDER BY r.created_at DESC
LIMIT 5;

# Expected: 
# - Latest run should have status='partial' or 'success'
# - Should have at least 1 offer (from DCU)
```

### Verify Sample Data

```bash
# Check sample data exists
SELECT COUNT(*) FROM offers_normalized WHERE data_source = 'sample';
# Expected: 19

# Check sample run
SELECT * FROM runs WHERE run_type = 'sample' ORDER BY created_at DESC LIMIT 1;
# Expected: status='success'
```

### Verify RPC Function

```sql
-- Test real data (should return DCU offer)
SELECT 
  lender_name, 
  category, 
  rate, 
  apr, 
  data_source, 
  is_fallback
FROM get_latest_rates_with_fallback(true)
WHERE category = '30Y fixed'
LIMIT 5;

-- Expected result if real data exists:
-- lender_name | category   | rate | apr   | data_source | is_fallback
-- DCU         | 30Y fixed  | 5.75 | 5.933 | real        | false

-- Expected result if no real data:
-- [multiple lenders] | 30Y fixed | [various] | [various] | sample | true
```

### Verify Website

```typescript
// In browser console after loading rates page
console.log(rates)
// Should see array of rate objects with data_source and is_fallback fields

// Check badge
document.querySelector('[class*="badge"]').textContent
// Should be "Live Rates" (if real data) or "Sample Data" (if fallback)
```

---

## 🚀 Deployment Checklist

- [x] Database migration 002 applied (run_type, data_source columns)
- [x] RPC function created (get_latest_rates_with_fallback)
- [x] Collector updated with --run-type argument
- [x] Sample data loaded (19 offers)
- [x] Real data collection tested (DCU working)
- [x] GitHub Actions updated (--run-type real)
- [x] Website updated (RPC call with is_fallback badge)
- [ ] Verify website deployment (check badge displays correctly)
- [ ] Monitor first production run (GitHub Actions)
- [ ] Verify RPC returns correct data type

---

## 📈 Monitoring

### Key Metrics

1. **Real Data Collection Rate**
   - Target: At least 1 lender returning real data per day
   - Current: 1/3 sources (DCU working)

2. **Run Success Rate**
   - Track: `runs` table status distribution
   - Alert if: No successful/partial runs in 48 hours

3. **Data Freshness**
   - Real data: Updated daily at 7:30 AM ET
   - Sample data: Manual updates as needed

4. **Fallback Usage**
   - Monitor `is_fallback=true` frequency
   - Indicates real data collection issues if high

### SQL Monitoring Queries

```sql
-- Recent runs summary
SELECT 
  run_type,
  status,
  COUNT(*) as count,
  MAX(created_at) as latest_run
FROM runs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY run_type, status
ORDER BY latest_run DESC;

-- Data source breakdown
SELECT 
  data_source,
  COUNT(*) as total_offers,
  COUNT(DISTINCT source_id) as unique_lenders,
  MIN(created_at) as oldest,
  MAX(created_at) as newest
FROM offers_normalized
GROUP BY data_source;

-- Latest offers by type
SELECT 
  o.data_source,
  s.name as lender,
  o.category,
  o.rate,
  o.apr,
  o.created_at
FROM offers_normalized o
JOIN sources s ON o.source_id = s.id
WHERE o.run_id IN (
  SELECT id FROM runs 
  WHERE created_at > NOW() - INTERVAL '24 hours'
)
ORDER BY o.created_at DESC;
```

---

## 🎓 Summary

| Aspect | Real Data | Sample Data |
|--------|-----------|-------------|
| **Source** | Live scraping | Manual scripts |
| **Purpose** | Production rates | Testing/fallback |
| **Command** | `--run-type real` | `add_sample_data.py` |
| **Database** | `data_source='real'` | `data_source='sample'` |
| **Website Badge** | "Live Rates" 🟢 | "Sample Data" 🔵 |
| **Priority** | Primary | Backup |
| **Update Freq** | Daily (automated) | Manual |
| **Current Count** | 1 offer (DCU) | 19 offers (9 lenders) |

**The system automatically prefers real data and falls back to sample data gracefully.**

Users always see something useful, and the badge makes it clear which type they're viewing! 🎯
