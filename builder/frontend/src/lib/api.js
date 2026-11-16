/**
 * کلاینت API سازنده ERP
 *
 * همه مسیرها نسبی‌اند تا هم در حالت توسعه (پروکسی Vite) و هم در حالت تولید
 * (سرو شدن dist توسط خود FastAPI) بدون تغییر کار کنند.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function request(path, options = {}) {
  const { method = 'GET', body, params, signal } = options
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
    })
  }

  let response
  try {
    response = await fetch(url.toString(), {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (error) {
    throw new ApiError(error?.message || 'اتصال به سرویس سازنده برقرار نشد', 0, null)
  }

  const text = await response.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = { detail: text.slice(0, 400) }
    }
  }

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || `خطای ${response.status}`
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status, payload)
  }
  return payload
}

export const api = {
  get: (path, params, signal) => request(path, { params, signal }),
  post: (path, body, signal) => request(path, { method: 'POST', body, signal }),
  put: (path, body, signal) => request(path, { method: 'PUT', body, signal }),
  delete: (path, signal) => request(path, { method: 'DELETE', signal }),
}

/** سلامت و متادیتای سرویس */
export const health = () => api.get('/health')
export const meta = () => api.get('/meta')

/** کاتالوگ چهارسطحی */
export const catalogApi = {
  all: (params) => api.get('/catalog', params),
  stats: () => api.get('/catalog/stats'),
  search: (q, limit = 60) => api.get('/catalog/search', { q, limit }),
  module: (code) => api.get(`/catalog/modules/${code}`),
  aiPoints: (params) => api.get('/catalog/ai-points', params),
  dependencies: (params) => api.get('/catalog/dependencies', params),
}

/** پریست‌های صنعتی */
export const presetsApi = {
  list: () => api.get('/presets'),
  apply: (key) => api.post(`/presets/${key}/apply`),
}

/** حل وابستگی‌ها و تحلیل انتخاب */
export const selectionApi = {
  resolve: (selection) => api.post('/resolve', { selection }),
  expand: (selection) => api.post('/selection/expand', { selection }),
}

/** دستیار هوشمند */
export const advisorApi = {
  recommend: (payload) => api.post('/advisor/recommend', payload),
  recommendFast: (payload) => api.post('/advisor/recommend-fast', payload),
  phases: (payload) => api.post('/advisor/phases', payload),
  chat: (payload) => api.post('/chat', payload),
}

/** پروژه‌ها */
export const projectsApi = {
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  create: (project) => api.post('/projects', project),
  update: (id, project) => api.put(`/projects/${id}`, project),
  remove: (id) => api.delete(`/projects/${id}`),
  phases: (id) => api.post(`/projects/${id}/phases`),
  /** ذخیره: در صورت داشتن id به‌روزرسانی، وگرنه ایجاد */
  save: (project) => (project.id ? api.put(`/projects/${project.id}`, project) : api.post('/projects', project)),
}

/** تولید و مرور بسته‌ها */
export const packagesApi = {
  generate: (project, saveProject = true) => api.post('/generate', { project, save_project: saveProject }),
  list: () => api.get('/packages'),
  manifest: (id) => api.get(`/packages/${id}/manifest`),
  tree: (id) => api.get(`/packages/${id}/tree`),
  file: (id, path) => api.get(`/packages/${id}/file`, { path }),
  remove: (id) => api.delete(`/packages/${id}`),
  downloadUrl: (id) => `${BASE}/packages/${id}/download`,
}

export default api
