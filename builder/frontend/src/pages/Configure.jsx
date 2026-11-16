import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import AdvisorPanel from '../components/AdvisorPanel.jsx'
import CatalogTree from '../components/CatalogTree.jsx'
import ChatPanel from '../components/ChatPanel.jsx'
import GenerateBar from '../components/GenerateBar.jsx'
import SelectionCart from '../components/SelectionCart.jsx'
import SettingsForm from '../components/SettingsForm.jsx'
import { projectsApi } from '../lib/api.js'
import { formatJalali, toPersianDigits } from '../lib/format.js'
import { useApp } from '../lib/store.jsx'

const TABS = [
  { key: 'catalog', label: 'کاتالوگ و انتخاب' },
  { key: 'settings', label: 'تنظیمات کارخانه' },
  { key: 'advisor', label: 'دستیار و گفت‌وگو' },
  { key: 'projects', label: 'پروژه‌های ذخیره‌شده' },
  { key: 'generate', label: 'تولید بسته' },
]

function ProjectsPanel({ onDone }) {
  const { projects, projectsLoading, refreshProjects, removeProject, notify } = useApp()
  const [detail, setDetail] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = async (project) => {
    setBusyId(project.id)
    try {
      const full = await projectsApi.get(project.id)
      const phases = await projectsApi.phases(project.id).catch(() => ({ phases: [], total_months: 0 }))
      setDetail({ ...full, phases: phases.phases || [], total_months: phases.total_months || 0 })
    } catch (error) {
      notify(error.message, 'error')
    } finally {
      setBusyId(null)
    }
  }

  const remove = async (project) => {
    try {
      await removeProject(project.id)
      setDetail(null)
    } catch (error) {
      notify(error.message, 'error')
    }
  }

  const clone = async (project) => {
    try {
      const copy = await projectsApi.save({
        name: `${project.name} (کپی)`,
        name_en: `${project.name_en || ''} (copy)`.trim(),
        description: project.description || '',
        industry: project.industry || '',
        settings: project.settings || {},
        selection: project.selection || {},
      })
      await refreshProjects()
      notify(`پروژه «${copy.name}» ذخیره شد`, 'ok')
    } catch (error) {
      notify(error.message, 'error')
    }
  }

  useEffect(() => {
    refreshProjects()
  }, [refreshProjects])

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">پروژه‌های ذخیره‌شده</h3>
          <p className="card-subtitle">
            هر پروژه شامل انتخاب ماژول‌ها، تنظیمات و اطلاعات کارخانه است؛ برای بازتولید بسته یا فازبندی استفاده کنید.
          </p>
        </div>
        <button type="button" className="btn ghost sm" onClick={refreshProjects}>
          ↻ تازه‌سازی
        </button>
      </div>

      {projectsLoading && !projects.length ? (
        Array.from({ length: 3 }).map((_, index) => <div className="skeleton" key={index} style={{ height: 62, marginBottom: 8 }} />)
      ) : projects.length === 0 ? (
        <div className="empty">
          هنوز پروژه‌ای ذخیره نشده است. در تب «تولید بسته» گزینه ذخیره پروژه را روشن کنید.
        </div>
      ) : (
        <div className="table-scroll" style={{ maxHeight: 420 }}>
          <table className="data">
            <thead>
              <tr>
                <th>نام پروژه</th>
                <th>صنعت</th>
                <th>انتخاب</th>
                <th>تنظیمات</th>
                <th>ایجاد</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <strong>{project.name}</strong>
                    <div className="tiny dim">{project.id}</div>
                  </td>
                  <td className="tiny">{project.industry || '—'}</td>
                  <td className="tiny muted">
                    {toPersianDigits(project.selection?.modules?.length || 0)} ماژول ·{' '}
                    {toPersianDigits(project.selection?.ai_points?.length || 0)} AI
                  </td>
                  <td className="tiny muted">{toPersianDigits(Object.keys(project.settings || {}).length)} کلید</td>
                  <td className="tiny dim num">{project.created_at ? formatJalali(project.created_at) : '—'}</td>
                  <td>
                    <div className="row" style={{ gap: 5, justifyContent: 'flex-end' }}>
                      <button type="button" className="btn ghost xs" onClick={() => load(project)} disabled={busyId === project.id}>
                        {busyId === project.id ? '…' : 'جزئیات/فازها'}
                      </button>
                      <button type="button" className="btn ghost xs" onClick={() => clone(project)}>
                        کپی
                      </button>
                      <button type="button" className="btn ghost xs" onClick={() => remove(project)}>
                        حذف
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {detail && (
        <div className="mt-18">
          <hr className="sep" />
          <div className="between mb-10">
            <div>
              <h4 className="card-title">{detail.name}</h4>
              <p className="card-subtitle mono" style={{ direction: 'ltr', textAlign: 'right' }}>
                {detail.id}
              </p>
            </div>
            <button
              type="button"
              className="btn primary sm"
              onClick={async () => {
                try {
                  const loaded = await projectsApi.load(detail.id)
                  onDone?.(loaded)
                  notify(`پروژه «${detail.name}» باز شد و به انتخاب اعمال شد`, 'ok')
                } catch (error) {
                  notify(error.message, 'error')
                }
              }}
            >
              باز کردن در پیکربندی فعلی
            </button>
          </div>

          <dl className="kv mb-14">
            <dt>نام انگلیسی</dt>
            <dd>{detail.name_en || '—'}</dd>
            <dt>توضیح</dt>
            <dd>{detail.description || '—'}</dd>
            <dt>صنعت</dt>
            <dd>{detail.industry || '—'}</dd>
            <dt>ماژول‌های انتخابی</dt>
            <dd>{toPersianDigits(detail.selection?.modules?.length || 0)}</dd>
            <dt>نقاط AI</dt>
            <dd>{toPersianDigits(detail.selection?.ai_points?.length || 0)}</dd>
          </dl>

          {detail.phases?.length ? (
            <>
              <div className="small muted mb-10">
                فازبندی استقرار — مجموع {toPersianDigits(detail.total_months)} ماه
              </div>
              <div className="table-scroll" style={{ maxHeight: 340 }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th>فاز</th>
                      <th>عنوان</th>
                      <th>مدت</th>
                      <th>ماژول</th>
                      <th>AI</th>
                      <th>تحویل‌دادنی‌ها</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.phases.map((phase) => (
                      <tr key={phase.order}>
                        <td className="num">{toPersianDigits(phase.order)}</td>
                        <td>
                          <strong>{phase.title}</strong>
                          <div className="tiny dim">{phase.description}</div>
                        </td>
                        <td className="num">{toPersianDigits(phase.duration_months)} ماه</td>
                        <td className="num">{toPersianDigits((phase.modules || []).length)}</td>
                        <td className="num">{toPersianDigits((phase.ai_points || []).length)}</td>
                        <td className="tiny muted">{(phase.deliverables || []).join('، ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="empty">برای این پروژه فازبندی ذخیره نشده است.</div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Configure() {
  const { loadProject } = useApp()
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'catalog'

  const setTab = (key) => {
    const next = new URLSearchParams(params)
    next.set('tab', key)
    setParams(next, { replace: true })
  }

  return (
    <div className="page">
      <div className="between mb-14">
        <div>
          <h1 style={{ fontSize: 20 }}>پیکربندی بسته ERP</h1>
          <p className="card-subtitle">
            انتخاب ماژول‌ها در سمت چپ، تنظیمات و دستیار هوشمند در همین صفحه — خروجی نهایی یک بسته استقرار کامل است.
          </p>
        </div>
        <div className="tabs" style={{ marginBottom: 0 }}>
          {TABS.map((item) => (
            <button key={item.key} type="button" className={tab === item.key ? 'active' : ''} onClick={() => setTab(item.key)}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'catalog' && (
        <div className="grid cols-2">
          <CatalogTree />
          <SelectionCart />
        </div>
      )}

      {tab === 'settings' && <SettingsForm />}

      {tab === 'advisor' && (
        <div className="grid cols-2">
          <AdvisorPanel />
          <div className="col">
            <ChatPanel />
            <SelectionCart />
          </div>
        </div>
      )}

      {tab === 'projects' && <ProjectsPanel onDone={(project) => {
        loadProject(project)
        setTab('catalog')
      }} />}

      {tab === 'generate' && (
        <div className="grid cols-2">
          <GenerateBar />
          <div className="col">
            <SelectionCart />
            <SettingsForm />
          </div>
        </div>
      )}
    </div>
  )
}
