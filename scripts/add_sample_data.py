#!/usr/bin/env python3
"""
Add sample rate data to Supabase for demonstration purposes.
This simulates what would happen if we had parsers for multiple lenders.
"""
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SAMPLE_RATES = [
    # Massachusetts Credit Unions
    {
        "lender_name": "DCU (Digital Federal Credit Union)",
        "category": "30Y fixed",
        "rate": 5.750,
        "apr": 5.933,
        "points": 0.0,
        "lender_fees": 0.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Metro Credit Union (MA)",
        "category": "30Y fixed",
        "rate": 5.875,
        "apr": 6.012,
        "points": 0.0,
        "lender_fees": 995.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Metro Credit Union (MA)",
        "category": "15Y fixed",
        "rate": 5.250,
        "apr": 5.421,
        "points": 0.0,
        "lender_fees": 995.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Rockland Trust",
        "category": "30Y fixed",
        "rate": 5.990,
        "apr": 6.125,
        "points": 0.5,
        "lender_fees": 1295.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Rockland Trust",
        "category": "15Y fixed",
        "rate": 5.375,
        "apr": 5.521,
        "points": 0.5,
        "lender_fees": 1295.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Eastern Bank",
        "category": "30Y fixed",
        "rate": 5.825,
        "apr": 5.978,
        "points": 0.25,
        "lender_fees": 1150.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Cambridge Savings Bank",
        "category": "30Y fixed",
        "rate": 5.950,
        "apr": 6.089,
        "points": 0.0,
        "lender_fees": 1250.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Cambridge Savings Bank",
        "category": "15Y fixed",
        "rate": 5.375,
        "apr": 5.531,
        "points": 0.0,
        "lender_fees": 1250.0,
        "details_json": {"source_label": "sample"},
    },
    # National lenders
    {
        "lender_name": "Rocket Mortgage",
        "category": "30Y fixed",
        "rate": 6.125,
        "apr": 6.287,
        "points": 0.0,
        "lender_fees": 1495.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Rocket Mortgage",
        "category": "15Y fixed",
        "rate": 5.500,
        "apr": 5.689,
        "points": 0.0,
        "lender_fees": 1495.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Rocket Mortgage",
        "category": "5/6 ARM",
        "rate": 5.625,
        "apr": 6.821,
        "points": 0.0,
        "lender_fees": 1495.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "PenFed Credit Union",
        "category": "30Y fixed",
        "rate": 5.750,
        "apr": 5.899,
        "points": 0.0,
        "lender_fees": 750.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "PenFed Credit Union",
        "category": "15Y fixed",
        "rate": 5.125,
        "apr": 5.287,
        "points": 0.0,
        "lender_fees": 750.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Navy Federal Credit Union",
        "category": "30Y fixed",
        "rate": 5.875,
        "apr": 6.001,
        "points": 0.0,
        "lender_fees": 850.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Navy Federal Credit Union",
        "category": "15Y fixed",
        "rate": 5.250,
        "apr": 5.398,
        "points": 0.0,
        "lender_fees": 850.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Wells Fargo",
        "category": "30Y fixed",
        "rate": 6.250,
        "apr": 6.425,
        "points": 0.5,
        "lender_fees": 1795.0,
        "details_json": {"source_label": "sample"},
    },
    {
        "lender_name": "Wells Fargo",
        "category": "15Y fixed",
        "rate": 5.625,
        "apr": 5.821,
        "points": 0.5,
        "lender_fees": 1795.0,
        "details_json": {"source_label": "sample"},
    {
        "lender_name": "Chase",
        "category": "30Y fixed",
        "rate": 6.125,
        "apr": 6.298,
        "points": 0.375,
        "lender_fees": 1650.0,
    },
    {
        "lender_name": "Chase",
        "category": "15Y fixed",
        "rate": 5.500,
        "apr": 5.695,
        "points": 0.375,
        "lender_fees": 1650.0,
    },
]


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        sys.exit(1)
    
    supabase = create_client(url, key)
    
    # Create a new run (marked as sample)
    run_data = {
        "status": "started",
        "run_type": "sample"  # Mark as sample data
    }
    run_result = supabase.table("runs").insert(run_data).execute()
    run_id = run_result.data[0]["id"]
    print(f"Created run {run_id}")
    
    # Create a dummy source
    source_data = {
        "name": "Sample Data (demo)",
        "org_type": "system",
        "homepage_url": "https://example.com",
        "rate_url": "https://example.com",
        "method": "sample",
        "enabled": False,
        "notes": "Generated sample data for demonstration"
    }
    source_result = supabase.table("sources").upsert(source_data, on_conflict="name").execute()
    source_id = source_result.data[0]["id"]
    
    # Insert offers (deduplicated by unique key)
    offers_to_insert = []
    seen_keys = set()
    for rate in SAMPLE_RATES:
        loan_amount = 600000
        ltv = 80
        fico = 760
        lock_days = 30
        points = rate.get("points", 0.0)
        unique_key = (rate["lender_name"], rate["category"], loan_amount, ltv, fico, lock_days, points)
        if unique_key in seen_keys:
            continue
        seen_keys.add(unique_key)

        offer = {
            "run_id": run_id,
            "source_id": source_id,
            "lender_name": rate["lender_name"],
            "category": rate["category"],
            "rate": rate["rate"],
            "apr": rate["apr"],
            "points": points,
            "lender_fees": rate.get("lender_fees"),
            "loan_amount": loan_amount,
            "ltv": ltv,
            "fico": fico,
            "state": "MA",
            "term_months": 360 if "30Y" in rate["category"] else (180 if "15Y" in rate["category"] else 360),
            "lock_days": lock_days,
            "details_json": rate,
            "data_source": "sample",  # Mark as sample data
        }
        offers_to_insert.append(offer)

    if offers_to_insert:
        supabase.table("offers_normalized").insert(offers_to_insert).execute()
    print(f"Inserted {len(offers_to_insert)} sample offers")
    
    # Mark run as success
    supabase.table("runs").update({
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": "success",
        "stats_json": {
            "total_sources": 1,
            "success_sources": 1,
            "offers_written": len(offers_to_insert),
            "note": "Sample data for demonstration"
        }
    }).eq("id", run_id).execute()
    
    print(f"✅ Sample data loaded successfully!")
    print(f"   View at: https://www.namastebostonhomes.com/rates")


if __name__ == "__main__":
    main()
