import { useRef, useState } from 'react'

import { toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

const SUGGESTIONS = [
  'برای یک کارخانه ۳۰۰ نفره قطعه‌سازی چه ماژول‌هایی لازم دارم؟',
  'تفاوت ماژول‌های A1 و A2 چیست؟',
  'کدام نقاط AI برای کاهش ضایعات مفید است؟',
  'حداقل سخت‌افزار برای استقرار این ERP چیست؟',
]

/** گفت‌وگو با دستیار سازنده (AvalAI در صورت فعال بودن، وگرنه پاسخ قاعده‌محور) */
export default function ChatPanel() {
  const { askAssistant, healthInfo } = useApp()
  const [history, setHistory] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const logRef = useRef(null)

  const send = async (text) => {
    const message = (text ?? draft).trim()
    if (!message || busy) return
    const nextHistory = [...history, { role: 'user', content: message }]
    setHistory(nextHistory)
    setDraft('')
    setBusy(true)
    try {
      const payload = await askAssistant(message, history.slice(-6))
      setHistory((current) => [
        ...current,
        { role: 'assistant', content: payload.answer || 'پاسخی دریافت نشد.', source: payload.source },
      ])
      requestAnimationFrame(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">گفت‌وگو با دستیار سازنده</h3>
          <p className="card-subtitle">
            {healthInfo?.avalai_configured
              ? 'پاسخ‌ها با AvalAI تولید می‌شوند و در نبود آن، موتور دانش داخلی پاسخ می‌دهد.'
              : 'کلید AvalAI تنظیم نشده؛ موتور دانش داخلی (قاعده‌محور) پاسخ می‌دهد.'}
          </p>
        </div>
        <span className="badge ai">AI</span>
      </div>

      {history.length === 0 && (
        <div className="row mb-14" style={{ gap: 6 }}>
          {SUGGESTIONS.map((item) => (
            <button key={item} type="button" className="section-chip" onClick={() => send(item)}>
              {item}
            </button>
          ))}
        </div>
      )}

      <div className="chat-log" ref={logRef}>
        {history.length === 0 ? (
          <div className="empty">پرسش خود را بنویسید یا یکی از پیشنهادها را انتخاب کنید.</div>
        ) : (
          history.map((item, index) => (
            <div key={index} className={`bubble ${item.role === 'user' ? 'user' : 'bot'}`}>
              {item.content}
              {item.source && item.role !== 'user' ? (
                <div className="tiny dim mt-6">منبع: {item.source}</div>
              ) : null}
            </div>
          ))
        )}
        {busy && (
          <div className="bubble bot">
            <span className="row">
              <span className="spinner" /> در حال فکر کردن…
            </span>
          </div>
        )}
      </div>

      <div className="row mt-14">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              send()
            }
          }}
          placeholder="پرسش خود را بنویسید… (Enter برای ارسال، Shift+Enter برای خط جدید)"
          style={{ flex: 1, minHeight: 54 }}
        />
        <button type="button" className="btn primary" onClick={() => send()} disabled={busy || !draft.trim()}>
          ارسال
        </button>
        {history.length > 0 && (
          <button
            type="button"
            className="btn ghost sm"
            onClick={() => setHistory([])}
            title="پاک کردن گفت‌وگو"
          >
            پاک کردن ({toPersianDigits(history.length)})
          </button>
        )}
      </div>
    </div>
  )
}
