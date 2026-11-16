import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import Toasts from './components/Toasts.jsx'
import TopBar from './components/TopBar.jsx'
import Configure from './pages/Configure.jsx'
import Engines from './pages/Engines.jsx'
import Home from './pages/Home.jsx'
import PackageDetail from './pages/PackageDetail.jsx'
import Packages from './pages/Packages.jsx'
import { AppProvider, useApp } from './lib/store.jsx'

function Shell() {
  const { error, loading, meta } = useApp()

  if (!meta && !error && loading.meta) {
    return (
      <div className="shell">
        <TopBar />
        <main className="page">
          <div className="skeleton" style={{ height: 130, marginBottom: 14 }} />
          <div className="grid cols-6">
            {Array.from({ length: 6 }).map((_, index) => (
              <div className="skeleton" key={index} style={{ height: 76 }} />
            ))}
          </div>
          <div className="skeleton mt-18" style={{ height: 320 }} />
        </main>
      </div>
    )
  }

  return (
    <div className="shell">
      <TopBar />
      {error && !meta ? (
        <main className="page">
          <div className="error-box">
            اتصال به سرویس سازنده برقرار نشد: {error}
            <div className="tiny dim mt-10">
              سرویس بک‌اند باید روی پورت ۸۰۰۰ در حال اجرا باشد (<span className="mono">uvicorn app.main:app</span>).
            </div>
          </div>
        </main>
      ) : (
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/configure" element={<Configure />} />
        <Route path="/engines" element={<Engines />} />
        <Route path="/packages" element={<Packages />} />
        <Route path="/packages/:packageId" element={<PackageDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      )}
      <Toasts />
      <footer className="page tiny dim" style={{ paddingTop: 8, paddingBottom: 26 }}>
        سازنده ERP هوشمند کارخانه‌ای · نسخه {meta?.version || '—'} · کاتالوگ {meta?.catalog_version || '—'} ·
        منبع کاتالوگ: <span className="mono">builder/backend/app/catalog/sections</span>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Shell />
      </AppProvider>
    </BrowserRouter>
  )
}
