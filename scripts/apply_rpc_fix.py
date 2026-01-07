#!/usr/bin/env python3
"""Apply the fixed RPC function directly via Supabase client."""

import os
from supabase import create_client, Client

# Read the SQL file
with open('/Users/Sanjeev/mrt/supabase/migrations/003_fix_rpc.sql', 'r') as f:
    sql = f.read()

# Connect to Supabase
url = "https://wefbwfwftxdgxsydfdis.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndlZmJ3ZndmdHhkZ3hzeWRmZGlzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjkyNTkxMywiZXhwIjoyMDYyNTAxOTEzfQ.UKw6c1dGqNyD3soBD8lTiB0vZKOUeXk3CbQPWUjZzqU"

supabase: Client = create_client(url, key)

# Execute the SQL
print("📝 Applying RPC fix...")
try:
    response = supabase.rpc('exec_sql', {'sql': sql}).execute()
    print("✅ RPC function recreated successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying alternative approach...")
    
    # Alternative: use postgrest directly
    import requests
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Prefer": "return=representation"
    }
    
    # Use the SQL Editor API endpoint
    response = requests.post(
        f"{url}/rest/v1/rpc/query",
        headers=headers,
        data={"query": sql}
    )
    
    if response.status_code < 300:
        print("✅ RPC function recreated successfully via REST API!")
    else:
        print(f"❌ REST API error: {response.status_code} - {response.text}")
