import { useState } from 'react'

import { formatNumber, toPersianDigits } from '../lib/format.js'
import { coverageColor } from '../lib/format.js'
import { useApp, useSelectionSummary } from '../lib/store.jsx'

/** سبد انتخاب: آمار زنده، پوشش بخش‌ها، پیش‌نیازهای خودکار و موتورهای AI */
export default function SelectionCart() {
  const { resolution, resolving, clearSelection, selectEverything, meta, selection } = useApp()
  const summary = useSelectionSummary()
  const [tab, setTab] = useState('summary')

  const totals = meta?.counts || summary.totals || {}
  const coverage = (summary.coverage || []).filter((row) => row.modules_selected > 0)

  const percent = (value, total) => (total ? Math.round((value / total) * 100) : 0)

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">سبد انتخاب</h3>
          <p className="card-subtitle">
            {resolving ? 'در حال حل وابستگی‌ها…' : resolution ? 'وابستگی‌ها حل شد' : 'منتظر انتخاب ماژول'}
          </p>
        </div>
        <div className="btn-row">
          <button type="button" className="btn ghost xs" onClick={selectEverything}>
            کل کاتالوگ
          </button>
          <button type="button" className="btn ghost xs" onClick={clearSelection}>
            پاک کردن
          </button>
        </div>
      </div>

      <div className="grid cols-3 mb-14">
        <div className="stat accent">
          <span className="value">{toPersianDigits(summary.modules)}</span>
          <span className="label">ماژول فعال</span>
          <span className="hint">از {toPersianDigits(totals.modules || 130)}</span>
        </div>
        <div className="stat">
          <span className="value">{formatNumber(summary.items)}</span>
          <span className="label">زیرمجموعه</span>
          <span className="hint">از {formatNumber(totals.items || 2157)}</span>
        </div>
        <div className="stat">
          <span className="value">{toPersianDigits(summary.ai_points)}</span>
          <span className="label">نقطه AI</span>
          <span className="hint">از {toPersianDigits(totals.ai_points || 266)}</span>
        </div>
      </div>

      <div className="tabs">
        {[
          ['summary', 'برآورد'],
          ['coverage', 'پوشش'],
          ['deps', `پیش‌نیازها (${toPersianDigits(summary.auto_added.length)})`],
          ['engines', `موتورها (${toPersianDigits((resolution?.ai_engines || []).length)})`],
        ].map(([key, label]) => (
          <button key={key} type="button" className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'summary' && (
        <div className="col" style={{ gap: 8 }}>
          <dl className="kv">
            <dt>بخش‌های درگیر</dt>
            <dd>{toPersianDigits(summary.sections)}</dd>
            <dt>زیرماژول‌ها</dt>
            <dd>{formatNumber(summary.groups)}</dd>
            <dt>جداول پایگاه داده</dt>
            <dd>{summary.tables === null ? '—' : formatNumber(summary.tables)}</dd>
            <dt>فیلدها</dt>
            <dd>{summary.fields === null ? '—' : formatNumber(summary.fields)}</dd>
            <dt>موتورهای AI لازم</dt>
            <dd>{summary.ai_engines === null ? '—' : toPersianDigits(summary.ai_engines)}</dd>
            <dt>فایل‌های برآوردی</dt>
            <dd>{summary.estimated_files === null ? '—' : formatNumber(summary.estimated_files)}</dd>
            <dt>حالت انتخاب</dt>
            <dd>{selection.mode === 'all' ? 'کل کاتالوگ' : 'سفارشی'}</dd>
          </dl>
          {summary.tables === null && (
            <div className="note-box">
              برای دیدن برآورد دقیق جدول‌ها و فایل‌ها، دست‌کم یک ماژول انتخاب کنید.
            </div>
          )}
        </div>
      )}

      {tab === 'coverage' && (
        <div className="coverage">
          {coverage.length === 0 ? (
            <div className="empty">هنوز بخشی انتخاب نشده است.</div>
          ) : (
            coverage.map((row) => (
              <div className="coverage-row" key={row.code}>
                <span className="name" title={`${row.name} (${row.name_en})`}>
                  {row.name}
                </span>
                <span className="coverage-bar">
                  <i
                    style={{
                      width: `${percent(row.modules_selected, row.modules_total)}%`,
                      background: coverageColor(percent(row.modules_selected, row.modules_total)),
                    }}
                  />
                </span>
                <span className="pct">
                  {toPersianDigits(row.modules_selected)}/{toPersianDigits(row.modules_total)}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'deps' && (
        <div className="col" style={{ gap: 6 }}>
          {summary.auto_added.length === 0 ? (
            <div className="empty">پیش‌نیاز خودکاری افزوده نشد.</div>
          ) : (
            <>
              <div className="tiny dim mb-10">
                این ماژول‌ها برای سازگاری داده‌ای و عملکردی به انتخاب شما افزوده شدند (ماژول‌های سیستمی + پشتیبانی).
              </div>
              <div className="table-scroll" style={{ maxHeight: 320 }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th>ماژول</th>
                      <th>دلیل</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.auto_added.map((code) => (
                      <tr key={code}>
                        <td className="nowrap">
                          <span className="mono dim">{code}</span>
                        </td>
                        <td className="small">{summary.reasons[code] || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'engines' && (
        <div className="col" style={{ gap: 8 }}>
          {(resolution?.ai_engines || []).length === 0 ? (
            <div className="empty">نقطه هوش مصنوعی فعالی در انتخاب شما نیست.</div>
          ) : (
            (resolution?.ai_engines || []).map((engine) => (
              <div key={engine.engine} className="card card-pad-sm flat" style={{ background: 'rgba(15,23,42,.5)' }}>
                <div className="between">
                  <strong style={{ fontSize: 12.5 }}>{engine.name_fa}</strong>
                  <span className="badge ai">{toPersianDigits(engine.count)} قابلیت</span>
                </div>
                <div className="tiny dim mt-6" style={{ direction: 'ltr', textAlign: 'right' }}>
                  {engine.endpoint}
                </div>
                <div className="row tiny mt-6">
                  {(engine.algorithms || []).slice(0, 4).map((algorithm) => (
                    <span className="pill" key={algorithm}>
                      {algorithm}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
