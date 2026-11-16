/**
 * ابزارهای نمایش فارسی: رقم، پول، درصد، تاریخ شمسی و اندازه فایل.
 */

const FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
const EN_DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

/** تبدیل رقم‌های لاتین به فارسی */
export function toPersianDigits(value) {
  if (value === null || value === undefined) return ''
  return String(value).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)])
}

/** تبدیل رقم‌های فارسی/عربی به لاتین */
export function toLatinDigits(value) {
  if (value === null || value === undefined) return ''
  return String(value)
    .replace(/[۰-۹]/g, (d) => EN_DIGITS[d.charCodeAt(0) - 0x06f0])
    .replace(/[٠-٩]/g, (d) => EN_DIGITS[d.charCodeAt(0) - 0x0660])
}

/** جداسازی هزارگان با رقم فارسی */
export function formatNumber(value) {
  const num = Number(toLatinDigits(value))
  if (!Number.isFinite(num)) return toPersianDigits(value ?? '')
  return toPersianDigits(num.toLocaleString('en-US'))
}

/** عدد مختصر برای آمارهای بزرگ */
export function compactNumber(value) {
  const num = Number(toLatinDigits(value)) || 0
  if (num >= 1000) return toPersianDigits((num / 1000).toFixed(num >= 10000 ? 0 : 1)) + ' هزار'
  return toPersianDigits(num.toLocaleString('en-US'))
}

export function formatPercent(value, digits = 0) {
  const num = Number(toLatinDigits(value)) || 0
  return `${toPersianDigits(num.toFixed(digits))}٪`
}

export function formatBytes(bytes) {
  const value = Number(bytes) || 0
  if (value < 1024) return `${toPersianDigits(value)} بایت`
  const units = ['کیلوبایت', 'مگابایت', 'گیگابایت']
  let size = value / 1024
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${toPersianDigits(size.toFixed(size >= 100 ? 0 : 1))} ${units[unit]}`
}

/** تبدیل میلادی به شمسی (الگوریتم جلالی، بدون وابستگی بیرونی) */
export function toJalali(gy, gm, gd) {
  const gDaysInMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
  const gy2 = gm > 2 ? gy + 1 : gy
  let days =
    355666 +
    365 * gy +
    Math.floor((gy2 + 3) / 4) -
    Math.floor((gy2 + 99) / 100) +
    Math.floor((gy2 + 399) / 400) +
    gd +
    gDaysInMonth[gm - 1]
  let jy = -1595 + 33 * Math.floor(days / 12053)
  days %= 12053
  jy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    jy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }
  const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30)
  const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30)
  return { jy, jm, jd }
}

export const JALALI_MONTHS = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

/** نمایش تاریخ ISO به شمسی */
export function formatJalali(iso, withTime = false) {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return String(iso)
  const { jy, jm, jd } = toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
  const base = `${toPersianDigits(jd)} ${JALALI_MONTHS[jm - 1]} ${toPersianDigits(jy)}`
  if (!withTime) return base
  const hh = String(date.getUTCHours()).padStart(2, '0')
  const mm = String(date.getUTCMinutes()).padStart(2, '0')
  return `${base} — ${toPersianDigits(`${hh}:${mm}`)} UTC`
}

/** نمایش نسبی زمان («۳ دقیقه پیش») */
export function timeAgo(iso) {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return String(iso)
  const diff = Math.max(0, Date.now() - then)
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'هم‌اکنون'
  if (minutes < 60) return `${toPersianDigits(minutes)} دقیقه پیش`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${toPersianDigits(hours)} ساعت پیش`
  const days = Math.floor(hours / 24)
  return `${toPersianDigits(days)} روز پیش`
}

/** برچسب خوانا برای کلیدهای snake_case (مثل db_driver) */
export function humanKey(key) {
  return String(key)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

/** رنگ برچسب‌دار برای درصد پوشش */
export function coverageColor(percent) {
  if (percent >= 75) return 'var(--emerald)'
  if (percent >= 40) return 'var(--cyan)'
  if (percent >= 15) return 'var(--amber)'
  return 'var(--rose)'
}

/** آیکون متنی برای نام‌های lucide-like کاتالوگ (بدون کتابخانه آیکون) */
const ICONS = {
  factory: '🏭', box: '📦', gauge: '📊', shield: '🛡️', cpu: '🧠', cpu2: '🤖',
  wrench: '🔧', truck: '🚚', cart: '🛒', wallet: '💳', users: '👥', blueprint: '📐',
  kanban: '🗂️', cpuChip: '💠', bulb: '💡', chart: '📈', helmet: '⛑️', zap: '⚡',
  balance: '⚖️', file: '📄', bus: '🚌', target: '🎯', building: '🏢', hardhat: '🦺',
  activity: '📡', database: '🗄️', settings: '⚙️', layers: '🧱', flask: '🧪',
  leaf: '🌿', clock: '⏱️', key: '🔑', bell: '🔔', map: '🗺️', tag: '🏷️',
}

export function iconFor(name, fallback = '📦') {
  if (!name) return fallback
  if (ICONS[name]) return ICONS[name]
  const key = Object.keys(ICONS).find((k) => name.toLowerCase().includes(k.toLowerCase()))
  return key ? ICONS[key] : fallback
}

/** هایلایت ساده و امن کد (بدون کتابخانه؛ خروجی HTML فرار‌شده) */
export function highlight(code, language = '') {
  const escaped = String(code ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  const isPhp = language === 'php' || /^\s*<\?php/.test(escaped)
  const isJs = language === 'js' || language === 'jsx' || language === 'json'
  const isPy = language === 'py' || language === 'python'

  if (!isPhp && !isJs && !isPy) return escaped

  const keywords = isPhp
    ? 'namespace|use|class|extends|implements|public|protected|private|static|function|return|if|else|foreach|for|while|new|null|true|false|array|fn|match|try|catch|throw|const|abstract|final|interface|trait|enum|readonly'
    : isPy
      ? 'def|class|return|if|elif|else|for|while|import|from|as|with|try|except|raise|None|True|False|and|or|not|in|is|lambda|yield|async|await|self'
      : 'const|let|var|function|return|if|else|for|while|import|export|from|default|new|null|true|false|class|extends|async|await|try|catch|throw|typeof|of|in'

  return escaped
    .replace(/(["'`])(?:\\.|(?!\1)[^\\])*\1/g, (m) => `<span class="tok-str">${m}</span>`)
    .replace(/(\/\/[^\n]*|#[^\n]*|\/\*[\s\S]*?\*\/)/g, (m) =>
      m.includes('tok-str') ? m : `<span class="tok-com">${m}</span>`,
    )
    .replace(new RegExp(`\\b(${keywords})\\b`, 'g'), (m, _g, offset, whole) => {
      // از رنگ‌کردن داخل رشته‌ها و کامنت‌های قبلاً نشانه‌گذاری‌شده جلوگیری می‌شود
      const before = whole.slice(Math.max(0, offset - 40), offset)
      if (/class="tok-(str|com)">[^<]*$/.test(before)) return m
      return `<span class="tok-key">${m}</span>`
    })
    .replace(/\b(\d+(?:\.\d+)?)\b/g, (m, _g, offset, whole) => {
      const before = whole.slice(Math.max(0, offset - 30), offset)
      if (/class="tok-(str|com|key)">[^<]*$/.test(before)) return m
      return `<span class="tok-num">${m}</span>`
    })
}

export function languageOf(path) {
  const name = String(path || '').toLowerCase()
  if (name.endsWith('.php')) return 'php'
  if (name.endsWith('.jsx')) return 'jsx'
  if (name.endsWith('.js') || name.endsWith('.mjs') || name.endsWith('.json')) return 'js'
  if (name.endsWith('.py')) return 'py'
  if (name.endsWith('.css')) return 'css'
  if (name.endsWith('.md')) return 'md'
  return ''
}

export default {
  toPersianDigits,
  toLatinDigits,
  formatNumber,
  compactNumber,
  formatPercent,
  formatBytes,
  formatJalali,
  timeAgo,
  iconFor,
  highlight,
  languageOf,
}
