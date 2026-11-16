import { Link } from 'react-router-dom'

import StatCard from '../components/StatCard.jsx'
import { packagesApi } from '../lib/api.js'
import { formatBytes, formatNumber, timeAgo, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

/** فهرست بسته‌های تولیدشده */
export default function Packages() {
  const { packages, refreshPackages, removePackage, notify } = useApp()

  const totals = packages.reduce(
    (acc, item) => ({
      files: acc.files + (item.file_count || 0),
      lines: acc.lines + (item.line_count || 0),
      bytes: acc.bytes + (item.zip_size_bytes || 0),
    }),
    { files: 0, lines: 0, bytes: 0 },
  )

  return (
    <div className="page">
      <div className="between mb-14">
        <div>
          <h1 style={{ fontSize: 20 }}>بسته‌های تولیدشده</h1>
          <p className="card-subtitle">
            هر بسته یک پوشه کامل استقرار به‌همراه فایل zip است؛ می‌توانید ساختار، مانیفست و هر فایل را مرور و
            دانلود کنید.
          </p>
        </div>
        <div className="btn-row">
          <Link to="/configure?tab=generate" className="btn primary">
            تولید بسته جدید
          </Link>
          <button type="button" className="btn ghost" onClick={refreshPackages}>
            ↻ تازه‌سازی
          </button>
        </div>
      </div>

      <div className="grid cols-4 mb-14">
        <StatCard label="بسته" value={packages.length} accent />
        <StatCard label="مجموع فایل‌ها" value={totals.files} />
        <StatCard label="مجموع خط‌های کد" value={totals.lines} />
        <StatCard label="حجم zip" value={formatBytes(totals.bytes)} />
      </div>

      {packages.length === 0 ? (
        <div className="card">
          <div className="empty">
            هنوز بسته‌ای تولید نشده است. ماژول‌ها را انتخاب کنید و از تب «تولید بسته» خروجی بگیرید.
          </div>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th>بسته</th>
                <th>پروژه / پریست</th>
                <th>ایجاد</th>
                <th>ماژول</th>
                <th>جدول</th>
                <th>AI</th>
                <th>فایل</th>
                <th>خط</th>
                <th>zip</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {packages.map((item) => (
                <tr key={item.package_id}>
                  <td>
                    <strong>{item.name}</strong>
                    <div className="tiny dim mono" style={{ direction: 'ltr', textAlign: 'right' }}>
                      {item.package_id}
                    </div>
                  </td>
                  <td className="tiny muted">
                    {item.project_name || '—'}
                    {item.preset_key ? <div className="tiny dim mono">{item.preset_key}</div> : null}
                  </td>
                  <td className="tiny dim num">
                    {item.created_at_jalali ? toPersianDigits(item.created_at_jalali) : '—'}
                    {item.created_at ? <div className="tiny dim">{timeAgo(item.created_at)}</div> : null}
                  </td>
                  <td className="num">{toPersianDigits(item.modules ?? '—')}</td>
                  <td className="num">{toPersianDigits(item.entities ?? '—')}</td>
                  <td className="num">{toPersianDigits(item.ai_points ?? '—')}</td>
                  <td className="num">{item.file_count ? formatNumber(item.file_count) : '—'}</td>
                  <td className="num">{item.line_count ? formatNumber(item.line_count) : '—'}</td>
                  <td className="num tiny">
                    {item.zip_exists ? formatBytes(item.zip_size_bytes) : <span className="dim">ندارد</span>}
                  </td>
                  <td>
                    <div className="row" style={{ gap: 5, justifyContent: 'flex-end' }}>
                      <Link className="btn ghost xs" to={`/packages/${item.package_id}`}>
                        مرور
                      </Link>
                      {item.zip_exists && (
                        <a className="btn ghost xs" href={packagesApi.downloadUrl(item.package_id)} download>
                          ⬇
                        </a>
                      )}
                      <button
                        type="button"
                        className="btn ghost xs danger"
                        onClick={async () => {
                          if (!window.confirm(`بسته ${item.package_id} حذف شود؟`)) return
                          const done = await removePackage(item.package_id)
                          if (!done) notify('حذف بسته ناموفق بود', 'error')
                        }}
                      >
                        حذف
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
