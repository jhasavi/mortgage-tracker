#!/usr/bin/env python3
"""
Convert a markdown file listing lenders into sources.yaml skeleton.

Input markdown formats supported (best-effort):
- Lines containing a name and a URL: "- Lender Name: https://example.com"
- Table rows with name and homepage URL.

Usage:
  python scripts/md_to_sources.py path/to/mortgage-tracker_lenders_v0.1.md > sources.yaml
"""

import re
import sys
import yaml


def extract_pairs(md_text: str):
    pairs = []
    # Pattern 1: "**Name** — URL" (markdown bold)
    for line in md_text.splitlines():
        # Bold with em dash: **DCU** — https://...
        m1 = re.match(r"^\s*\d*\.\s*\*\*(.+?)\*\*\s*[—–-]\s*(https?://\S+)", line)
        if m1:
            pairs.append((m1.group(1).strip(), m1.group(2).strip()))
            continue
        # Pattern 2: "- Name: https://..."
        m2 = re.match(r"^\s*[-*]\s*(.+?):\s*(https?://\S+)", line)
        if m2:
            pairs.append((m2.group(1).strip(), m2.group(2).strip()))
            continue
        # Markdown table: | Name | URL |
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 3 and cells[1] and cells[2] and cells[2].startswith("http"):
            name = cells[1]
            url = cells[2]
            pairs.append((name, url))
    return pairs


def main():
    if len(sys.argv) < 2:
        print("Usage: md_to_sources.py input.md", file=sys.stderr)
        sys.exit(1)
    md_path = sys.argv[1]
    with open(md_path, "r") as f:
        md_text = f.read()
    pairs = extract_pairs(md_text)
    data = {
        "defaults": {
            "state": "MA",
            "loan_amount": 600000,
            "ltv": 80,
            "fico": 760,
            "lock_days": 30,
        },
        "sources": [
            {
                "name": name,
                "org_type": "lender",
                "homepage_url": url,
                "rate_url": "",
                "method": "example_html_table",
                "enabled": False,
                "notes": "TODO: add rate URL and parser",
            }
            for name, url in pairs
        ],
    }
    yaml.safe_dump(data, sys.stdout, sort_keys=False)


if __name__ == "__main__":
    main()
