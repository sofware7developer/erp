import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { packagesApi } from '../lib/api.js'
import { formatBytes, formatNumber, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

/** نوار تولید بسته: بررسی نهایی، اجرای تولید و نمایش نتیجه */
export default function GenerateBar() {
  const { generate, generating, hasSelection, resolution, lastPackage, notify, project } = useApp()
  const navigate = useNavigate()
  const [saveProject, setSaveProject] = useState(true)
  const [result, setResult] = useState(lastPackage)

  const run = async () => {
    const payload = await generate({ saveProject })
    if (payload) {
      setResult(payload)
      notify('بسته آماده دانلود است', 'ok')
    }
  }

  const counts = resolution?.counts || null

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">تولید بسته استقرار</h3>
          <p className="card-subtitle">
            خروجی: پوشه کامل backend + frontend + ai-service + deploy + docs همراه با فایل zip.
          </p>
        </div>
        {generating ? <span className="spinner lg" /> : null}
      </div>

      {!hasSelection ? (
        <div className="warn-box">
          هنوز ماژولی انتخاب نشده است. از درخت کاتالوگ یا یکی از پریست‌ها شروع کنید.
        </div>
      ) : (
        <>
          <dl className="kv mb-14">
            <dt>ماژول‌های نهایی</dt>
            <dd>{counts ? toPersianDigits(counts.modules) : '—'}</dd>
            <dt>جداول پایگاه داده</dt>
            <dd>{counts ? formatNumber(counts.tables) : '—'}</dd>
            <dt>فیلدها</dt>
            <dd>{counts ? formatNumber(counts.fields) : '—'}</dd>
            <dt>نقاط هوش مصنوعی</dt>
            <dd>{counts ? toPersianDigits(counts.ai_points) : '—'}</dd>
            <dt>برآورد فایل خروجی</dt>
            <dd>{counts ? formatNumber(counts.estimated_files) : '—'}</dd>
          </dl>

          <label className="switch-row mb-14">
            <input type="checkbox" checked={saveProject} onChange={(e) => setSaveProject(e.target.checked)} />
            <span className="txt">
              <strong>ذخیره پروژه در لیست پروژه‌ها</strong>
              <span>برای بازتولید بعدی با همان انتخاب و تنظیمات</span>
            </span>
          </label>

          <button type="button" className="btn primary block" onClick={run} disabled={generating}>
            {generating ? 'در حال تولید بسته…' : `تولید بسته «${project.name || 'ERP کارخانه'}»`}
          </button>
        </>
      )}

      {result && (
        <div className="mt-18">
          <hr className="sep" />
          <div className="between mb-10">
            <div>
              <h4 className="card-title">بسته ساخته شد</h4>
              <p className="card-subtitle mono" style={{ direction: 'ltr', textAlign: 'right' }}>
                {result.package_id}
              </p>
            </div>
            <div className="btn-row">
              <a className="btn sm" href={packagesApi.downloadUrl(result.package_id)} download>
                ⬇ دانلود zip ({formatBytes(result.zip_size_bytes)})
              </a>
              <button
                type="button"
                className="btn primary sm"
                onClick={() => navigate(`/packages/${result.package_id}`)}
              >
                مرور بسته
              </button>
            </div>
          </div>

          <div className="grid cols-4 mb-14">
            <div className="stat">
              <span className="value">{formatNumber(result.file_count)}</span>
              <span className="label">فایل</span>
            </div>
            <div className="stat">
              <span className="value">{formatNumber(result.line_count)}</span>
              <span className="label">خط کد</span>
            </div>
            <div className="stat">
              <span className="value">{formatBytes(result.zip_size_bytes)}</span>
              <span className="label">حجم zip</span>
            </div>
            <div className="stat">
              <span className="value">{toPersianDigits(result.stats?.areas ? Object.keys(result.stats.areas).length : 0)}</span>
              <span className="label">ناحیه خروجی</span>
            </div>
          </div>

          {result.notes?.length ? (
            <div className="col" style={{ gap: 6 }}>
              {result.notes.map((note, index) => (
                <div key={index} className={note.startsWith('هشدار') ? 'warn-box' : 'note-box'}>
                  {note}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
