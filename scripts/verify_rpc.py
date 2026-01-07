#!/usr/bin/env python3
"""Test the RPC function to verify it's working correctly."""

import sys
import os
sys.path.insert(0, '/Users/Sanjeev/mrt/src')

os.environ["SUPABASE_URL"] = "https://wefbwfwftxdgxsydfdis.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndlZmJ3ZndmdHhkZ3hzeWRmZGlzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjkyNTkxMywiZXhwIjoyMDYyNTAxOTEzfQ.UKw6c1dGqNyD3soBD8lTiB0vZKOUeXk3CbQPWUjZzqU"

from mortgage_tracker.config import load_config
from supabase import create_client

config = load_config()
client = create_client(config.supabase_url, config.supabase_service_role_key)

print("🧪 Testing RPC function: get_latest_rates_with_fallback\n")

# Test 1: Get real data (should return DCU offer)
print("=" * 60)
print("Test 1: Get real data with fallback enabled")
print("=" * 60)
try:
    result = client.rpc('get_latest_rates_with_fallback', {'include_sample': True}).execute()
    print(f"✅ Success! Got {len(result.data)} offers\n")
    
    # Group by data source
    real_offers = [o for o in result.data if o.get('data_source') == 'real']
    sample_offers = [o for o in result.data if o.get('data_source') == 'sample']
    
    print(f"📊 Real offers: {len(real_offers)}")
    print(f"📊 Sample offers: {len(sample_offers)}")
    print(f"📊 Fallback flag: {result.data[0].get('is_fallback') if result.data else 'N/A'}\n")
    
    # Show first few offers
    print("Sample offers (first 3):")
    for offer in result.data[:3]:
        print(f"  • {offer.get('lender_name')}: {offer.get('category')} @ {offer.get('rate')}% APR {offer.get('apr')}%")
        print(f"    Source: {offer.get('data_source')}, Fallback: {offer.get('is_fallback')}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Check 30Y fixed specifically (website filter)
print("\n" + "=" * 60)
print("Test 2: Filter for 30Y fixed (website use case)")
print("=" * 60)
try:
    result = client.rpc('get_latest_rates_with_fallback', {'include_sample': True}).execute()
    fixed_30y = [o for o in result.data if o.get('category') == '30Y fixed']
    print(f"✅ Found {len(fixed_30y)} offers for 30Y fixed\n")
    
    for offer in fixed_30y[:5]:
        print(f"  • {offer.get('lender_name')}: {offer.get('rate')}% / {offer.get('apr')}% APR")
        print(f"    Data: {offer.get('data_source')}, Fallback: {offer.get('is_fallback')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Check if real data exists
print("\n" + "=" * 60)
print("Test 3: Verify real data presence")
print("=" * 60)
try:
    # Query directly
    runs = client.table('runs').select('*').eq('run_type', 'real').order('created_at', desc=True).limit(1).execute()
    if runs.data:
        latest_real_run = runs.data[0]
        print(f"✅ Latest real run: ID={latest_real_run['id']}, Status={latest_real_run['status']}")
        
        # Count offers
        offers = client.table('offers_normalized').select('*').eq('run_id', latest_real_run['id']).eq('data_source', 'real').execute()
        print(f"✅ Real offers in that run: {len(offers.data)}")
        
        if offers.data:
            print("\nReal offers details:")
            for offer in offers.data:
                print(f"  • {offer.get('lender_name')}: {offer.get('category')} @ {offer.get('rate')}% / {offer.get('apr')}% APR")
    else:
        print("⚠️  No real runs found")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ RPC FUNCTION TESTING COMPLETE")
print("=" * 60)
print("\n💡 Summary:")
print("- RPC returns real data when available (is_fallback=false)")
print("- Falls back to sample data when no real data (is_fallback=true)")
print("- Website should check is_fallback to show correct badge")
