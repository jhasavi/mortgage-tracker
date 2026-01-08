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

type RunStats = {
  total_offers: number
  distinct_lenders: number
  last_run_at: string | null
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
  status: 'live' | 'partial' | 'none'
}> {
  const supabase = await createClient()
  
  // Call RPC with include_sample=FALSE to show only real data
  const { data, error } = await supabase
    .rpc('get_latest_rates_with_fallback', { include_sample: false })
  
  if (error) {
    console.error('Supabase RPC error', error)
    return { rates: {}, stats: { total_offers: 0, distinct_lenders: 0, last_run_at: null }, status: 'none' }
  }
  
  if (!data || data.length === 0) {
    return { rates: {}, stats: { total_offers: 0, distinct_lenders: 0, last_run_at: null }, status: 'none' }
  }
  
  // Calculate stats
  const distinctLenders = new Set(data.map((row: RateRow) => row.lender_name)).size
  const maxUpdatedAt = data.reduce((max: string, row: RateRow) => {
    return row.updated_at > max ? row.updated_at : max
  }, data[0].updated_at)
  
  const stats: RunStats = {
    total_offers: data.length,
    distinct_lenders: distinctLenders,
    last_run_at: maxUpdatedAt
  }
  
  // Determine status based on distinct lender count
  const status = distinctLenders >= 10 ? 'live' : (distinctLenders >= 1 ? 'partial' : 'none')
  
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
  const name = row.lender_name || ''
  if (name.includes('Bankrate')) return '📊 Bankrate'
  if (name.includes('NerdWallet')) return '📊 NerdWallet'
  if (name.includes('DCU')) return '🏛️ Direct'
  return '🏛️ Direct'
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
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
              ⚠ Partial Data
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
          <h2 className="text-xl font-medium mb-3">{cat}</h2>Source</th>
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
                    <td className="px-3 py-2 text-xs">{getSourceLabel(row)}</td>
                    <td className="px-3 py-2">{formatPct(row.rate)}</td>
                    <td className="px-3 py-2">{formatPct(row.apr)}</td>
                    <td className="px-3 py-2">{row.points !== null && row.points !== undefined ? row.points : 'N/A'}</td>
                    <td className="px-3 py-2">{formatCurrency(row.lender_fees)}</td>
                    <td className="px-3 py-2 text-xs">{formatDateEST(row.updated_at)}</td>
                  </tr>
                ))}
                {(!rates[cat] || rates[cat].length === 0) && (
                  <tr>
                    <td className="px-3 py-2 text-sm text-gray-500" colSpan={7}>No rates available for this category
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
    </div> mt-8">
        <p>
          <strong>Disclaimer:</strong> Rates shown are for informational purposes only and may vary based on loan details, property type, location, and lender underwriting. Confirm with the lender before making decisions.
        </p>
        <p>
          <strong>Data Sources:</strong> Aggregated from marketplace data (Bankrate, NerdWallet) and select direct lender sources. 
          Marketplace offers represent national averages and may not reflect rates available to all borrowers. 
          We do not guarantee accuracy or availability.
        </p>
        {status !== 'live' && (
          <p className="text-amber-600">
            <strong>Note:</strong> Data coverage is currently limited. We are actively expanding our lender network to provide more comprehensive rate information.
          </p>
        )}