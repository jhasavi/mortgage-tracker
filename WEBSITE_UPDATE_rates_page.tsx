import { createClient } from '@/lib/supabase/server'

type RateRow = {
  lender_name: string
  category: string
  rate: number | null
  apr: number | null
  points: number | null
  lender_fees: number | null
  state: string | null
  loan_amount: number | null
  ltv: number | null
  fico: number | null
  lock_days: number | null
  updated_at: string
  source_id: number
  source_name: string
  data_source: string
  is_fallback: boolean
  details_json: { source_label?: string } | null
}

type RunStats = {
  total_offers: number
  distinct_lenders: number
  last_run_at: string | null
  is_fallback: boolean
}

const CATEGORIES = [
  '30Y fixed',
  '15Y fixed',
  '5/6 ARM',
  'FHA 30Y',
  'VA 30Y',
]

async function fetchRates(): Promise<{ 
  rates: Record<string, RateRow[]>
  stats: RunStats
  status: 'live' | 'partial' | 'sample' | 'none'
}> {
  const supabase = await createClient()
  
  const { data, error } = await supabase
    .rpc('get_latest_rates_with_fallback', { include_sample: true })
  
  if (error) {
    console.error('Supabase RPC error', error)
    return { rates: {}, stats: { total_offers: 0, distinct_lenders: 0, last_run_at: null, is_fallback: false }, status: 'none' }
  }
  
  if (!data || data.length === 0) {
    return { rates: {}, stats: { total_offers: 0, distinct_lenders: 0, last_run_at: null, is_fallback: false }, status: 'none' }
  }
  
  const isFallback = data[0]?.is_fallback ?? false
  
  // Calculate stats
  const distinctLenders = new Set(data.map((row: RateRow) => row.lender_name)).size
  const maxUpdatedAt = data.reduce((max: string, row: RateRow) => {
    return row.updated_at > max ? row.updated_at : max
  }, data[0].updated_at)
  
  const stats: RunStats = {
    total_offers: data.length,
    distinct_lenders: distinctLenders,
    last_run_at: maxUpdatedAt,
    is_fallback: isFallback
  }
  
  // Determine status
  let status: 'live' | 'partial' | 'sample' | 'none' = 'none'
  if (isFallback) {
    status = 'sample'
  } else if (distinctLenders >= 10) {
    status = 'live'
  } else if (distinctLenders >= 1) {
    status = 'partial'
  }
  
  // Group by category
  const rates: Record<string, RateRow[]> = {}
  for (const cat of CATEGORIES) {
    rates[cat] = data
      .filter((row: RateRow) => row.category === cat)
      .sort((a: RateRow, b: RateRow) => {
        // Sort by APR first, then rate
        if (a.apr !== b.apr) return (a.apr || 999) - (b.apr || 999)
        return (a.rate || 999) - (b.rate || 999)
      })
      .slice(0, 10) // Top 10 per category
  }
  
  return { rates, stats, status }
}

function formatPct(v: number | null) {
  if (v === null || v === undefined) return '—'
  return `${v.toFixed(3)}%`
}

function formatCurrency(v: number | null) {
  if (v === null || v === undefined) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v)
}

function formatDateEST(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('en-US', { 
    timeZone: 'America/New_York',
    month: 'numeric',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

function getSourceLabel(row: RateRow): string {
  if (row.details_json?.source_label === 'sample') {
    return 'Sample'
  }
  return row.source_name || 'Direct'
}

export default async function RatesPage() {
  const { rates, stats, status } = await fetchRates()

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-semibold">Mortgage Rates</h1>
        <div className="flex items-center gap-3">
          {status === 'live' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              ✓ Live Data
            </span>
          )}
          {status === 'partial' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              ⚠ Partial Live Data ({stats.distinct_lenders} lenders)
            </span>
          )}
          {status === 'sample' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              ⓘ Sample Data
            </span>
          )}
          {status === 'none' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
              ✗ No Data
            </span>
          )}
        </div>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          {stats.last_run_at ? `As of ${formatDateEST(stats.last_run_at)} EST` : 'Awaiting first run'}
          {' • '}
          {stats.distinct_lenders} {stats.distinct_lenders === 1 ? 'lender' : 'lenders'}
          {' • '}
          {stats.total_offers} {stats.total_offers === 1 ? 'offer' : 'offers'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Assumptions: $600,000 loan, 80% LTV, 760 FICO, 30-day lock, owner-occupied
        </p>
      </div>

      {CATEGORIES.map((cat) => (
        <div key={cat} className="mb-10">
          <h2 className="text-xl font-medium mb-3">{cat}</h2>
          <div className="overflow-x-auto rounded border">
            <table className="min-w-full divide-y">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Lender</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Source</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Rate</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">APR</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Points</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Fees</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(rates[cat] ?? []).map((row, idx) => (
                  <tr key={`${cat}-${row.source_id}-${row.lender_name}-${idx}`}>
                    <td className="px-3 py-2 font-medium">{row.lender_name}</td>
                    <td className="px-3 py-2 text-sm text-gray-600">{getSourceLabel(row)}</td>
                    <td className="px-3 py-2">{formatPct(row.rate)}</td>
                    <td className="px-3 py-2">{formatPct(row.apr)}</td>
                    <td className="px-3 py-2">{row.points !== null && row.points !== undefined ? row.points : 'N/A'}</td>
                    <td className="px-3 py-2">{formatCurrency(row.lender_fees)}</td>
                    <td className="px-3 py-2 text-xs">{formatDateEST(row.updated_at)}</td>
                  </tr>
                ))}
                {(rates[cat] == null || rates[cat].length === 0) && (
                  <tr>
                    <td className="px-3 py-2 text-sm text-gray-500" colSpan={7}>No rates available for this category yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      <div className="text-xs text-gray-600 space-y-2 mt-8">
        <p>
          <strong>Disclaimer:</strong> Rates shown are for informational purposes only and may vary based on loan details, property type, location, and lender underwriting. Confirm with the lender before making decisions.
        </p>
        <p>
          <strong>Data Sources:</strong> Aggregated from marketplace data (Bankrate, NerdWallet) and select direct lender sources. Marketplace offers represent national averages and may not reflect rates available to all borrowers. We do not guarantee accuracy or availability.
        </p>
        {status !== 'live' && (
          <p className="text-amber-600">
            <strong>Note:</strong> Data coverage is currently limited. We are actively expanding our lender network to provide more comprehensive rate information.
          </p>
        )}
      </div>
    </div>
  )
}