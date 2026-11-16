import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import StatCard from '../components/StatCard.jsx'
import { packagesApi } from '../lib/api.js'
import { formatBytes, formatNumber, highlight, iconFor, languageOf, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

const FILE_ICONS = { php: '🐘', jsx: '⚛️', js: '🟨', py: '🐍', css: '🎨', md: '📄', json: '🧾' }

function fileIcon(path) {
  return FILE_ICONS[languageOf(path)] || '📄'
}

/** درخت فایل‌ها با باز/بسته شدن تدریجی (برای آزمون دود هم export می‌شود) */
export function FileTree({ nodes, depth = 0, active, onOpen, openSet, toggleDir }) {
  return (
    <div className="filetree">
      {nodes.map((node) => {
        const isDir = node.type === 'dir'
        const open = openSet.has(node.path)
        return (
          <div key={node.path}>
            <div
              className={`filetree-row${active === node.path ? ' active' : ''}`}
              style={{ paddingInlineStart: 8 + depth * 12 }}
              onClick={() => (isDir ? toggleDir(node.path) : onOpen(node.path))}
              title={node.path}
            >
              <span className="caret">{isDir ? (open ? '▾' : '▸') : ''}</span>
              <span>{isDir ? '📁' : fileIcon(node.name)}</span>
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {node.name}
              </span>
              <span className="size">
                {isDir ? `${toPersianDigits((node.children || []).length)}` : formatBytes(node.size)}
              </span>
            </div>
            {isDir && open && node.children?.length ? (
              <FileTree
                nodes={node.children}
                depth={depth + 1}
                active={active}
                onOpen={onOpen}
                openSet={openSet}
                toggleDir={toggleDir}
              />
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

export default function PackageDetail() {
  const { packageId } = useParams()
  const { notify } = useApp()
  const [tab, setTab] = useState('files')
  const [summary, setSummary] = useState(null)
  const [manifest, setManifest] = useState(null)
  const [tree, setTree] = useState([])
  const [openSet, setOpenSet] = useState(new Set(['backend', 'frontend', 'ai-service', 'deploy', 'docs']))
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(true)
  const [query, setQuery] = useState('')

  useEffect(() => {
    let alive = true
    setBusy(true)
    ;(async () => {
      try {
        const [detail, manifestPayload] = await Promise.all([
          packagesApi.get(packageId),
          packagesApi.manifest(packageId).catch(() => null),
        ])
        if (!alive) return
        setSummary(detail)
        setManifest(manifestPayload)
      } catch (err) {
        if (alive) notify(err.message || 'بسته یافت نشد', 'error')
      } finally {
        if (alive) setBusy(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [packageId, notify])

  useEffect(() => {
    if (tab !== 'files' || tree.length) return
    let alive = true
    packagesApi
      .tree(packageId)
      .then((payload) => alive && setTree(payload.tree || []))
      .catch((err) => alive && notify(err.message || 'دریافت درخت فایل ناموفق بود', 'error'))
    return () => {
      alive = false
    }
  }, [tab, tree.length, packageId, notify])

  const open = useCallback(
    async (path) => {
      try {
        const payload = await packagesApi.file(packageId, path)
        setFile(payload)
      } catch (err) {
        notify(err.message || 'خواندن فایل ناموفق بود', 'error')
      }
    },
    [packageId, notify],
  )

  const toggleDir = useCallback((path) => {
    setOpenSet((current) => {
      const next = new Set(current)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }, [])

  /** فهرست مسطح فایل‌ها برای جست‌وجو */
  const flatFiles = useMemo(() => {
    const out = []
    const walk = (nodes) => {
      nodes.forEach((node) => {
        if (node.type === 'dir') walk(node.children || [])
        else out.push(node)
      })
    }
    if (tree.length) walk(tree)
    return out
  }, [tree])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return flatFiles.filter((node) => node.path.toLowerCase().includes(q)).slice(0, 80)
  }, [flatFiles, query])

  const stats = summary?.stats || {}
  const areas = stats.areas || {}
  const counts = summary?.manifest_counts || manifest?.counts || {}
  const highlighted = useMemo(
    () => (file ? highlight(file.content, languageOf(file.path)) : ''),
    [file],
  )

  if (busy && !summary) {
    return (
      <div className="page">
        <div className="skeleton" style={{ height: 120, marginBottom: 14 }} />
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="page">
        <div className="error-box">بسته «{packageId}» یافت نشد.</div>
        <Link to="/packages" className="btn ghost mt-14">
          بازگشت به فهرست بسته‌ها
        </Link>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="between mb-14">
        <div>
          <h1 style={{ fontSize: 20 }}>{summary.name}</h1>
          <p className="card-subtitle mono" style={{ direction: 'ltr', textAlign: 'right' }}>
            {summary.package_id}
          </p>
        </div>
        <div className="btn-row">
          <Link to="/packages" className="btn ghost">
            ← فهرست بسته‌ها
          </Link>
          {summary.zip_exists && (
            <a className="btn primary" href={packagesApi.downloadUrl(packageId)} download>
              ⬇ دانلود zip ({formatBytes(summary.zip_size_bytes)})
            </a>
          )}
        </div>
      </div>

      <div className="grid cols-6 mb-14">
        <StatCard label="فایل" value={summary.file_count} accent />
        <StatCard label="خط کد" value={summary.line_count} />
        <StatCard label="ماژول" value={counts.modules ?? summary.modules?.length ?? '—'} />
        <StatCard label="جدول" value={counts.entities ?? counts.tables ?? '—'} />
        <StatCard label="نقطه AI" value={counts.ai_points ?? '—'} />
        <StatCard label="حجم zip" value={formatBytes(summary.zip_size_bytes)} />
      </div>

      <div className="tabs">
        {[
          { key: 'files', label: 'فایل‌ها' },
          { key: 'modules', label: 'ماژول‌ها' },
          { key: 'manifest', label: 'مانیفست' },
          { key: 'areas', label: 'ناحیه‌های خروجی' },
        ].map((item) => (
          <button key={item.key} type="button" className={tab === item.key ? 'active' : ''} onClick={() => setTab(item.key)}>
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'files' && (
        <div className="pkg-grid">
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">درخت فایل‌ها</h3>
                <p className="card-subtitle">
                  {formatNumber(flatFiles.length)} فایل در بسته — برای مشاهده محتوا روی فایل کلیک کنید.
                </p>
              </div>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="جست‌وجوی مسیر… (مثلاً Migration)"
                style={{ width: 230 }}
                dir="ltr"
              />
            </div>

            {query.trim() ? (
              <div className="filetree tree-scroll">
                {filtered.length === 0 ? (
                  <div className="empty">موردی یافت نشد.</div>
                ) : (
                  filtered.map((node) => (
                    <div
                      key={node.path}
                      className={`filetree-row${file?.path === node.path ? ' active' : ''}`}
                      onClick={() => open(node.path)}
                    >
                      <span>{fileIcon(node.name)}</span>
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {node.path}
                      </span>
                      <span className="size">{formatBytes(node.size)}</span>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="tree-scroll">
                <FileTree nodes={tree} active={file?.path} onOpen={open} openSet={openSet} toggleDir={toggleDir} />
              </div>
            )}
          </div>

          <div className="card">
            {file ? (
              <div className="code-wrap">
                <div className="code-head">
                  <span className="path" title={file.path}>
                    {file.path}
                  </span>
                  <span className="spacer" />
                  <span className="badge">{toPersianDigits(file.lines)} خط</span>
                  <span className="badge">{formatBytes(file.size)}</span>
                </div>
                <div className="code-body">
                  <div className="code-lines">
                    {Array.from({ length: Math.min(file.lines, 4000) }, (_, index) => index + 1).join('\n')}
                  </div>
                  <pre dangerouslySetInnerHTML={{ __html: highlighted }} />
                </div>
              </div>
            ) : (
              <div className="empty">یک فایل از درخت انتخاب کنید تا محتوای آن اینجا نمایش داده شود.</div>
            )}
          </div>
        </div>
      )}

      {tab === 'modules' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">ماژول‌های بسته</h3>
              <p className="card-subtitle">
                {toPersianDigits(summary.modules?.length || 0)} ماژول تولیدشده به‌همراه شمارش جدول و نقاط AI.
              </p>
            </div>
          </div>
          <div className="table-scroll" style={{ maxHeight: 620 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>کد</th>
                  <th>ماژول</th>
                  <th>گروه منو</th>
                  <th>جدول</th>
                  <th>AI</th>
                  <th>زیرماژول</th>
                  <th>زیرمجموعه</th>
                  <th>مسیر روت</th>
                </tr>
              </thead>
              <tbody>
                {(summary.modules || []).map((module) => (
                  <tr key={module.code}>
                    <td className="mono">
                      {module.code}
                      {module.derived ? <span className="badge" title="مدل داده این ماژول به‌صورت مشتق‌شده ساخته شده">مشتق</span> : null}
                    </td>
                    <td>
                      <strong>{module.label_fa}</strong>
                      <div className="tiny dim">{module.name_en || ''}</div>
                    </td>
                    <td className="tiny muted">{module.menu_group || '—'}</td>
                    <td className="num">{toPersianDigits(module.entities ?? 0)}</td>
                    <td className="num">{toPersianDigits(module.ai_points ?? 0)}</td>
                    <td className="num">{toPersianDigits(module.groups ?? 0)}</td>
                    <td className="num">{toPersianDigits(module.items ?? 0)}</td>
                    <td className="mono tiny" style={{ direction: 'ltr', textAlign: 'right' }}>
                      routes/modules/{module.slug}.php
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'manifest' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">manifest.json</h3>
              <p className="card-subtitle">
                شناسنامه بسته: شمارش‌ها، موتورهای AI، پیش‌نیازهای خودکار و بخش reproduce برای ساخت مجدد.
              </p>
            </div>
            <span className="badge indigo">{iconFor('tag', '🧾')} شناسنامه</span>
          </div>
          {manifest ? (
            <div className="code-wrap">
              <div className="code-head">
                <span className="path">manifest.json</span>
                <span className="spacer" />
                <span className="badge">{toPersianDigits(Object.keys(manifest).length)} کلید ریشه</span>
              </div>
              <div className="code-body">
                <pre dangerouslySetInnerHTML={{ __html: highlight(JSON.stringify(manifest, null, 2), 'json') }} />
              </div>
            </div>
          ) : (
            <div className="empty">مانیفست این بسته در دسترس نیست.</div>
          )}
        </div>
      )}

      {tab === 'areas' && (
        <div className="grid cols-3">
          {Object.entries(areas).map(([area, data]) => (
            <div className="card" key={area}>
              <div className="row mb-10">
                <span className="badge indigo">{iconFor(area, '📦')}</span>
                <strong className="mono">{area}</strong>
              </div>
              <dl className="kv">
                <dt>فایل</dt>
                <dd>{formatNumber(data.files ?? 0)}</dd>
                <dt>خط</dt>
                <dd>{formatNumber(data.lines ?? 0)}</dd>
                <dt>حجم</dt>
                <dd>{formatBytes(data.bytes ?? 0)}</dd>
              </dl>
            </div>
          ))}
          {Object.keys(areas).length === 0 && <div className="empty">آمار ناحیه‌ها در مانیفست نیست.</div>}
        </div>
      )}

      {summary.notes?.length ? (
        <div className="card mt-18">
          <div className="card-header">
            <div>
              <h3 className="card-title">یادداشت‌های تولید</h3>
              <p className="card-subtitle">هشدارها و راهنمای استقرار پس از تولید بسته.</p>
            </div>
          </div>
          <div className="col" style={{ gap: 7 }}>
            {summary.notes.map((note, index) => (
              <div key={index} className={String(note).startsWith('هشدار') ? 'warn-box' : 'note-box'}>
                {note}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
