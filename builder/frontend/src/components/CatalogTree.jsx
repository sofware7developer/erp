import { useEffect, useMemo, useRef, useState } from 'react'

import { catalogApi } from '../lib/api.js'
import { formatNumber, iconFor, toPersianDigits } from '../lib/format.js'
import { checkboxState, nodeCounts } from '../lib/selection.js'
import { useApp } from '../lib/store.jsx'

/** چک‌باکس با حالت «نسبی» (indeterminate) */
function Checkbox({ state, onChange, label }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = state === 'partial'
  }, [state])
  return (
    <input
      ref={ref}
      type="checkbox"
      checked={state === 'all'}
      onChange={onChange}
      aria-label={label}
      onClick={(event) => event.stopPropagation()}
    />
  )
}

/** جست‌وجوی کاتالوگ با debounce */
function useCatalogSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    const text = query.trim()
    if (text.length < 2) {
      setResults(null)
      setSearching(false)
      return undefined
    }
    setSearching(true)
    const timer = window.setTimeout(async () => {
      try {
        const payload = await catalogApi.search(text, 80)
        setResults(payload.results || [])
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 320)
    return () => window.clearTimeout(timer)
  }, [query])

  return { query, setQuery, results, searching }
}

/** درخت چهارسطحی کاتالوگ قابلیت‌ها
 *
 * `initialSection` کد بخشی است که باید هنگام ورود باز شود (مثلاً وقتی کاربر در
 * صفحه خانه روی چیپ یک بخش کلیک می‌کند و با `?section=A` به پیکربندگر می‌آید).
 */
export default function CatalogTree({ initialSection = null }) {
  const { catalog, hierarchy, derived, toggleCode, toggleAi, selection, resolution } = useApp()
  const [open, setOpen] = useState(() => new Set())
  const [onlyAi, setOnlyAi] = useState(false)
  const [onlySelected, setOnlySelected] = useState(false)
  const { query, setQuery, results, searching } = useCatalogSearch()

  const sections = catalog?.sections || []

  const toggleOpen = (code) => {
    setOpen((current) => {
      const next = new Set(current)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  const openAll = () => setOpen(new Set(sections.map((s) => s.code)))
  const closeAll = () => setOpen(new Set())

  // باز کردن بخش درخواست‌شده از URL و خاموش کردن فیلترها تا دیده شود
  useEffect(() => {
    if (!initialSection) return
    setOpen((current) => new Set([...current, initialSection]))
    setOnlyAi(false)
    setOnlySelected(false)
  }, [initialSection])

  const selectedModules = derived?.modules || new Set()
  const autoAdded = useMemo(() => new Set(resolution?.auto_added || []), [resolution])

  /* ------------------------------------------------------------- فیلترها */
  const moduleVisible = (module) => {
    if (onlySelected && !selectedModules.has(module.code)) return false
    if (onlyAi && !(module.ai_count > 0)) return false
    return true
  }

  const groupVisible = (group) => {
    if (onlySelected && !derived.groups.has(group.code)) return false
    if (onlyAi && !(group.ai_count > 0)) return false
    return true
  }

  const itemVisible = (item) => {
    if (onlySelected && !derived.items.has(item.code)) return false
    if (onlyAi && !item.ai) return false
    return true
  }

  if (!catalog) {
    return (
      <div className="card">
        <div className="skeleton" style={{ height: 18, marginBottom: 10 }} />
        <div className="skeleton" style={{ height: 18, marginBottom: 10 }} />
        <div className="skeleton" style={{ height: 18, width: '60%' }} />
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">کاتالوگ قابلیت‌ها</h3>
          <p className="card-subtitle">
            چهار سطح: بخش ← ماژول ← زیرماژول ← زیرمجموعه. انتخاب هر سطح، همه زیرمجموعه‌هایش را فعال می‌کند.
          </p>
        </div>
        <div className="btn-row">
          <button type="button" className="btn ghost sm" onClick={openAll}>
            باز کردن بخش‌ها
          </button>
          <button type="button" className="btn ghost sm" onClick={closeAll}>
            بستن همه
          </button>
        </div>
      </div>

      <div className="row mb-14">
        <input
          type="search"
          value={query}
          placeholder="جست‌وجو در ۲۱۵۷ قابلیت… (مثلاً «ردیابی»، «SPC»، «بهای تمام‌شده»)"
          onChange={(event) => setQuery(event.target.value)}
          style={{ flex: 1, minWidth: 220 }}
        />
        <label className="switch-row" style={{ padding: '7px 11px' }}>
          <input type="checkbox" checked={onlyAi} onChange={(e) => setOnlyAi(e.target.checked)} />
          <span className="txt">
            <strong>فقط نقاط AI</strong>
          </span>
        </label>
        <label className="switch-row" style={{ padding: '7px 11px' }}>
          <input type="checkbox" checked={onlySelected} onChange={(e) => setOnlySelected(e.target.checked)} />
          <span className="txt">
            <strong>فقط انتخاب‌شده</strong>
          </span>
        </label>
      </div>

      {/* ------------------------------------------------------- نتایج جست‌وجو */}
      {results ? (
        <div className="col" style={{ gap: 6 }}>
          <div className="between">
            <span className="small muted">
              {searching ? 'در حال جست‌وجو…' : `${toPersianDigits(results.length)} نتیجه برای «${query}»`}
            </span>
            <button type="button" className="btn ghost xs" onClick={() => setQuery('')}>
              پاک کردن جست‌وجو
            </button>
          </div>
          {results.length === 0 && !searching ? <div className="empty">نتیجه‌ای یافت نشد.</div> : null}
          <div className="tree-scroll" style={{ maxHeight: '58vh' }}>
            {results.map((item) => {
              const on = derived.items.has(item.code)
              return (
                <div key={item.code} className={`tree-row${on ? ' selected' : ''}`}>
                  <Checkbox
                    state={on ? 'all' : 'none'}
                    label={item.name}
                    onChange={() => toggleCode(item.code)}
                  />
                  <div className="title">
                    <span className="code">{item.code}</span>
                    {item.name}
                    <span className="en">
                      {item.module_code} · {item.module_name} — {item.section_name}
                    </span>
                  </div>
                  <div className="meta">
                    {item.ai ? <span className="badge ai">AI</span> : null}
                    <button
                      type="button"
                      className="btn ghost xs"
                      onClick={() => {
                        setOpen((current) => new Set([...current, item.section_code, item.module_code, item.group_code]))
                        setQuery('')
                      }}
                    >
                      نمایش در درخت
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        /* ------------------------------------------------------------ درخت */
        <div className="tree-scroll">
          <div className="tree">
            {sections.map((section) => {
              const counts = nodeCounts(hierarchy, derived, 'sections', section.code)
              const state = checkboxState(counts)
              const isOpen = open.has(section.code)
              const visibleModules = (section.modules || []).filter(moduleVisible)
              if (visibleModules.length === 0 && (onlyAi || onlySelected)) return null

              return (
                <div key={section.code}>
                  <div
                    className={`tree-row${state === 'all' ? ' selected' : state === 'partial' ? ' partial' : ''}`}
                    onClick={() => toggleOpen(section.code)}
                  >
                    <span className={`caret${isOpen ? ' open' : ''}`}>▼</span>
                    <Checkbox
                      state={state}
                      label={section.name}
                      onChange={() => toggleCode(section.code)}
                    />
                    <span
                      className="swatch"
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: 3,
                        background: section.color || '#6366f1',
                        flex: 'none',
                      }}
                    />
                    <div className="title">
                      <span className="code">{section.code}</span>
                      <strong>{section.name}</strong>
                      <span className="en">{section.name_en}</span>
                    </div>
                    <div className="meta">
                      <span className="badge">{iconFor(section.icon, '🏭')}</span>
                      <span className="badge">
                        {toPersianDigits(counts.selected)}/{toPersianDigits(counts.total)} ماژول
                      </span>
                      <span className="badge ai">{toPersianDigits(section.ai_count)} AI</span>
                    </div>
                  </div>

                  {isOpen && (
                    <div className="tree-children mt-6">
                      <div className="tiny dim mb-10" style={{ lineHeight: 1.9 }}>
                        {section.description}
                      </div>
                      {visibleModules.map((module) => {
                        const mCounts = nodeCounts(hierarchy, derived, 'modules', module.code)
                        const mState = checkboxState(mCounts)
                        const mOpen = open.has(module.code)
                        const visibleGroups = (module.groups || []).filter(groupVisible)
                        const isAuto = autoAdded.has(module.code) && !selection.modules.includes(module.code)

                        return (
                          <div key={module.code}>
                            <div
                              className={`tree-row${mState === 'all' ? ' selected' : mState === 'partial' ? ' partial' : ''}`}
                              onClick={() => toggleOpen(module.code)}
                            >
                              <span className={`caret${mOpen ? ' open' : ''}`}>▼</span>
                              <Checkbox
                                state={mState}
                                label={module.name}
                                onChange={() => toggleCode(module.code)}
                              />
                              <div className="title">
                                <span className="code">{module.code}</span>
                                {module.name}
                                {isAuto ? <span className="badge warn">پیش‌نیاز خودکار</span> : null}
                                {module.derived ? <span className="badge">دامنه مشتق‌شده</span> : null}
                                <span className="en">{module.name_en}</span>
                              </div>
                              <div className="meta">
                                <span className="badge">
                                  {toPersianDigits(module.group_count)} زیرماژول
                                </span>
                                <span className="badge">{formatNumber(module.item_count)} مورد</span>
                                {module.ai_count > 0 ? (
                                  <span className="badge ai">{toPersianDigits(module.ai_count)} AI</span>
                                ) : null}
                              </div>
                            </div>

                            {mOpen && (
                              <div className="tree-children mt-6">
                                {module.summary ? (
                                  <div className="tiny dim mb-10">{module.summary}</div>
                                ) : null}
                                {visibleGroups.length === 0 ? (
                                  <div className="empty">موردی با این فیلترها در این ماژول نیست.</div>
                                ) : null}
                                {visibleGroups.map((group) => {
                                  const gCounts = nodeCounts(hierarchy, derived, 'groups', group.code)
                                  const gState = checkboxState(gCounts)
                                  const gOpen = open.has(group.code)
                                  const visibleItems = (group.items || []).filter(itemVisible)

                                  return (
                                    <div key={group.code}>
                                      <div
                                        className={`tree-row${gState === 'all' ? ' selected' : gState === 'partial' ? ' partial' : ''}`}
                                        onClick={() => toggleOpen(group.code)}
                                      >
                                        <span className={`caret${gOpen ? ' open' : ''}`}>▼</span>
                                        <Checkbox
                                          state={gState}
                                          label={group.name}
                                          onChange={() => toggleCode(group.code)}
                                        />
                                        <div className="title">
                                          <span className="code">{group.code}</span>
                                          {group.name}
                                          <span className="en">{group.name_en}</span>
                                        </div>
                                        <div className="meta">
                                          <span className="badge">{toPersianDigits(gCounts.total)} مورد</span>
                                          {gCounts.aiTotal > 0 ? (
                                            <span className="badge ai">{toPersianDigits(gCounts.aiTotal)} AI</span>
                                          ) : null}
                                        </div>
                                      </div>

                                      {gOpen && (
                                        <div className="tree-children mt-6">
                                          {visibleItems.length === 0 ? (
                                            <div className="empty">موردی با این فیلترها نیست.</div>
                                          ) : null}
                                          {visibleItems.map((item) => {
                                            const on = derived.items.has(item.code)
                                            const aiOn = item.ai && derived.ai.has(item.code)
                                            return (
                                              <div key={item.code} className={`tree-row${on ? ' selected' : ''}`}>
                                                <Checkbox
                                                  state={on ? 'all' : 'none'}
                                                  label={item.name}
                                                  onChange={() => toggleCode(item.code)}
                                                />
                                                <div className="title">
                                                  <span className="code">{item.code}</span>
                                                  {item.name}
                                                  {item.role ? (
                                                    <span className="en">نقش: {item.role}</span>
                                                  ) : null}
                                                </div>
                                                <div className="meta">
                                                  {item.entity ? (
                                                    <span className="badge mono">{item.entity}</span>
                                                  ) : null}
                                                  {(item.deps || []).length > 0 ? (
                                                    <span
                                                      className="badge"
                                                      title={`وابسته به: ${item.deps.join('، ')}`}
                                                    >
                                                      {toPersianDigits(item.deps.length)} وابستگی
                                                    </span>
                                                  ) : null}
                                                  {item.ai ? (
                                                    <button
                                                      type="button"
                                                      className={`btn xs ${aiOn ? 'ai' : 'ghost'}`}
                                                      title={aiOn ? 'خاموش کردن نقطه AI' : 'روشن کردن نقطه AI'}
                                                      onClick={(event) => {
                                                        event.stopPropagation()
                                                        toggleAi(item.code)
                                                      }}
                                                    >
                                                      AI {aiOn ? '✓' : '○'}
                                                    </button>
                                                  ) : null}
                                                </div>
                                              </div>
                                            )
                                          })}
                                        </div>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
