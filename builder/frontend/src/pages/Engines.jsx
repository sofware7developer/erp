import { useEffect, useMemo, useState } from 'react'

import { catalogApi } from '../lib/api.js'
import { formatNumber, iconFor, toPersianDigits } from '../lib/format.js'
import { useApp, useSelectionSummary } from '../lib/store.jsx'

/** موتورهای هوش مصنوعی و فهرست نقاط AI کاتالوگ */
export default function Engines() {
  const { meta, error, notify, selection } = useApp()
  const summary = useSelectionSummary()
  const engines = meta?.ai_engines || []
  const [engineFilter, setEngineFilter] = useState('')
  const [points, setPoints] = useState([])
  const [busy, setBusy] = useState(true)
  const [activeEngine, setActiveEngine] = useState(null)

  const selectedModules = useMemo(() => new Set(selection.modules || []), [selection.modules])

  useEffect(() => {
    let alive = true
    setBusy(true)
    catalogApi
      .aiPoints(engineFilter ? { engine: engineFilter } : undefined)
      .then((payload) => alive && setPoints(payload.ai_points || []))
      .catch((err) => alive && notify(err.message || 'دریافت نقاط AI ناموفق بود', 'error'))
      .finally(() => alive && setBusy(false))
    return () => {
      alive = false
    }
  }, [engineFilter, notify])

  const byEngine = useMemo(() => {
    const map = new Map()
    points.forEach((point) => {
      const key = point.engine || '—'
      if (!map.has(key)) map.set(key, [])
      map.get(key).push(point)
    })
    return map
  }, [points])

  const detail = activeEngine ? engines.find((item) => item.key === activeEngine) : null

  return (
    <div className="page">
      <div className="between mb-14">
        <div>
          <h1 style={{ fontSize: 20 }}>موتورهای هوش مصنوعی</h1>
          <p className="card-subtitle">
            میکروسرویس <span className="mono">ai-service</span> (FastAPI) این موتورهای واقعی را پیاده‌سازی می‌کند؛
            هر نقطه AI در کاتالوگ به یکی از آن‌ها متصل است و با یک فلگ قابلیت در بک‌اند کنترل می‌شود.
          </p>
        </div>
        <span className="badge ai">
          {toPersianDigits(engines.length)} موتور · {toPersianDigits(meta?.counts?.ai_points || 266)} نقطه AI
        </span>
      </div>

      {error && <div className="error-box mb-14">{error}</div>}

      <div className="grid cols-3">
        {engines.map((engine) => {
          const isActive = activeEngine === engine.key
          return (
            <button
              key={engine.key}
              type="button"
              className={`card engine-card${isActive ? ' active' : ''}`}
              onClick={() => {
                setActiveEngine(isActive ? null : engine.key)
                setEngineFilter(isActive ? '' : engine.key)
              }}
            >
              <div className="between mb-10">
                <div className="row">
                  <span className="badge indigo">{iconFor(engine.category, '🧠')}</span>
                  <strong>{engine.name_fa}</strong>
                </div>
                <span className="mono tiny dim">{engine.key}</span>
              </div>
              <div className="tiny muted" style={{ direction: 'ltr', textAlign: 'right' }}>
                {engine.name_en}
              </div>
              <p className="tiny dim mt-10" style={{ lineHeight: 1.8, margin: 0 }}>
                {engine.description}
              </p>
              <div className="row mt-10" style={{ gap: 5 }}>
                <span className="pill mono">{engine.endpoint}</span>
                {engine.uses_llm && <span className="pill ai">LLM</span>}
                {engine.realtime && <span className="pill ok">بلادرنگ</span>}
                <span className="pill">{toPersianDigits((engine.algorithms || []).length)} الگوریتم</span>
              </div>
              <div className="tiny dim mt-10">
                {toPersianDigits(byEngine.get(engine.key)?.length || 0)} نقطه در کاتالوگ
              </div>
            </button>
          )
        })}
      </div>

      {detail && (
        <div className="card mt-18">
          <div className="card-header">
            <div>
              <h3 className="card-title">{detail.name_fa} — جزئیات فنی</h3>
              <p className="card-subtitle mono" style={{ direction: 'ltr', textAlign: 'right' }}>
                POST {detail.endpoint}
              </p>
            </div>
            <button type="button" className="btn ghost sm" onClick={() => setActiveEngine(null)}>
              بستن
            </button>
          </div>
          <div className="grid cols-2">
            <div>
              <div className="small muted mb-10">الگوریتم‌ها</div>
              <div className="row tiny">
                {(detail.algorithms || []).map((item) => (
                  <span className="pill mono" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="small muted mb-10">خروجی/سنجه‌ها</div>
              <div className="row tiny">
                {(detail.metrics || []).map((item) => (
                  <span className="pill" key={item}>
                    {item}
                  </span>
                ))}
              </div>
              <dl className="kv mt-14">
                <dt>دسته</dt>
                <dd>{detail.category}</dd>
                <dt>نیاز به LLM</dt>
                <dd>{detail.uses_llm ? 'بله (AvalAI در صورت فعال بودن)' : 'خیر — صرفاً الگوریتمی'}</dd>
                <dt>بلادرنگ</dt>
                <dd>{detail.realtime ? 'بله' : 'خیر'}</dd>
              </dl>
            </div>
          </div>
        </div>
      )}

      <div className="card mt-18">
        <div className="card-header">
          <div>
            <h3 className="card-title">فهرست نقاط AI</h3>
            <p className="card-subtitle">
              {busy
                ? 'در حال دریافت…'
                : `${formatNumber(points.length)} نقطه${engineFilter ? ` از موتور ${engineFilter}` : ''} · ${toPersianDigits(summary.ai_points)} نقطه در انتخاب فعلی فعال است`}
            </p>
          </div>
          <div className="row">
            <select
              value={engineFilter}
              onChange={(event) => {
                setEngineFilter(event.target.value)
                setActiveEngine(event.target.value || null)
              }}
            >
              <option value="">همه موتورها</option>
              {engines.map((engine) => (
                <option key={engine.key} value={engine.key}>
                  {engine.name_fa} ({engine.key})
                </option>
              ))}
            </select>
          </div>
        </div>

        {busy && !points.length ? (
          <div className="col">
            {Array.from({ length: 6 }).map((_, index) => (
              <div className="skeleton" key={index} style={{ height: 30 }} />
            ))}
          </div>
        ) : (
          <div className="table-scroll" style={{ maxHeight: 560 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>کد</th>
                  <th>نام قابلیت</th>
                  <th>ماژول</th>
                  <th>موتور</th>
                  <th>مدل</th>
                  <th>فلگ</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {points.map((point) => (
                  <tr key={point.code} className={selectedModules.has(point.module_code) ? 'selected' : ''}>
                    <td className="mono">{point.code}</td>
                    <td>{point.name}</td>
                    <td className="tiny">
                      <span className="pill mono">{point.module_code}</span> {point.module_name}
                    </td>
                    <td className="tiny">{point.engine_name_fa || point.engine}</td>
                    <td className="mono tiny">{point.model_id}</td>
                    <td className="mono tiny dim">{point.feature_flag}</td>
                    <td>{selectedModules.has(point.module_code) && <span className="badge ok">در انتخاب</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
