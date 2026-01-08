CREATE OR REPLACE FUNCTION public.get_latest_rates_with_fallback(
  include_sample boolean DEFAULT false
)
RETURNS TABLE (
  id bigint,
  run_id bigint,
  source_id bigint,
  source_name text,
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
  is_fallback boolean,
  details_json jsonb
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
  SELECT COUNT(DISTINCT o.lender_name) INTO real_count
  FROM public.offers_normalized o
  WHERE o.run_id = latest_real_run_id
    AND o.data_source = 'real';

  -- If we have real data, return it
  IF real_count > 0 THEN
    RETURN QUERY
      WITH latest_offers AS (
        SELECT DISTINCT ON (o.lender_name, o.category, o.loan_amount, o.ltv, o.fico, o.lock_days, o.points)
          o.id,
          o.run_id,
          s.id as source_id,
          s.name as source_name,
          o.lender_name,
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
          false as is_fallback,
          o.details_json
        FROM public.offers_normalized o
        JOIN public.sources s ON o.source_id = s.id
        WHERE o.run_id = latest_real_run_id
          AND o.data_source = 'real'
        ORDER BY o.lender_name, o.category, o.loan_amount, o.ltv, o.fico, o.lock_days, o.points, o.created_at DESC
      )
      SELECT * FROM latest_offers ORDER BY category, apr, rate;
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
        WITH latest_samples AS (
          SELECT DISTINCT ON (o.lender_name, o.category, o.loan_amount, o.ltv, o.fico, o.lock_days, o.points)
            o.id,
            o.run_id,
            s.id as source_id,
            s.name as source_name,
            o.lender_name,
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
            true as is_fallback,
            o.details_json
          FROM public.offers_normalized o
          JOIN public.sources s ON o.source_id = s.id
          WHERE o.run_id = latest_sample_run_id
            AND o.data_source = 'sample'
          ORDER BY o.lender_name, o.category, o.loan_amount, o.ltv, o.fico, o.lock_days, o.points, o.created_at DESC
        )
        SELECT * FROM latest_samples ORDER BY category, apr, rate;
      RETURN;
    END IF;
  END IF;
END;
$$;
