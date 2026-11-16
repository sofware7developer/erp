/**
 * حداقلِ محیط مرورگر برای رندر سمت سرور
 *
 * این فایل فقط در آزمون دود (npm run smoke) استفاده می‌شود تا کدی که به
 * window/localStorage اشاره می‌کند در Node خطا ندهد. باید «پیش از» ماژول‌های
 * دیگر import شود (ترتیب ارزیابی ESM).
 */
if (typeof globalThis.window === 'undefined') {
  const store = new Map()
  globalThis.window = {
    location: { origin: 'http://localhost:8000', search: '' },
    setTimeout: (...args) => setTimeout(...args),
    clearTimeout: (...args) => clearTimeout(...args),
    requestAnimationFrame: (fn) => setTimeout(fn, 0),
    confirm: () => true,
    localStorage: {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => store.set(key, String(value)),
      removeItem: (key) => store.delete(key),
    },
  }
  globalThis.localStorage = globalThis.window.localStorage
}

// رندر سمت سرور react-router هشدار useLayoutEffect می‌دهد که برای این آزمون
// بی‌اهمیت است؛ فقط همین پیام فیلتر می‌شود تا هشدارهای واقعی دیده شوند.
const IGNORED = ['useLayoutEffect does nothing on the server']
const originalError = console.error.bind(console)
console.error = (...args) => {
  const text = typeof args[0] === 'string' ? args[0] : ''
  if (IGNORED.some((needle) => text.includes(needle))) return
  originalError(...args)
}

export {}
