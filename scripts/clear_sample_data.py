#!/usr/bin/env python3
"""
Clear sample data from Supabase database.
This removes all runs marked as run_type='sample' and their associated offers.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        sys.exit(1)
    
    supabase = create_client(url, key)
    
    print("🔍 Finding sample data...")
    
    # Find all sample runs
    sample_runs = supabase.table("runs").select("id").eq("run_type", "sample").execute()
    run_ids = [r["id"] for r in sample_runs.data]
    
    if not run_ids:
        print("✅ No sample data found")
        return
    
    print(f"📋 Found {len(run_ids)} sample run(s)")
    
    # Delete offers from sample runs
    for run_id in run_ids:
        offers_result = supabase.table("offers_normalized")\
            .delete()\
            .eq("run_id", run_id)\
            .execute()
        if hasattr(offers_result, 'data') and offers_result.data:
            print(f"   Deleted {len(offers_result.data)} offers from run {run_id}")
    
    # Delete sample runs
    supabase.table("runs").delete().eq("run_type", "sample").execute()
    print(f"🗑️  Deleted {len(run_ids)} sample run(s)")
    
    print("✅ Sample data cleared successfully!")


if __name__ == "__main__":
    main()
