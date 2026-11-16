/**
 * آزمون دود رابط کاربری سازنده ERP
 *
 * این اسکریپت داده «واقعی» را از API سازنده می‌گیرد، وضعیت فروشگاه را بازسازی
 * می‌کند و هر صفحه/کامپوننت را با react-dom/server رندر می‌کند. هدف، گرفتن
 * سه دسته خطاست:
 *   ۱) عدم تطابق شکل پاسخ API با آنچه کامپوننت می‌خواند (undefined در خروجی)
 *   ۲) خطای زمان اجرا در JSX (property access روی null)
 *   ۳) نشتی مقدار خام مثل [object Object] یا NaN در متن فارسی
 *
 * اجرا:  npm run smoke            (نیاز به سرویس در حال اجرا روی پورت ۸۰۰۰)
 *        SMOKE_API=http://host:port/api npm run smoke
 */
import './globals-shim.js'

import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import AppContext from '../src/lib/store.jsx'
import { buildHierarchy, derive, emptySelection, selectionFromModules } from '../src/lib/selection.js'

import TopBar from '../src/components/TopBar.jsx'
import Toasts from '../src/components/Toasts.jsx'
import StatCard from '../src/components/StatCard.jsx'
import PresetGrid from '../src/components/PresetGrid.jsx'
import CatalogTree from '../src/components/CatalogTree.jsx'
import SelectionCart from '../src/components/SelectionCart.jsx'
import SettingsForm from '../src/components/SettingsForm.jsx'
import AdvisorPanel from '../src/components/AdvisorPanel.jsx'
import ChatPanel from '../src/components/ChatPanel.jsx'
import GenerateBar from '../src/components/GenerateBar.jsx'
import Home from '../src/pages/Home.jsx'
import Configure from '../src/pages/Configure.jsx'
import Engines from '../src/pages/Engines.jsx'
import Packages from '../src/pages/Packages.jsx'
import PackageDetail, { FileTree } from '../src/pages/PackageDetail.jsx'

const BASE = process.env.SMOKE_API || 'http://localhost:8000/api'

const FORBIDDEN = ['>undefined<', '[object Object]', 'NaN', '>null<']
const results = []
let failures = 0

function check(name, markup, { min = 120, must = [], forbidden = FORBIDDEN } = {}) {
  const problems = []
  if (!markup || markup.length < min) problems.push(`خروجی کوتاه است (${markup?.length || 0} < ${min})`)
  forbidden.forEach((token) => {
    if (markup.includes(token)) problems.push(`نشتی «${token}»`)
  })
  must.forEach((needle) => {
    if (!markup.includes(needle)) problems.push(`مقدار انتظار‌رفته «${needle}» دیده نشد`)
  })
  if (problems.length) {
    failures += 1
    results.push({ name, ok: false, problems, size: markup?.length || 0 })
  } else {
    results.push({ name, ok: true, problems: [], size: markup.length })
  }
}

function render(name, element, options = {}) {
  try {
    const markup = renderToStaticMarkup(element)
    check(name, markup, options)
  } catch (error) {
    failures += 1
    results.push({ name, ok: false, problems: [`خطای رندر: ${error.message}`], size: 0 })
  }
}

/** ساخت مقدار فروشگاه از داده واقعی API */
function buildStoreValue(data) {
  const hierarchy = buildHierarchy(data.catalog)
  const selection = selectionFromModules(hierarchy, data.presetModules, data.presetAi)
  const derived = derive(hierarchy, selection)
  const noop = () => {}
  return {
    healthInfo: data.health,
    meta: data.meta,
    catalog: data.catalog,
    hierarchy,
    derived,
    loading: { meta: false, catalog: false },
    error: '',
    selection,
    setSelection: noop,
    resolution: data.resolution,
    resolving: false,
    hasSelection: derived.modules.size > 0,
    settings: data.settings,
    project: data.project,
    presets: data.presets,
    packages: data.packages,
    projects: data.projects,
    projectsLoading: false,
    generating: false,
    lastPackage: data.lastPackage,
    toasts: [{ id: 't1', message: 'آزمون دود رابط کاربری', kind: 'ok' }],
    notify: noop,
    dismissToast: noop,
    toggleCode: noop,
    toggleAi: noop,
    clearSelection: noop,
    selectEverything: noop,
    applyPreset: async () => null,
    applyAdvisor: noop,
    patchSettings: noop,
    patchProject: noop,
    generate: async () => null,
    refreshPackages: async () => {},
    refreshProjects: async () => {},
    removePackage: async () => true,
    removeProject: async () => true,
    loadProject: noop,
    askAssistant: async () => ({ answer: 'پاسخ آزمون', source: 'heuristic' }),
  }
}

function withStore(value, children, route = '/') {
  return (
    <AppContext.Provider value={value}>
      <MemoryRouter initialEntries={[route]}>
        {children}
      </MemoryRouter>
    </AppContext.Provider>
  )
}

async function get(path) {
  const response = await fetch(BASE + path)
  if (!response.ok) throw new Error(`${path} → ${response.status}`)
  return response.json()
}

async function post(path, body) {
  const response = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${path} → ${response.status}`)
  return response.json()
}

async function main() {
  const health = await get('/health')
  const meta = await get('/meta')
  const catalog = await get('/catalog?depth=4')
  const presetsPayload = await get('/presets')
  const packagesPayload = await get('/packages')
  const projectsPayload = await get('/projects')

  const presets = presetsPayload.presets || []
  const packages = packagesPayload.packages || []
  const projects = projectsPayload.projects || []

  // یک پریست واقعی را حل می‌کنیم تا resolution واقعی داشته باشیم
  const presetKey = presets.find((item) => item.key === 'automotive')?.key || presets[0]?.key
  const applied = presetKey ? await post(`/presets/${presetKey}/apply`) : { modules: [], ai_points: [] }
  const resolution = await post('/resolve', {
    selection: { ...emptySelection(), modules: applied.modules || [], ai_points: applied.ai_points || [] },
  })

  const settings = { ...meta.default_settings, ...(applied.settings || {}) }
  const project = {
    name: 'آزمون دود ERP',
    name_en: 'ERP Smoke Test',
    description: 'پروژه نمونه برای آزمون رندر رابط کاربری',
    preset_key: presetKey,
  }

  const data = {
    health,
    meta,
    catalog,
    presets,
    packages,
    projects,
    resolution,
    settings,
    project,
    presetModules: applied.modules || [],
    presetAi: applied.ai_points || [],
    lastPackage: packages[0]
      ? {
          package_id: packages[0].package_id,
          file_count: packages[0].file_count,
          line_count: packages[0].line_count,
          zip_size_bytes: packages[0].zip_size_bytes,
          stats: packages[0].stats,
          notes: ['بسته نمونه برای آزمون رندر'],
        }
      : null,
  }

  const value = buildStoreValue(data)

  /* ------------------------------------------------------------- کامپوننت‌ها */
  render('TopBar', withStore(value, <TopBar />), {
    must: [meta.app_name_fa, 'پیکربندگر', 'موتورهای AI', 'انتخاب فعال'],
  })
  render('Toasts', withStore(value, <Toasts />), { must: ['آزمون دود رابط کاربری'] })
  render('StatCard', withStore(value, <StatCard label="ماژول" value={42} hint="آزمون" />), {
    min: 60,
    must: ['ماژول', '۴۲', 'آزمون'],
  })
  render('PresetGrid', withStore(value, <PresetGrid />), {
    must: [presets[0]?.name || 'پریست'],
  })
  render('CatalogTree', withStore(value, <CatalogTree />), {
    must: ['جست‌وجو'],
  })
  render('SelectionCart', withStore(value, <SelectionCart />), {
    must: ['برآورد'],
  })
  // در فرم تنظیمات فقط تب فعال رندر می‌شود (پیش‌فرض: هویت کارخانه)
  render('SettingsForm', withStore(value, <SettingsForm />), {
    must: ['هویت کارخانه', 'نام کارخانه', 'شناسه ملی', 'نام پروژه'],
  })
  render('AdvisorPanel', withStore(value, <AdvisorPanel />), {
    must: ['دستیار هوشمند انتخاب ماژول'],
  })
  render('ChatPanel', withStore(value, <ChatPanel />), {
    must: ['گفت‌وگو با دستیار سازنده'],
  })
  render('GenerateBar', withStore(value, <GenerateBar />), {
    must: ['تولید بسته استقرار'],
  })

  /* ------------------------------------------------------------------- صفحه‌ها */
  render('Home', withStore(value, <Home />), {
    min: 4000,
    must: ['سازنده ERP هوشمند کارخانه‌ای', 'پریست‌های صنعتی', 'موتورهای هوش مصنوعی'],
  })
  ;['catalog', 'settings', 'advisor', 'projects', 'generate'].forEach((tab) => {
    render(`Configure?tab=${tab}`, withStore(value, <Configure />, `/configure?tab=${tab}`), {
      min: 1200,
    })
  })
  render('Engines', withStore(value, <Engines />, '/engines'), {
    min: 2500,
    must: ['موتورهای هوش مصنوعی', meta.ai_engines[0].name_fa],
  })
  render('Packages', withStore(value, <Packages />, '/packages'), {
    min: 800,
    must: ['بسته‌های تولیدشده'],
  })

  /* ------------------------------------------------------ جزئیات بسته (واقعی) */
  if (packages.length) {
    const packageId = packages[0].package_id
    const [detail, manifest, treePayload] = await Promise.all([
      get(`/packages/${packageId}`),
      get(`/packages/${packageId}/manifest`).catch(() => null),
      get(`/packages/${packageId}/tree`).catch(() => ({ tree: [] })),
    ])
    const tree = treePayload.tree || []
    const firstFile = (() => {
      let found = null
      const walk = (nodes) => {
        nodes.forEach((node) => {
          if (found) return
          if (node.type === 'file') found = node
          else walk(node.children || [])
        })
      }
      walk(tree)
      return found
    })()

    // PackageDetail داده خود را در effect می‌گیرد؛ در SSR فقط اسکلت رندر می‌شود،
    // بنابراین اجزای اصلی آن (درخت فایل‌ها) جداگانه با داده واقعی آزمون می‌شوند.
    render(
      'PackageDetail (skeleton)',
      withStore(value, (
        <Routes>
          <Route path="/packages/:packageId" element={<PackageDetail />} />
        </Routes>
      ), `/packages/${packageId}`),
      { min: 100 },
    )
    render('FileTree', withStore(value, (
      <FileTree nodes={tree} active={null} onOpen={() => {}} openSet={new Set(['backend'])} toggleDir={() => {}} />
    )), {
      min: 500,
      must: ['backend'],
      forbidden: ['>undefined<', '[object Object]', 'NaN'],
    })

    if (manifest) {
      const moduleRow = (manifest.modules || [])[0]
      check('manifest.modules shape', JSON.stringify(moduleRow), {
        min: 40,
        must: ['"code"', '"label_fa"', '"slug"', '"entities"', '"ai_points"'],
        forbidden: [],
      })
      check('detail.top_level shape', JSON.stringify(detail.top_level || []), {
        min: 20,
        must: ['"name"', '"path"', '"type"'],
        forbidden: [],
      })
    }
    if (firstFile) {
      const filePayload = await get(`/packages/${packageId}/file?path=${encodeURIComponent(firstFile.path)}`)
      check('package file content', JSON.stringify(filePayload), {
        min: 40,
        must: ['"path"', '"content"', '"lines"'],
        forbidden: [],
      })
    }
  } else {
    results.push({ name: 'PackageDetail', ok: false, problems: ['هیچ بسته‌ای برای آزمون وجود ندارد'], size: 0 })
    failures += 1
  }

  /* -------------------------------------------------- قرارداد داده فروشگاه */
  const contract = [
    ['sections', value.catalog.sections.length, 22],
    ['modules', value.hierarchy.moduleByCode.size, 130],
    ['groups', value.hierarchy.groupByCode.size, 515],
    ['items', value.hierarchy.itemByCode.size, 2157],
    ['ai_items', value.hierarchy.aiItems.size, 266],
    ['derived.modules', value.derived.modules.size, null],
    ['derived.items', value.derived.items.size, null],
    ['resolution.counts.modules', value.resolution?.counts?.modules, null],
    ['resolution.counts.tables', value.resolution?.counts?.tables, null],
    ['presets', value.presets.length, 11],
  ]
  contract.forEach(([name, actual, expected]) => {
    if (actual === undefined || actual === null) {
      failures += 1
      results.push({ name: `contract:${name}`, ok: false, problems: ['مقدار تعریف‌نشده'], size: 0 })
      return
    }
    if (expected !== null && actual !== expected) {
      failures += 1
      results.push({ name: `contract:${name}`, ok: false, problems: [`انتظار ${expected} بود، ${actual} دیده شد`], size: 0 })
      return
    }
    results.push({ name: `contract:${name}`, ok: true, problems: [], size: actual })
  })

  /* ------------------------------------------------------------------- گزارش */
  results.forEach((item) => {
    const mark = item.ok ? 'PASS' : 'FAIL'
    console.log(`  ${mark}  ${item.name} (${item.size}${item.ok && item.name.startsWith('contract:') ? '' : ' بایت'})`)
    item.problems.forEach((problem) => console.log(`        ${problem}`))
  })
  console.log('')
  console.log(`failures: ${failures}`)
  console.log(`api: ${BASE}`)
  process.exit(failures ? 1 : 0)
}

main().catch((error) => {
  console.error('آزمون دود اجرا نشد:', error.message)
  process.exit(2)
})
