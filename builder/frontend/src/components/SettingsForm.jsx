import { useMemo, useState } from 'react'

import { toLatinDigits, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

/**
 * فرم تنظیمات کارخانه
 *
 * همه کلیدها همان نام‌هایی هستند که موتور تولید می‌خواند (settings_map)؛
 * بنابراین مقدارهای این فرم مستقیماً در بسته خروجی اثر می‌گذارند.
 */

const CURRENCIES = [
  { id: 'IRR', label: 'ریال ایران (IRR)' },
  { id: 'IRT', label: 'تومان (IRT)' },
  { id: 'USD', label: 'دلار آمریکا (USD)' },
  { id: 'EUR', label: 'یورو (EUR)' },
  { id: 'AED', label: 'درهم امارات (AED)' },
]

const CALENDARS = [
  { id: 'jalali', label: 'شمسی (جلالی)' },
  { id: 'gregorian', label: 'میلادی' },
  { id: 'both', label: 'هر دو (شمسی اصلی + میلادی فرعی)' },
]

const COSTING = [
  { id: 'weighted_average', label: 'میانگین موزون' },
  { id: 'fifo', label: 'FIFO (اولین صادره از اولین وارده)' },
  { id: 'standard', label: 'بهای استاندارد' },
  { id: 'specific', label: 'شناسایی ویژه (سریال/لات)' },
]

const WEEK_DAYS = [
  { id: 'saturday', label: 'شنبه' },
  { id: 'sunday', label: 'یکشنبه' },
  { id: 'monday', label: 'دوشنبه' },
  { id: 'tuesday', label: 'سه‌شنبه' },
  { id: 'wednesday', label: 'چهارشنبه' },
  { id: 'thursday', label: 'پنجشنبه' },
  { id: 'friday', label: 'جمعه' },
]

const MAIL_DRIVERS = [
  { id: 'smtp', label: 'SMTP' },
  { id: 'log', label: 'فقط لاگ (آزمون)' },
  { id: 'array', label: 'حافظه موقت' },
]

function Field({ descriptor, value, onChange }) {
  const { key, label, type = 'text', hint, options, placeholder, min, max, step, dir } = descriptor

  if (type === 'switch') {
    return (
      <label className="switch-row">
        <input type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(key, e.target.checked)} />
        <span className="txt">
          <strong>{label}</strong>
          {hint ? <span>{hint}</span> : null}
        </span>
      </label>
    )
  }

  if (type === 'select') {
    return (
      <label className="field">
        <span>{label}</span>
        <select value={value ?? ''} onChange={(e) => onChange(key, e.target.value)}>
          {(options || []).map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
        {hint ? <span className="tiny dim">{hint}</span> : null}
      </label>
    )
  }

  if (type === 'textarea') {
    return (
      <label className="field">
        <span>{label}</span>
        <textarea
          value={value ?? ''}
          placeholder={placeholder}
          onChange={(e) => onChange(key, e.target.value)}
        />
        {hint ? <span className="tiny dim">{hint}</span> : null}
      </label>
    )
  }

  if (type === 'checkbox-list') {
    const current = Array.isArray(value) ? value : []
    return (
      <fieldset>
        <legend>{label}</legend>
        <div className="form-grid tight">
          {(options || []).map((option) => (
            <label className="switch-row" key={option.id} style={{ padding: '6px 10px' }}>
              <input
                type="checkbox"
                checked={current.includes(option.id)}
                onChange={(e) =>
                  onChange(
                    key,
                    e.target.checked
                      ? [...current, option.id]
                      : current.filter((item) => item !== option.id),
                  )
                }
              />
              <span className="txt">
                <strong>{option.label}</strong>
              </span>
            </label>
          ))}
        </div>
        {hint ? <span className="tiny dim">{hint}</span> : null}
      </fieldset>
    )
  }

  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type === 'password' ? 'password' : type === 'number' ? 'number' : 'text'}
        value={value ?? ''}
        min={min}
        max={max}
        step={step}
        dir={dir}
        placeholder={placeholder}
        onChange={(e) => {
          const next = type === 'number' ? Number(toLatinDigits(e.target.value)) : e.target.value
          onChange(key, next)
        }}
      />
      {hint ? <span className="tiny dim">{hint}</span> : null}
    </label>
  )
}

export default function SettingsForm() {
  const { settings, patchSettings, meta, project, patchProject } = useApp()
  const [tab, setTab] = useState('identity')

  const dbDrivers = meta?.db_drivers?.map((d) => ({ id: d.id, label: d.label })) || [
    { id: 'mysql', label: 'MySQL 8.4' },
    { id: 'mariadb', label: 'MariaDB 11.4' },
    { id: 'pgsql', label: 'PostgreSQL 16' },
    { id: 'sqlite', label: 'SQLite' },
  ]
  const queueDrivers = meta?.queue_drivers?.map((d) => ({ id: d.id, label: d.label })) || []
  const storageDrivers = meta?.storage_drivers?.map((d) => ({ id: d.id, label: d.label })) || []
  const deployTargets = meta?.deploy_targets?.map((d) => ({ id: d.id, label: d.label })) || []

  const TABS = useMemo(
    () => [
      {
        key: 'identity',
        label: 'هویت کارخانه',
        fields: [
          { key: 'company_name', label: 'نام کارخانه (فارسی)', placeholder: 'صنایع پارس' },
          { key: 'company_name_en', label: 'نام کارخانه (انگلیسی)', dir: 'ltr', placeholder: 'Pars Industries' },
          { key: 'company_legal_name', label: 'نام حقوقی / ثبتی' },
          { key: 'company_national_id', label: 'شناسه ملی', dir: 'ltr' },
          { key: 'economic_code', label: 'کد اقتصادی', dir: 'ltr' },
          { key: 'registration_no', label: 'شماره ثبت', dir: 'ltr' },
          { key: 'industry', label: 'صنعت', hint: 'کلید پریست یا توضیح صنعت' },
          { key: 'province', label: 'استان' },
          { key: 'city', label: 'شهر' },
          { key: 'address', label: 'نشانی', type: 'textarea' },
          { key: 'postal_code', label: 'کد پستی', dir: 'ltr' },
          { key: 'phone', label: 'تلفن', dir: 'ltr' },
          { key: 'website', label: 'وب‌سایت', dir: 'ltr' },
          { key: 'employees_count', label: 'تعداد کارکنان', type: 'number', min: 1 },
          { key: 'shifts_per_day', label: 'شیفت در روز', type: 'number', min: 1, max: 4 },
          { key: 'production_lines', label: 'خط تولید', type: 'number', min: 1 },
          { key: 'warehouses_count', label: 'تعداد انبار', type: 'number', min: 1 },
        ],
      },
      {
        key: 'fiscal',
        label: 'تقویم و مالی',
        fields: [
          { key: 'currency', label: 'واحد پول', type: 'select', options: CURRENCIES },
          { key: 'currency_label', label: 'برچسب فارسی پول', placeholder: 'ریال' },
          { key: 'calendar', label: 'تقویم', type: 'select', options: CALENDARS },
          { key: 'timezone', label: 'منطقه زمانی', dir: 'ltr' },
          { key: 'week_start', label: 'آغاز هفته', type: 'select', options: WEEK_DAYS },
          { key: 'weekend_days', label: 'روزهای تعطیل', type: 'checkbox-list', options: WEEK_DAYS },
          { key: 'fiscal_year_start_month', label: 'ماه آغاز سال مالی', type: 'number', min: 1, max: 12 },
          {
            key: 'tax_rate_default',
            label: 'نرخ مالیات بر ارزش افزوده',
            type: 'number',
            step: 0.01,
            min: 0,
            max: 1,
            hint: 'مثلاً ۰٫۱۰ برای ۱۰٪',
          },
          {
            key: 'moadian_enabled',
            label: 'سامانه مودیان مالیاتی',
            type: 'switch',
            hint: 'صورتحساب الکترونیکی و کارپوشه ایرانیان',
          },
          { key: 'costing_method', label: 'روش بهای تمام‌شده', type: 'select', options: COSTING },
        ],
      },
      {
        key: 'infra',
        label: 'پایگاه داده و زیرساخت',
        fields: [
          { key: 'db_driver', label: 'موتور پایگاه داده', type: 'select', options: dbDrivers },
          { key: 'db_host', label: 'میزبان پایگاه داده', dir: 'ltr' },
          { key: 'db_port', label: 'پورت داخلی', type: 'number', dir: 'ltr' },
          { key: 'db_host_port', label: 'پورت روی میزبان (Docker)', type: 'number', dir: 'ltr' },
          { key: 'db_database', label: 'نام پایگاه داده', dir: 'ltr' },
          { key: 'db_username', label: 'کاربر پایگاه داده', dir: 'ltr' },
          {
            key: 'db_password',
            label: 'گذرواژه پایگاه داده',
            type: 'password',
            dir: 'ltr',
            hint: 'خالی بگذارید تا گذرواژه امن تصادفی تولید شود',
          },
          { key: 'cache_driver', label: 'کش', type: 'select', options: [{ id: 'redis', label: 'Redis' }, { id: 'file', label: 'فایل' }, { id: 'database', label: 'پایگاه داده' }] },
          { key: 'queue_driver', label: 'صف', type: 'select', options: queueDrivers.length ? queueDrivers : [{ id: 'redis', label: 'Redis' }, { id: 'database', label: 'پایگاه داده' }, { id: 'sync', label: 'هم‌زمان (sync)' }] },
          { key: 'session_driver', label: 'نشست', type: 'select', options: [{ id: 'database', label: 'پایگاه داده' }, { id: 'redis', label: 'Redis' }, { id: 'file', label: 'فایل' }] },
          { key: 'storage_disk', label: 'ذخیره‌سازی فایل', type: 'select', options: storageDrivers.length ? storageDrivers : [{ id: 'local', label: 'دیسک محلی' }, { id: 's3', label: 'S3 / MinIO' }] },
          { key: 'redis_host', label: 'میزبان Redis', dir: 'ltr' },
          { key: 'redis_port', label: 'پورت Redis', type: 'number', dir: 'ltr' },
        ],
      },
      {
        key: 'ai',
        label: 'هوش مصنوعی',
        fields: [
          { key: 'ai_enabled', label: 'سرویس هوش مصنوعی فعال باشد', type: 'switch', hint: 'میکروسرویس FastAPI با ۱۱ موتور' },
          { key: 'ai_human_approval', label: 'تأیید انسانی برای تصمیم‌های AI', type: 'switch', hint: 'پیشنهادها بدون تأیید اعمال نمی‌شوند' },
          { key: 'ai_service_url', label: 'نشانی سرویس AI', dir: 'ltr' },
          { key: 'avalai_enabled', label: 'استفاده از AvalAI (LLM فارسی)', type: 'switch' },
          { key: 'avalai_api_key', label: 'کلید AvalAI', type: 'password', dir: 'ltr', hint: 'بدون کلید، موتور قاعده‌محور داخلی پاسخ می‌دهد' },
          { key: 'avalai_base_url', label: 'نشانی پایه AvalAI', dir: 'ltr' },
          { key: 'avalai_model', label: 'مدل زبانی', dir: 'ltr' },
        ],
      },
      {
        key: 'iot',
        label: 'IoT و اتصال',
        fields: [
          { key: 'iot_enabled', label: 'ماژول IoT و MQTT فعال باشد', type: 'switch', hint: 'افزودن سرویس mosquitto به docker-compose' },
          { key: 'mqtt_host', label: 'میزبان MQTT', dir: 'ltr' },
          { key: 'mqtt_port', label: 'پورت MQTT', type: 'number', dir: 'ltr' },
          { key: 'mqtt_topic_prefix', label: 'پیشوند تاپیک', dir: 'ltr' },
          { key: 'iot_sampling_seconds', label: 'فاصله نمونه‌برداری (ثانیه)', type: 'number', min: 1 },
          { key: 'cors_origins', label: 'مبدأهای مجاز CORS', dir: 'ltr', hint: 'خالی = مشتق از نشانی برنامه' },
          { key: 'stateful_domains', label: 'دامنه‌های Sanctum', dir: 'ltr' },
        ],
      },
      {
        key: 'mail',
        label: 'ایمیل و اطلاع‌رسانی',
        fields: [
          { key: 'mail_enabled', label: 'ارسال ایمیل فعال باشد', type: 'switch' },
          { key: 'mail_driver', label: 'درایور ایمیل', type: 'select', options: MAIL_DRIVERS },
          { key: 'mail_host', label: 'میزبان SMTP', dir: 'ltr' },
          { key: 'mail_port', label: 'پورت SMTP', type: 'number', dir: 'ltr' },
          { key: 'mail_encryption', label: 'رمزنگاری', type: 'select', options: [{ id: 'tls', label: 'TLS' }, { id: 'ssl', label: 'SSL' }, { id: '', label: 'بدون رمزنگاری' }] },
          { key: 'mail_username', label: 'کاربر SMTP', dir: 'ltr' },
          { key: 'mail_password', label: 'گذرواژه SMTP', type: 'password', dir: 'ltr' },
          { key: 'mail_from', label: 'ایمیل فرستنده', dir: 'ltr' },
          { key: 'mail_from_name', label: 'نام فرستنده' },
          { key: 'sms_enabled', label: 'ارسال پیامک فعال باشد', type: 'switch' },
          { key: 'sms_provider', label: 'ارائه‌دهنده پیامک', dir: 'ltr' },
          { key: 'sms_api_key', label: 'کلید پیامک', type: 'password', dir: 'ltr' },
        ],
      },
      {
        key: 'admin',
        label: 'مدیر و پشتیبان‌گیری',
        fields: [
          { key: 'admin_name', label: 'نام کاربر مدیر' },
          { key: 'admin_email', label: 'ایمیل کاربر مدیر', dir: 'ltr' },
          {
            key: 'admin_password',
            label: 'گذرواژه کاربر مدیر',
            type: 'password',
            dir: 'ltr',
            hint: 'خالی = گذرواژه امن تصادفی (در manifest بسته نوشته می‌شود)',
          },
          { key: 'backup_enabled', label: 'پشتیبان‌گیری خودکار', type: 'switch' },
          { key: 'backup_cron', label: 'زمان‌بندی cron', dir: 'ltr', hint: 'پیش‌فرض: هر شب ساعت ۲' },
          { key: 'backup_keep_days', label: 'نگهداری (روز)', type: 'number', min: 1 },
          { key: 'backup_disk', label: 'دیسک پشتیبان', type: 'select', options: [{ id: 'local', label: 'محلی' }, { id: 's3', label: 'S3 / MinIO' }] },
        ],
      },
      {
        key: 'output',
        label: 'محتوای بسته خروجی',
        fields: [
          { key: 'app_url', label: 'نشانی برنامه', dir: 'ltr' },
          { key: 'host_port', label: 'پورت وب روی میزبان', type: 'number', dir: 'ltr' },
          { key: 'project_slug', label: 'اسلاگ پروژه', dir: 'ltr', hint: 'در نام کانتینرها، حجم‌ها و مسیرها استفاده می‌شود' },
          { key: 'deploy_target', label: 'هدف استقرار', type: 'select', options: deployTargets },
          { key: 'app_env', label: 'محیط اجرا', type: 'select', options: [{ id: 'production', label: 'production' }, { id: 'local', label: 'local' }] },
          { key: 'app_debug', label: 'حالت اشکال‌زدایی', type: 'switch' },
          { key: 'ssl_enabled', label: 'HTTPS/SSL فعال باشد', type: 'switch' },
          { key: 'multi_tenant', label: 'چندکارخانه‌ای (multi-tenant)', type: 'switch' },
          { key: 'include_demo_data', label: 'داده نمونه در seederها', type: 'switch' },
          { key: 'demo_data_months', label: 'بازه تاریخچه داده نمونه (ماه)', type: 'number', min: 1, max: 120, dir: 'ltr', hint: 'تاریخچه عملیاتی پیوسته برای نمودارها و موتورهای AI' },
          { key: 'demo_data_rows', label: 'ردیف پایه هر جدول', type: 'number', min: 1, max: 500, dir: 'ltr', hint: 'جداول جزئیات/دفتر چند برابر این مقدار ردیف می‌گیرند' },
          { key: 'demo_data_seed', label: 'بذر تصادفی داده نمونه', type: 'number', dir: 'ltr', hint: 'عدد ثابت ⇒ خروجی تکرارپذیر؛ برای تغییر داده آن را عوض کنید' },
          { key: 'include_tests', label: 'آزمون‌های Feature (PHPUnit)', type: 'switch' },
          { key: 'include_docs', label: 'مستندات کامل فارسی (docs/)', type: 'switch' },
          { key: 'generate_api_docs', label: 'سند مرجع API', type: 'switch' },
          { key: 'include_report_templates', label: 'قالب‌های گزارش آماده', type: 'switch' },
          { key: 'include_mobile_pwa', label: 'PWA موبایل و کار آفلاین', type: 'switch' },
        ],
      },
    ],
    [dbDrivers, deployTargets, queueDrivers, storageDrivers],
  )

  const active = TABS.find((item) => item.key === tab) || TABS[0]
  const onChange = (key, value) => patchSettings({ [key]: value })

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">تنظیمات کارخانه</h3>
          <p className="card-subtitle">
            این مقدارها مستقیماً در فایل‌های .env، docker-compose، nginx و مستندات بسته نوشته می‌شوند.
          </p>
        </div>
        <span className="badge indigo">{toPersianDigits(TABS.length)} گروه</span>
      </div>

      <div className="grid cols-2 mb-14">
        <label className="field">
          <span>نام پروژه</span>
          <input value={project.name || ''} onChange={(e) => patchProject({ name: e.target.value })} />
        </label>
        <label className="field">
          <span>نام پروژه (انگلیسی)</span>
          <input
            dir="ltr"
            value={project.name_en || ''}
            onChange={(e) => patchProject({ name_en: e.target.value })}
          />
        </label>
        <label className="field" style={{ gridColumn: '1 / -1' }}>
          <span>توضیح پروژه (در README و manifest بسته درج می‌شود)</span>
          <textarea
            value={project.description || ''}
            onChange={(e) => patchProject({ description: e.target.value })}
            placeholder="ERP کارخانه قطعه‌سازی با تمرکز بر ردیابی کیفیت و نت پیشگیرانه"
          />
        </label>
      </div>

      <div className="tabs">
        {TABS.map((item) => (
          <button key={item.key} type="button" className={tab === item.key ? 'active' : ''} onClick={() => setTab(item.key)}>
            {item.label}
          </button>
        ))}
      </div>

      <div className="form-grid">
        {active.fields.map((descriptor) => (
          <div
            key={descriptor.key}
            style={descriptor.type === 'textarea' || descriptor.type === 'checkbox-list' ? { gridColumn: '1 / -1' } : undefined}
          >
            <Field descriptor={descriptor} value={settings[descriptor.key]} onChange={onChange} />
          </div>
        ))}
      </div>

      <hr className="sep" />
      <div className="row tiny dim">
        <span>
          گذرواژه‌های خالی (پایگاه داده و کاربر مدیر) هنگام تولید بسته با مقدار امن تصادفی پر می‌شوند و در
          <span className="mono"> manifest.json</span> و <span className="mono">.env</span> بسته نوشته می‌شوند.
        </span>
      </div>
    </div>
  )
}
