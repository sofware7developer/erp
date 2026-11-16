import { formatNumber } from '../lib/format.js'

/** کارت آمار تک‌عددی */
export default function StatCard({ label, value, hint, accent = false }) {
  return (
    <div className={`stat${accent ? ' accent' : ''}`}>
      <span className="value">{typeof value === 'number' ? formatNumber(value) : value}</span>
      <span className="label">{label}</span>
      {hint ? <span className="hint">{hint}</span> : null}
    </div>
  )
}
