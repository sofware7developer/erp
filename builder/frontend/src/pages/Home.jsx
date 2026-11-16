import { Link } from 'react-router-dom'

import PresetGrid from '../components/PresetGrid.jsx'
import StatCard from '../components/StatCard.jsx'
import { formatNumber, iconFor, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

/** خانه: نمای کلی کاتالوگ، پریست‌ها، موتورهای AI و مسیر شروع سریع */
export default function Home() {
  const { meta, catalog, error, loading, packages, presets } = useApp()
  const counts = meta?.counts || catalog?.stats?.totals || {}
  const sections = catalog?.sections || []
  const coverage = meta?.domain_coverage || {}
  const engines = meta?.ai_engines || []

  return (
    <div className="page">
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="between" style={{ alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: 22 }}>سازنده ERP هوشمند کارخانه‌ای</h1>
            <p className="card-subtitle" style={{ maxWidth: 780, marginTop: 8 }}>
              کاتالوگ کامل قابلیت‌های ERP صنعتی در چهار سطح (بخش ← ماژول ← زیرماژول ← زیرمجموعه) را مرور کنید،
              ماژول‌های مورد نیاز کارخانه خود را انتخاب کنید و یک بسته استقرار کامل شامل بک‌اند لاراول،
              رابط کاربری ری‌اکت، میکروسرویس هوش مصنوعی پایتون، پیکربندی Docker/Nginx و مستندات فارسی
              تحویل بگیرید.
            </p>
            <div className="btn-row mt-14">
              <Link to="/configure" className="btn primary">
                شروع پیکربندی
              </Link>
              <Link to="/engines" className="btn">
                مرور موتورهای هوش مصنوعی
              </Link>
              <Link to="/packages" className="btn ghost">
                بسته‌های تولیدشده ({toPersianDigits(packages.length)})
              </Link>
              <a className="btn ghost" href="/api/docs" target="_blank" rel="noreferrer">
                مستندات API
              </a>
            </div>
          </div>
          <div className="col tiny dim" style={{ alignItems: 'flex-end', gap: 6 }}>
            <span className="badge indigo">نسخه {meta?.version || '1.0.0'}</span>
            <span className="badge">کاتالوگ {meta?.catalog_version || '1.0.0'}</span>
            <span className={`badge ${meta?.avalai?.configured ? 'ai' : ''}`}>
              {meta?.avalai?.configured ? 'AvalAI متصل است' : 'AvalAI تنظیم نشده'}
            </span>
          </div>
        </div>
      </div>

      {error && <div className="error-box mb-14">{error}</div>}

      <div className="grid cols-6">
        <StatCard label="بخش صنعتی" value={counts.sections || 0} accent />
        <StatCard label="ماژول" value={counts.modules || 0} />
        <StatCard label="زیرماژول" value={counts.groups || 0} />
        <StatCard label="زیرمجموعه" value={counts.items || 0} />
        <StatCard label="نقطه هوش مصنوعی" value={counts.ai_points || 0} hint="۱۱ موتور الگوریتمی" />
        <StatCard
          label="جدول داده"
          value={coverage.entities_total ?? 0}
          hint={coverage.total_modules ? `از ${toPersianDigits(coverage.total_modules)} ماژول` : ''}
        />
      </div>

      <h2 className="section-title">
        <span className="bar" /> پریست‌های صنعتی — شروع در یک کلیک
      </h2>
      <PresetGrid />

      <div className="grid cols-2 mt-18">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">۲۲ بخش کاتالوگ</h3>
              <p className="card-subtitle">هر بخش شامل ماژول‌ها، زیرماژول‌ها و نقاط AI اختصاصی است.</p>
            </div>
            <Link to="/configure" className="btn ghost sm">
              مرور کامل
            </Link>
          </div>
          <div className="row" style={{ gap: 7 }}>
            {loading.catalog && !sections.length
              ? Array.from({ length: 12 }).map((_, index) => (
                  <span className="skeleton" key={index} style={{ width: 96, height: 26 }} />
                ))
              : sections.map((section) => (
                  <Link key={section.code} to={`/configure?section=${section.code}`} className="section-chip">
                    <span className="swatch" style={{ background: section.color || '#6366f1' }} />
                    {iconFor(section.icon, '🏭')} {section.name}
                    <span className="dim">{toPersianDigits(section.module_count)}</span>
                  </Link>
                ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">موتورهای هوش مصنوعی</h3>
              <p className="card-subtitle">
                هر موتور الگوریتم‌های واقعی خود را در میکروسرویس پایتون پیاده‌سازی می‌کند و در نبود داده کافی،
                پاسخ قاعده‌محور فارسی برمی‌گرداند.
              </p>
            </div>
            <Link to="/engines" className="btn ghost sm">
              جزئیات
            </Link>
          </div>
          <div className="table-scroll" style={{ maxHeight: 300 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>موتور</th>
                  <th>اندپوینت</th>
                  <th>الگوریتم‌ها</th>
                </tr>
              </thead>
              <tbody>
                {engines.map((engine) => (
                  <tr key={engine.key}>
                    <td>
                      <strong>{engine.name_fa}</strong>
                      <div className="tiny dim" style={{ direction: 'ltr', textAlign: 'right' }}>
                        {engine.name_en}
                      </div>
                    </td>
                    <td className="mono tiny">{engine.endpoint}</td>
                    <td className="tiny muted">{(engine.algorithms || []).slice(0, 4).join('، ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <h2 className="section-title">
        <span className="bar" /> بسته خروجی چه دارد؟
      </h2>
      <div className="grid cols-3">
        {[
          {
            title: 'backend/ — لاراول ۱۱',
            body: 'مایگریشن، مدل، کنترلر API، FormRequest، Resource، Policy، Factory، آزمون Feature، Seeder و Service برای هر موجودیت؛ پشتیبانی جلالی، متن فارسی، ممیزی، مجوزها و دستورهای artisan.',
            icon: 'database',
          },
          {
            title: 'frontend/ — React + Vite',
            body: 'SPA راست‌به‌چپ بدون کتابخانه UI: منوی پویا از ماژول‌های انتخابی، صفحه داده‌محور CRUD برای هر جدول، مرکز AI، گزارش‌ساز، ممیزی و PWA موبایل.',
            icon: 'layers',
          },
          {
            title: 'ai-service/ — FastAPI',
            body: '۱۱ موتور هوش مصنوعی با numpy/pandas/scikit-learn: پیش‌بینی، ناهنجاری، SPC، قابلیت اطمینان، بهینه‌سازی، طبقه‌بندی، NLP فارسی، پیشنهاد، بینایی ماشین، شبیه‌سازی و MLOps.',
            icon: 'cpu',
          },
          {
            title: 'deploy/ — استقرار یک‌دستوره‌ای',
            body: 'docker-compose (db/redis/mqtt/ai/app/queue/scheduler/web)، nginx، systemd، crontab، deploy.sh، اسکریپت پشتیبان/ارتقا/سلامت و Makefile با ۱۹ هدف.',
            icon: 'settings',
          },
          {
            title: 'docs/ — مستندات فارسی',
            body: 'README فارسی و ۹ سند: معماری، نصب، ماژول‌ها، مدل داده، قابلیت‌های AI، مرجع API، عملیات، راهنمای کاربر و بازتولید بسته.',
            icon: 'file',
          },
          {
            title: 'manifest.json — شناسنامه بسته',
            body: 'فهرست ماژول‌ها، شمارش‌ها، موتورهای AI، پیش‌نیازهای خودکار و بخش reproduce برای ساخت مجدد بسته با همان انتخاب و تنظیمات.',
            icon: 'tag',
          },
        ].map((item) => (
          <div className="card" key={item.title}>
            <div className="row mb-10">
              <span className="badge indigo" style={{ fontSize: 14 }}>
                {iconFor(item.icon, '📦')}
              </span>
              <strong style={{ fontSize: 13.5 }}>{item.title}</strong>
            </div>
            <p className="tiny muted" style={{ margin: 0, lineHeight: 1.9 }}>
              {item.body}
            </p>
          </div>
        ))}
      </div>

      <h2 className="section-title">
        <span className="bar" /> آمار پوشش مدل داده
      </h2>
      <div className="grid cols-4">
        <StatCard
          label="ماژول با مدل داده"
          value={(coverage.handwritten_count || 0) + (coverage.derived_count || 0)}
          hint={`از ${formatNumber(coverage.total_modules || counts.modules || 130)} ماژول`}
        />
        <StatCard label="موجودیت/جدول" value={coverage.entities_total || 0} />
        <StatCard label="فیلد" value={coverage.fields_total || 0} />
        <StatCard
          label="مشخصات دستی / مشتق‌شده"
          value={`${toPersianDigits(coverage.handwritten_count ?? 0)} / ${toPersianDigits(coverage.derived_count ?? 0)}`}
        />
      </div>
    </div>
  )
}
