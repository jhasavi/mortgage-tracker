# Mortgage Tracker

Daily mortgage rate collector that fetches rates from 50+ lenders, normalizes them into standard categories, stores in Supabase, and powers a public `/rates` page on your website.

## Overview

**Goal**: Automate daily collection of mortgage rates from reputable lenders/credit unions and display the best offers on `namastebostonhomes.com/rates`.

**Architecture**:
- **This repo** (`mortgage-tracker`): Python collector + parsers + GitHub Actions cron job
- **Website repo** (`/Users/Sanjeev/nb`): Next.js `/rates` page that reads from Supabase
- **Supabase**: Shared database with RLS for secure public reads

## Features

- ✅ Fetches rates from 50+ configurable sources
- ✅ Normalizes into 5 categories: 30Y fixed, 15Y fixed, 5/6 ARM, FHA 30Y, VA 30Y
- ✅ Stores raw snapshots + normalized offers in Supabase
- ✅ RLS-protected: public can only view latest results via safe VIEW
- ✅ Daily GitHub Actions job (07:30 ET)
- ✅ Per-source error handling (one failure doesn't kill entire run)
- ✅ Structured JSON logging
- ✅ Request timeouts + retries

## Setup

### 1. Prerequisites

- Python 3.9+
- PostgreSQL client (`psql`)
- Supabase project (existing)
- GitHub repo for hosting collector

### 2. Install dependencies

```bash
cd /Users/Sanjeev/mrt
python3 -m pip install .
```

### 3. Configure environment

Create `.env` file (already done):

```bash
# Supabase
SUPABASE_URL=https://wefbwfwftxdgxsydfdis.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Defaults for rate assumptions
DEFAULT_STATE=MA
DEFAULT_LOAN_AMOUNT=600000
DEFAULT_LTV=80
DEFAULT_FICO=760
DEFAULT_LOCK_DAYS=30
```

### 4. Apply database migration

```bash
psql "postgresql://postgres:<password>@db.wefbwfwftxdgxsydfdis.supabase.co:5432/postgres" \
  -f supabase/migrations/001_rates.sql
```

This creates:
- Tables: `sources`, `runs`, `rate_snapshots`, `offers_normalized`, `lenders`
- RLS policies: anon can only read latest successful run via view
- View: `latest_rates_view` (safe public access)

### 5. Configure sources

Edit `sources.yaml` to add/enable lenders. Helper script to convert markdown list:

```bash
python3 scripts/md_to_sources.py mortgage-tracker_lenders_v0.1.md > sources_generated.yaml
```

Then manually update `rate_url` and `method` for each source, and set `enabled: true`.

### 6. Run collector locally

```bash
export $(cat .env | xargs)
python3 -m mortgage_tracker.main
```

### 7. Set up GitHub Actions

Add these secrets to your GitHub repo:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DEFAULT_STATE` (optional, defaults in workflow)
- `DEFAULT_LOAN_AMOUNT` (optional)
- `DEFAULT_LTV` (optional)
- `DEFAULT_FICO` (optional)
- `DEFAULT_LOCK_DAYS` (optional)

Workflow runs daily at 07:30 ET (12:30 UTC). See [.github/workflows/daily.yml](.github/workflows/daily.yml).

## Project Structure

```
mortgage-tracker/
├── .env                          # Local environment variables (not committed)
├── .github/
│   └── workflows/
│       └── daily.yml             # GitHub Actions cron job
├── pyproject.toml                # Python package config
├── sources.yaml                  # Lender list with URLs + parsers
├── mortgage-tracker_lenders_v0.1.md  # Source list (50 lenders)
├── scripts/
│   └── md_to_sources.py          # Convert markdown → sources.yaml
├── src/mortgage_tracker/
│   ├── __init__.py
│   ├── main.py                   # Entrypoint (run_once)
│   ├── config.py                 # Load env + sources.yaml
│   ├── fetch.py                  # HTTP requests with retries
│   ├── normalize.py              # Raw offers → standard schema
│   ├── supabase_client.py        # Writes to Supabase
│   ├── rank.py                   # Top N per category
│   ├── emailer.py                # Optional email summary (stub)
│   └── parsers/
│       ├── base.py               # Parser interface
│       ├── example_html_table.py # Sample HTML parser
│       └── example_json_endpoint.py  # Sample JSON parser
└── supabase/
    └── migrations/
        └── 001_rates.sql         # Database schema + RLS
```

## Database Schema

### Core Tables

- **`sources`**: Lender metadata (name, homepage, rate_url, method, enabled)
- **`runs`**: Each collector execution (started_at, status, stats)
- **`rate_snapshots`**: Raw HTTP responses per source/run
- **`offers_normalized`**: Parsed offers (rate, APR, points, fees, category, etc.)
- **`lenders`**: Manual curation (favorites, exclusions)

### Public Access

- **`latest_rates_view`**: Read-only view of offers from latest successful run
- RLS policy: anon role can SELECT from view only (no direct table access)

## Writing Parsers

Each source needs a parser that implements `BaseParser`:

```python
from typing import List, Dict, Any, Optional
from .base import BaseParser

class MyLenderParser(BaseParser):
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        offers = []
        # Parse HTML/JSON → extract offers
        # Return list of dicts with keys:
        # - lender_name, category, rate, apr, points, lender_fees, etc.
        return offers
```

Register in `sources.yaml`:

```yaml
- name: My Lender
  rate_url: https://mylender.com/rates
  method: my_lender_parser
  enabled: true
```

Update `main.py` `_get_parser()` to load your parser.

## Website Integration

Add `/rates` page to Next.js website repo (`/Users/Sanjeev/nb`).

### 1. Install Supabase client

```bash
cd /Users/Sanjeev/nb
npm install @supabase/supabase-js
```

### 2. Add environment variables

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://wefbwfwftxdgxsydfdis.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
NEXT_PUBLIC_DEFAULT_LOAN_AMOUNT=600000
NEXT_PUBLIC_DEFAULT_LTV=80
NEXT_PUBLIC_DEFAULT_FICO=760
NEXT_PUBLIC_DEFAULT_LOCK_DAYS=30
```

### 3. Create `/rates` page

See example in deployment notes below. Place as `app/rates/page.tsx` (App Router) or `pages/rates.tsx` (Pages Router).

**Key points**:
- Use `NEXT_PUBLIC_SUPABASE_ANON_KEY` (NOT service role)
- Query `latest_rates_view` table
- Group by category, take top 10 per category
- Show "as of" timestamp + assumptions disclaimer

## Logging

Structured JSON logs for easy parsing:

```json
{"event": "run_created", "run_id": 1}
{"event": "source_done", "name": "DCU", "offers": 3, "snapshot_id": 42}
{"event": "source_error", "name": "Bank X", "error": "timeout"}
{"event": "run_finished", "run_id": 1, "status": "success", "stats": {...}}
```

## Error Handling

- **Per-source try/catch**: One broken source doesn't kill entire run
- **Request retries**: Exponential backoff (default 2 retries)
- **Timeouts**: 10s default per request
- **Partial success**: Run marked `partial` if some sources succeed
- **Snapshots saved**: Even failed fetches recorded with error text

## Security

- **Service role key**: NEVER commit to repo; use GitHub secrets + local `.env`
- **RLS policies**: Public can only read `latest_rates_view`
- **No raw data exposure**: Snapshots table blocked from anon access
- **HTTPS only**: All requests over TLS

## Maintenance

### Adding a new lender

1. Find rate URL (table, JSON endpoint, or quote flow)
2. Add to `sources.yaml`:
   ```yaml
   - name: New Bank
     org_type: bank
     homepage_url: https://newbank.com
     rate_url: https://newbank.com/rates
     method: example_html_table
     enabled: true
   ```
3. Write custom parser if needed (or reuse existing)
4. Test locally: `python3 -m mortgage_tracker.main`
5. Commit + push

### Disabling a source

Set `enabled: false` in `sources.yaml`.

### Viewing run history

```sql
SELECT id, started_at, status, stats_json
FROM runs
ORDER BY started_at DESC
LIMIT 10;
```

### Checking latest rates

```sql
SELECT lender_name, category, rate, apr, points
FROM latest_rates_view
ORDER BY category, rate
LIMIT 20;
```

## Troubleshooting

### Collector fails with "SUPABASE_URL required"

Load `.env`: `export $(cat .env | xargs)`

### GitHub Action fails

Check:
1. Secrets configured in repo settings
2. `sources.yaml` committed to repo
3. Migration applied to Supabase

### No data in `latest_rates_view`

Run status must be `success` or `partial`. Check:

```sql
SELECT * FROM runs ORDER BY started_at DESC LIMIT 1;
```

If status is `failed`, check error logs or re-run.

### Parser returns empty list

- Verify `rate_url` is accessible
- Check HTML/JSON structure hasn't changed
- Add debug logging to parser
- Test fetch manually: `curl -v <rate_url>`

## Roadmap

- [ ] Add 50 real parsers for all lenders
- [ ] Email daily summary (SendGrid/Postmark)
- [ ] Historical rate charts
- [ ] Alert when rates drop
- [ ] Auto-detect stale sources (haven't updated in 7+ days)
- [ ] Add more categories (10Y, 20Y, Jumbo)
- [ ] API endpoint for third-party integrations

## License

MIT

## Support

Questions? Open an issue or contact team.

---

**Last updated**: January 6, 2026
