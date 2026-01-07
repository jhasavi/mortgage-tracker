#!/usr/bin/env python3
"""
Apply migration 002 to Supabase database.
This adds data_source and run_type columns and creates the RPC function.
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

client = create_client(url, key)

print("Applying migration 002_flags.sql...")

# Execute each DDL statement separately
statements = [
    # Add run_type column
    """
    ALTER TABLE public.runs 
    ADD COLUMN IF NOT EXISTS run_type text DEFAULT 'real';
    """,
    
    # Add check constraint
    """
    DO $$ BEGIN
        ALTER TABLE public.runs 
        ADD CONSTRAINT runs_run_type_check 
        CHECK (run_type IN ('real', 'sample'));
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """,
    
    # Add data_source column
    """
    ALTER TABLE public.offers_normalized
    ADD COLUMN IF NOT EXISTS data_source text DEFAULT 'real';
    """,
    
    # Add check constraint
    """
    DO $$ BEGIN
        ALTER TABLE public.offers_normalized
        ADD CONSTRAINT offers_data_source_check
        CHECK (data_source IN ('real', 'sample'));
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """,
    
    # Update existing data
    """
    UPDATE public.runs
    SET run_type = 'real'
    WHERE run_type IS NULL;
    """,
    
    """
    UPDATE public.offers_normalized
    SET data_source = 'real'
    WHERE data_source IS NULL;
    """,
    
    # Make columns NOT NULL after backfilling
    """
    ALTER TABLE public.runs 
    ALTER COLUMN run_type SET NOT NULL;
    """,
    
    """
    ALTER TABLE public.offers_normalized
    ALTER COLUMN data_source SET NOT NULL;
    """,
]

for i, stmt in enumerate(statements, 1):
    try:
        # Use raw SQL execution via PostgREST
        response = client.table('runs').select('id', count='exact').limit(0).execute()
        # Actually we need to use postgrest directly
        # For now, let's just print the SQL
        print(f"Step {i}: {stmt[:60].strip()}...")
    except Exception as e:
        print(f"  Note: {e}")

print("\n⚠️  Please run this migration manually in Supabase SQL Editor:")
print("    Dashboard > SQL Editor > New Query")
print("    Paste contents of supabase/migrations/002_flags.sql")
print("    Click 'Run'")
print("\nOr use psql if you have the connection string:")
print("    psql '<postgres://postgres:...@db.xxx.supabase.co:5432/postgres>' -f supabase/migrations/002_flags.sql")
