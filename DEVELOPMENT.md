# Development Guide

Guide for developers working on the mortgage tracker collector.

## Development Environment

### Prerequisites

- Python 3.9+
- Git
- PostgreSQL client
- Text editor/IDE (VS Code recommended)

### Initial Setup

```bash
# Clone repo
git clone https://github.com/jhasavi/mortgage-tracker.git
cd mortgage-tracker

# Install in editable mode
python3 -m pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your Supabase credentials
```

### Running Tests

Currently no automated tests. To test:

```bash
# Test collector end-to-end
export $(cat .env | xargs)
python3 -m mortgage_tracker.main

# Test individual parser
python3 -c "
from src.mortgage_tracker.parsers.example_html_table import ExampleHtmlTableParser
p = ExampleHtmlTableParser()
offers = p.parse(text='<html>...</html>')
print(offers)
"
```

## Code Structure

### Main Entry Point

**`src/mortgage_tracker/main.py`**

- `run_once()`: Main execution loop
- `_get_parser()`: Parser registry
- Per-source error handling
- Structured logging

Key flow:
1. Load config
2. Create run record
3. For each enabled source:
   - Fetch URL
   - Parse response
   - Normalize offers
   - Insert to Supabase
4. Update run status

### Configuration

**`src/mortgage_tracker/config.py`**

- Loads `sources.yaml`
- Reads environment variables
- Validates required settings

Environment variables:
- `SUPABASE_URL` (required)
- `SUPABASE_SERVICE_ROLE_KEY` (required)
- `DEFAULT_*` (optional, fallback to sources.yaml)

### HTTP Fetching

**`src/mortgage_tracker/fetch.py`**

- `fetch_url()`: Requests with retry logic
- Exponential backoff
- Timeout handling
- Returns (status, text, json)

Retry logic:
```python
# Attempt 0: immediate
# Attempt 1: wait 1.5^0 = 1.0s
# Attempt 2: wait 1.5^1 = 1.5s
# Total: 3 attempts
```

### Parsers

**`src/mortgage_tracker/parsers/`**

Each parser implements `BaseParser.parse()`:

```python
def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Parse raw HTTP response into list of offer dicts.
    
    Args:
        text: HTML/text response
        js: JSON response (if content-type application/json)
    
    Returns:
        List of offer dicts with keys:
        - lender_name (str)
        - category (str): one of ALLOWED_CATEGORIES
        - rate (float): interest rate
        - apr (float): annual percentage rate
        - points (float): discount points
        - lender_fees (float): origination fees
        - loan_amount (int, optional)
        - ltv (int, optional)
        - fico (int, optional)
        - state (str, optional)
        - term_months (int, optional)
        - lock_days (int, optional)
    """
```

**Adding a new parser**:

1. Create `src/mortgage_tracker/parsers/my_lender.py`:

```python
from typing import List, Dict, Any, Optional
from .base import BaseParser

class MyLenderParser(BaseParser):
    def parse(self, *, text: Optional[str] = None, js: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Your parsing logic
        return [
            {
                "lender_name": "My Lender",
                "category": "30Y fixed",
                "rate": 6.5,
                "apr": 6.6,
                "points": 0.0,
                "lender_fees": 1000.0,
            }
        ]
```

2. Register in `main.py`:

```python
def _get_parser(method: str):
    if method == "my_lender":
        from .parsers.my_lender import MyLenderParser
        return MyLenderParser()
    # ... existing parsers
```

3. Update `sources.yaml`:

```yaml
- name: My Lender
  rate_url: https://mylender.com/rates
  method: my_lender
  enabled: true
```

### Normalization

**`src/mortgage_tracker/normalize.py`**

- Validates category (must be in `ALLOWED_CATEGORIES`)
- Fills missing fields with defaults
- Type coercion (str → float/int)
- Embeds raw offer in `details_json`

Categories:
- `30Y fixed`
- `15Y fixed`
- `5/6 ARM`
- `FHA 30Y`
- `VA 30Y`

### Supabase Client

**`src/mortgage_tracker/supabase_client.py`**

Methods:
- `create_run()`: Start new run, returns run_id
- `finish_run()`: Update run with status/stats
- `upsert_source()`: Insert or update source by name
- `insert_snapshot()`: Save raw HTTP response
- `insert_offers()`: Bulk insert normalized offers

All methods use **service role key** (bypasses RLS).

### Ranking

**`src/mortgage_tracker/rank.py`**

- `top_n_per_category()`: Sort by rate/APR, take top N
- Used by emailer (future) for summary

## Parser Development

### Tools

**BeautifulSoup** (HTML parsing):

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(text, 'html.parser')
table = soup.find('table', {'id': 'rates'})
for row in table.find_all('tr')[1:]:  # skip header
    cells = row.find_all('td')
    rate = float(cells[1].text.strip('%'))
    # ...
```

**JSON** (already parsed):

```python
for item in js.get('rates', []):
    rate = item['rate']
    # ...
```

**Regex** (structured text):

```python
import re
matches = re.findall(r'(\d+Y Fixed): ([\d.]+)%', text)
for term, rate in matches:
    # ...
```

### Testing Parsers

```bash
# Fetch real page
curl -o test.html https://lender.com/rates

# Test parser
python3 -c "
from src.mortgage_tracker.parsers.my_parser import MyParser
with open('test.html') as f:
    text = f.read()
p = MyParser()
offers = p.parse(text=text)
import json
print(json.dumps(offers, indent=2))
"
```

### Common Patterns

**HTML table**:

```python
soup = BeautifulSoup(text, 'html.parser')
rows = soup.select('table.rates tbody tr')
for row in rows:
    cells = row.find_all('td')
    yield {
        'category': cells[0].text.strip(),
        'rate': float(cells[1].text.strip('%')),
        'apr': float(cells[2].text.strip('%')),
        # ...
    }
```

**JSON endpoint**:

```python
for item in js.get('products', []):
    if item['productType'] == 'mortgage':
        yield {
            'category': item['term'],
            'rate': item['interestRate'],
            # ...
        }
```

**Embedded JSON in HTML**:

```python
import json
import re

match = re.search(r'var ratesData = ({.*?});', text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    for rate in data['rates']:
        # ...
```

## Database Operations

### Querying Directly

```bash
psql "$DATABASE_URL" -c "SELECT * FROM runs ORDER BY started_at DESC LIMIT 1;"
```

### Schema Migrations

When modifying schema:

1. Update `supabase/migrations/001_rates.sql`
2. Test locally:
   ```bash
   psql "$DATABASE_URL" -f supabase/migrations/001_rates.sql
   ```
3. For production: Supabase dashboard → SQL editor, paste migration

**⚠️ Never drop tables in production without backup!**

### Adding Columns

```sql
ALTER TABLE offers_normalized 
ADD COLUMN IF NOT EXISTS new_field text;
```

### Adding Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_offers_lender 
ON offers_normalized(lender_name);
```

## Logging

Use structured JSON:

```python
logger.info(json.dumps({
    "event": "parser_success",
    "source": "DCU",
    "offers_count": len(offers),
}))
```

Log levels:
- `INFO`: Normal operation (source done, run finished)
- `WARNING`: Recoverable errors (fetch retry, parse failed)
- `ERROR`: Serious errors (no sources succeeded)

## Error Handling

### Per-Source Isolation

Each source wrapped in try/catch:

```python
for src in sources:
    try:
        # fetch + parse + insert
    except Exception as e:
        logger.error(json.dumps({"event": "source_error", "name": src['name'], "error": str(e)}))
        # Continue to next source
```

Run status:
- `success`: All enabled sources succeeded
- `partial`: Some sources succeeded
- `failed`: No sources succeeded

### Retry Strategy

HTTP requests auto-retry (exponential backoff). Don't retry:
- Parser errors (fix parser, not transient)
- 404/403 (URL wrong or auth needed)

Do retry:
- Timeouts
- 500/502/503 (server errors)

## Performance

### Current Bottleneck

Sequential fetching: 50 sources × 10s = 8.3 min

### Future Optimizations

**1. Parallel fetching** (threads):

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_and_parse, src) for src in sources]
    for future in futures:
        result = future.result()
```

**2. Async/await**:

```python
import asyncio
import aiohttp

async def fetch_all(sources):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_async(session, src) for src in sources]
        return await asyncio.gather(*tasks)
```

**3. Caching** (Redis):

Cache parsed offers for 1 hour to reduce DB queries.

## Git Workflow

```bash
# Create feature branch
git checkout -b add-dcu-parser

# Make changes
# ... edit files ...

# Test locally
export $(cat .env | xargs)
python3 -m mortgage_tracker.main

# Commit
git add src/mortgage_tracker/parsers/dcu.py sources.yaml
git commit -m "Add DCU parser"

# Push
git push origin add-dcu-parser

# Create PR on GitHub
```

## Debugging

### Enable verbose logging

```python
logging.basicConfig(level=logging.DEBUG)
```

### Print requests

```python
# In fetch.py
print(f"Fetching: {url}")
print(f"Response status: {resp.status_code}")
print(f"Response headers: {resp.headers}")
print(f"Response body: {resp.text[:500]}")
```

### Supabase query logs

Supabase dashboard → Logs → Postgres logs

### GitHub Actions logs

GitHub repo → Actions → Select run → View logs

## Common Issues

### Import Errors

```bash
# Reinstall package
python3 -m pip install --upgrade --force-reinstall --no-deps .
```

### Python Version Conflicts

Check type hints:
- Python 3.9: Use `Optional[X]`, not `X | None`
- Python 3.9: Use `tuple`, not `tuple[X, Y]`

### Supabase Connection Timeout

Increase timeout in supabase-py (default 10s):

```python
from supabase import create_client

client = create_client(url, key, options={
    'postgrest': {'timeout': 30}
})
```

## Code Style

Follow PEP 8:

```bash
# Auto-format
black src/
isort src/

# Lint
pylint src/
```

Type hints:

```python
from typing import List, Dict, Any, Optional

def my_func(x: int) -> Optional[str]:
    return None
```

Docstrings:

```python
def parse(self, text: str) -> List[Dict[str, Any]]:
    """
    Parse HTML into offer dicts.
    
    Args:
        text: Raw HTML string
    
    Returns:
        List of offer dictionaries
    
    Raises:
        ValueError: If HTML structure invalid
    """
```

## Resources

- [Supabase Python docs](https://supabase.com/docs/reference/python/introduction)
- [BeautifulSoup docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [requests docs](https://requests.readthedocs.io/)
- [GitHub Actions docs](https://docs.github.com/en/actions)

## Getting Help

- Check existing parsers in `src/mortgage_tracker/parsers/`
- Review logs in GitHub Actions
- Query Supabase for data issues
- Open issue on GitHub

---

**Happy parsing!** 🏡
