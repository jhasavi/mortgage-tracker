-- Migration 002: Add data source flags and enhanced RPC functions
-- This allows us to separate real vs sample data and provide fallback behavior

-- =====================================================
-- STEP 1: Add flags to track data source
-- =====================================================

-- Add run_type to runs table
ALTER TABLE public.runs 
ADD COLUMN IF NOT EXISTS run_type text NOT NULL DEFAULT 'real'
CHECK (run_type IN ('real', 'sample'));

COMMENT ON COLUMN public.runs.run_type IS 
  'Type of run: real (from actual parsers) or sample (demonstration data)';

-- Add data_source to offers_normalized
ALTER TABLE public.offers_normalized
ADD COLUMN IF NOT EXISTS data_source text NOT NULL DEFAULT 'real'
CHECK (data_source IN ('real', 'sample'));

COMMENT ON COLUMN public.offers_normalized.data_source IS
  'Source of offer data: real (parsed from lender) or sample (demonstration)';

-- =====================================================
-- STEP 2: Update latest_rates_view to show only REAL data
-- =====================================================

DROP VIEW IF EXISTS public.latest_rates_view;

CREATE VIEW public.latest_rates_view AS
WITH latest_successful_real_run AS (
  SELECT id, created_at
  FROM public.runs
  WHERE status = 'success' 
    AND run_type = 'real'
  ORDER BY created_at DESC
  LIMIT 1
)
SELECT 
  o.id,
  o.run_id,
  s.id as source_id,
  COALESCE(l.name, s.name) as lender_name,
  o.category,
  o.rate,
  o.apr,
  o.points,
  o.lender_fees,
  o.state,
  o.loan_amount,
  o.ltv,
  o.fico,
  o.lock_days,
  o.created_at as updated_at,
  o.data_source
FROM public.offers_normalized o
JOIN latest_successful_real_run lr ON o.run_id = lr.id
JOIN public.sources s ON o.source_id = s.id
LEFT JOIN public.lenders l ON s.lender_id = l.id
WHERE o.data_source = 'real'
ORDER BY o.category, o.rate, o.apr;

COMMENT ON VIEW public.latest_rates_view IS
  'Public view showing only REAL rates from the most recent successful real run';

-- =====================================================
-- STEP 3: Create RPC function with smart fallback
-- =====================================================

CREATE OR REPLACE FUNCTION public.get_latest_rates_with_fallback(
  include_sample boolean DEFAULT false
)
RETURNS TABLE (
  id bigint,
  run_id bigint,
  source_id bigint,
  lender_name text,
  category text,
  rate numeric,
  apr numeric,
  points numeric,
  lender_fees numeric,
  state text,
  loan_amount numeric,
  ltv integer,
  fico integer,
  lock_days integer,
  updated_at timestamptz,
  data_source text,
  is_fallback boolean
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  real_count integer;
  latest_real_run_id bigint;
  latest_sample_run_id bigint;
BEGIN
  -- Find the latest successful real run
  SELECT r.id INTO latest_real_run_id
  FROM public.runs r
  WHERE r.status = 'success' AND r.run_type = 'real'
  ORDER BY r.created_at DESC
  LIMIT 1;

  -- Count real offers from that run
  SELECT COUNT(*) INTO real_count
  FROM public.offers_normalized o
  WHERE o.run_id = latest_real_run_id
    AND o.data_source = 'real';

  -- If we have real data, return it
  IF real_count > 0 THEN
    RETURN QUERY
    SELECT 
      o.id,
      o.run_id,
      s.id as source_id,
      COALESCE(l.name, s.name) as lender_name,
      o.category,
      o.rate,
      o.apr,
      o.points,
      o.lender_fees,
      o.state,
      o.loan_amount,
      o.ltv,
      o.fico,
      o.lock_days,
      o.created_at as updated_at,
      o.data_source,
      false as is_fallback
    FROM public.offers_normalized o
    JOIN public.sources s ON o.source_id = s.id
    LEFT JOIN public.lenders l ON s.lender_id = l.id
    WHERE o.run_id = latest_real_run_id
      AND o.data_source = 'real'
    ORDER BY o.category, o.apr, o.rate;
    RETURN;
  END IF;

  -- If no real data and fallback is enabled, return sample data
  IF include_sample THEN
    -- Find latest successful sample run
    SELECT r.id INTO latest_sample_run_id
    FROM public.runs r
    WHERE r.status = 'success' AND r.run_type = 'sample'
    ORDER BY r.created_at DESC
    LIMIT 1;

    IF latest_sample_run_id IS NOT NULL THEN
      RETURN QUERY
      SELECT 
        o.id,
        o.run_id,
        s.id as source_id,
        COALESCE(l.name, s.name) as lender_name,
        o.category,
        o.rate,
        o.apr,
        o.points,
        o.lender_fees,
        o.state,
        o.loan_amount,
        o.ltv,
        o.fico,
        o.lock_days,
        o.created_at as updated_at,
        o.data_source,
        true as is_fallback
      FROM public.offers_normalized o
      JOIN public.sources s ON o.source_id = s.id
      LEFT JOIN public.lenders l ON s.lender_id = l.id
      WHERE o.run_id = latest_sample_run_id
        AND o.data_source = 'sample'
      ORDER BY o.category, o.apr, o.rate;
      RETURN;
    END IF;
  END IF;

  -- If we get here, return nothing
  RETURN;
END;
$$;

COMMENT ON FUNCTION public.get_latest_rates_with_fallback IS
  'Returns latest real rates, falling back to sample data if include_sample=true and no real data exists';

-- Grant execute to anon role
GRANT EXECUTE ON FUNCTION public.get_latest_rates_with_fallback(boolean) TO anon;

-- =====================================================
-- STEP 4: Ensure existing data is marked as 'real'
-- =====================================================

-- Update any existing runs without run_type
UPDATE public.runs
SET run_type = 'real'
WHERE run_type IS NULL OR run_type = '';

-- Update any existing offers without data_source  
UPDATE public.offers_normalized
SET data_source = 'real'
WHERE data_source IS NULL OR data_source = '';

-- =====================================================
-- STEP 5: Update stats schema to track more details
-- =====================================================

COMMENT ON COLUMN public.runs.stats_json IS
  'Run statistics: sources_total, sources_enabled, sources_success, sources_failed, offers_inserted, parse_errors';
