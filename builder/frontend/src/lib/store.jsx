/**
 * وضعیت سراسری سازنده ERP
 *
 * یک Context شامل: متادیتای سرویس، کاتالوگ کامل، انتخاب کاربر (با ذخیره در
 * localStorage)، نتیجه حل وابستگی‌ها از سرور، تنظیمات کارخانه، وضعیت تولید
 * بسته و پیام‌های موقت.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import {
  advisorApi,
  catalogApi,
  health,
  meta as fetchMeta,
  packagesApi,
  presetsApi,
  projectsApi,
  selectionApi,
} from './api.js'
import { buildHierarchy, derive, emptySelection, selectionFromModules, toggle, toggleAiPoint } from './selection.js'

const AppContext = createContext(null)
const STORAGE_KEY = 'erp-builder.state.v1'

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AppProvider({ children }) {
  const stored = useRef(loadStored()).current

  const [healthInfo, setHealthInfo] = useState(null)
  const [meta, setMeta] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const [loading, setLoading] = useState({ meta: true, catalog: true })
  const [error, setError] = useState('')
  const [toasts, setToasts] = useState([])

  const [selection, setSelection] = useState(stored?.selection || emptySelection())
  const [resolution, setResolution] = useState(null)
  const [resolving, setResolving] = useState(false)
  const [settings, setSettings] = useState(stored?.settings || {})
  const [project, setProject] = useState(
    stored?.project || {
      name: 'ERP کارخانه من',
      name_en: 'My Factory ERP',
      description: '',
      preset_key: null,
    },
  )
  const [presets, setPresets] = useState([])
  const [packages, setPackages] = useState([])
  const [generating, setGenerating] = useState(false)
  const [lastPackage, setLastPackage] = useState(null)
  const [projects, setProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)

  const notify = useCallback((message, kind = 'info', timeout = 4200) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((current) => [...current, { id, message, kind }])
    window.setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), timeout)
  }, [])

  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  /* -------------------------------------------------- بارگذاری اولیه داده */
  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const [healthPayload, metaPayload] = await Promise.all([health(), fetchMeta()])
        if (!alive) return
        setHealthInfo(healthPayload)
        setMeta(metaPayload)
        setLoading((state) => ({ ...state, meta: false }))
        setSettings((current) => {
          const base = { ...(metaPayload.default_settings || {}) }
          return { ...base, ...current }
        })
      } catch (err) {
        if (!alive) return
        setError(err.message || 'بارگذاری متادیتا ناموفق بود')
        setLoading((state) => ({ ...state, meta: false }))
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const payload = await catalogApi.all({ depth: 4 })
        if (!alive) return
        setCatalog(payload)
        setLoading((state) => ({ ...state, catalog: false }))
      } catch (err) {
        if (!alive) return
        setError(err.message || 'بارگذاری کاتالوگ ناموفق بود')
        setLoading((state) => ({ ...state, catalog: false }))
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    let alive = true
    presetsApi
      .list()
      .then((payload) => alive && setPresets(payload.presets || []))
      .catch(() => undefined)
    packagesApi
      .list()
      .then((payload) => alive && setPackages(payload.packages || []))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  /* ------------------------------------------------------- ذخیره محلی */
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ selection, settings, project }))
    } catch {
      /* حافظه محلی در دسترس نیست */
    }
  }, [selection, settings, project])

  /* -------------------------------------------- حل وابستگی‌ها (debounce) */
  const hierarchy = useMemo(() => (catalog ? buildHierarchy(catalog) : null), [catalog])
  const derived = useMemo(() => (hierarchy ? derive(hierarchy, selection) : null), [hierarchy, selection])

  const hasSelection = Boolean(derived && derived.modules.size > 0)

  useEffect(() => {
    if (!hierarchy) return undefined
    if (!hasSelection) {
      setResolution(null)
      return undefined
    }
    const timer = window.setTimeout(async () => {
      setResolving(true)
      try {
        const payload = await selectionApi.resolve({ ...selection, mode: selection.mode || 'custom' })
        setResolution(payload)
      } catch (err) {
        notify(err.message || 'حل وابستگی‌ها ناموفق بود', 'error')
      } finally {
        setResolving(false)
      }
    }, 380)
    return () => window.clearTimeout(timer)
  }, [hierarchy, hasSelection, selection, notify])

  /* --------------------------------------------------------- عملیات‌ها */
  const toggleCode = useCallback(
    (code) => {
      if (!hierarchy) return
      setSelection((current) => toggle(hierarchy, current, code))
    },
    [hierarchy],
  )

  const toggleAi = useCallback(
    (code) => {
      if (!hierarchy) return
      setSelection((current) => toggleAiPoint(hierarchy, current, code))
    },
    [hierarchy],
  )

  const clearSelection = useCallback(() => {
    setSelection(emptySelection())
    setProject((current) => ({ ...current, preset_key: null }))
  }, [])

  const selectEverything = useCallback(() => setSelection(emptySelection('all')), [])

  const applyPreset = useCallback(
    async (key) => {
      try {
        const payload = await presetsApi.apply(key)
        const next = hierarchy
          ? selectionFromModules(hierarchy, payload.modules || [], payload.ai_points || [])
          : { ...emptySelection(), modules: payload.modules || [], ai_points: payload.ai_points || [] }
        setSelection(next)
        setProject((current) => ({ ...current, preset_key: key }))
        if (payload.settings) {
          setSettings((current) => ({ ...current, ...payload.settings }))
        }
        if (payload.resolution) setResolution(payload.resolution)
        notify(`پریست «${payload.preset_name}» اعمال شد`, 'ok')
        return payload
      } catch (err) {
        notify(err.message || 'اعمال پریست ناموفق بود', 'error')
        return null
      }
    },
    [hierarchy, notify],
  )

  const applyAdvisor = useCallback(
    (modules, aiPoints, note) => {
      if (!hierarchy) return
      setSelection(selectionFromModules(hierarchy, modules, aiPoints))
      if (note) notify(note, 'ok')
    },
    [hierarchy, notify],
  )

  const patchSettings = useCallback((patch) => {
    setSettings((current) => ({ ...current, ...patch }))
  }, [])

  const patchProject = useCallback((patch) => {
    setProject((current) => ({ ...current, ...patch }))
  }, [])

  const refreshPackages = useCallback(async () => {
    try {
      const payload = await packagesApi.list()
      setPackages(payload.packages || [])
    } catch (err) {
      notify(err.message || 'دریافت فهرست بسته‌ها ناموفق بود', 'error')
    }
  }, [notify])

  const refreshProjects = useCallback(async () => {
    setProjectsLoading(true)
    try {
      const payload = await projectsApi.list()
      setProjects(payload.projects || [])
    } catch {
      /* پروژه‌ها اختیاری‌اند */
    } finally {
      setProjectsLoading(false)
    }
  }, [])

  const removeProject = useCallback(
    async (projectId) => {
      try {
        await projectsApi.remove(projectId)
        setProjects((current) => current.filter((item) => item.id !== projectId))
        notify(`پروژه ${projectId} حذف شد`, 'ok')
        return true
      } catch (err) {
        notify(err.message || 'حذف پروژه ناموفق بود', 'error')
        return false
      }
    },
    [notify],
  )

  /** بازگرداندن یک پروژه ذخیره‌شده در پیکربندی جاری */
  const loadProject = useCallback((project) => {
    const raw = project?.selection || {}
    setSelection(
      hierarchy
        ? selectionFromModules(hierarchy, raw.modules || [], raw.ai_points || [], {
            groups: raw.groups || [],
            items: raw.items || [],
          })
        : { ...emptySelection(), ...raw },
    )
    if (project.settings && Object.keys(project.settings).length) {
      setSettings((current) => ({ ...current, ...project.settings }))
    }
    setProject((current) => ({
      ...current,
      id: project.id || current.id,
      name: project.name || current.name,
      name_en: project.name_en || current.name_en,
      description: project.description || '',
      preset_key: project.preset_key || null,
    }))
  }, [hierarchy])

  const generate = useCallback(
    async ({ saveProject = true } = {}) => {
      if (!hasSelection) {
        notify('دست‌کم یک ماژول انتخاب کنید', 'error')
        return null
      }
      setGenerating(true)
      try {
        const payload = {
          project: {
            name: project.name || 'ERP کارخانه',
            name_en: project.name_en || 'Factory ERP',
            description: project.description || '',
            preset_key: project.preset_key || null,
            selection: { ...selection, mode: selection.mode || 'custom' },
            settings,
          },
          save_project: saveProject,
        }
        const result = await packagesApi.generate(payload.project, saveProject)
        setLastPackage(result)
        await refreshPackages()
        if (saveProject) refreshProjects()
        notify(
          `بسته «${result.package_id}» با ${result.file_count.toLocaleString('en-US')} فایل ساخته شد`,
          'ok',
          6000,
        )
        return result
      } catch (err) {
        notify(err.message || 'تولید بسته ناموفق بود', 'error', 7000)
        return null
      } finally {
        setGenerating(false)
      }
    },
    [hasSelection, notify, project, refreshPackages, refreshProjects, selection, settings],
  )

  const removePackage = useCallback(
    async (packageId) => {
      try {
        await packagesApi.remove(packageId)
        await refreshPackages()
        notify(`بسته ${packageId} حذف شد`, 'ok')
        return true
      } catch (err) {
        notify(err.message || 'حذف بسته ناموفق بود', 'error')
        return false
      }
    },
    [notify, refreshPackages],
  )

  const askAssistant = useCallback(
    async (message, history = []) => {
      try {
        const payload = await advisorApi.chat({
          message,
          history,
          context: {
            selected_modules: [...(derived?.modules || [])],
            counts: resolution?.counts || null,
            settings: {
              industry: settings.industry,
              employees_count: settings.employees_count,
              shifts_per_day: settings.shifts_per_day,
            },
          },
        })
        return payload
      } catch (err) {
        notify(err.message || 'پاسخ دستیار ناموفق بود', 'error')
        return { answer: 'دستیار در دسترس نیست؛ لطفاً دوباره تلاش کنید.', llm_used: false, source: 'error' }
      }
    },
    [derived, notify, resolution, settings],
  )

  const value = useMemo(
    () => ({
      healthInfo,
      meta,
      catalog,
      hierarchy,
      derived,
      loading,
      error,
      selection,
      setSelection,
      resolution,
      resolving,
      hasSelection,
      settings,
      project,
      presets,
      packages,
      projects,
      generating,
      lastPackage,
      toasts,
      notify,
      dismissToast,
      toggleCode,
      toggleAi,
      clearSelection,
      selectEverything,
      applyPreset,
      applyAdvisor,
      patchSettings,
      patchProject,
      generate,
      refreshPackages,
      refreshProjects,
      removePackage,
      removeProject,
      loadProject,
      projectsLoading,
      askAssistant,
    }),
    [
      askAssistant, applyAdvisor, applyPreset, catalog, clearSelection, derived, dismissToast, error,
      generate, hasSelection, healthInfo, hierarchy, lastPackage, loadProject, loading, meta, notify,
      packages, patchProject, patchSettings, presets, project, projects, projectsLoading,
      refreshPackages, refreshProjects, removePackage, removeProject, resolution, resolving,
      selectEverything, selection, settings, toggleAi, toggleCode, toasts, generating,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp باید داخل AppProvider استفاده شود')
  return context
}

/** آمار انتخاب برای نمایش سریع */
export function useSelectionSummary() {
  const { derived, resolution, meta } = useApp()
  return useMemo(() => {
    const local = {
      sections: derived?.sections.size || 0,
      modules: derived?.modules.size || 0,
      groups: derived?.groups.size || 0,
      items: derived?.items.size || 0,
      ai_points: derived?.ai.size || 0,
    }
    const server = resolution?.counts || null
    return {
      ...local,
      tables: server?.tables ?? null,
      fields: server?.fields ?? null,
      estimated_files: server?.estimated_files ?? null,
      ai_engines: server?.ai_engines ?? null,
      auto_added: resolution?.auto_added || [],
      reasons: resolution?.reasons || {},
      coverage: resolution?.sections || [],
      totals: meta?.counts || null,
    }
  }, [derived, meta, resolution])
}

export default AppContext
