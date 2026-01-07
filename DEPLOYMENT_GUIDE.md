# Migration & Deployment Guide

## Overview
This guide covers deploying the data separation system (real vs sample data) with enhanced collector features.

---

## STEP 1: Apply Database Migration

The migration file is ready at: `supabase/migrations/002_flags.sql`

### Option A: Via Supabase Dashboard (Recommended)
1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor**
4. Click **New Query**
5. Copy the entire contents of `supabase/migrations/002_flags.sql`
6. Paste and click **Run**
7. Verify success (should see "Success. No rows returned")

### Option B: Via psql (if you have direct database access)
```bash
# Get your connection string from Supabase Dashboard > Settings > Database
# Format: postgres://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

psql "postgres://postgres:...@db.xxx.supabase.co:5432/postgres" \
  -f supabase/migrations/002_flags.sql
```

### What This Migration Does:
- ✅ Adds `run_type` column to `runs` table ('real' or 'sample')
- ✅ Adds `data_source` column to `offers_normalized` ('real' or 'sample')
- ✅ Updates `latest_rates_view` to show only real data
- ✅ Creates `get_latest_rates_with_fallback(include_sample)` RPC function
- ✅ Backfills existing data as 'real'

---

## STEP 2: Test Collector Locally

### Clear Old Sample Data
```bash
cd /Users/Sanjeev/mrt
export $(cat .env | xargs)
python3 scripts/clear_sample_data.py
```

### Run Real Collector
```bash
python3 -m src.mortgage_tracker.main --run-type real
```

Expected output:
```
2026-01-06 15:30:00 [INFO] Starting collector run (type=real, sources=sources.yaml)
2026-01-06 15:30:01 [INFO] Created run 8 (type=real)
2026-01-06 15:30:01 [INFO] ⏭️  Skipping disabled source: Rockland Federal Credit Union
2026-01-06 15:30:02 [INFO] 📥 Fetching DCU (Digital Federal Credit Union) from https://...
2026-01-06 15:30:03 [INFO] ✅ Parsed 1 offers from DCU (Digital Federal Credit Union)
2026-01-06 15:30:03 [INFO] ✅ DCU (Digital Federal Credit Union): Inserted 1 offers (snapshot_id=42)
2026-01-06 15:30:04 [INFO] 📥 Fetching Metro Credit Union (MA) from https://...
2026-01-06 15:30:05 [INFO] ⚠️  No offers parsed from Metro Credit Union (MA)
2026-01-06 15:30:06 [INFO] 📥 Fetching Rockland Trust from https://...
2026-01-06 15:30:07 [INFO] ⚠️  No offers parsed from Rockland Trust
2026-01-06 15:30:07 [INFO] 🏁 Run 8 finished with status=partial
   Sources: 3 enabled, 1 success, 2 failed, 47 skipped
   Offers inserted: 1
```

### Run Sample Data Generator
```bash
python3 scripts/add_sample_data.py
```

### Verify Database
Check that you now have:
- At least one run with `run_type='real'` and offers with `data_source='real'`
- At least one run with `run_type='sample'` and offers with `data_source='sample'`

Query to verify:
```sql
-- Check runs
SELECT id, run_type, status, created_at, (stats_json->>'offers_inserted')::int as offers
FROM runs 
ORDER BY created_at DESC 
LIMIT 5;

-- Check offers by data_source
SELECT data_source, category, COUNT(*) as count
FROM offers_normalized
GROUP BY data_source, category
ORDER BY data_source, category;
```

---

## STEP 3: Update Website

### Copy New rates Page
1. Navigate to your website repo:
   ```bash
   cd /Users/Sanjeev/nb
   ```

2. Replace `app/rates/page.tsx` with the contents from:
   `/Users/Sanjeev/mrt/WEBSITE_UPDATE_rates_page.tsx`

3. Verify the changes:
   - Uses `get_latest_rates_with_fallback` RPC function
   - Shows badge: "Live Rates" (green) or "Sample Data" (amber)
   - Sorts by APR then rate
   - Limits to top 10 per category

### Test Locally
```bash
cd /Users/Sanjeev/nb
npm run dev
```

Visit http://localhost:3000/rates

- If you have real data: Should show "Live Rates" badge with DCU
- If only sample data: Should show "Sample Data" badge with all lenders

### Deploy to Production
```bash
git add app/rates/page.tsx
git commit -m "feat: Use RPC with real/sample fallback and status badges"
git push
```

Vercel will auto-deploy. Visit: https://www.namastebostonhomes.com/rates

---

## STEP 4: Update GitHub Actions

Update `.github/workflows/daily.yml`:

```yaml
- name: Run mortgage collector
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE }}
    RUN_TYPE: real  # Add this line
  run: |
    python -m src.mortgage_tracker.main --run-type real
```

Commit and push:
```bash
cd /Users/Sanjeev/mrt
git add .github/workflows/daily.yml
git commit -m "chore: Set RUN_TYPE=real for GitHub Actions"
git push
```

---

## STEP 5: Commit All Changes

```bash
cd /Users/Sanjeev/mrt

# Review changes
git status
git diff

# Commit everything
git add -A
git commit -m "feat: Data separation system with real/sample flags and enhanced collector

- Add run_type and data_source columns with migration 002
- Implement parser registry for pluggable parsers
- Refactor main.py with enhanced stats and per-source error handling
- Add Metro CU and Rockland Trust parsers (quote-flow detection)
- Update sample data scripts to mark data_source=sample
- Add clear_sample_data.py script
- Create RPC function get_latest_rates_with_fallback
- Support --run-type CLI argument (real|sample)
- Improve logging with emoji indicators"

git push
```

---

## STEP 6: Verification Checklist

### Database
- [ ] Migration 002 applied successfully
- [ ] `runs` table has `run_type` column
- [ ] `offers_normalized` table has `data_source` column
- [ ] `latest_rates_view` returns only real data
- [ ] RPC function `get_latest_rates_with_fallback` exists

### Collector
- [ ] Can run with `--run-type real`
- [ ] Can run with `--run-type sample`
- [ ] DCU parser returns 1 offer
- [ ] Metro CU parser logs "quote flow" and returns 0 offers
- [ ] Rockland Trust parser logs "application flow" and returns 0 offers
- [ ] Stats include sources_total, sources_enabled, sources_success, sources_failed

### Website
- [ ] Shows "Live Rates" badge when real data exists
- [ ] Shows "Sample Data" badge when falling back to sample
- [ ] Rates sorted by APR then rate
- [ ] Top 10 per category
- [ ] Timestamp shows EST timezone

### GitHub Actions
- [ ] Workflow has RUN_TYPE=real environment variable
- [ ] Daily cron runs successfully
- [ ] Real data appears on website after cron run

---

## Next Steps

### Incrementally Add More Parsers

To add a new lender parser:

1. **Check if the site publishes rates**
   ```bash
   curl -s "https://lender.com/rates" | grep -i "rate\|apr" | head -20
   ```

2. **Create parser file**
   ```bash
   # Example: src/mortgage_tracker/parsers/salem_five.py
   touch src/mortgage_tracker/parsers/salem_five.py
   ```

3. **Implement parser** (copy from dcu.py or metro_cu.py as template)

4. **Register parser** in `src/mortgage_tracker/parsers/__init__.py`:
   ```python
   from .salem_five import SalemFiveParser
   
   PARSER_REGISTRY = {
       # ... existing parsers
       'salem_five': SalemFiveParser,
   }
   ```

5. **Enable in sources.yaml**:
   ```yaml
   - id: salem_five
     name: Salem Five Bank
     parser_key: salem_five
     rate_url: https://www.salemfive.com/rates
     enabled: true
   ```

6. **Test locally**:
   ```bash
   python3 -m src.mortgage_tracker.main --run-type real
   ```

### Priority Lenders to Implement Next

Based on your list, good candidates for parsers:
1. **Cape Cod 5** - Regional bank, may publish rates
2. **Eastern Bank** - Large MA bank
3. **PenFed** - National credit union with published rates
4. **Navy Federal** - Large credit union

### Maintaining Sample Data

Keep sample data fresh:
```bash
# Clear old sample data
python3 scripts/clear_sample_data.py

# Regenerate with updated rates
python3 scripts/add_sample_data.py
```

This keeps the UI populated while you build real parsers incrementally.

---

## Troubleshooting

### "Parser not found" error
- Check that parser is imported in `parsers/__init__.py`
- Check that parser_key in sources.yaml matches registry key

### Website shows "Sample Data" when it should show "Live Rates"
- Verify real run completed successfully (check Supabase runs table)
- Check that real offers exist: `SELECT * FROM offers_normalized WHERE data_source='real'`
- Clear sample data if it's interfering

### Migration fails
- Check if columns already exist (migration is idempotent but may show warnings)
- Verify you're using service role key, not anon key
- Check Supabase logs in dashboard

---

## Summary

You now have:
- ✅ Real vs sample data separation
- ✅ Smart fallback (shows sample only if no real data)
- ✅ Parser registry system for easy extension
- ✅ Enhanced collector with detailed stats
- ✅ 3 working parsers: DCU (returns data), Metro CU & Rockland Trust (graceful failures)
- ✅ Website badge system showing data source
- ✅ Scripts to manage sample data

**Current State:**
- DCU parser works → returns real 5.75% rate
- Metro CU & Rockland Trust detect quote flows → return 0 offers (expected)
- Website falls back to sample data to keep UI populated
- As you add more real parsers, they'll automatically replace sample data
