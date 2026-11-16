import { NavLink } from 'react-router-dom'

import { toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

const LINKS = [
  { to: '/', label: 'خانه', end: true },
  { to: '/configure', label: 'پیکربندگر' },
  { to: '/engines', label: 'موتورهای AI' },
  { to: '/packages', label: 'بسته‌ها' },
]

/** نوار بالای برنامه: برند، ناوبری، شمارنده انتخاب و وضعیت سرویس */
export default function TopBar() {
  const { healthInfo, meta, loading, error, derived, packages } = useApp()
  const ok = Boolean(healthInfo?.status === 'ok') && !error
  const counts = meta?.counts || null

  return (
    <header className="topbar">
      <div className="brand">
        <div className="badge-logo">E</div>
        <div>
          <strong>سازنده ERP هوشمند کارخانه‌ای</strong>
          <span>
            {counts
              ? `${toPersianDigits(counts.modules)} ماژول · ${toPersianDigits(counts.items)} قابلیت · ${toPersianDigits(counts.ai_points)} نقطه AI`
              : 'در حال بارگذاری کاتالوگ…'}
          </span>
        </div>
      </div>

      <nav className="topnav">
        {LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => (isActive ? 'active' : '')}>
            {link.label}
            {link.to === '/packages' && packages.length > 0 ? ` (${toPersianDigits(packages.length)})` : ''}
          </NavLink>
        ))}
      </nav>

      <div className="spacer" />

      {derived && derived.modules.size > 0 && (
        <NavLink to="/configure" className="badge indigo">
          انتخاب فعال: {toPersianDigits(derived.modules.size)} ماژول
        </NavLink>
      )}

      <div className="health">
        <span className={`dot ${loading.meta ? 'busy' : ok ? 'ok' : 'err'}`} />
        {loading.meta
          ? 'در حال اتصال…'
          : ok
            ? `سرویس آماده — v${healthInfo?.version || '1.0'}`
            : 'قطع ارتباط با سرویس'}
        {healthInfo?.avalai_configured ? <span className="badge ai">AvalAI</span> : null}
      </div>
    </header>
  )
}
