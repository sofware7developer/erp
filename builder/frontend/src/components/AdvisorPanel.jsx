import { useState } from 'react'

import { advisorApi } from '../lib/api.js'
import { toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

const BUDGETS = [
  { id: 'low', label: 'محدود (حداقل‌ها)' },
  { id: 'medium', label: 'متوازن' },
  { id: 'high', label: 'گسترده (پوشش کامل)' },
]

const AI_APPETITES = [
  { id: 'low', label: 'کم — فقط گزارش' },
  { id: 'medium', label: 'متوسط — پیشنهادهای هوشمند' },
  { id: 'high', label: 'زیاد — حداکثر قابلیت AI' },
]

/** دستیار هوشمند انتخاب ماژول: پرسش درباره کارخانه، پاسخ با فهرست ماژول و فازها */
export default function AdvisorPanel() {
  const { meta, settings, applyAdvisor, notify, healthInfo } = useApp()
  const goals = meta?.advisor_goals || []
  const industries = meta?.industries || []

  const [form, setForm] = useState({
    industry: settings.industry || 'general_discrete',
    employees_count: Number(settings.employees_count || 150),
    shifts_per_day: Number(settings.shifts_per_day || 2),
    production_lines: Number(settings.production_lines || 3),
    warehouses_count: Number(settings.warehouses_count || 2),
    budget_level: 'medium',
    ai_appetite: 'medium',
    note: '',
  })
  const [chosenGoals, setChosenGoals] = useState([])
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [phases, setPhases] = useState(null)
  const [useLlm, setUseLlm] = useState(false)

  const patch = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  const run = async () => {
    setBusy(true)
    setPhases(null)
    try {
      const payload = { ...form, goals: chosenGoals }
      const response = useLlm && healthInfo?.avalai_configured
        ? await advisorApi.recommend(payload)
        : await advisorApi.recommendFast(payload)
      // دو مسیر پیشنهاد کلیدهای متفاوتی دارند: recommend-fast از
      // modules/ai_points و recommend (LLM) از recommended_modules/
      // recommended_ai_points. اینجا یکدست می‌شوند تا بقیه قسمت‌ها یکسان کار کنند.
      setResult({
        ...response,
        modules: response?.modules || response?.recommended_modules || [],
        ai_points: response?.ai_points || response?.recommended_ai_points || [],
      })
      if (response?.llm_note) notify(response.llm_note, 'info', 6000)
    } catch (error) {
      notify(error.message || 'پیشنهاد ماژول ناموفق بود', 'error')
    } finally {
      setBusy(false)
    }
  }

  const planPhases = async () => {
    if (!result?.modules?.length) return
    setBusy(true)
    try {
      const payload = await advisorApi.phases({ modules: result.modules, ai_points: result.ai_points || [] })
      setPhases(payload)
    } catch (error) {
      notify(error.message || 'ساخت فازبندی ناموفق بود', 'error')
    } finally {
      setBusy(false)
    }
  }

  const apply = () => {
    if (!result?.modules?.length) return
    applyAdvisor(
      result.modules,
      result.ai_points || null,
      `${toPersianDigits(result.modules.length)} ماژول از پیشنهاد دستیار اعمال شد`,
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">دستیار هوشمند انتخاب ماژول</h3>
          <p className="card-subtitle">
            با توصیف کارخانه، فهرست ماژول‌ها، نقاط AI و دلیل هر پیشنهاد را دریافت کنید.
          </p>
        </div>
        {healthInfo?.avalai_configured ? (
          <span className="badge ai">AvalAI فعال</span>
        ) : (
          <span className="badge">قاعده‌محور</span>
        )}
      </div>

      <div className="form-grid tight">
        <label className="field">
          <span>صنعت</span>
          <select value={form.industry} onChange={(e) => patch('industry', e.target.value)}>
            {industries.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>تعداد کارکنان</span>
          <input type="number" min="1" value={form.employees_count} onChange={(e) => patch('employees_count', Number(e.target.value))} />
        </label>
        <label className="field">
          <span>شیفت در روز</span>
          <input type="number" min="1" max="4" value={form.shifts_per_day} onChange={(e) => patch('shifts_per_day', Number(e.target.value))} />
        </label>
        <label className="field">
          <span>خط تولید</span>
          <input type="number" min="1" value={form.production_lines} onChange={(e) => patch('production_lines', Number(e.target.value))} />
        </label>
        <label className="field">
          <span>تعداد انبار</span>
          <input type="number" min="1" value={form.warehouses_count} onChange={(e) => patch('warehouses_count', Number(e.target.value))} />
        </label>
        <label className="field">
          <span>بودجه استقرار</span>
          <select value={form.budget_level} onChange={(e) => patch('budget_level', e.target.value)}>
            {BUDGETS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>اشتیاق به هوش مصنوعی</span>
          <select value={form.ai_appetite} onChange={(e) => patch('ai_appetite', e.target.value)}>
            {AI_APPETITES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-14">
        <div className="small muted mb-10">اهداف کسب‌وکاری (چند مورد انتخاب کنید)</div>
        <div className="row" style={{ gap: 6 }}>
          {goals.map((goal) => {
            const active = chosenGoals.includes(goal)
            return (
              <button
                key={goal}
                type="button"
                className={`section-chip${active ? ' active' : ''}`}
                onClick={() =>
                  setChosenGoals((current) =>
                    active ? current.filter((g) => g !== goal) : [...current, goal],
                  )
                }
              >
                {goal}
              </button>
            )
          })}
        </div>
      </div>

      <label className="field mt-14">
        <span>توضیح آزاد (اختیاری)</span>
        <textarea
          value={form.note}
          onChange={(e) => patch('note', e.target.value)}
          placeholder="مثلاً: دو کارخانه داریم، صدور صورتحساب مودیان الزامی است و خط رنگ به‌زودی اضافه می‌شود."
        />
      </label>

      <div className="btn-row mt-14">
        <button type="button" className="btn primary" onClick={run} disabled={busy}>
          {busy ? <span className="spinner" /> : null} دریافت پیشنهاد ماژول‌ها
        </button>
        {healthInfo?.avalai_configured && (
          <label className="switch-row" style={{ padding: '6px 10px' }}>
            <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
            <span className="txt">
              <strong>تحلیل با AvalAI</strong>
              <span>در غیر این صورت موتور قاعده‌محور پاسخ می‌دهد</span>
            </span>
          </label>
        )}
      </div>

      {result && (
        <div className="mt-18">
          <div className="between mb-10">
            <h4 className="card-title">
              پیشنهاد: {toPersianDigits(result.modules?.length || 0)} ماژول ·{' '}
              {toPersianDigits(result.ai_points?.length || 0)} نقطه AI
            </h4>
            <div className="btn-row">
              <button type="button" className="btn sm" onClick={planPhases} disabled={busy}>
                فازبندی استقرار
              </button>
              <button type="button" className="btn primary sm" onClick={apply}>
                اعمال در انتخاب
              </button>
            </div>
          </div>

          <div className="row tiny mb-10">
            <span className="badge indigo">سطح AI: {result.ai_level || '—'}</span>
            <span className="badge">اندازه: {result.size_bucket || '—'}</span>
            <span className="badge mono">{result.preset_key || '—'}</span>
            <span className="badge warn">{toPersianDigits((result.auto_added || []).length)} پیش‌نیاز خودکار</span>
          </div>

          <div className="col" style={{ gap: 7 }}>
            {(result.rationale || []).map((item, index) => (
              <div key={`${item.type}-${index}`} className="card card-pad-sm flat" style={{ background: 'rgba(15,23,42,.55)' }}>
                <div className="between">
                  <strong style={{ fontSize: 12.5 }}>{item.title}</strong>
                  <span className="badge mono">{item.type}</span>
                </div>
                <div className="tiny muted mt-6">{item.detail}</div>
              </div>
            ))}
          </div>

          <div className="mt-14">
            <div className="small muted mb-10">ماژول‌های پیشنهادی</div>
            <div className="row tiny">
              {(result.modules || []).map((code) => (
                <span className="pill mono" key={code}>
                  {code}
                </span>
              ))}
            </div>
          </div>

          {phases && (
            <div className="mt-18">
              <div className="between mb-10">
                <h4 className="card-title">برنامه فازبندی ({toPersianDigits(phases.total_months)} ماه)</h4>
              </div>
              <div className="table-scroll" style={{ maxHeight: 380 }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th>فاز</th>
                      <th>عنوان</th>
                      <th>مدت</th>
                      <th>ماژول‌ها</th>
                      <th>نقاط AI</th>
                      <th>تحویل‌دادنی‌ها</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(phases.phases || []).map((phase) => (
                      <tr key={phase.order}>
                        <td className="num">{toPersianDigits(phase.order)}</td>
                        <td>
                          <strong>{phase.title}</strong>
                          <div className="tiny dim">{phase.description}</div>
                        </td>
                        <td className="num">{toPersianDigits(phase.duration_months)} ماه</td>
                        <td className="tiny">{toPersianDigits((phase.modules || []).length)}</td>
                        <td className="num">{toPersianDigits((phase.ai_points || []).length)}</td>
                        <td className="tiny muted">{(phase.deliverables || []).join('، ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
