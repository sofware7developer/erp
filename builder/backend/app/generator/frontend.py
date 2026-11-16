# -*- coding: utf-8 -*-
"""
تولید رابط کاربری React (ERP کارخانه)
======================================
SPA با React 18 + Vite، راست‌به‌چپ، تم تیره صنعتی، بدون وابستگی سنگین:

  * کتابخانه UI داخلی (DataTable، فرم، نمودار SVG، مودال، توست)
  * صفحه‌های داده‌محور: همه موجودیت‌ها از `config/schemas.js` ساخته می‌شوند
  * اتصال به API لاراول با توکن Sanctum
  * ویجت‌های هوش مصنوعی متصل به سرویس پایتون
"""

from __future__ import annotations

import json
from typing import Any

from .writers import Package, render

PACKAGE_JSON = """{
  "name": "@@slug@@-frontend",
  "private": true,
  "version": "@@version@@",
  "description": "@@app_name_fa@@ — رابط کاربری کارخانه",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "vite build",
    "build:only": "vite build --mode production",
    "preview": "vite preview --host 0.0.0.0 --port 4173"
  },
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "react-router-dom": "6.28.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "4.3.4",
    "vite": "6.0.5"
  }
}
"""

VITE_CONFIG = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// پیکربندی Vite برای استقرار پشت nginx یا docker
// مسیر /api به بک‌اند لاراول پروکسی می‌شود تا مشکل CORS در توسعه حل شود.
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/storage': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
})
"""

INDEX_HTML = """<!doctype html>
<html lang="fa" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#0b1020" />
@@pwa_head@@    <meta name="description" content="@@app_name_fa@@ — سامانه یکپارچه مدیریت کارخانه" />
    <title>@@app_name_fa@@</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <style>
      /* فونت پیش از بارگذاری React تا پرش چیدمان رخ ندهد */
      html, body, #root { height: 100%; margin: 0; background: #0b1020; }
      .boot-splash {
        height: 100%; display: flex; flex-direction: column; align-items: center;
        justify-content: center; gap: 14px; color: #c7d2fe;
        font-family: 'Vazirmatn', 'Segoe UI', Tahoma, sans-serif;
      }
      .boot-splash .spinner {
        width: 42px; height: 42px; border-radius: 50%;
        border: 3px solid rgba(129, 140, 248, 0.25); border-top-color: #818cf8;
        animation: boot-spin 0.9s linear infinite;
      }
      @keyframes boot-spin { to { transform: rotate(360deg); } }
    </style>
  </head>
  <body>
    <div id="root">
      <div class="boot-splash">
        <div class="spinner"></div>
        <div>در حال بارگذاری @@app_name_fa@@…</div>
      </div>
    </div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

ENV_FRONTEND = """# آدرس API لاراول (در حالت توسعه از پروکسی Vite استفاده می‌شود)
VITE_API_BASE_URL=/api
VITE_APP_NAME=@@app_name@@
VITE_APP_NAME_FA=@@app_name_fa@@
VITE_COMPANY_NAME=@@company_name@@
VITE_CURRENCY=@@currency@@
VITE_CALENDAR=@@calendar@@
VITE_AI_ENABLED=true
VITE_PROXY_TARGET=http://localhost:8000
"""

MAIN_JSX = r"""import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.jsx'
import { AppProvider } from './lib/store.jsx'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppProvider>
        <App />
      </AppProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
"""

APP_JSX = r"""import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import RequireAuth from './components/RequireAuth.jsx'
import AiHub from './pages/AiHub.jsx'
import AuditLog from './pages/AuditLog.jsx'
import Dashboard from './pages/Dashboard.jsx'
import EntityPage from './pages/EntityPage.jsx'
import Login from './pages/Login.jsx'
import ModulePage from './pages/ModulePage.jsx'
import ModulesIndex from './pages/ModulesIndex.jsx'
import NotFound from './pages/NotFound.jsx'
import Reports from './pages/Reports.jsx'
import Settings from './pages/Settings.jsx'
import { MODULES } from './config/menu.js'

/**
 * مسیریابی برنامه
 *
 * صفحه هر موجودیت از روی `config/schemas.js` ساخته می‌شود، بنابراین
 * افزودن ماژول جدید به سامانه نیاز به نوشتن صفحه جدید ندارد.
 */
export default function App() {
  const entityRoutes = []
  MODULES.forEach((module) => {
    module.entities.forEach((entity) => {
      entityRoutes.push(
        <Route
          key={`${module.slug}-${entity.table}`}
          path={`/modules/${module.slug}/${entity.table}`}
          element={<EntityPage moduleSlug={module.slug} table={entity.table} />}
        />,
      )
    })
  })

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/modules" element={<ModulesIndex />} />
          <Route path="/modules/:moduleSlug" element={<ModulePage />} />
          {entityRoutes}
          <Route path="/ai" element={<AiHub />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>

      <Route path="/index.html" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
"""

GLOBAL_CSS = r""":root {
  --bg: #0b1020;
  --bg-soft: #121a33;
  --panel: #151d38;
  --panel-2: #1b2444;
  --border: #26315a;
  --border-soft: #1e2848;
  --text: #e6ebff;
  --text-dim: #9aa8d4;
  --text-mute: #6f7fb3;
  --primary: #6366f1;
  --primary-soft: rgba(99, 102, 241, 0.16);
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #38bdf8;
  --ai: #a855f7;
  --radius: 14px;
  --radius-sm: 9px;
  --shadow: 0 18px 40px rgba(2, 6, 23, 0.45);
  --font: 'Vazirmatn', 'Segoe UI', Tahoma, 'Iranian Sans', sans-serif;
}

* { box-sizing: border-box; }

html, body, #root {
  height: 100%;
  margin: 0;
}

body {
  background:
    radial-gradient(1100px 600px at 88% -10%, rgba(99, 102, 241, 0.18), transparent 60%),
    radial-gradient(900px 520px at 0% 0%, rgba(56, 189, 248, 0.12), transparent 55%),
    var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.75;
  direction: rtl;
  -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }
button { font-family: inherit; }

/* --- اسکرول‌بار --- */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #35407a; }

/* --- چیدمان اصلی --- */
.app-shell { display: flex; min-height: 100vh; }
.app-sidebar {
  width: 268px; flex-shrink: 0; background: rgba(11, 16, 32, 0.86);
  backdrop-filter: blur(8px); border-inline-start: 1px solid var(--border-soft);
  display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh;
}
.app-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.app-topbar {
  position: sticky; top: 0; z-index: 30; display: flex; align-items: center; gap: 14px;
  padding: 12px 22px; background: rgba(11, 16, 32, 0.82); backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-soft);
}
.app-content { padding: 22px; display: flex; flex-direction: column; gap: 18px; }

/* --- برند کناری --- */
.brand { display: flex; align-items: center; gap: 10px; padding: 18px 18px 14px; }
.brand-badge {
  width: 38px; height: 38px; border-radius: 11px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--primary), #22d3ee); color: #050a1c;
  font-weight: 800; font-size: 15px; box-shadow: 0 8px 22px rgba(99, 102, 241, 0.35);
}
.brand-text strong { display: block; font-size: 13.5px; letter-spacing: 0.2px; }
.brand-text span { font-size: 11px; color: var(--text-mute); }

/* --- منو --- */
.nav-scroll { overflow-y: auto; padding: 4px 10px 18px; flex: 1; }
.nav-group-title {
  font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.6px;
  padding: 14px 10px 6px; text-transform: uppercase;
}
.nav-item {
  display: flex; align-items: center; gap: 9px; padding: 8px 10px; border-radius: 10px;
  color: var(--text-dim); font-size: 13px; cursor: pointer; transition: 0.16s;
  border: 1px solid transparent;
}
.nav-item:hover { background: var(--panel); color: var(--text); }
.nav-item.active {
  background: var(--primary-soft); border-color: rgba(99, 102, 241, 0.35); color: #dbe2ff;
}
.nav-item .dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--text-mute); flex-shrink: 0;
}
.nav-item.active .dot { background: var(--primary); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18); }
.nav-badge {
  margin-inline-start: auto; font-size: 10.5px; padding: 1px 7px; border-radius: 999px;
  background: rgba(148, 163, 184, 0.14); color: var(--text-mute);
}
.nav-badge.ai { background: rgba(168, 85, 247, 0.18); color: #d8b4fe; }

/* --- کارت و پنل --- */
.card {
  background: linear-gradient(180deg, var(--panel), rgba(21, 29, 56, 0.7));
  border: 1px solid var(--border-soft); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 18px;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  margin-bottom: 14px; flex-wrap: wrap;
}
.card-title { font-size: 15px; font-weight: 700; margin: 0; }
.card-subtitle { font-size: 12px; color: var(--text-mute); margin: 2px 0 0; }

.grid { display: grid; gap: 16px; }
.grid.cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid.cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid.cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
@media (max-width: 1280px) { .grid.cols-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) {
  .grid.cols-2, .grid.cols-3, .grid.cols-4 { grid-template-columns: 1fr; }
  .app-sidebar { position: fixed; inset-block: 0; inset-inline-start: 0; z-index: 60; transform: translateX(100%); }
  .app-sidebar.open { transform: translateX(0); }
}

/* --- دکمه --- */
.btn {
  display: inline-flex; align-items: center; gap: 7px; padding: 8px 15px;
  border-radius: 10px; border: 1px solid var(--border); background: var(--panel-2);
  color: var(--text); font-size: 13px; cursor: pointer; transition: 0.16s; white-space: nowrap;
}
.btn:hover { border-color: #3b4a86; transform: translateY(-1px); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.btn.primary {
  background: linear-gradient(135deg, var(--primary), #4f46e5);
  border-color: transparent; color: #fff; box-shadow: 0 10px 24px rgba(79, 70, 229, 0.32);
}
.btn.ghost { background: transparent; }
.btn.danger { background: rgba(239, 68, 68, 0.14); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5; }
.btn.sm { padding: 5px 11px; font-size: 12px; border-radius: 8px; }
.btn.icon { padding: 7px; }

/* --- فرم --- */
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12.5px; color: var(--text-dim); }
.field .hint { font-size: 11px; color: var(--text-mute); }
.input, .select, .textarea {
  width: 100%; padding: 9px 12px; border-radius: 10px; border: 1px solid var(--border);
  background: rgba(8, 12, 28, 0.72); color: var(--text); font-family: inherit; font-size: 13px;
  transition: 0.16s;
}
.input:focus, .select:focus, .textarea:focus {
  outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18);
}
.textarea { min-height: 92px; resize: vertical; }
.select option { background: #101832; }
.form-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
@media (max-width: 1100px) { .form-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 700px) { .form-grid { grid-template-columns: 1fr; } }
.field-error { font-size: 11.5px; color: #fca5a5; }

/* --- جدول --- */
.table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border-soft); }
table.data { width: 100%; border-collapse: collapse; font-size: 13px; }
table.data thead th {
  position: sticky; top: 0; background: var(--panel-2); color: var(--text-dim);
  text-align: right; padding: 11px 12px; font-weight: 600; font-size: 12px;
  border-bottom: 1px solid var(--border); white-space: nowrap; cursor: pointer; user-select: none;
}
table.data tbody td {
  padding: 10px 12px; border-bottom: 1px solid rgba(38, 49, 90, 0.45);
  white-space: nowrap; max-width: 320px; overflow: hidden; text-overflow: ellipsis;
}
table.data tbody tr:hover { background: rgba(99, 102, 241, 0.07); }
table.data tbody tr:last-child td { border-bottom: none; }

/* --- نشان وضعیت --- */
.badge {
  display: inline-flex; align-items: center; gap: 5px; padding: 2px 10px;
  border-radius: 999px; font-size: 11.5px; border: 1px solid var(--border);
  background: rgba(148, 163, 184, 0.1); color: var(--text-dim);
}
.badge.success { background: rgba(34, 197, 94, 0.14); border-color: rgba(34, 197, 94, 0.35); color: #86efac; }
.badge.warning { background: rgba(245, 158, 11, 0.14); border-color: rgba(245, 158, 11, 0.35); color: #fcd34d; }
.badge.danger { background: rgba(239, 68, 68, 0.14); border-color: rgba(239, 68, 68, 0.35); color: #fca5a5; }
.badge.info { background: rgba(56, 189, 248, 0.14); border-color: rgba(56, 189, 248, 0.35); color: #7dd3fc; }
.badge.ai { background: rgba(168, 85, 247, 0.16); border-color: rgba(168, 85, 247, 0.4); color: #d8b4fe; }

/* --- کارت شاخص --- */
.kpi { display: flex; flex-direction: column; gap: 6px; padding: 16px; }
.kpi .label { font-size: 12px; color: var(--text-mute); display: flex; align-items: center; gap: 7px; }
.kpi .value { font-size: 25px; font-weight: 800; letter-spacing: -0.5px; }
.kpi .foot { font-size: 11.5px; color: var(--text-dim); }
.kpi .icon-dot { width: 9px; height: 9px; border-radius: 3px; }

/* --- ابزارها --- */
.toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.toolbar .grow { flex: 1; min-width: 180px; }
.search {
  display: flex; align-items: center; gap: 8px; padding: 7px 12px; border-radius: 10px;
  border: 1px solid var(--border); background: rgba(8, 12, 28, 0.72);
}
.search input { background: transparent; border: none; outline: none; color: var(--text); width: 100%; font-family: inherit; }
.pagination { display: flex; align-items: center; gap: 8px; justify-content: center; padding: 12px; font-size: 12.5px; color: var(--text-dim); }
.loader { display: grid; place-items: center; padding: 46px; color: var(--text-mute); gap: 12px; }
.spinner {
  width: 26px; height: 26px; border-radius: 50%;
  border: 3px solid rgba(99, 102, 241, 0.22); border-top-color: var(--primary);
  animation: spin 0.85s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty { padding: 40px; text-align: center; color: var(--text-mute); }
.error-box {
  padding: 14px 16px; border-radius: var(--radius); border: 1px solid rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.1); color: #fecaca; font-size: 13px;
}

/* --- مودال و توست --- */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(3, 7, 18, 0.72); backdrop-filter: blur(4px);
  display: grid; place-items: center; z-index: 90; padding: 20px;
}
.modal {
  width: min(880px, 100%); max-height: 88vh; overflow-y: auto; background: var(--panel);
  border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow);
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 18px; border-bottom: 1px solid var(--border-soft); position: sticky; top: 0;
  background: var(--panel); z-index: 2;
}
.modal-body { padding: 18px; }
.modal-footer {
  display: flex; gap: 10px; justify-content: flex-start; padding: 14px 18px;
  border-top: 1px solid var(--border-soft); position: sticky; bottom: 0; background: var(--panel);
}
.toasts { position: fixed; bottom: 22px; inset-inline-start: 22px; z-index: 120; display: flex; flex-direction: column; gap: 10px; }
.toast {
  min-width: 260px; max-width: 420px; padding: 12px 15px; border-radius: 12px;
  border: 1px solid var(--border); background: var(--panel-2); box-shadow: var(--shadow); font-size: 13px;
}
.toast.success { border-color: rgba(34, 197, 94, 0.4); }
.toast.error { border-color: rgba(239, 68, 68, 0.4); }

/* --- صفحه ورود --- */
.auth-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
.auth-card { width: min(430px, 100%); }
.auth-logo { display: grid; place-items: center; gap: 8px; margin-bottom: 18px; text-align: center; }
.auth-logo .brand-badge { width: 52px; height: 52px; font-size: 19px; border-radius: 15px; }

/* --- نمودار --- */
.chart { width: 100%; overflow: visible; }
.chart .axis-label { fill: var(--text-mute); font-size: 10px; }
.chart .grid-line { stroke: rgba(38, 49, 90, 0.55); stroke-width: 1; }
.chart .series-line { fill: none; stroke-width: 2.2; stroke-linejoin: round; stroke-linecap: round; }
.chart .area-fill { opacity: 0.16; }
.chart-bar { transition: 0.2s; }
.chart-bar:hover { opacity: 0.82; }
.chart-legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-dim); }
.chart-legend span { display: inline-flex; align-items: center; gap: 6px; }
.chart-legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }

/* --- برگه‌ها --- */
.tabs { display: flex; gap: 6px; border-bottom: 1px solid var(--border-soft); overflow-x: auto; }
.tab {
  padding: 9px 15px; font-size: 13px; color: var(--text-dim); cursor: pointer;
  border-bottom: 2px solid transparent; white-space: nowrap; background: none; border-top: none;
  border-inline: none;
}
.tab.active { color: var(--text); border-bottom-color: var(--primary); }

/* --- کارت ماژول --- */
.module-card { display: flex; flex-direction: column; gap: 10px; transition: 0.18s; }
.module-card:hover { transform: translateY(-2px); border-color: #3b4a86; }
.module-card .module-icon {
  width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
  font-weight: 800; font-size: 14px; color: #060b1c;
}
.module-card h3 { margin: 0; font-size: 14.5px; }
.module-card p { margin: 0; font-size: 12px; color: var(--text-mute); min-height: 38px; }
.module-meta { display: flex; gap: 8px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-dim); }

/* --- ویجت AI --- */
.ai-widget {
  border: 1px solid rgba(168, 85, 247, 0.28); background: rgba(168, 85, 247, 0.07);
  border-radius: var(--radius); padding: 16px;
}
.ai-widget .ai-head { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #d8b4fe; margin-bottom: 10px; }
.ai-result { font-size: 13px; color: var(--text); white-space: pre-wrap; }
.ai-meta { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--text-mute); margin-top: 10px; }

/* --- متن و ابزار --- */
.muted { color: var(--text-mute); }
.dim { color: var(--text-dim); }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 12px; direction: ltr; display: inline-block; }
.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.between { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.stack { display: flex; flex-direction: column; gap: 10px; }
.mt-0 { margin-top: 0; }
.text-start { text-align: start; }
.pre-wrap { white-space: pre-wrap; }
"""

API_JS = r"""/**
 * لایه ارتباط با API لاراول
 *
 * توکن Sanctum در localStorage نگهداری می‌شود و در همه درخواست‌ها
 * به‌همراه شناسه شرکت فعال ارسال می‌گردد.
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const TOKEN_KEY = '@@slug@@.token'
const COMPANY_KEY = '@@slug@@.company'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getCompanyId() {
  return localStorage.getItem(COMPANY_KEY) || ''
}

export function setCompanyId(id) {
  if (id) localStorage.setItem(COMPANY_KEY, String(id))
  else localStorage.removeItem(COMPANY_KEY)
}

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.status = status
    this.payload = payload || {}
  }
}

async function request(path, options = {}) {
  const headers = {
    Accept: 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...options.headers,
  }

  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const companyId = getCompanyId()
  if (companyId) headers['X-Company-Id'] = companyId

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  let payload = null
  const text = await response.text()
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = { message: text.slice(0, 400) }
    }
  }

  if (!response.ok) {
    const message =
      payload?.message ||
      (response.status === 401 ? 'نشست شما پایان یافته است؛ دوباره وارد شوید.' : 'درخواست ناموفق بود.')
    throw new ApiError(message, response.status, payload)
  }

  return payload
}

export const api = {
  get: (path, params) => {
    const query = new URLSearchParams(
      Object.entries(params || {}).filter(([, value]) => value !== undefined && value !== null && value !== ''),
    ).toString()
    return request(query ? `${path}?${query}` : path)
  },
  post: (path, body) => request(path, { method: 'POST', body: body || {} }),
  put: (path, body) => request(path, { method: 'PUT', body: body || {} }),
  patch: (path, body) => request(path, { method: 'PATCH', body: body || {} }),
  delete: (path) => request(path, { method: 'DELETE' }),
}

// --- احراز هویت ---
export const auth = {
  login: (login, password, deviceName = 'web') =>
    api.post('/v1/auth/login', { login, password, device_name: deviceName }),
  logout: () => api.post('/v1/auth/logout'),
  me: () => api.get('/v1/auth/me'),
  changePassword: (body) => api.post('/v1/auth/password', body),
  updateProfile: (body) => api.put('/v1/auth/profile', body),
}

// --- سامانه ---
export const system = {
  health: () => api.get('/v1/health'),
  dashboard: () => api.get('/v1/dashboard'),
  modules: () => api.get('/v1/modules'),
  features: (params) => api.get('/v1/features', params),
  permissions: () => api.get('/v1/permissions'),
  audit: (params) => api.get('/v1/audit-events', params),
}

// --- هوش مصنوعی ---
export const ai = {
  engines: () => api.get('/v1/ai/engines'),
  capabilities: () => api.get('/v1/ai/capabilities'),
  run: (code, body) => api.post(`/v1/ai/capabilities/${code}`, body),
  chat: (body) => api.post('/v1/ai/chat', body),
  summarize: (body) => api.post('/v1/ai/summarize', body),
  insight: (body) => api.post('/v1/ai/insight', body),
  classify: (body) => api.post('/v1/ai/classify', body),
}

// --- گزارش ---
export const reports = {
  tables: () => api.get('/v1/reports/tables'),
  templates: () => api.get('/v1/reports/templates'),
  aggregate: (body) => api.post('/v1/reports/aggregate', body),
  export: (body) => api.post('/v1/reports/export', body),
}

/** ساخت کلاینت منابع یک موجودیت */
export function resource(moduleSlug, table) {
  const base = `/v1/${moduleSlug}/${table}`
  return {
    list: (params) => api.get(base, params),
    get: (id) => api.get(`${base}/${id}`),
    create: (body) => api.post(base, body),
    update: (id, body) => api.put(`${base}/${id}`, body),
    changeStatus: (id, body) => api.patch(`${base}/${id}/status`, body),
    remove: (id) => api.delete(`${base}/${id}`),
  }
}

export default api
"""

FORMAT_JS = r"""/**
 * قالب‌بندی فارسی: ارقام، تاریخ شمسی، مبلغ و وضعیت‌ها
 *
 * تاریخ‌ها از سرور به دو شکل میلادی و *_jalali می‌رسند؛ در اینجا
 * برای نمایش، نسخه شمسی ترجیح داده می‌شود.
 */

const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

export const CURRENCY_LABEL = import.meta.env.VITE_CURRENCY === 'IRR' ? 'ریال' : import.meta.env.VITE_CURRENCY || 'ریال'

/** تبدیل ارقام لاتین به فارسی */
export function toPersianDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)])
}

/** تبدیل ارقام فارسی/عربی به لاتین */
export function toLatinDigits(value) {
  return String(value ?? '')
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x06f0))
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660))
}

/** عدد با جداکننده هزارگان و ارقام فارسی */
export function formatNumber(value, decimals = 0) {
  const number = Number(toLatinDigits(value))
  if (!Number.isFinite(number)) return '—'
  return toPersianDigits(number.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }))
}

/** مبلغ با واحد پول */
export function formatMoney(value, withLabel = true) {
  const number = Number(toLatinDigits(value))
  if (!Number.isFinite(number)) return '—'
  const text = formatNumber(Math.round(number))
  return withLabel ? `${text} ${CURRENCY_LABEL}` : text
}

/** درصد */
export function formatPercent(value, decimals = 1) {
  const number = Number(toLatinDigits(value))
  if (!Number.isFinite(number)) return '—'
  return `${toPersianDigits(number.toFixed(decimals))}٪`
}

/** تبدیل تاریخ میلادی به شمسی (الگوریتم jalaali) */
export function toJalali(gy, gm, gd) {
  const gDaysInMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
  const gy2 = gm > 2 ? gy + 1 : gy
  let days =
    355666 + 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) +
    Math.floor((gy2 + 399) / 400) + gd + gDaysInMonth[gm - 1]

  let jy = -1595 + 33 * Math.floor(days / 12053)
  days %= 12053
  jy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    jy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }

  let jm
  let jd
  if (days < 186) {
    jm = 1 + Math.floor(days / 31)
    jd = 1 + (days % 31)
  } else {
    jm = 7 + Math.floor((days - 186) / 30)
    jd = 1 + ((days - 186) % 30)
  }
  return { jy, jm, jd }
}

const JALALI_MONTHS = [
  'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
  'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

const WEEK_DAYS = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه']

/** قالب تاریخ شمسی: ۱۴۰۵/۰۱/۰۱ */
export function formatDate(value, jalaliValue = null) {
  if (jalaliValue) return toPersianDigits(String(jalaliValue).slice(0, 10))
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const { jy, jm, jd } = toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
  return toPersianDigits(`${jy}/${String(jm).padStart(2, '0')}/${String(jd).padStart(2, '0')}`)
}

/** قالب تاریخ و ساعت شمسی */
export function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const { jy, jm, jd } = toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  return toPersianDigits(`${jy}/${String(jm).padStart(2, '0')}/${String(jd).padStart(2, '0')} ${time}`)
}

/** قالب بلند: شنبه ۱ فروردین ۱۴۰۵ */
export function formatDateLong(value) {
  const date = new Date(value || Date.now())
  const { jy, jm, jd } = toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
  return `${WEEK_DAYS[date.getDay()]} ${toPersianDigits(jd)} ${JALALI_MONTHS[jm - 1]} ${toPersianDigits(jy)}`
}

export function jalaliMonthName(month) {
  return JALALI_MONTHS[Number(month) - 1] || ''
}

/** امروز شمسی */
export function todayJalali() {
  const date = new Date()
  return toJalali(date.getFullYear(), date.getMonth() + 1, date.getDate())
}

/** نگاشت وضعیت‌ها به برچسب فارسی و رنگ */
const STATUS_MAP = {
  draft: ['پیش‌نویس', ''],
  pending: ['در انتظار', 'warning'],
  open: ['باز', 'info'],
  in_progress: ['در حال انجام', 'info'],
  active: ['فعال', 'success'],
  approved: ['تأییدشده', 'success'],
  completed: ['تکمیل‌شده', 'success'],
  done: ['انجام‌شده', 'success'],
  closed: ['بسته', ''],
  cancelled: ['لغوشده', 'danger'],
  rejected: ['ردشده', 'danger'],
  overdue: ['عقب‌افتاده', 'danger'],
  expired: ['منقضی', 'danger'],
  planned: ['برنامه‌ریزی‌شده', 'info'],
  released: ['آزادشده', 'success'],
  paused: ['متوقف', 'warning'],
  blocked: ['مسدود', 'danger'],
  inspection: ['در حال بازرسی', 'info'],
  quarantine: ['قرنطینه', 'warning'],
  maintenance: ['در حال تعمیر', 'warning'],
  critical: ['بحرانی', 'danger'],
  high: ['بالا', 'danger'],
  medium: ['متوسط', 'warning'],
  low: ['پایین', 'success'],
}

export function statusLabel(value) {
  const key = String(value ?? '').toLowerCase()
  return STATUS_MAP[key]?.[0] || toPersianDigits(value || '—')
}

export function statusTone(value) {
  const key = String(value ?? '').toLowerCase()
  return STATUS_MAP[key]?.[1] || ''
}

/** کوتاه‌سازی متن */
export function truncate(text, length = 60) {
  const value = String(text ?? '')
  return value.length > length ? `${value.slice(0, length)}…` : value
}

/** مقدار نمایشی یک فیلد بر اساس نوع آن */
export function displayValue(field, row) {
  const raw = row?.[field.name]
  if (raw === null || raw === undefined || raw === '') return '—'

  switch (field.type) {
    case 'boolean':
      return raw ? 'بله' : 'خیر'
    case 'decimal':
      return field.money ? formatMoney(raw) : formatNumber(raw, 2)
    case 'integer':
    case 'bigint':
      return formatNumber(raw)
    case 'date':
      return formatDate(raw, row?.[`${field.name}_jalali`])
    case 'datetime':
      return formatDateTime(raw)
    case 'enum':
      return field.options_fa?.[raw] || statusLabel(raw)
    case 'json':
      return truncate(JSON.stringify(raw), 50)
    default:
      return truncate(raw, 60)
  }
}

/** دانلود CSV در سمت مرورگر */
export function downloadCsv(filename, content) {
  const blob = new Blob([`\uFEFF${content}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
"""

STORE_JSX = r"""import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { ai, auth, getToken, setToken, system } from '../lib/api.js'

const AppContext = createContext(null)

/**
 * وضعیت سراسری برنامه: کاربر، مجوزها، قابلیت‌ها، سلامت AI و اعلان‌ها
 */
export function AppProvider({ children }) {
  const [user, setUser] = useState(null)
  const [systemInfo, setSystemInfo] = useState(null)
  const [capabilities, setCapabilities] = useState([])
  const [aiEngines, setAiEngines] = useState([])
  const [aiHealth, setAiHealth] = useState(null)
  const [toasts, setToasts] = useState([])
  const [bootstrapping, setBootstrapping] = useState(Boolean(getToken()))
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const notify = useCallback((message, tone = 'success') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((current) => [...current, { id, message, tone }])
    setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 4800)
  }, [])

  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const loadSession = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      setBootstrapping(false)
      return
    }
    try {
      const payload = await auth.me()
      setUser(payload.user)
      setSystemInfo(payload.system)
    } catch {
      setToken('')
      setUser(null)
    } finally {
      setBootstrapping(false)
    }
  }, [])

  const loadAi = useCallback(async () => {
    try {
      const [engines, caps] = await Promise.all([ai.engines(), ai.capabilities()])
      setAiEngines(engines?.engines || [])
      setAiHealth(engines?.service || null)
      const grouped = caps?.capabilities_by_engine || {}
      const flat = []
      Object.entries(grouped).forEach(([engine, list]) => {
        list.forEach((item) => flat.push({ ...item, engine }))
      })
      setCapabilities(flat)
    } catch {
      setAiEngines([])
      setCapabilities([])
    }
  }, [])

  useEffect(() => {
    loadSession()
  }, [loadSession])

  useEffect(() => {
    if (user) loadAi()
  }, [user, loadAi])

  const login = useCallback(async (credentials) => {
    const payload = await auth.login(credentials.login, credentials.password)
    setToken(payload.token)
    setUser(payload.user)
    const info = await auth.me().catch(() => null)
    if (info?.system) setSystemInfo(info.system)
    return payload
  }, [])

  const logout = useCallback(async () => {
    try {
      await auth.logout()
    } catch {
      /* خروج محلی حتی در صورت خطای شبکه */
    }
    setToken('')
    setUser(null)
    setSystemInfo(null)
  }, [])

  const hasPermission = useCallback(
    (code) => {
      if (!user) return false
      if (user.is_super_admin) return true
      const permissions = user.permissions || []
      if (permissions.includes('*')) return true
      if (permissions.includes(code)) return true
      const prefix = String(code).split('.')[0]
      return permissions.includes(`${prefix}.*`)
    },
    [user],
  )

  const value = useMemo(
    () => ({
      user,
      systemInfo,
      capabilities,
      aiEngines,
      aiHealth,
      toasts,
      bootstrapping,
      sidebarOpen,
      setSidebarOpen,
      notify,
      dismissToast,
      login,
      logout,
      hasPermission,
      refreshSession: loadSession,
      refreshAi: loadAi,
    }),
    [user, systemInfo, capabilities, aiEngines, aiHealth, toasts, bootstrapping, sidebarOpen,
      notify, dismissToast, login, logout, hasPermission, loadSession, loadAi],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp باید داخل AppProvider استفاده شود')
  return context
}

export function useSystemInfo() {
  const { systemInfo } = useApp()
  return (
    systemInfo || {
      app_name_fa: import.meta.env.VITE_APP_NAME_FA || 'سامانه کارخانه',
      company: import.meta.env.VITE_COMPANY_NAME || '',
      currency: import.meta.env.VITE_CURRENCY || 'IRR',
      calendar: 'jalali',
      stats: {},
    }
  )
}
"""

LAYOUT_JSX = r"""import { useEffect } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import { MODULES, MENU_GROUPS } from '../config/menu.js'
import { useApp, useSystemInfo } from '../lib/store.jsx'
import { formatDateLong } from '../lib/format.js'
import Toasts from './Toasts.jsx'

/** چیدمان اصلی: نوار کناری + سربرگ + محتوا */
export default function Layout() {
  const { user, logout, sidebarOpen, setSidebarOpen } = useApp()
  const info = useSystemInfo()
  const location = useLocation()
  const groups = MENU_GROUPS

  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname, setSidebarOpen])

  const initials = String(info.app_name_fa || 'ERP')
    .split(' ')
    .slice(0, 2)
    .map((word) => word[0])
    .join('')

  return (
    <div className="app-shell">
      <aside className={`app-sidebar${sidebarOpen ? ' open' : ''}`}>
        <div className="brand">
          <div className="brand-badge">{initials}</div>
          <div className="brand-text">
            <strong>{info.app_name_fa}</strong>
            <span>{info.company || 'کارخانه'}</span>
          </div>
        </div>

        <nav className="nav-scroll">
          <div className="nav-group-title">کلی</div>
          <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> داشبورد فرماندهی
          </NavLink>
          <NavLink to="/modules" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> ماژول‌ها
            <span className="nav-badge">{MODULES.length}</span>
          </NavLink>
          <NavLink to="/ai" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> مرکز هوش مصنوعی
            <span className="nav-badge ai">AI</span>
          </NavLink>
          <NavLink to="/reports" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> گزارش‌ساز
          </NavLink>
          <NavLink to="/audit" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> ممیزی
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <span className="dot" /> تنظیمات
          </NavLink>

          {groups.map((group) => (
            <div key={group}>
              <div className="nav-group-title">{group}</div>
              {MODULES.filter((module) => module.menu_group === group).map((module) => (
                <NavLink
                  key={module.code}
                  to={`/modules/${module.slug}`}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <span className="dot" style={{ background: module.color }} />
                  {module.label_fa}
                  {module.ai_points > 0 && <span className="nav-badge ai">{module.ai_points}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <button className="btn ghost icon" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="منو">
            ☰
          </button>
          <div className="stack" style={{ gap: 0 }}>
            <strong style={{ fontSize: 13.5 }}>{formatDateLong()}</strong>
            <span className="muted" style={{ fontSize: 11.5 }}>
              {info.app_name_fa} — نسخه {info.version || ''}
            </span>
          </div>

          <div className="toolbar" style={{ marginInlineStart: 'auto' }}>
            <span className="badge info">{info.calendar === 'jalali' ? 'تقویم شمسی' : 'تقویم میلادی'}</span>
            <span className="badge">{user?.full_name || 'کاربر'}</span>
            {user?.is_super_admin && <span className="badge success">مدیر کل</span>}
            <button className="btn sm ghost" onClick={logout}>خروج</button>
          </div>
        </header>

        <main className="app-content">
          <Outlet />
        </main>
      </div>

      <Toasts />
    </div>
  )
}
"""

REQUIRE_AUTH_JSX = r"""import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { getToken } from '../lib/api.js'
import { useApp } from '../lib/store.jsx'

/** محافظ مسیر: بدون توکن معتبر به صفحه ورود می‌رود */
export default function RequireAuth() {
  const { user, bootstrapping } = useApp()
  const location = useLocation()

  if (bootstrapping) {
    return (
      <div className="loader" style={{ minHeight: '100vh' }}>
        <div className="spinner" />
        <span>در حال بررسی نشست کاربر…</span>
      </div>
    )
  }

  if (!getToken() || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
"""

TOASTS_JSX = r"""import { useApp } from '../lib/store.jsx'

/** اعلان‌های گذرا (موفقیت/خطا) */
export default function Toasts() {
  const { toasts, dismissToast } = useApp()
  if (!toasts.length) return null

  return (
    <div className="toasts">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${toast.tone}`} onClick={() => dismissToast(toast.id)}>
          {toast.message}
        </div>
      ))}
    </div>
  )
}
"""

CHARTS_JSX = r"""import { toPersianDigits } from '../lib/format.js'

/**
 * نمودارهای SVG سبک (بدون کتابخانه خارجی)
 * همه نمودارها راست‌به‌چپ رسم می‌شوند.
 */

function useScale(values, height, padding) {
  const max = Math.max(...values, 0)
  const min = Math.min(...values, 0)
  const span = max - min || 1
  return (value) => height - padding - ((value - min) / span) * (height - padding * 2)
}

export function LineChart({ labels = [], series = [], height = 220, color = '#6366f1' }) {
  if (!series.length) return <div className="empty">داده‌ای برای رسم نیست</div>

  const width = 640
  const padding = 26
  const values = series.flatMap((row) => (Array.isArray(row.values) ? row.values : [row.values]))
  const y = useScale(values.map(Number), height, padding)
  const count = Math.max(labels.length, values.length, 2)
  const step = (width - padding * 2) / (count - 1)

  const points = values
    .map((value, index) => [padding + index * step, y(Number(value))])
    .map(([px, py]) => `${px},${py}`)
    .join(' ')

  const areaPath = `M ${padding},${height - padding} L ${points
    .split(' ')
    .join(' L ')} L ${padding + (values.length - 1) * step},${height - padding} Z`

  return (
    <div>
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ height }}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <line
            key={ratio}
            className="grid-line"
            x1={padding}
            x2={width - padding}
            y1={padding + ratio * (height - padding * 2)}
            y2={padding + ratio * (height - padding * 2)}
          />
        ))}
        <path d={areaPath} className="area-fill" fill={color} />
        <polyline className="series-line" points={points} stroke={color} />
        {values.slice(0, 60).map((value, index) => (
          <circle key={index} cx={padding + index * step} cy={y(Number(value))} r="2.6" fill={color} />
        ))}
      </svg>
      <div className="chart-legend" style={{ marginTop: 8 }}>
        <span>
          <i style={{ background: color }} /> {series[0]?.name || 'مقدار'}
        </span>
        <span className="muted">
          نخستین: {toPersianDigits(Number(values[0] ?? 0).toFixed(1))} — آخرین:{' '}
          {toPersianDigits(Number(values[values.length - 1] ?? 0).toFixed(1))}
        </span>
      </div>
    </div>
  )
}

export function BarChart({ labels = [], values = [], height = 220, color = '#38bdf8', horizontal = false }) {
  if (!values.length) return <div className="empty">داده‌ای برای رسم نیست</div>

  const width = 640
  const padding = 26
  const max = Math.max(...values.map(Number), 1)
  const slot = (width - padding * 2) / values.length
  const barWidth = Math.min(slot * 0.62, 46)

  if (horizontal) {
    const rowHeight = 26
    const totalHeight = values.length * rowHeight + padding
    return (
      <svg className="chart" viewBox={`0 0 ${width} ${totalHeight}`} style={{ height: totalHeight }}>
        {values.map((value, index) => {
          const length = ((Number(value) / max) * (width - 220)).toFixed(1)
          return (
            <g key={index}>
              <text x={width - 8} y={padding + index * rowHeight + 4} textAnchor="end" className="axis-label">
                {labels[index] ?? index + 1}
              </text>
              <rect
                className="chart-bar"
                x={0}
                y={padding + index * rowHeight - 8}
                width={length}
                height="14"
                rx="4"
                fill={color}
              />
              <text x={Number(length) + 6} y={padding + index * rowHeight + 4} className="axis-label">
                {toPersianDigits(Number(value).toFixed(1))}
              </text>
            </g>
          )
        })}
      </svg>
    )
  }

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} style={{ height }}>
      {[0, 0.5, 1].map((ratio) => (
        <line
          key={ratio}
          className="grid-line"
          x1={padding}
          x2={width - padding}
          y1={padding + ratio * (height - padding * 2)}
          y2={padding + ratio * (height - padding * 2)}
        />
      ))}
      {values.map((value, index) => {
        const barHeight = (Number(value) / max) * (height - padding * 2)
        return (
          <g key={index}>
            <rect
              className="chart-bar"
              x={padding + index * slot + (slot - barWidth) / 2}
              y={height - padding - barHeight}
              width={barWidth}
              height={Math.max(barHeight, 1)}
              rx="5"
              fill={color}
            />
            {values.length <= 24 && (
              <text
                x={padding + index * slot + slot / 2}
                y={height - 8}
                textAnchor="middle"
                className="axis-label"
              >
                {String(labels[index] ?? '').slice(0, 8)}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export function DonutChart({ data = [], size = 190 }) {
  const total = data.reduce((sum, row) => sum + Number(row.value || 0), 0)
  if (!total) return <div className="empty">داده‌ای برای رسم نیست</div>

  const radius = size / 2 - 12
  const circumference = 2 * Math.PI * radius
  let offset = 0

  return (
    <div className="row" style={{ alignItems: 'center', gap: 18 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          {data.map((row, index) => {
            const portion = Number(row.value) / total
            const dash = portion * circumference
            const circle = (
              <circle
                key={index}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={row.color || '#6366f1'}
                strokeWidth="16"
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-offset}
              />
            )
            offset += dash
            return circle
          })}
        </g>
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fill="#e6ebff" fontSize="20" fontWeight="700">
          {toPersianDigits(total)}
        </text>
      </svg>
      <div className="chart-legend" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 7 }}>
        {data.map((row, index) => (
          <span key={index}>
            <i style={{ background: row.color || '#6366f1' }} /> {row.label}: {toPersianDigits(row.value)}
            <span className="muted"> ({Math.round((row.value / total) * 100)}٪)</span>
          </span>
        ))}
      </div>
    </div>
  )
}

export function Sparkline({ values = [], color = '#22c55e', width = 120, height = 34 }) {
  if (values.length < 2) return null
  const max = Math.max(...values.map(Number))
  const min = Math.min(...values.map(Number))
  const span = max - min || 1
  const step = width / (values.length - 1)
  const points = values
    .map((value, index) => `${index * step},${height - ((Number(value) - min) / span) * (height - 4) - 2}`)
    .join(' ')

  return (
    <svg width={width} height={height} className="chart">
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}

export function ControlChart({ means = [], ucl, lcl, center, height = 220, violations = [] }) {
  if (!means.length) return <div className="empty">داده‌ای برای نمودار کنترلی نیست</div>

  const width = 640
  const padding = 30
  const values = [...means, ucl, lcl, center].filter((v) => typeof v === 'number')
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1
  const y = (value) => height - padding - ((value - min) / span) * (height - padding * 2)
  const step = (width - padding * 2) / Math.max(means.length - 1, 1)
  const violated = new Set(violations.map((v) => Number(v.subgroup) - 1))

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} style={{ height }}>
      {[
        { value: ucl, label: 'UCL', color: '#ef4444' },
        { value: center, label: 'CL', color: '#22c55e' },
        { value: lcl, label: 'LCL', color: '#ef4444' },
      ].map((line) =>
        typeof line.value === 'number' ? (
          <g key={line.label}>
            <line
              x1={padding}
              x2={width - padding}
              y1={y(line.value)}
              y2={y(line.value)}
              stroke={line.color}
              strokeDasharray="5 4"
              strokeWidth="1.4"
              opacity="0.75"
            />
            <text x={width - padding} y={y(line.value) - 5} textAnchor="end" className="axis-label" fill={line.color}>
              {line.label}
            </text>
          </g>
        ) : null,
      )}
      <polyline
        className="series-line"
        stroke="#38bdf8"
        points={means.map((value, index) => `${padding + index * step},${y(value)}`).join(' ')}
      />
      {means.map((value, index) => (
        <circle
          key={index}
          cx={padding + index * step}
          cy={y(value)}
          r={violated.has(index) ? 5 : 3.2}
          fill={violated.has(index) ? '#ef4444' : '#38bdf8'}
        />
      ))}
    </svg>
  )
}
"""

DATA_TABLE_JSX = r"""import { useMemo, useState } from 'react'

import { displayValue, toPersianDigits } from '../lib/format.js'

/**
 * جدول داده با مرتب‌سازی، انتخاب و صفحه‌بندی سمت سرور
 */
export default function DataTable({
  fields = [],
  rows = [],
  loading = false,
  meta = null,
  onPage = () => {},
  onRowClick = null,
  actions = null,
  emptyMessage = 'رکوردی یافت نشد',
}) {
  const [sort, setSort] = useState({ by: null, dir: 'desc' })

  const sortedRows = useMemo(() => {
    if (!sort.by) return rows
    const factor = sort.dir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const left = a[sort.by]
      const right = b[sort.by]
      if (left === right) return 0
      if (left === null || left === undefined) return 1
      if (right === null || right === undefined) return -1
      if (typeof left === 'number' && typeof right === 'number') return (left - right) * factor
      return String(left).localeCompare(String(right), 'fa') * factor
    })
  }, [rows, sort])

  const visibleFields = fields.filter((field) => !field.hidden).slice(0, 9)

  if (loading) {
    return (
      <div className="loader">
        <div className="spinner" />
        <span>در حال بارگذاری داده…</span>
      </div>
    )
  }

  if (!sortedRows.length) return <div className="empty">{emptyMessage}</div>

  const toggleSort = (name) =>
    setSort((current) => ({
      by: name,
      dir: current.by === name && current.dir === 'desc' ? 'asc' : 'desc',
    }))

  return (
    <div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              {visibleFields.map((field) => (
                <th key={field.name} onClick={() => toggleSort(field.name)}>
                  {field.label}
                  {sort.by === field.name ? (sort.dir === 'asc' ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
              {actions && <th style={{ cursor: 'default' }}>عملیات</th>}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, index) => (
              <tr
                key={row.id ?? index}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                style={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {visibleFields.map((field) => (
                  <td key={field.name} title={String(row[field.name] ?? '')}>
                    {displayValue(field, row)}
                  </td>
                ))}
                {actions && <td onClick={(event) => event.stopPropagation()}>{actions(row)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {meta && (
        <div className="pagination">
          <button
            className="btn sm ghost"
            disabled={meta.current_page <= 1}
            onClick={() => onPage(meta.current_page - 1)}
          >
            قبلی
          </button>
          <span>
            صفحه {toPersianDigits(meta.current_page)} از {toPersianDigits(meta.last_page)} —{' '}
            {toPersianDigits(meta.total)} رکورد
          </span>
          <button
            className="btn sm ghost"
            disabled={meta.current_page >= meta.last_page}
            onClick={() => onPage(meta.current_page + 1)}
          >
            بعدی
          </button>
        </div>
      )}
    </div>
  )
}
"""

FORM_JSX = r"""import { useEffect, useState } from 'react'

import { toLatinDigits, toPersianDigits } from '../lib/format.js'

/**
 * فرم داده‌محور — فیلدها از `config/schemas.js` خوانده می‌شوند
 */

function FieldShell({ field, error, children }) {
  return (
    <div className="field">
      <label htmlFor={`field-${field.name}`}>
        {field.label}
        {field.required && !field.nullable && <span style={{ color: '#f87171' }}> *</span>}
      </label>
      {children}
      {field.help && <span className="hint">{field.help}</span>}
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}

export function Field({ field, value, error, onChange, options = {} }) {
  const id = `field-${field.name}`
  const common = {
    id,
    value: value ?? '',
    onChange: (event) => onChange(field.name, event.target.value),
    disabled: options.disabled,
  }

  switch (field.type) {
    case 'boolean':
      return (
        <FieldShell field={field} error={error}>
          <label className="row" style={{ gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={Boolean(value)}
              onChange={(event) => onChange(field.name, event.target.checked)}
              disabled={options.disabled}
            />
            <span className="dim">{value ? 'بله' : 'خیر'}</span>
          </label>
        </FieldShell>
      )

    case 'text':
    case 'json':
      return (
        <FieldShell field={field} error={error}>
          <textarea
            {...common}
            className="textarea"
            value={field.type === 'json' ? JSON.stringify(value ?? {}, null, 2) : value ?? ''}
            onChange={(event) => {
              const text = event.target.value
              if (field.type === 'json') {
                try {
                  onChange(field.name, JSON.parse(text))
                } catch {
                  onChange(field.name, text)
                }
                return
              }
              onChange(field.name, text)
            }}
          />
        </FieldShell>
      )

    case 'enum':
      return (
        <FieldShell field={field} error={error}>
          <select {...common} className="select">
            <option value="">— انتخاب کنید —</option>
            {(field.options || []).map((option) => (
              <option key={option} value={option}>
                {field.options_fa?.[option] || option}
              </option>
            ))}
          </select>
        </FieldShell>
      )

    case 'foreign':
      return (
        <FieldShell field={field} error={error}>
          <input
            {...common}
            className="input"
            type="number"
            min="1"
            placeholder={`شناسه ${field.references_table || 'رکورد مرتبط'}`}
            onChange={(event) => onChange(field.name, event.target.value === '' ? null : Number(event.target.value))}
          />
        </FieldShell>
      )

    case 'integer':
    case 'bigint':
    case 'decimal':
      return (
        <FieldShell field={field} error={error}>
          <input
            {...common}
            className="input"
            inputMode="decimal"
            placeholder={field.money ? 'مبلغ به ریال' : 'مقدار عددی'}
            onChange={(event) => {
              const cleaned = toLatinDigits(event.target.value).replace(/[,\s]/g, '')
              if (cleaned === '') return onChange(field.name, null)
              const number = Number(cleaned)
              onChange(field.name, Number.isFinite(number) ? number : cleaned)
            }}
          />
        </FieldShell>
      )

    case 'date':
      return (
        <FieldShell field={field} error={error}>
          <input {...common} className="input" type="date" />
        </FieldShell>
      )

    case 'datetime':
      return (
        <FieldShell field={field} error={error}>
          <input {...common} className="input" type="datetime-local" />
        </FieldShell>
      )

    case 'time':
      return (
        <FieldShell field={field} error={error}>
          <input {...common} className="input" type="time" />
        </FieldShell>
      )

    default:
      return (
        <FieldShell field={field} error={error}>
          <input {...common} className="input" type="text" />
        </FieldShell>
      )
  }
}

export default function EntityForm({ fields = [], initial = {}, errors = {}, onSubmit, onCancel, submitLabel = 'ذخیره' }) {
  const [values, setValues] = useState(initial)

  useEffect(() => {
    setValues(initial)
  }, [initial])

  const editableFields = fields.filter((field) => !['id', 'created_at', 'updated_at', 'deleted_at'].includes(field.name))

  const update = (name, value) => setValues((current) => ({ ...current, [name]: value }))

  const submit = (event) => {
    event.preventDefault()
    const payload = {}
    editableFields.forEach((field) => {
      const value = values[field.name]
      if (value === undefined) return
      if (value === '' && (field.nullable || !field.required)) {
        payload[field.name] = null
        return
      }
      if (['integer', 'bigint', 'decimal'].includes(field.type) && value !== null) {
        const number = Number(toLatinDigits(value))
        payload[field.name] = Number.isFinite(number) ? number : value
        return
      }
      payload[field.name] = value
    })
    onSubmit(payload)
  }

  return (
    <form onSubmit={submit}>
      <div className="form-grid">
        {editableFields.map((field) => (
          <Field
            key={field.name}
            field={field}
            value={values[field.name]}
            error={errors[field.name]?.[0] || errors[field.name]}
            onChange={update}
          />
        ))}
      </div>

      <div className="modal-footer" style={{ padding: '16px 0 0', borderTop: 'none' }}>
        <button type="submit" className="btn primary">
          {submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="btn ghost" onClick={onCancel}>
            انصراف
          </button>
        )}
        <span className="muted" style={{ fontSize: 11.5, marginInlineStart: 'auto' }}>
          {toPersianDigits(editableFields.length)} فیلد قابل ویرایش
        </span>
      </div>
    </form>
  )
}
"""

MODAL_JSX = r"""import { useEffect } from 'react'

/** مودال ساده با بستن توسط Escape */
export default function Modal({ open, title, subtitle, onClose, children, footer = null, wide = false }) {
  useEffect(() => {
    if (!open) return undefined
    const handler = (event) => {
      if (event.key === 'Escape') onClose?.()
    }
    window.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', handler)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        style={{ width: wide ? 'min(1100px, 100%)' : undefined }}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h3 className="card-title">{title}</h3>
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          <button className="btn ghost icon" onClick={onClose} aria-label="بستن">
            ✕
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}
"""

AI_WIDGET_JSX = r"""import { useState } from 'react'

import { ai } from '../lib/api.js'
import { useApp } from '../lib/store.jsx'
import { formatNumber, toPersianDigits } from '../lib/format.js'

/**
 * ویجت هوش مصنوعی — یک قابلیت کاتالوگ را اجرا و نتیجه را با توضیح فارسی نشان می‌دهد
 */
export default function AiWidget({ capability, title, defaultPayload = {}, compact = false }) {
  const { notify } = useApp()
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)

  const run = async () => {
    setLoading(true)
    setResponse(null)
    try {
      const result = await ai.run(capability, { payload: defaultPayload })
      setResponse(result)
      if (result.fallback) notify('سرویس AI در حالت جایگزین پاسخ داد', 'error')
    } catch (error) {
      notify(error.message || 'فراخوانی هوش مصنوعی ناموفق بود', 'error')
      setResponse({ ok: false, explanation: error.message })
    } finally {
      setLoading(false)
    }
  }

  const metrics = response?.metrics || {}

  return (
    <div className="ai-widget">
      <div className="ai-head">
        <span className="badge ai">🤖 AI</span>
        <strong>{title}</strong>
        <span className="mono" style={{ marginInlineStart: 'auto', fontSize: 11 }}>{capability}</span>
      </div>

      {!compact && (
        <p className="muted" style={{ fontSize: 12, margin: '0 0 10px' }}>
          این قابلیت از سرویس هوش مصنوعی کارخانه اجرا می‌شود و نتیجه با توضیح فارسی ارائه می‌گردد.
        </p>
      )}

      <div className="row">
        <button className="btn primary sm" onClick={run} disabled={loading}>
          {loading ? 'در حال پردازش…' : 'اجرای تحلیل'}
        </button>
        {response?.fallback && <span className="badge warning">حالت جایگزین</span>}
        {metrics?.latency_ms !== undefined && (
          <span className="muted" style={{ fontSize: 11.5 }}>
            {toPersianDigits(Math.round(metrics.latency_ms))} میلی‌ثانیه
          </span>
        )}
      </div>

      {loading && (
        <div className="loader" style={{ padding: 18 }}>
          <div className="spinner" />
        </div>
      )}

      {response && !loading && (
        <div style={{ marginTop: 12 }}>
          {response.explanation && <div className="ai-result">{response.explanation}</div>}

          {response.result && Object.keys(response.result).length > 0 && (
            <details style={{ marginTop: 10 }}>
              <summary className="dim" style={{ cursor: 'pointer', fontSize: 12 }}>
                مشاهده خروجی کامل
              </summary>
              <pre
                className="mono pre-wrap"
                style={{
                  background: 'rgba(8,12,28,0.7)', padding: 12, borderRadius: 10,
                  maxHeight: 280, overflow: 'auto', fontSize: 11, marginTop: 8,
                }}
              >
                {JSON.stringify(response.result, null, 2)}
              </pre>
            </details>
          )}

          {Object.keys(metrics).length > 0 && (
            <div className="ai-meta">
              {Object.entries(metrics)
                .slice(0, 6)
                .map(([key, value]) => (
                  <span key={key}>
                    {key}: {typeof value === 'number' ? formatNumber(value, 2) : String(value)}
                  </span>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
"""

LOGIN_JSX = r"""import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useApp, useSystemInfo } from '../lib/store.jsx'

/** صفحه ورود — احراز هویت با Sanctum */
export default function Login() {
  const { login, user, notify } = useApp()
  const info = useSystemInfo()
  const location = useLocation()
  const [form, setForm] = useState({ login: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to={location.state?.from || '/'} replace />

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form)
      notify('ورود موفق — خوش آمدید')
    } catch (apiError) {
      const fieldErrors = apiError.payload?.errors
      setError(fieldErrors ? Object.values(fieldErrors).flat().join(' ') : apiError.message)
    } finally {
      setLoading(false)
    }
  }

  const initials = String(info.app_name_fa || 'ERP')
    .split(' ')
    .slice(0, 2)
    .map((word) => word[0])
    .join('')

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <div className="auth-logo">
          <div className="brand-badge">{initials}</div>
          <h2 className="card-title">{info.app_name_fa}</h2>
          <p className="card-subtitle mt-0">{info.company || 'سامانه یکپارچه مدیریت کارخانه'}</p>
        </div>

        <form onSubmit={submit} className="stack" style={{ gap: 14 }}>
          <div className="field">
            <label htmlFor="login">نام کاربری، ایمیل یا شماره همراه</label>
            <input
              id="login"
              className="input"
              value={form.login}
              autoComplete="username"
              onChange={(event) => setForm({ ...form, login: event.target.value })}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">گذرواژه</label>
            <input
              id="password"
              type="password"
              className="input"
              value={form.password}
              autoComplete="current-password"
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
            />
          </div>

          {error && <div className="error-box">{error}</div>}

          <button className="btn primary" type="submit" disabled={loading} style={{ justifyContent: 'center' }}>
            {loading ? 'در حال ورود…' : 'ورود به سامانه'}
          </button>
        </form>

        <p className="muted" style={{ fontSize: 11.5, textAlign: 'center', marginTop: 16 }}>
          تقویم شمسی — {info.currency === 'IRR' ? 'واحد پول: ریال' : `واحد پول: ${info.currency}`}
        </p>
      </div>
    </div>
  )
}
"""

DASHBOARD_JSX = r"""import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { system } from '../lib/api.js'
import { formatNumber, formatPercent, statusTone, statusLabel } from '../lib/format.js'
import { useApp, useSystemInfo } from '../lib/store.jsx'
import { BarChart, DonutChart } from '../components/Charts.jsx'

/** داشبورد فرماندهی کارخانه */
export default function Dashboard() {
  const { capabilities, aiHealth } = useApp()
  const info = useSystemInfo()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    system
      .dashboard()
      .then(setData)
      .catch((apiError) => setError(apiError.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="loader">
        <div className="spinner" />
        <span>در حال آماده‌سازی داشبورد…</span>
      </div>
    )
  }

  if (error) return <div className="error-box">{error}</div>

  const cards = data?.cards || []
  const alerts = data?.alerts || []
  const stats = data?.stats || info.stats || {}

  const aiByEngine = capabilities.reduce((acc, item) => {
    acc[item.engine] = (acc[item.engine] || 0) + 1
    return acc
  }, {})
  const enginePalette = ['#6366f1', '#22c55e', '#f59e0b', '#38bdf8', '#a855f7', '#ef4444', '#14b8a6', '#ec4899']

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>داشبورد فرماندهی</h2>
          <p className="card-subtitle">
            {data?.date_jalali_long} — {data?.company}
          </p>
        </div>
        <div className="row">
          <span className={`badge ${aiHealth?.ok ? 'success' : 'warning'}`}>
            سرویس AI: {aiHealth?.ok ? 'در دسترس' : 'خارج از دسترس'}
          </span>
          <span className="badge info">{formatNumber(stats.modules || 0)} ماژول فعال</span>
          <span className="badge ai">{formatNumber(stats.ai_points || 0)} نقطه هوش مصنوعی</span>
        </div>
      </div>

      <div className="grid cols-4">
        {cards.map((card) => (
          <div className="card kpi" key={card.key}>
            <span className="label">
              <span className="icon-dot" style={{ background: card.color }} />
              {card.title}
            </span>
            <span className="value">{formatNumber(card.value)}</span>
            <span className="foot">
              {card.unit || 'رکورد ثبت‌شده'}
              {card.route && (
                <>
                  {' · '}
                  <Link to={card.route} style={{ color: '#a5b4fc' }}>مشاهده</Link>
                </>
              )}
            </span>
          </div>
        ))}
      </div>

      <div className="grid cols-2">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">توزیع نقاط هوش مصنوعی بر اساس موتور</h3>
              <p className="card-subtitle">قابلیت‌های فعال در این استقرار</p>
            </div>
            <Link to="/ai" className="btn sm ghost">مرکز AI</Link>
          </div>
          {Object.keys(aiByEngine).length ? (
            <DonutChart
              data={Object.entries(aiByEngine).map(([engine, value], index) => ({
                label: engine,
                value,
                color: enginePalette[index % enginePalette.length],
              }))}
            />
          ) : (
            <div className="empty">نقطه هوش مصنوعی فعالی انتخاب نشده است.</div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">هشدارهای فعال</h3>
              <p className="card-subtitle">نیازمند رسیدگی</p>
            </div>
            <span className="badge warning">{formatNumber(alerts.length)}</span>
          </div>

          {alerts.length === 0 ? (
            <div className="empty">هشدار بازی وجود ندارد — وضعیت پایدار است.</div>
          ) : (
            <div className="stack">
              {alerts.map((alert) => (
                <div className="between" key={alert.id} style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 8 }}>
                  <div>
                    <div style={{ fontSize: 13 }}>{alert.title}</div>
                    <span className="muted" style={{ fontSize: 11.5 }}>{alert.created_at_jalali}</span>
                  </div>
                  <span className={`badge ${statusTone(alert.severity) || 'warning'}`}>
                    {statusLabel(alert.severity)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">شاخص‌های کلیدی</h3>
            <p className="card-subtitle">مقایسه مقدار کارت‌های عملیاتی</p>
          </div>
        </div>
        <BarChart
          labels={cards.map((card) => card.title)}
          values={cards.map((card) => Number(card.value || 0))}
          color="#6366f1"
        />
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">پوشش استقرار</h3>
            <p className="card-subtitle">آمار تولیدشده توسط سازنده ERP</p>
          </div>
        </div>
        <div className="grid cols-4">
          {[
            ['ماژول‌ها', stats.modules],
            ['زیرماژول‌ها', stats.groups],
            ['زیرمجموعه‌ها', stats.items],
            ['جداول داده', stats.tables],
          ].map(([label, value]) => (
            <div className="stack" key={label} style={{ gap: 2 }}>
              <span className="muted" style={{ fontSize: 12 }}>{label}</span>
              <strong style={{ fontSize: 21 }}>{formatNumber(value || 0)}</strong>
            </div>
          ))}
        </div>
        <p className="muted" style={{ fontSize: 11.5, marginTop: 14 }}>
          نرخ پوشش قابلیت‌های هوش مصنوعی نسبت به کل ماژول‌ها:{' '}
          {stats.modules ? formatPercent(((stats.ai_points || 0) / stats.modules) * 100, 0) : '—'}
        </p>
      </div>
    </>
  )
}
"""

MODULES_INDEX_JSX = r"""import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { MODULES, MENU_GROUPS } from '../config/menu.js'
import { formatNumber, toPersianDigits } from '../lib/format.js'

/** فهرست ماژول‌های فعال با جست‌وجو و فیلتر گروه */
export default function ModulesIndex() {
  const [query, setQuery] = useState('')
  const [group, setGroup] = useState('all')

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return MODULES.filter((module) => {
      if (group !== 'all' && module.menu_group !== group) return false
      if (!needle) return true
      return (
        module.label_fa.includes(needle) ||
        module.code.toLowerCase().includes(needle) ||
        module.slug.includes(needle) ||
        (module.description || '').includes(needle)
      )
    })
  }, [query, group])

  const totals = useMemo(
    () =>
      MODULES.reduce(
        (acc, module) => ({
          entities: acc.entities + module.entities.length,
          items: acc.items + module.items_count,
          ai: acc.ai + module.ai_points,
        }),
        { entities: 0, items: 0, ai: 0 },
      ),
    [],
  )

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>ماژول‌های فعال</h2>
          <p className="card-subtitle">
            {toPersianDigits(MODULES.length)} ماژول · {formatNumber(totals.entities)} جدول داده ·{' '}
            {formatNumber(totals.items)} زیرمجموعه · {formatNumber(totals.ai)} نقطه AI
          </p>
        </div>
      </div>

      <div className="card">
        <div className="toolbar">
          <div className="search grow">
            <span>🔍</span>
            <input
              placeholder="جست‌وجوی ماژول (نام فارسی، کد یا توضیح)…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <select className="select" style={{ width: 220 }} value={group} onChange={(event) => setGroup(event.target.value)}>
            <option value="all">همه گروه‌ها</option>
            {MENU_GROUPS.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card empty">ماژولی با این مشخصات یافت نشد.</div>
      ) : (
        <div className="grid cols-3">
          {filtered.map((module) => (
            <Link to={`/modules/${module.slug}`} key={module.code} className="card module-card">
              <div className="row">
                <div className="module-icon" style={{ background: module.color }}>{module.code}</div>
                <div>
                  <h3>{module.label_fa}</h3>
                  <span className="muted" style={{ fontSize: 11.5 }}>{module.name_en}</span>
                </div>
                {module.ai_points > 0 && (
                  <span className="badge ai" style={{ marginInlineStart: 'auto' }}>
                    🤖 {toPersianDigits(module.ai_points)}
                  </span>
                )}
              </div>

              <p>{module.description || '—'}</p>

              <div className="module-meta">
                <span className="badge">{toPersianDigits(module.entities.length)} جدول</span>
                <span className="badge">{toPersianDigits(module.items_count)} زیرمجموعه</span>
                <span className="badge">{module.menu_group}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  )
}
"""

MODULE_PAGE_JSX = r"""import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../lib/api.js'
import { MODULES } from '../config/menu.js'
import { formatNumber, toPersianDigits } from '../lib/format.js'
import AiWidget from '../components/AiWidget.jsx'

/** صفحه یک ماژول: داشبورد اختصاصی + فهرست موجودیت‌ها + قابلیت‌های AI */
export default function ModulePage() {
  const { moduleSlug } = useParams()
  const module = MODULES.find((item) => item.slug === moduleSlug)
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!module) return
    api
      .get(`/v1/${module.slug}/dashboard`)
      .then(setDashboard)
      .catch((apiError) => setError(apiError.message))
  }, [module])

  if (!module) {
    return (
      <div className="card empty">
        ماژول «{moduleSlug}» در این استقرار فعال نیست.{' '}
        <Link to="/modules" style={{ color: '#a5b4fc' }}>بازگشت به فهرست ماژول‌ها</Link>
      </div>
    )
  }

  const aiCapabilities = (module.ai_capabilities || []).slice(0, 3)

  return (
    <>
      <div className="between">
        <div className="row">
          <div className="module-icon" style={{ background: module.color, color: '#060b1c' }}>{module.code}</div>
          <div>
            <h2 className="card-title" style={{ fontSize: 19 }}>{module.label_fa}</h2>
            <p className="card-subtitle mt-0">{module.description}</p>
          </div>
        </div>
        <div className="row">
          <span className="badge">{module.menu_group}</span>
          <span className="badge info">{toPersianDigits(module.items_count)} زیرمجموعه</span>
          {module.ai_points > 0 && <span className="badge ai">🤖 {toPersianDigits(module.ai_points)} نقطه AI</span>}
        </div>
      </div>

      <div className="grid cols-4">
        {(dashboard ? Object.entries(dashboard).filter(([, value]) => typeof value === 'number') : []).slice(0, 8).map(([key, value]) => (
          <div className="card kpi" key={key}>
            <span className="label">{key.replace(/_/g, ' ')}</span>
            <span className="value">{formatNumber(value)}</span>
          </div>
        ))}
      </div>

      {error && <div className="error-box">دریافت داشبورد ماژول ناموفق بود: {error}</div>}

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">موجودیت‌های داده ({toPersianDigits(module.entities.length)})</h3>
            <p className="card-subtitle">برای مدیریت رکوردها روی هر مورد کلیک کنید</p>
          </div>
        </div>

        {module.entities.length === 0 ? (
          <div className="empty">این ماژول جدول مستقلی ندارد.</div>
        ) : (
          <div className="grid cols-3">
            {module.entities.map((entity) => (
              <Link
                key={entity.table}
                to={`/modules/${module.slug}/${entity.table}`}
                className="card module-card"
                style={{ padding: 14 }}
              >
                <div className="between">
                  <strong style={{ fontSize: 13.5 }}>{entity.label_fa}</strong>
                  <span className="badge">{toPersianDigits(entity.fields_count)} فیلد</span>
                </div>
                <span className="mono muted">{entity.table}</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {aiCapabilities.length > 0 && (
        <div className="grid cols-3">
          {aiCapabilities.map((capability) => (
            <AiWidget
              key={capability.code}
              capability={capability.code}
              title={capability.name}
              defaultPayload={{ module_code: module.code }}
            />
          ))}
        </div>
      )}
    </>
  )
}
"""

ENTITY_PAGE_JSX = r"""import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { resource } from '../lib/api.js'
import { MODULES } from '../config/menu.js'
import { getSchema } from '../lib/schemas.js'
import { formatNumber, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'
import DataTable from '../components/DataTable.jsx'
import EntityForm from '../components/Form.jsx'
import Modal from '../components/Modal.jsx'

/**
 * صفحه مدیریت یک موجودیت (CRUD کامل)
 *
 * فیلدها، برچسب‌های فارسی و قواعد نمایش از `config/schemas.js` خوانده می‌شوند؛
 * بنابراین افزودن ماژول جدید نیازی به کدنویسی صفحه جدید ندارد.
 */
export default function EntityPage() {
  const { moduleSlug, table } = useParams()
  const { notify, hasPermission } = useApp()

  const module = MODULES.find((item) => item.slug === moduleSlug)

  const [schema, setSchema] = useState(null)
  const [schemaMissing, setSchemaMissing] = useState(false)
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [editing, setEditing] = useState(null)
  const [creating, setCreating] = useState(false)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const client = useMemo(() => resource(moduleSlug, table), [moduleSlug, table])

  // طرحواره از chunk جداگانه بارگذاری می‌شود تا بسته اصلی کوچک بماند
  useEffect(() => {
    let alive = true
    setSchema(null)
    setSchemaMissing(false)
    getSchema(table).then((found) => {
      if (!alive) return
      if (found) setSchema(found)
      else setSchemaMissing(true)
    })
    return () => {
      alive = false
    }
  }, [table])

  const load = useCallback(async () => {
    if (!module || !schema) return
    setLoading(true)
    setError('')
    try {
      const payload = await client.list({ page, per_page: 25, q: query || undefined, status: statusFilter || undefined })
      setRows(payload.data || [])
      setMeta(payload.meta || null)
    } catch (apiError) {
      setError(apiError.message)
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [client, module, page, query, schema, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  if (!module) {
    return (
      <div className="card empty">
        ماژول «{moduleSlug}» یافت نشد.{' '}
        <Link to="/modules" style={{ color: '#a5b4fc' }}>فهرست ماژول‌ها</Link>
      </div>
    )
  }

  if (!schema && !schemaMissing) {
    return (
      <div className="card empty">
        <div className="spinner" aria-hidden="true" /> در حال بارگذاری ساختار «{table}»…
      </div>
    )
  }

  if (!schema) {
    return (
      <div className="card empty">
        موجودیت «{table}» در ماژول «{moduleSlug}» یافت نشد.{' '}
        <Link to="/modules" style={{ color: '#a5b4fc' }}>فهرست ماژول‌ها</Link>
      </div>
    )
  }

  const permissionBase = `${module.slug}.${table}`
  const statusOptions = schema.status_options || []

  const submit = async (payload) => {
    setSaving(true)
    setFormErrors({})
    try {
      if (creating) {
        await client.create(payload)
        notify('رکورد با موفقیت ایجاد شد')
        setCreating(false)
      } else {
        await client.update(editing.id, payload)
        notify('تغییرات ذخیره شد')
        setEditing(null)
      }
      await load()
    } catch (apiError) {
      if (apiError.status === 422 && apiError.payload?.errors) {
        setFormErrors(apiError.payload.errors)
        notify('اعتبارسنجی فرم ناموفق بود', 'error')
      } else {
        notify(apiError.message || 'ذخیره ناموفق بود', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  const remove = async (row) => {
    if (!window.confirm(`آیا از حذف «${row.code || row.title || row.id}» مطمئن هستید؟`)) return
    try {
      await client.remove(row.id)
      notify('رکورد حذف شد')
      await load()
    } catch (apiError) {
      notify(apiError.message || 'حذف ناموفق بود', 'error')
    }
  }

  return (
    <>
      <div className="between">
        <div>
          <div className="row" style={{ gap: 8 }}>
            <Link to={`/modules/${module.slug}`} className="badge">{module.label_fa}</Link>
            <span className="muted">/</span>
            <h2 className="card-title" style={{ fontSize: 18 }}>{schema.label_fa}</h2>
          </div>
          <p className="card-subtitle">
            <span className="mono">{table}</span> · {toPersianDigits(schema.fields.length)} فیلد
            {meta ? ` · ${formatNumber(meta.total)} رکورد` : ''}
          </p>
        </div>

        <div className="toolbar">
          <button className="btn ghost sm" onClick={load}>↻ بروزرسانی</button>
          {hasPermission(`${permissionBase}.create`) && (
            <button className="btn primary sm" onClick={() => { setCreating(true); setFormErrors({}) }}>
              + رکورد جدید
            </button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="toolbar" style={{ marginBottom: 14 }}>
          <div className="search grow">
            <span>🔍</span>
            <input
              placeholder={`جست‌وجو در ${schema.label_fa}…`}
              value={query}
              onChange={(event) => { setQuery(event.target.value); setPage(1) }}
            />
          </div>
          {statusOptions.length > 0 && (
            <select
              className="select"
              style={{ width: 190 }}
              value={statusFilter}
              onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}
            >
              <option value="">همه وضعیت‌ها</option>
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          )}
        </div>

        {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

        <DataTable
          fields={schema.fields}
          rows={rows}
          loading={loading}
          meta={meta}
          onPage={setPage}
          onRowClick={(row) => hasPermission(`${permissionBase}.edit`) && setEditing(row)}
          actions={(row) => (
            <div className="row" style={{ gap: 6 }}>
              {hasPermission(`${permissionBase}.edit`) && (
                <button className="btn sm ghost" onClick={() => setEditing(row)}>ویرایش</button>
              )}
              {hasPermission(`${permissionBase}.delete`) && (
                <button className="btn sm danger" onClick={() => remove(row)}>حذف</button>
              )}
            </div>
          )}
          emptyMessage="رکوردی ثبت نشده است — با دکمه «رکورد جدید» اولین مورد را بسازید."
        />
      </div>

      <Modal
        open={creating || Boolean(editing)}
        title={creating ? `ایجاد ${schema.label_fa}` : `ویرایش ${schema.label_fa}`}
        subtitle={editing ? `شناسه ${toPersianDigits(editing.id)}` : 'فیلدهای ستاره‌دار الزامی هستند'}
        onClose={() => { setCreating(false); setEditing(null); setFormErrors({}) }}
        wide
      >
        <EntityForm
          fields={schema.fields}
          initial={editing || schema.defaults || {}}
          errors={formErrors}
          onSubmit={submit}
          onCancel={() => { setCreating(false); setEditing(null) }}
          submitLabel={saving ? 'در حال ذخیره…' : 'ذخیره'}
        />
      </Modal>
    </>
  )
}
"""

AI_HUB_JSX = r"""import { useMemo, useState } from 'react'

import { AI_ENABLED } from '../config/menu.js'
import { ai } from '../lib/api.js'
import { useApp, useSystemInfo } from '../lib/store.jsx'
import { formatNumber, toPersianDigits } from '../lib/format.js'
import AiWidget from '../components/AiWidget.jsx'

const ENGINE_LABELS = {
  forecasting: 'پیش‌بینی سری زمانی',
  reliability: 'قابلیت اطمینان و PdM',
  optimization: 'بهینه‌سازی و تجویز',
  anomaly: 'تشخیص ناهنجاری',
  computer_vision: 'بینایی ماشین',
  nlp: 'پردازش زبان طبیعی',
  recommendation: 'توصیه‌گر هوشمند',
  quality_spc: 'کنترل کیفیت آماری',
  classification: 'طبقه‌بندی',
  simulation: 'شبیه‌سازی و سناریو',
  mlops: 'عملیات یادگیری ماشین',
}

/** مرکز هوش مصنوعی — گفت‌وگو، موتورهای فعال و اجرای قابلیت‌ها */
export default function AiHub() {
  if (!AI_ENABLED) {
    return (
      <>
        <h2 className="card-title" style={{ fontSize: 19 }}>مرکز هوش مصنوعی</h2>
        <div className="card">
          <p className="card-subtitle">
            هوش مصنوعی در این استقرار غیرفعال است (ai_enabled=false).
            برای فعال‌سازی، بسته را با گزینه «هوش مصنوعی» فعال دوباره بسازید.
          </p>
        </div>
      </>
    )
  }

  const { capabilities, aiEngines, aiHealth, notify } = useApp()
  const info = useSystemInfo()
  const [tab, setTab] = useState('chat')
  const [engine, setEngine] = useState('all')
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)

  const grouped = useMemo(() => {
    const filtered = capabilities.filter((item) => {
      if (engine !== 'all' && item.engine !== engine) return false
      if (!query.trim()) return true
      const needle = query.trim()
      return (
        String(item.name).includes(needle) ||
        String(item.code).toLowerCase().includes(needle.toLowerCase()) ||
        String(item.engine).includes(needle)
      )
    })

    return filtered.reduce((acc, item) => {
      acc[item.engine] = acc[item.engine] || []
      acc[item.engine].push(item)
      return acc
    }, {})
  }, [capabilities, engine, query])

  const send = async (event) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text) return

    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setDraft('')
    setSending(true)

    try {
      const result = await ai.chat({ message: text, history: messages.slice(-8) })
      setMessages([...next, { role: 'assistant', content: result.answer, meta: result }])
    } catch (error) {
      setMessages([...next, { role: 'assistant', content: error.message || 'پاسخی دریافت نشد.', error: true }])
      notify('دستیار هوشمند پاسخ نداد', 'error')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>مرکز هوش مصنوعی</h2>
          <p className="card-subtitle">
            {toPersianDigits(capabilities.length)} قابلیت فعال · {toPersianDigits(aiEngines.length)} موتور ·{' '}
            {aiHealth?.ok ? 'سرویس AI در دسترس' : 'سرویس AI خارج از دسترس'}
          </p>
        </div>
        <div className="tabs">
          {[
            ['chat', 'دستیار گفت‌وگو'],
            ['capabilities', 'قابلیت‌ها'],
            ['engines', 'موتورها'],
          ].map(([key, label]) => (
            <button key={key} className={`tab${tab === key ? ' active' : ''}`} onClick={() => setTab(key)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'chat' && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">دستیار هوشمند کارخانه</h3>
              <p className="card-subtitle">
                پرسش‌های عملیاتی بپرسید؛ پاسخ‌ها بر اساس کاتالوگ {info.app_name_fa} تولید می‌شود.
              </p>
            </div>
            <span className="badge ai">AvalAI</span>
          </div>

          <div className="stack" style={{ minHeight: 240, maxHeight: 420, overflowY: 'auto', marginBottom: 14 }}>
            {messages.length === 0 && (
              <div className="empty">
                گفت‌وگو را شروع کنید. نمونه: «چطور ضایعات خط تزریق را کاهش دهم؟» یا
                «شاخص‌های نت را برای این ماه تحلیل کن.»
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className="card"
                style={{
                  padding: 14,
                  alignSelf: message.role === 'user' ? 'flex-start' : 'stretch',
                  borderColor: message.role === 'user' ? 'rgba(99,102,241,0.4)' : 'var(--border-soft)',
                }}
              >
                <div className="muted" style={{ fontSize: 11.5, marginBottom: 6 }}>
                  {message.role === 'user' ? 'شما' : 'دستیار'}
                  {message.meta?.llm_used === false && ' · پاسخ داخلی (بدون AvalAI)'}
                </div>
                <div className="pre-wrap">{message.content}</div>
              </div>
            ))}
            {sending && (
              <div className="loader" style={{ padding: 18 }}>
                <div className="spinner" />
                <span>دستیار در حال پاسخ‌دادن…</span>
              </div>
            )}
          </div>

          <form onSubmit={send} className="row">
            <input
              className="input"
              style={{ flex: 1 }}
              placeholder="پرسش خود را بنویسید…"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={sending}
            />
            <button className="btn primary" type="submit" disabled={sending || !draft.trim()}>
              ارسال
            </button>
          </form>
        </div>
      )}

      {tab === 'capabilities' && (
        <>
          <div className="card">
            <div className="toolbar">
              <div className="search grow">
                <span>🔍</span>
                <input placeholder="جست‌وجوی قابلیت (نام یا کد)…" value={query} onChange={(event) => setQuery(event.target.value)} />
              </div>
              <select className="select" style={{ width: 240 }} value={engine} onChange={(event) => setEngine(event.target.value)}>
                <option value="all">همه موتورها</option>
                {Object.entries(ENGINE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {Object.keys(grouped).length === 0 ? (
            <div className="card empty">قابلیتی با این فیلتر یافت نشد.</div>
          ) : (
            Object.entries(grouped).map(([key, items]) => (
              <div className="card" key={key}>
                <div className="card-header">
                  <div>
                    <h3 className="card-title">{ENGINE_LABELS[key] || key}</h3>
                    <p className="card-subtitle">{toPersianDigits(items.length)} قابلیت فعال</p>
                  </div>
                  <span className="badge info">{key}</span>
                </div>
                <div className="grid cols-3">
                  {items.slice(0, 9).map((item) => (
                    <AiWidget key={item.code} capability={item.code} title={item.name} compact />
                  ))}
                </div>
                {items.length > 9 && (
                  <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>
                    و {formatNumber(items.length - 9)} قابلیت دیگر در همین موتور…
                  </p>
                )}
              </div>
            ))
          )}
        </>
      )}

      {tab === 'engines' && (
        <div className="grid cols-3">
          {(aiEngines.length ? aiEngines : []).map((item) => (
            <div className="card" key={item.key || item}>
              <div className="between">
                <h3 className="card-title" style={{ fontSize: 14 }}>{ENGINE_LABELS[item.key] || item.key}</h3>
                <span className="badge success">فعال</span>
              </div>
              <p className="muted" style={{ fontSize: 12, minHeight: 40 }}>{item.name_fa || item.key}</p>
              <div className="row">
                {(item.algorithms || []).slice(0, 3).map((algorithm) => (
                  <span className="badge" key={algorithm}>{algorithm}</span>
                ))}
              </div>
              <span className="mono muted" style={{ fontSize: 11, marginTop: 8 }}>{item.endpoint}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
"""

REPORTS_JSX = r"""import { useEffect, useState } from 'react'

import { reports } from '../lib/api.js'
import { downloadCsv, formatNumber, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'
import { BarChart } from '../components/Charts.jsx'

/** گزارش‌ساز عمومی روی همه جداول فعال */
export default function Reports() {
  const { notify } = useApp()
  const [tables, setTables] = useState([])
  const [templates, setTemplates] = useState([])
  const [form, setForm] = useState({ table: '', metric: 'count', column: '', group_by: '', limit: 30 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    reports.tables().then((payload) => {
      const flat = []
      ;(payload.tables || []).forEach((module) => {
        module.tables.forEach((table) => flat.push({ table, module: module.module_name, code: module.module }))
      })
      setTables(flat)
      if (flat.length) setForm((current) => ({ ...current, table: flat[0].table }))
    }).catch((apiError) => setError(apiError.message))

    reports.templates()
      .then((payload) => setTemplates(payload.templates || []))
      .catch(() => setTemplates([]))
  }, [])

  const applyTemplate = (template) => {
    setForm({
      table: template.table,
      metric: template.metric || 'count',
      column: template.column || '',
      group_by: template.group_by || '',
      limit: 30,
    })
    notify(`قالب «${template.title}» بارگذاری شد`)
  }

  const run = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const payload = await reports.aggregate({ ...form, limit: Number(form.limit) })
      setResult(payload)
    } catch (apiError) {
      setError(apiError.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const exportCsv = async () => {
    try {
      const payload = await reports.export({ table: form.table, limit: 5000 })
      downloadCsv(payload.filename, payload.content)
      notify('فایل CSV دریافت شد')
    } catch (apiError) {
      notify(apiError.message || 'خروجی گرفتن ناموفق بود', 'error')
    }
  }

  const rows = (result?.rows || []).map((row) => ({ ...row, value: Number(row.value || 0) }))

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>گزارش‌ساز</h2>
          <p className="card-subtitle">
            تجمیع روی هر جدول فعال — {toPersianDigits(tables.length)} جدول در این استقرار
          </p>
        </div>
        <button className="btn ghost sm" onClick={exportCsv} disabled={!form.table}>⬇ خروجی CSV</button>
      </div>

      {templates.length > 0 && (
        <div className="card">
          <div className="card-title" style={{ fontSize: 15 }}>قالب‌های گزارش آماده</div>
          <p className="card-subtitle">
            {toPersianDigits(templates.length)} قالب پیش‌فرض از ماژول‌های انتخاب‌شده —
            برای پر شدن خودکار فرم کلیک کنید.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
            {templates.slice(0, 24).map((template) => (
              <button
                key={template.id}
                type="button"
                className="btn ghost sm"
                onClick={() => applyTemplate(template)}
                title={`${template.module_name} — ${template.table}`}
              >
                {template.title}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <form onSubmit={run} className="form-grid">
          <div className="field">
            <label htmlFor="table">جدول</label>
            <select id="table" className="select" value={form.table} onChange={(event) => setForm({ ...form, table: event.target.value })}>
              {tables.map((item) => (
                <option key={item.table} value={item.table}>
                  {item.table} — {item.module}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="metric">سنجه</label>
            <select id="metric" className="select" value={form.metric} onChange={(event) => setForm({ ...form, metric: event.target.value })}>
              <option value="count">تعداد</option>
              <option value="sum">مجموع</option>
              <option value="avg">میانگین</option>
              <option value="max">بیشینه</option>
              <option value="min">کمینه</option>
            </select>
          </div>

          <div className="field">
            <label htmlFor="column">ستون عددی</label>
            <input
              id="column"
              className="input"
              placeholder="مثلاً amount"
              value={form.column}
              onChange={(event) => setForm({ ...form, column: event.target.value })}
            />
          </div>

          <div className="field">
            <label htmlFor="group_by">گروه‌بندی بر اساس</label>
            <input
              id="group_by"
              className="input"
              placeholder="مثلاً status یا department_id"
              value={form.group_by}
              onChange={(event) => setForm({ ...form, group_by: event.target.value })}
            />
          </div>

          <div className="field">
            <label htmlFor="limit">حداکثر سطرها</label>
            <input
              id="limit"
              type="number"
              className="input"
              min="1"
              max="1000"
              value={form.limit}
              onChange={(event) => setForm({ ...form, limit: event.target.value })}
            />
          </div>

          <div className="field" style={{ justifyContent: 'flex-end' }}>
            <button className="btn primary" type="submit" disabled={loading || !form.table}>
              {loading ? 'در حال اجرا…' : 'اجرای گزارش'}
            </button>
          </div>
        </form>
      </div>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                {result.metric} روی <span className="mono">{result.table}</span>
              </h3>
              <p className="card-subtitle">زمان تولید: {result.generated_at_jalali}</p>
            </div>
            <span className="badge info">{toPersianDigits(rows.length)} سطر</span>
          </div>

          {rows.length === 0 ? (
            <div className="empty">نتیجه‌ای یافت نشد.</div>
          ) : (
            <>
              <BarChart
                labels={rows.map((row) => String(row[form.group_by] ?? 'کل'))}
                values={rows.map((row) => row.value)}
                color="#22c55e"
                height={Math.min(120 + rows.length * 16, 420)}
                horizontal={rows.length > 12}
              />
              <div className="table-wrap" style={{ marginTop: 16 }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th>{form.group_by || '—'}</th>
                      <th>مقدار</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.slice(0, 100).map((row, index) => (
                      <tr key={index}>
                        <td>{String(row[form.group_by] ?? 'کل')}</td>
                        <td>{formatNumber(row.value, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </>
  )
}
"""

AUDIT_JSX = r"""import { useCallback, useEffect, useState } from 'react'

import { system } from '../lib/api.js'
import { formatNumber, toPersianDigits } from '../lib/format.js'
import DataTable from '../components/DataTable.jsx'

const FIELDS = [
  { name: 'code', label: 'شماره', type: 'string' },
  { name: 'action', label: 'عملیات', type: 'string' },
  { name: 'user', label: 'کاربر', type: 'string' },
  { name: 'module_code', label: 'ماژول', type: 'string' },
  { name: 'entity_type', label: 'موضوع', type: 'string' },
  { name: 'ip_address', label: 'آدرس IP', type: 'string' },
  { name: 'occurred_at_jalali', label: 'زمان (شمسی)', type: 'string' },
]

/** گزارش ممیزی سامانه */
export default function AuditLog() {
  const [rows, setRows] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [query, setQuery] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await system.audit({ page, per_page: 25, action: query || undefined })
      setRows(payload.data || [])
      setMeta(payload.meta || null)
    } catch (apiError) {
      setError(apiError.message)
    } finally {
      setLoading(false)
    }
  }, [page, query])

  useEffect(() => {
    load()
  }, [load])

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>گزارش ممیزی</h2>
          <p className="card-subtitle">چه کسی، چه چیزی را، چه زمانی تغییر داده است</p>
        </div>
        <span className="badge info">{meta ? formatNumber(meta.total) : '—'} رویداد</span>
      </div>

      <div className="card">
        <div className="toolbar" style={{ marginBottom: 14 }}>
          <div className="search grow">
            <span>🔍</span>
            <input
              placeholder="جست‌وجو در عملیات…"
              value={query}
              onChange={(event) => { setQuery(event.target.value); setPage(1) }}
            />
          </div>
          <button className="btn ghost sm" onClick={load}>↻ بروزرسانی</button>
        </div>

        {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

        <DataTable
          fields={FIELDS}
          rows={rows}
          loading={loading}
          meta={meta}
          onPage={setPage}
          emptyMessage="رویدادی ثبت نشده است."
        />
      </div>
    </>
  )
}
"""

SETTINGS_JSX = r"""import { useState } from 'react'

import { auth } from '../lib/api.js'
import { toPersianDigits } from '../lib/format.js'
import { useApp, useSystemInfo } from '../lib/store.jsx'
import { MODULES } from '../config/menu.js'

/** تنظیمات کاربر و اطلاعات استقرار */
export default function Settings() {
  const { user, notify, refreshSession } = useApp()
  const info = useSystemInfo()
  const [passwords, setPasswords] = useState({ current_password: '', password: '', password_confirmation: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const stats = info.stats || {}

  const changePassword = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await auth.changePassword(passwords)
      notify('گذرواژه تغییر کرد — همه نشست‌های دیگر خارج شدند')
      setPasswords({ current_password: '', password: '', password_confirmation: '' })
      await refreshSession()
    } catch (apiError) {
      setError(apiError.payload?.errors ? Object.values(apiError.payload.errors).flat().join(' ') : apiError.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="between">
        <div>
          <h2 className="card-title" style={{ fontSize: 19 }}>تنظیمات</h2>
          <p className="card-subtitle">پروفایل کاربری و اطلاعات استقرار</p>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">پروفایل من</h3>
          </div>
          <div className="stack" style={{ gap: 8 }}>
            {[
              ['نام و نام خانوادگی', user?.full_name],
              ['نام کاربری', user?.username],
              ['ایمیل', user?.email],
              ['شماره همراه', user?.mobile],
              ['نقش‌ها', (user?.roles || []).join('، ') || '—'],
              ['دسترسی مدیر کل', user?.is_super_admin ? 'بله' : 'خیر'],
            ].map(([label, value]) => (
              <div className="between" key={label} style={{ borderBottom: '1px solid var(--border-soft)', paddingBottom: 7 }}>
                <span className="muted" style={{ fontSize: 12.5 }}>{label}</span>
                <span style={{ fontSize: 13 }}>{toPersianDigits(value ?? '—')}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">تغییر گذرواژه</h3>
          </div>
          <form onSubmit={changePassword} className="stack">
            <div className="field">
              <label htmlFor="current_password">گذرواژه فعلی</label>
              <input
                id="current_password"
                type="password"
                className="input"
                value={passwords.current_password}
                onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="password">گذرواژه جدید</label>
              <input
                id="password"
                type="password"
                className="input"
                value={passwords.password}
                onChange={(event) => setPasswords({ ...passwords, password: event.target.value })}
                required
                minLength={8}
              />
              <span className="hint">حداقل ۸ نویسه</span>
            </div>
            <div className="field">
              <label htmlFor="password_confirmation">تکرار گذرواژه جدید</label>
              <input
                id="password_confirmation"
                type="password"
                className="input"
                value={passwords.password_confirmation}
                onChange={(event) => setPasswords({ ...passwords, password_confirmation: event.target.value })}
                required
              />
            </div>
            {error && <div className="error-box">{error}</div>}
            <button className="btn primary" type="submit" disabled={saving}>
              {saving ? 'در حال ذخیره…' : 'تغییر گذرواژه'}
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">اطلاعات استقرار</h3>
            <p className="card-subtitle">این مقادیر در زمان ساخت بسته توسط سازنده ERP تعیین شده است</p>
          </div>
        </div>
        <div className="grid cols-4">
          {[
            ['سامانه', info.app_name_fa],
            ['شرکت', info.company],
            ['واحد پول', info.currency === 'IRR' ? 'ریال' : info.currency],
            ['تقویم', info.calendar === 'jalali' ? 'شمسی' : info.calendar],
            ['نسخه', info.version],
            ['ماژول‌های فعال', toPersianDigits(MODULES.length)],
            ['جداول داده', toPersianDigits(stats.tables || 0)],
            ['نقاط هوش مصنوعی', toPersianDigits(stats.ai_points || 0)],
          ].map(([label, value]) => (
            <div className="stack" key={label} style={{ gap: 2 }}>
              <span className="muted" style={{ fontSize: 12 }}>{label}</span>
              <strong style={{ fontSize: 15 }}>{value ?? '—'}</strong>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
"""

NOTFOUND_JSX = r"""import { Link } from 'react-router-dom'

/** صفحه یافت نشد */
export default function NotFound() {
  return (
    <div className="card empty">
      <h2 className="card-title" style={{ fontSize: 22, marginBottom: 8 }}>۴۰۴</h2>
      <p className="card-subtitle">صفحه یا ماژول درخواستی در این استقرار فعال نیست.</p>
      <div className="row" style={{ justifyContent: 'center', marginTop: 16 }}>
        <Link to="/" className="btn primary">داشبورد فرماندهی</Link>
        <Link to="/modules" className="btn ghost">فهرست ماژول‌ها</Link>
      </div>
    </div>
  )
}
"""

FRONTEND_DOCKERFILE = """# ساخت رابط کاربری و سرو با nginx
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .
ARG VITE_API_BASE_URL=/api
ARG VITE_APP_NAME_FA="@@app_name_fa@@"
ARG VITE_COMPANY_NAME="@@company_name@@"
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_APP_NAME_FA=$VITE_APP_NAME_FA
ENV VITE_COMPANY_NAME=$VITE_COMPANY_NAME

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY deploy/nginx/frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""

FRONTEND_README = """# رابط کاربری @@app_name_fa@@

SPA با React 18 و Vite — راست‌به‌چپ، تم تیره صنعتی، بدون وابستگی سنگین.

## ساختار

```
src/
├── main.jsx              # نقطه ورود
├── App.jsx               # مسیریابی
├── lib/api.js            # لایه ارتباط با API لاراول (Sanctum)
├── lib/format.js         # ارقام فارسی، تاریخ شمسی، مبلغ
├── lib/store.jsx         # وضعیت سراسری (کاربر، قابلیت‌ها، اعلان‌ها)
├── components/           # کتابخانه UI داخلی (جدول، فرم، نمودار SVG، مودال، ویجت AI)
├── pages/                # داشبورد، ماژول‌ها، موجودیت‌ها، AI، گزارش، ممیزی، تنظیمات
└── config/menu.js        # ⚙ تولیدشده: ماژول‌ها، موجودیت‌ها و طرحواره فیلدها
```

## نکته کلیدی: صفحه‌های داده‌محور

فایل `src/config/menu.js` توسط سازنده ERP تولید شده و شامل **@@modules_count@@ ماژول**،
**@@entities_count@@ موجودیت** و **@@fields_count@@ فیلد** با برچسب فارسی، نوع داده،
گزینه‌های enum و قوائد نمایش است. صفحه `EntityPage.jsx` بر اساس همین طرحواره
جدول، فرم و اعتبارسنجی می‌سازد؛ بنابراین افزودن ماژول جدید به سامانه
نیاز به نوشتن صفحه جدید ندارد.

## اجرا در حالت توسعه

```bash
cd frontend
npm install
npm run dev
```

سرور توسعه روی پورت ۵۱۷۳ اجرا می‌شود و درخواست‌های `/api` را به
`http://localhost:8000` (لاراول) پروکسی می‌کند. برای تغییر مقصد:

```bash
VITE_PROXY_TARGET=http://erp-backend.local npm run dev
```

## ساخت برای استقرار

```bash
npm run build          # خروجی در frontend/dist
npm run preview        # پیش‌نمایش بیلد
```

## استقرار با Docker

```bash
docker build -t @@slug@@-frontend -f frontend/Dockerfile frontend
```

پیکربندی nginx در `deploy/nginx/frontend.conf` قرار دارد و درخواست‌های
`/api` را به سرویس لاراول هدایت می‌کند.

## احراز هویت

۱. کاربر در `/login` نام کاربری و گذرواژه را وارد می‌کند.
۲. لاراول توکن Sanctum برمی‌گرداند؛ توکن در `localStorage` ذخیره می‌شود.
۳. همه درخواست‌ها با سرآیند `Authorization: Bearer <token>` ارسال می‌شوند.
۴. دسترسی‌ها با `hasPermission('<slug>.<table>.<action>')` در رابط کنترل می‌شوند.
"""


# --------------------------------------------------------------------------- #
# PWA — نصب روی موبایل، کار آفلاین و آیکون
# --------------------------------------------------------------------------- #
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#312e81"/>
      <stop offset="100%" stop-color="#0b1020"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="url(#bg)"/>
  <g fill="none" stroke="#a5b4fc" stroke-width="22" stroke-linejoin="round" stroke-linecap="round">
    <path d="M104 372V228l84 52V228l84 52V180l136-52v244z"/>
    <path d="M104 372h304"/>
  </g>
  <g fill="#22d3ee">
    <rect x="150" y="316" width="40" height="40" rx="8"/>
    <rect x="234" y="316" width="40" height="40" rx="8"/>
    <rect x="318" y="316" width="40" height="40" rx="8"/>
  </g>
</svg>
"""

SERVICE_WORKER_JS = r"""/* Service Worker تولیدشده — @@app_name_fa@@
 *
 * سیاست کش:
 *   - ناوبری (HTML): network-first با بازگشت به نسخه کش‌شده هنگام آفلاین بودن
 *   - دارایی‌های هم‌مبدأ: cache-first
 *   - /api و /storage: هرگز کش نمی‌شوند (داده زنده)
 */
const CACHE = '@@slug@@-@@version@@'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).catch(() => undefined)
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/storage')) return

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone()
          caches.open(CACHE).then((cache) => cache.put('/index.html', copy)).catch(() => undefined)
          return response
        })
        .catch(() =>
          caches
            .match('/index.html')
            .then((cached) => cached || new Response('آفلاین هستید', { status: 503 }))
        )
    )
    return
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached
      return fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(CACHE).then((cache) => cache.put(request, copy)).catch(() => undefined)
          }
          return response
        })
        .catch(() => new Response('', { status: 503 }))
    })
  )
})
"""

SW_REGISTER_SNIPPET = r"""

// ثبت Service Worker — نصب به‌عنوان اپ موبایل و کار آفلاین (PWA)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => undefined)
  })
}
"""

ROBOTS_TXT = """User-agent: *
Disallow: /api/
Disallow: /storage/
Allow: /

Sitemap: @@app_url@@/sitemap.xml
"""


def _pwa_manifest(settings: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
    """manifest.webmanifest برای نصب سامانه روی موبایل."""
    short_name = str(common.get("company_name") or common.get("app_name_fa") or "ERP")
    return {
        "name": common.get("app_name_fa", "ERP کارخانه"),
        "short_name": short_name[:24],
        "description": f"{common.get('app_name_fa', '')} — سامانه یکپارچه مدیریت کارخانه",
        "lang": "fa",
        "dir": "rtl",
        "start_url": "/",
        "scope": "/",
        "id": "/",
        "display": "standalone",
        "display_override": ["window-controls-overlay", "standalone", "minimal-ui"],
        "orientation": "any",
        "background_color": "#0b1020",
        "theme_color": "#0b1020",
        "categories": ["business", "productivity"],
        "icons": [
            {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
            {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "داشبورد", "short_name": "داشبورد", "url": "/dashboard"},
            {"name": "گزارش‌ها", "short_name": "گزارش‌ها", "url": "/reports"},
            {"name": "ماژول‌ها", "short_name": "ماژول‌ها", "url": "/modules"},
        ],
        "related_applications": [],
        "prefer_related_applications": False,
    }


SCHEMAS_LOADER_JS = r"""/*
 * بارگذاری تنبل طرحواره موجودیت‌ها
 *
 * فایل `config/schemas.js` می‌تواند چند مگابایت باشد؛ با import پویا در
 * یک chunk جداگانه از بسته اصلی خارج می‌شود و فقط وقتی کاربر وارد صفحه یک
 * موجودیت شد بارگذاری می‌شود.
 */
let cache = null
let promise = null

export function loadSchemas() {
  if (!promise) {
    promise = import('../config/schemas.js')
      .then((module) => {
        cache = module.default || module.SCHEMAS || {}
        return cache
      })
      .catch(() => {
        cache = {}
        return cache
      })
  }
  return promise
}

/** طرحواره یک جدول (یا null اگر شناخته‌شده نباشد) */
export async function getSchema(table) {
  const all = await loadSchemas()
  return all[table] || null
}

/** فهرست نام جداول شناخته‌شده */
export async function schemaTables() {
  const all = await loadSchemas()
  return Object.keys(all)
}

export default { loadSchemas, getSchema, schemaTables }
"""


def _entity_schema_js(entity: dict[str, Any]) -> dict[str, Any]:
    """طرحواره JS یک موجودیت برای فرم/جدول داده‌محور."""
    fields = []
    for field in entity["fields"]:
        item: dict[str, Any] = {
            "name": field["name"],
            "label": field["label"],
            "type": field["type"],
            "nullable": bool(field.get("nullable")),
            "required": bool(field.get("required")) or not field.get("nullable"),
            "hidden": bool(field.get("hidden")),
            "searchable": bool(field.get("searchable")),
        }
        if field.get("options"):
            item["options"] = field["options"]
        if field.get("references_table"):
            item["references_table"] = field["references_table"]
        if field.get("default") is not None:
            item["default"] = field["default"]
        money_keys = ("amount", "price", "cost", "total", "balance", "salary", "value", "sum", "fee")
        item["money"] = field["type"] == "decimal" and any(key in field["name"] for key in money_keys)
        fields.append(item)

    status_field = next((f for f in entity["fields"] if f["name"] == "status" and f["type"] == "enum"), None)
    schema = {
        "name": entity["name"],
        "table": entity["table"],
        "label_fa": entity["label_fa"],
        "module_code": entity["module_code"],
        "icon": entity.get("icon", "file-text"),
        "fields": fields,
    }
    if status_field:
        schema["status_options"] = [{"value": option, "label": option} for option in status_field.get("options", [])]
    schema["defaults"] = {
        f["name"]: f["default"]
        for f in entity["fields"]
        if f.get("default") is not None and str(f.get("default")).lower() not in ("now", "today", "null")
    }
    return schema


def generate_frontend(
    package: Package,
    *,
    settings: dict[str, Any],
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    context: dict[str, Any],
) -> None:
    """تولید کامل رابط کاربری React."""
    slug = context["slug"]
    include_pwa = bool(settings.get("include_mobile_pwa", True))
    report_templates = bool(settings.get("include_report_templates", True))
    ai_enabled = bool(settings.get("ai_enabled", True)) and bool(ai_points)
    common = {
        "slug": slug,
        "app_name": settings.get("app_name", slug),
        "app_name_fa": settings.get("app_name_fa", context["app_name_fa"]),
        "company_name": settings.get("company_name", context["app_name_fa"]),
        "currency": settings.get("currency", "IRR"),
        "calendar": settings.get("calendar", "jalali"),
        "version": context["version"],
        "app_url": settings.get("app_url", context.get("app_url", "http://erp.local")),
    }

    package.add_rendered("frontend/package.json", PACKAGE_JSON, area="frontend", **common)
    package.add("frontend/vite.config.js", VITE_CONFIG, area="frontend")
    if include_pwa:
        title = str(common["app_name_fa"]).replace('"', "'")
        pwa_head = (
            '    <link rel="manifest" href="/manifest.webmanifest" />\n'
            '    <link rel="apple-touch-icon" href="/icon.svg" />\n'
            '    <meta name="mobile-web-app-capable" content="yes" />\n'
            '    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />\n'
            f'    <meta name="apple-mobile-web-app-title" content="{title}" />\n'
        )
        package.add(
            "frontend/public/manifest.webmanifest",
            json.dumps(_pwa_manifest(settings, common), ensure_ascii=False, indent=2) + "\n",
            area="frontend",
        )
        package.add("frontend/public/icon.svg", ICON_SVG, area="frontend")
        package.add_rendered("frontend/public/sw.js", SERVICE_WORKER_JS, area="frontend", **common)
        package.add_rendered("frontend/public/robots.txt", ROBOTS_TXT, area="frontend", **common)
    else:
        pwa_head = ""

    package.add_rendered(
        "frontend/index.html", INDEX_HTML, area="frontend", pwa_head=pwa_head, **common
    )
    package.add_rendered("frontend/.env", ENV_FRONTEND, area="frontend", **common)
    package.add_rendered("frontend/.env.example", ENV_FRONTEND, area="frontend", **common)
    package.add_rendered("frontend/Dockerfile", FRONTEND_DOCKERFILE, area="frontend", **common)
    package.add(
        "frontend/.gitignore",
        "node_modules\ndist\ndist-ssr\n*.local\n.vite\n",
        area="frontend",
    )

    main_jsx = MAIN_JSX + (render(SW_REGISTER_SNIPPET, **common) if include_pwa else "")
    package.add("frontend/src/main.jsx", main_jsx, area="frontend")
    package.add("frontend/src/App.jsx", APP_JSX, area="frontend")
    package.add("frontend/src/styles/global.css", GLOBAL_CSS, area="frontend")
    package.add_rendered("frontend/src/lib/api.js", API_JS, area="frontend", **common)
    package.add("frontend/src/lib/format.js", FORMAT_JS, area="frontend")
    package.add("frontend/src/lib/store.jsx", STORE_JSX, area="frontend")

    package.add("frontend/src/components/Layout.jsx", LAYOUT_JSX, area="frontend")
    package.add("frontend/src/components/RequireAuth.jsx", REQUIRE_AUTH_JSX, area="frontend")
    package.add("frontend/src/components/Toasts.jsx", TOASTS_JSX, area="frontend")
    package.add("frontend/src/components/Charts.jsx", CHARTS_JSX, area="frontend")
    package.add("frontend/src/components/DataTable.jsx", DATA_TABLE_JSX, area="frontend")
    package.add("frontend/src/components/Form.jsx", FORM_JSX, area="frontend")
    package.add("frontend/src/components/Modal.jsx", MODAL_JSX, area="frontend")
    package.add("frontend/src/components/AiWidget.jsx", AI_WIDGET_JSX, area="frontend")

    package.add("frontend/src/pages/Login.jsx", LOGIN_JSX, area="frontend")
    package.add("frontend/src/pages/Dashboard.jsx", DASHBOARD_JSX, area="frontend")
    package.add("frontend/src/pages/ModulesIndex.jsx", MODULES_INDEX_JSX, area="frontend")
    package.add("frontend/src/pages/ModulePage.jsx", MODULE_PAGE_JSX, area="frontend")
    package.add("frontend/src/pages/EntityPage.jsx", ENTITY_PAGE_JSX, area="frontend")
    package.add("frontend/src/pages/AiHub.jsx", AI_HUB_JSX, area="frontend")
    package.add("frontend/src/pages/Reports.jsx", REPORTS_JSX, area="frontend")
    package.add("frontend/src/pages/AuditLog.jsx", AUDIT_JSX, area="frontend")
    package.add("frontend/src/pages/Settings.jsx", SETTINGS_JSX, area="frontend")
    package.add("frontend/src/pages/NotFound.jsx", NOTFOUND_JSX, area="frontend")

    # --- config/menu.js: ماژول‌ها، موجودیت‌ها، طرحواره فیلدها و نقاط AI --- #
    entities_by_module: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        entities_by_module.setdefault(entity["module_code"], []).append(entity)

    ai_by_module: dict[str, list[dict[str, Any]]] = {}
    for point in ai_points:
        ai_by_module.setdefault(point["module_code"], []).append(
            {"code": point["code"], "name": point["name"], "engine": point["engine"]}
        )

    menu_modules = []
    schemas: dict[str, Any] = {}
    for module in modules:
        module_entities = entities_by_module.get(module["code"], [])
        menu_modules.append(
            {
                "code": module["code"],
                "slug": module["slug"],
                "label_fa": module["label_fa"],
                "name_en": module.get("name_en", ""),
                "menu_group": module.get("menu_group", "سایر"),
                "description": module.get("description", ""),
                "color": context["section_meta"].get(module["code"][:1], {}).get("color", "#4f46e5"),
                "icon": context["section_meta"].get(module["code"][:1], {}).get("icon", "box"),
                "groups_count": context["module_stats"].get(module["code"], {}).get("groups", 0),
                "items_count": context["module_stats"].get(module["code"], {}).get("items", 0),
                "ai_points": context["module_stats"].get(module["code"], {}).get("ai", 0),
                "ai_capabilities": ai_by_module.get(module["code"], []),
                "entities": [
                    {
                        "table": e["table"],
                        "name": e["name"],
                        "label_fa": e["label_fa"],
                        "fields_count": len(e["fields"]),
                        "icon": e.get("icon", "file-text"),
                    }
                    for e in module_entities
                ],
            }
        )
        for entity in module_entities:
            schemas[entity["table"]] = _entity_schema_js(entity)

    menu_groups = sorted({m["menu_group"] for m in menu_modules})

    header = (
        "/**\n"
        f" * پیکربندی تولیدشده توسط سازنده ERP — {context['generated_at']}\n"
        f" *\n * ماژول‌ها: {len(menu_modules)} | موجودیت‌ها: {len(schemas)}\n"
        " * این فایل را دستی ویرایش نکنید؛ با ساخت مجدد بسته بازنویسی می‌شود.\n"
        " */\n\n"
    )

    # menu.js: منو، پرچم‌ها و فهرست ماژول‌ها (کوچک؛ در بسته اصلی)
    menu_js = (
        header
        + f"export const AI_ENABLED = {str(bool(ai_enabled)).lower()}\n\n"
        + f"export const PWA_ENABLED = {str(bool(include_pwa)).lower()}\n\n"
        + f"export const REPORT_TEMPLATES_ENABLED = {str(bool(report_templates)).lower()}\n\n"
        + "export const MENU_GROUPS = "
        + json.dumps(menu_groups, ensure_ascii=False, indent=2)
        + "\n\n"
        + "export const MODULES = "
        + json.dumps(menu_modules, ensure_ascii=False, indent=2)
        + "\n\nexport default { MENU_GROUPS, MODULES }\n"
    )
    package.add("frontend/src/config/menu.js", menu_js, area="frontend-config")

    # schemas.js: ساختار فیلدها (JSON فشرده؛ به‌صورت chunk تنبل بارگذاری می‌شود)
    schemas_js = (
        header
        + "export const SCHEMAS = "
        + json.dumps(schemas, ensure_ascii=False, separators=(",", ":"))
        + "\n\nexport default SCHEMAS\n"
    )
    package.add("frontend/src/config/schemas.js", schemas_js, area="frontend-config")

    package.add("frontend/src/lib/schemas.js", SCHEMAS_LOADER_JS, area="frontend")

    field_count = sum(len(schema["fields"]) for schema in schemas.values())
    package.add_rendered(
        "frontend/README-fa.md",
        FRONTEND_README,
        area="docs",
        modules_count=len(menu_modules),
        entities_count=len(schemas),
        fields_count=field_count,
        **common,
    )
