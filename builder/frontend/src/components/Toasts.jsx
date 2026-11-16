import { useApp } from '../lib/store.jsx'

const ICONS = { ok: '✓', err: '✕', info: 'ℹ' }

/** پیام‌های موقت گوشه صفحه */
export default function Toasts() {
  const { toasts, dismissToast } = useApp()
  if (!toasts.length) return null

  return (
    <div className="toasts">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${toast.kind}`}>
          <strong aria-hidden="true">{ICONS[toast.kind] || ICONS.info}</strong>
          <span style={{ flex: 1 }}>{toast.message}</span>
          <button type="button" className="btn ghost xs" onClick={() => dismissToast(toast.id)}>
            بستن
          </button>
        </div>
      ))}
    </div>
  )
}
