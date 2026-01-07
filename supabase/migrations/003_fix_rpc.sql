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
  -- Find the latest successful real run (including partial)
  SELECT r.id INTO latest_real_run_id
  FROM public.runs r
  WHERE (r.status = 'success' OR r.status = 'partial') AND r.run_type = 'real'
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
        s.name as lender_name,
        o.category,
        o.rate,
        o.apr,
        o.points,
        o.lender_fees,
        o.state,
        o.loan_amount,
        o.ltv::integer,
        o.fico::integer,
        o.lock_days::integer,
        o.created_at as updated_at,
        o.data_source,
        false as is_fallback
    FROM public.offers_normalized o
    JOIN public.sources s ON o.source_id = s.id
    WHERE o.run_id = latest_real_run_id
      AND o.data_source = 'real'
    ORDER BY o.category, o.apr, o.rate;
    RETURN;
  END IF;

  -- If no real data and fallback is enabled, return sample data
  IF include_sample THEN
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
        s.name as lender_name,
        o.category,
        o.rate,
        o.apr,
        o.points,
        o.lender_fees,
        o.state,
        o.loan_amount,
        o.ltv::integer,
        o.fico::integer,
        o.lock_days::integer,
        o.created_at as updated_at,
        o.data_source,
        true as is_fallback
      FROM public.offers_normalized o
      JOIN public.sources s ON o.source_id = s.id
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

GRANT EXECUTE ON FUNCTION public.get_latest_rates_with_fallback(boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.get_latest_rates_with_fallback(boolean) TO authenticated;
