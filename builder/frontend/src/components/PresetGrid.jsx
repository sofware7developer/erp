import { useState } from 'react'

import { formatNumber, iconFor, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

/**
 * شبکه پریست‌های صنعتی
 *
 * هر کارت یک پیکربندی آماده (صنعت + اندازه + تمرکز AI) را نشان می‌دهد و با
 * کلیک، ماژول‌ها، نقاط AI و تنظیمات پیشنهادی را در پیکربندگر اعمال می‌کند.
 */
export default function PresetGrid({ limit = null, onApplied = null }) {
  const { presets, applyPreset, project } = useApp()
  const [busy, setBusy] = useState('')

  const shown = limit ? presets.slice(0, limit) : presets

  const onPick = async (preset) => {
    setBusy(preset.key)
    const payload = await applyPreset(preset.key)
    setBusy('')
    if (payload && onApplied) onApplied(payload)
  }

  if (!presets.length) {
    return <div className="empty">پریستی از سرویس دریافت نشد.</div>
  }

  return (
    <div className="grid cols-3">
      {shown.map((preset) => (
        <button
          key={preset.key}
          type="button"
          className={`preset-card${project.preset_key === preset.key ? ' active' : ''}`}
          onClick={() => onPick(preset)}
          disabled={busy === preset.key}
        >
          <div className="head">
            <span
              className="icon"
              style={{ background: `${preset.color || '#4f46e5'}22`, color: preset.color || '#a5b4fc' }}
            >
              {iconFor(preset.icon, '🏭')}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <strong style={{ fontSize: 13.5 }}>{preset.name}</strong>
              <div className="tiny dim" style={{ direction: 'ltr', textAlign: 'right' }}>
                {preset.name_en}
              </div>
            </div>
            {busy === preset.key ? <span className="spinner" /> : null}
          </div>

          <p>{preset.description}</p>

          <div className="row tiny">
            <span className="badge indigo">{toPersianDigits(preset.module_count)} ماژول</span>
            <span className="badge">{formatNumber(preset.item_count)} قابلیت</span>
            <span className="badge ai">{toPersianDigits(preset.ai_count)} AI</span>
          </div>

          <div className="row tiny dim">
            بخش‌ها: {(preset.sections || []).join('، ')}
          </div>
        </button>
      ))}
    </div>
  )
}
