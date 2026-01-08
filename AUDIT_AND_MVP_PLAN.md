# Mortgage Rate Tracker — Audit & MVP Requirements

**Date:** January 7, 2026  
**Live Page:** https://www.namastebostonhomes.com/rates

---

## 1. AUDIT SUMMARY — Why the Page Shows Wrong/Repeated Data

### Top 5 Root Causes

| # | Root Cause | Impact | Evidence |
|---|------------|--------|----------|
| **1** | **Only 1 real lender works** | Page fills with duplicates or sample data | DCU is the **only** source producing real offers. 5 other enabled parsers (Metro CU, Rockland Trust, First Tech, Patelco, Navy Federal) all fail silently or return empty results. |
| **2** | **Fallback mixes sample data** | Real + sample data appears together | The RPC `get_latest_rates_with_fallback(include_sample: true)` returns sample data (marked `is_fallback=true`) when real data is insufficient. The website calls this with `include_sample: true`, causing fake lender rows (Wells Fargo, Chase, Rocket Mortgage) to appear **that are not actually parsed—they're hardcoded** in `add_sample_data.py`. |
| **3** | **Broken source URLs / Parsers** | 0 offers from most sources | Navy Federal URL has anti-bot redirects; First Tech returns 404; Patelco's rates page only shows savings products (no mortgage rates); Metro CU and Rockland Trust require quote flows—none produce parseable HTML. |
| **4** | **No deduplication at display time** | Same lender repeated | The RPC sorts by `(category, apr, rate)` but does not deduplicate by `lender_name + category`. If multiple run offers exist, or sample duplicates real names, rows repeat. |
| **5** | **No data-quality enforcement** | Garbage rates published | The `validate.py` module exists but is **never called** in the ingest pipeline. Plausibility checks (rate 2–10%, APR ≥ rate) are not enforced before insert. A parser returning `0.0%` or `25%` rates would still be inserted. |

### Data Flow Summary

```
sources.yaml (6 enabled)
        ↓
   main.py → fetch_url → parser.parse()
        ↓
   normalize_offers() → insert to offers_normalized (data_source='real')
        ↓
   Supabase RPC get_latest_rates_with_fallback(true)
        ↓
   Returns: real offers (if any) + sample fallback (if include_sample=true)
        ↓
   Website /rates renders table
```

**Problem:** Only DCU returns valid offers. Everything else is either sample fallback or empty.

---

## 2. MVP REQUIREMENTS — Acceptance Criteria

These are **testable behaviors**, not implementation instructions.

### A. Public Rates Page

| ID | Requirement | Acceptance Test |
|----|-------------|-----------------|
| A1 | Display 5 loan categories: 30Y fixed, 15Y fixed, 5/6 ARM, FHA 30Y, VA 30Y | Visiting /rates shows a table/section for each category |
| A2 | Show **≥10 distinct lender names** with **real parsed data** | Each category table lists offers from at least 10 different lenders; no lender row is from hardcoded sample data |
| A3 | **No duplicate rows** for same lender + category unless intentionally showing multiple point/rate options | Given lender X in category Y, at most 1 row (or labeled variants like "0 points" vs "1 point") |
| A4 | Display "As of" timestamp and quote assumptions (State, Loan Amount, LTV, FICO, Lock, Points Policy) | Header or footer shows metadata; timestamp reflects latest successful run |
| A5 | Indicate **data freshness badge**: "Live Rates" (green) when from real run < 48 h old; "Stale" (amber) if > 48 h; "Sample/Demo" (red) if fallback | Badge reflects actual data state |
| A6 | Rate/APR/Points columns; if points unavailable, show "N/A" rather than 0 | No false zeros; missing data explicitly labeled |

### B. Automated Data Collection

| ID | Requirement | Acceptance Test |
|----|-------------|-----------------|
| B1 | Runs **automatically once per day** (GitHub Actions cron or equivalent) | GitHub Actions workflow triggers daily; commits/artifacts show daily run logs |
| B2 | Pulls from **≥10 automated sources** (no manual entry) | `sources.yaml` has ≥10 enabled entries with working parser_key; each produces ≥1 offer |
| B3 | Stores **raw snapshots** (HTML/JSON) and **normalized offers** | `rate_snapshots` and `offers_normalized` tables contain data per run |
| B4 | **Sanity checks** at ingest time: rate ∈ [2.0, 12.0], APR ≥ rate, APR ∈ [2.0, 15.0] | Offers outside range are rejected/flagged, not inserted |
| B5 | Source failures **do not publish garbage**: failing parser → source marked "unavailable" or skipped | On parse error, no fake offer inserted; stats show `sources_failed` count |
| B6 | Run status: "success" if 100% sources ok; "partial" if ≥1 but <100%; "failed" if 0 | Supabase `runs.status` column reflects this |

### C. Data Quality & Accuracy

| ID | Requirement | Acceptance Test |
|----|-------------|-----------------|
| C1 | **Unique key** = `lender_name + category + (loan_amount, ltv, fico, lock_days, points)` | No two rows in a single run share the same key |
| C2 | Deduplicate per run **before insert** | Query `offers_normalized` for a run shows no key duplicates |
| C3 | **Prefer APR for ranking** if present; else rate | ORDER BY uses COALESCE(apr, rate) |
| C4 | If points unknown, store NULL and display "N/A" | Column is nullable; UI shows "N/A" not "0" |
| C5 | Display only **latest successful real run** (status in success, partial) | RPC/view filters by max(run_id) where run_type='real' and status in ('success','partial') |
| C6 | **Sample/demo data is clearly separated** and only shown if real data missing | is_fallback flag or separate sample table; never mixed into live tables unless flagged |

### D. Alerts (Subscriber Notifications)

| ID | Requirement | Acceptance Test |
|----|-------------|-----------------|
| D1 | Visitor can subscribe with: email, category, threshold (e.g., APR ≤ 6.5%) | Subscription form on /rates or /alerts; record stored in DB |
| D2 | System evaluates alerts **daily after collection run** | GitHub Action step or cron job checks thresholds post-run |
| D3 | Email sent when condition met, includes: current rate, lender, unsubscribe link | Email received; clicking unsubscribe removes subscription |
| D4 | **Rate-limit**: max 1 alert email per subscriber per day | Subscriber cannot receive 10 emails in one day |
| D5 | **Confirmation email** on signup (anti-abuse) | New subscription triggers confirmation email; only confirmed subs receive alerts |
| D6 | Unsubscribe link in every email | Every alert email contains working unsubscribe link |

### E. Monitoring & Ops

| ID | Requirement | Acceptance Test |
|----|-------------|-----------------|
| E1 | **Health dashboard** shows: sources attempted, succeeded, failed, offers published, last run status | Admin page or Supabase dashboard query shows these metrics |
| E2 | Failures result in **reduced lender count + "partial" indicator**, not duplicated junk | If 5/10 sources fail, page shows 5 lenders (not 10 with garbage) |
| E3 | **Logs retained** for at least 7 days | GitHub Actions artifacts or Supabase logs queryable for past week |
| E4 | **No breaking deployments**: site always shows something (stale real data or labeled sample fallback) | If all sources fail, page shows previous run's data or sample with clear badge |

---

## 3. RESET RECOMMENDATION

### Verdict: **Partial Reset — Keep Infrastructure, Replace Data Sources**

| Component | Keep | Rebuild | Reason |
|-----------|------|---------|--------|
| Supabase schema | ✅ Keep | — | Tables are fine; RPC needs minor fix (lender_id bug) |
| Collector architecture | ✅ Keep | — | main.py, fetch.py, normalize.py, parser registry are solid |
| Parser implementations | — | 🔄 Replace | 90% of parsers fail; need new sources |
| sources.yaml | — | 🔄 Replace | Most URLs are broken/blocked; replace with aggregator sources |
| Website (Next.js) | ✅ Keep | — | Display logic is fine; just needs correct RPC call |
| GitHub Actions | ✅ Keep | — | Daily workflow structure is correct |
| Sample data | ❌ Remove | — | Delete `add_sample_data.py` fallback; it masks real failures |
| Alert system | — | 🆕 Build | Not yet implemented; build from scratch |

### Key Changes Required

1. **Replace 10 broken lender parsers with 2–3 aggregator sources** (Bankrate, NerdWallet, Zillow) that have 10+ lenders each in static HTML.
2. **Remove sample fallback** — show "No data" with a badge instead of fake data.
3. **Add validation** — call `validate_offer()` before insert.
4. **Fix RPC function** — remove `lender_id` reference (apply 003_fix_rpc.sql).
5. **Add deduplication** at insert time (unique constraint or UPSERT).

---

## 4. TARGET LENDER SOURCES — 10 Parseable Sources

Based on URL investigation, **direct lender parsing is unreliable** (anti-bot, quote flows, JS rendering). The pragmatic approach is to parse **aggregator sites** that already compile 10+ lenders.

### Recommended Strategy: Aggregator-First

| Priority | Source | URL | Format | Lenders | Notes |
|----------|--------|-----|--------|---------|-------|
| **1** | **NerdWallet** | https://www.nerdwallet.com/mortgages/mortgage-rates | Static HTML table | 10+ | Cleanest HTML; daily updates; no blocking; shows Rate, APR, Points |
| **2** | **Bankrate** | https://www.bankrate.com/mortgages/mortgage-rates/ | Static HTML table | 10+ | Timestamps included; Purchase + Refinance; reliable |
| **3** | **Zillow** | https://www.zillow.com/mortgage-rates/ | Static HTML cards | 10+ | Source for NerdWallet; includes points/costs |

### What This Provides

- **One aggregator parser** (e.g., Bankrate) gives you **10+ distinct lenders** automatically:
  - National banks (Chase, Wells Fargo, Bank of America)
  - Credit unions (Navy Federal, PenFed)
  - Non-banks (Rocket, loanDepot)
  - Regional lenders

- **Data includes**: 30Y, 15Y, 20Y, 10Y fixed; FHA, VA; ARMs

### Backup Direct-Lender Sources (if aggregators blocked)

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| DCU | https://www.dcu.org/borrow/mortgage-loans/home-mortgage-loans.html | ✅ Working | Keep existing parser |
| Ent CU (Colorado) | https://www.ent.com/rates/ | ⚠️ Partial | Only shows APR, needs rate extraction |
| Alliant CU | https://www.alliantcreditunion.org/bank/mortgage-rates | ❌ JS-rendered | Needs Playwright |
| Navy Federal | https://www.navyfederal.org/loans-cards/mortgage/mortgage-rates.html | ❌ Blocked | Anti-bot redirects |

### Implementation Path

1. **Phase 1 (MVP)**: Parse Bankrate OR NerdWallet → immediate 10 lenders.
2. **Phase 2**: Add Zillow for point/cost data validation.
3. **Phase 3**: Add 2–3 direct lenders (DCU, Ent CU) for local flavor.

---

## 5. SUMMARY

| Area | Current State | Required for MVP |
|------|---------------|------------------|
| Working sources | 1 (DCU) | ≥10 (via aggregator) |
| Data quality checks | Not enforced | Rate ∈ [2, 12], APR ≥ rate |
| Deduplication | None | By lender + category + profile |
| Sample fallback | Mixed with real | Removed or clearly labeled |
| Alerts | Not built | Email subscription + daily eval |
| Monitoring | Basic logs | Health dashboard |

**Bottom Line:**  
The architecture is sound but the **data sources are broken**. Switching to aggregator parsing (Bankrate/NerdWallet) solves the "10 real lenders" requirement immediately. Remove sample-data fallback to avoid confusion. Add validation and deduplication to ensure accuracy.

---

*Generated by audit on 2026-01-07*
