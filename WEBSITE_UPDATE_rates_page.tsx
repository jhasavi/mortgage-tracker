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
  data_source: string
  is_fallback: boolean
}

const CATEGORIES = [
  '30Y fixed',
  '15Y fixed',
  '5/6 ARM',
  'FHA 30Y',
  'VA 30Y',
]

async function fetchRates(): Promise<{ rates: Record<string, RateRow[]>, isFallback: boolean }> {
  const supabase = await createClient()
  
  // Call the RPC function with fallback enabled
  const { data, error } = await supabase
    .rpc('get_latest_rates_with_fallback', { include_sample: true })
  
  if (error) {
    console.error('Supabase RPC error', error)
    return { rates: {}, isFallback: false }
  }
  
  if (!data || data.length === 0) {
    return { rates: {}, isFallback: false }
  }
  
  // Check if we're using fallback data
  const isFallback = data[0]?.is_fallback || false
  
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
  
  return { rates, isFallback }
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

function getMaxUpdatedAt(rates: Record<string, RateRow[]>): string {
  let maxDate: Date | null = null
  let maxStr = ''
  
  for (const cat of Object.keys(rates)) {
    for (const row of rates[cat]) {
      const d = new Date(row.updated_at)
      if (!maxDate || d > maxDate) {
        maxDate = d
        maxStr = row.updated_at
      }
    }
  }
  
  return maxStr
}

export default async function RatesPage() {
  const { rates, isFallback } = await fetchRates()
  const asOfStr = getMaxUpdatedAt(rates)

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-semibold">Mortgage Rates</h1>
        {isFallback && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
            Sample Data
          </span>
        )}
        {!isFallback && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            Live Rates
          </span>
        )}
      </div>
      
      <p className="text-sm text-gray-600 mb-6">
        {asOfStr ? `As of ${formatDateEST(asOfStr)} EST` : 'Latest available run'} — Assumptions: $600,000 loan, 80% LTV, 760 FICO, 30-day lock, owner-occupied.
      </p>

      {CATEGORIES.map((cat) => (
        <div key={cat} className="mb-10">
          <h2 className="text-xl font-medium mb-3">{cat}</h2>
          <div className="overflow-x-auto rounded border">
            <table className="min-w-full divide-y">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Lender</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Rate</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">APR</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Points</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Fees</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">State</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Loan</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">LTV</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">FICO</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Lock</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {(rates[cat] ?? []).map((row) => (
                  <tr key={`${cat}-${row.source_id}-${row.lender_name}`}>
                    <td className="px-3 py-2">{row.lender_name}</td>
                    <td className="px-3 py-2">{formatPct(row.rate)}</td>
                    <td className="px-3 py-2">{formatPct(row.apr)}</td>
                    <td className="px-3 py-2">{row.points ?? '—'}</td>
                    <td className="px-3 py-2">{formatCurrency(row.lender_fees)}</td>
                    <td className="px-3 py-2">{row.state ?? '—'}</td>
                    <td className="px-3 py-2">{formatCurrency(row.loan_amount)}</td>
                    <td className="px-3 py-2">{row.ltv ?? '—'}</td>
                    <td className="px-3 py-2">{row.fico ?? '—'}</td>
                    <td className="px-3 py-2">{row.lock_days ?? '—'} days</td>
                    <td className="px-3 py-2">{formatDateEST(row.updated_at)}</td>
                  </tr>
                ))}
                {(!rates[cat] || rates[cat].length === 0) && (
                  <tr>
                    <td className="px-3 py-2 text-sm text-gray-500" colSpan={11}>No rates available yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      <div className="text-xs text-gray-600 space-y-2">
        <p>
          Disclaimer: Rates shown are for informational purposes only and may vary based on loan details, property type, location, and lender underwriting. Confirm with the lender before making decisions.
        </p>
        <p>
          Data is aggregated from publicly available lender sources. We do not guarantee accuracy and availability.
        </p>
      </div>
    </div>
  )
}
