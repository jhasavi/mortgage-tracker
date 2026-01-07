#!/usr/bin/env python3
"""Test and apply the RPC fix via direct SQL execution."""

import sys
import os
sys.path.insert(0, '/Users/Sanjeev/mrt/src')

from supabase import create_client

# Setup - load from environment
os.environ["SUPABASE_URL"] = "https://wefbwfwftxdgxsydfdis.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndlZmJ3ZndmdHhkZ3hzeWRmZGlzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjkyNTkxMywiZXhwIjoyMDYyNTAxOTEzfQ.UKw6c1dGqNyD3soBD8lTiB0vZKOUeXk3CbQPWUjZzqU"

from mortgage_tracker.config import load_config

config = load_config()
url = config.supabase_url
key = config.supabase_service_role_key

client = create_client(url, key)

# Read the SQL
with open('/Users/Sanjeev/mrt/supabase/migrations/003_fix_rpc.sql', 'r') as f:
    sql = f.read()

print("📝 Creating RPC function via Supabase...")

# Try using the REST API directly with raw SQL
import requests

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "text/plain",
}

# Use Supabase's query endpoint
response = requests.post(
    f"{url}/rest/v1/",
    headers=headers,
    data=sql
)

if response.status_code < 300:
    print("✅ Function created!")
else:
    print(f"Response: {response.status_code}")
    print(f"Body: {response.text}")
    
    # Try testing the existing function first
    print("\n🧪 Testing if RPC function already works...")
    try:
        result = client.rpc('get_latest_rates_with_fallback', {'include_sample': True}).execute()
        print(f"✅ RPC works! Got {len(result.data)} offers")
        
        # Show first offer
        if result.data:
            offer = result.data[0]
            print(f"\nSample offer:")
            print(f"  Lender: {offer.get('lender_name')}")
            print(f"  Category: {offer.get('category')}")
            print(f"  Rate: {offer.get('rate')}%")
            print(f"  APR: {offer.get('apr')}%")
            print(f"  Data source: {offer.get('data_source')}")
            print(f"  Is fallback: {offer.get('is_fallback')}")
    except Exception as e:
        print(f"❌ RPC test failed: {e}")
        print("\n💡 The function needs to be recreated. Please run this SQL in the Supabase SQL Editor:")
        print("\n" + "="*60)
        print(sql)
        print("="*60)
