# -*- coding: utf-8 -*-
"""روت‌های REST API پلتفرم سازنده ERP."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from ..ai.advisor import GOAL_MODULES, advise, build_phases, recommend_modules
from ..ai.llm import chat, is_configured
from ..ai.registry import ENGINES, capability_catalog, engine_summary
from ..catalog.registry import ai_points as catalog_ai_points
from ..catalog.registry import catalog, index, search as catalog_search, stats as catalog_stats
from ..config import (
    APP_NAME,
    APP_NAME_FA,
    APP_VERSION,
    AVALAI_API_KEY,
    AVALAI_BASE_URL,
    AVALAI_MODEL,
    CATALOG_VERSION,
    DB_DRIVERS,
    DEFAULT_FACTORY_SETTINGS,
    DEPLOY_TARGETS,
    OUTPUT_DIR,
    QUEUE_DRIVERS,
    STORAGE_DRIVERS,
)
from ..presets import preset_list
from ..domain.registry import (
    SUPPORT_MODULES,
    SYSTEM_MODULES,
    coverage_report,
    resolve_modules,
    specs_for_modules,
)
from ..projects import delete_project, get_project, list_projects, save_project
from ..schemas import (
    AdvisorRequest,
    ChatRequest,
    GenerateRequest,
    ProjectConfig,
    ResolveRequest,
    Selection,
)
from ..selection import ai_points_detail, coverage_by_section, expand_selection, resolve

router = APIRouter(prefix="/api")


# --------------------------------------------------------------------------- #
# سلامت و متادیتا
# --------------------------------------------------------------------------- #
@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": APP_NAME,
        "app_fa": APP_NAME_FA,
        "version": APP_VERSION,
        "catalog_version": CATALOG_VERSION,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "avalai_configured": is_configured(),
    }


@router.get("/meta")
def meta() -> dict[str, Any]:
    """متادیتای لازم برای رابط کاربری (گزینه‌ها، آمار، وضعیت)."""
    idx = index()
    return {
        "app_name": APP_NAME,
        "app_name_fa": APP_NAME_FA,
        "version": APP_VERSION,
        "catalog_version": CATALOG_VERSION,
        "counts": idx.counts(),
        "db_drivers": DB_DRIVERS,
        "queue_drivers": QUEUE_DRIVERS,
        "storage_drivers": STORAGE_DRIVERS,
        "deploy_targets": DEPLOY_TARGETS,
        "system_modules": SYSTEM_MODULES,
        "default_settings": DEFAULT_FACTORY_SETTINGS,
        "ai_engines": [
            {
                "key": engine.key,
                "name_fa": engine.name_fa,
                "name_en": engine.name_en,
                "category": engine.category,
                "algorithms": engine.algorithms,
                "endpoint": engine.endpoint,
                "uses_llm": engine.uses_llm,
                "realtime": engine.realtime,
                "metrics": engine.metrics,
                "description": engine.description,
            }
            for engine in ENGINES.values()
        ],
        "advisor_goals": advisor_goals(),
        "industries": [
            {"id": preset["key"], "label": preset["name"], "note": preset["description"]}
            for preset in preset_list()
        ],
        "avalai": {
            "configured": is_configured(),
            "base_url": AVALAI_BASE_URL,
            "model": AVALAI_MODEL,
            "key_set": bool(AVALAI_API_KEY),
        },
        "domain_coverage": coverage_report(),
    }


# --------------------------------------------------------------------------- #
# کاتالوگ
# --------------------------------------------------------------------------- #
@router.get("/catalog")
def get_catalog(
    section: str | None = Query(default=None, description="فقط یک بخش مشخص (مثلاً A)"),
    depth: int = Query(default=4, ge=1, le=4, description="عمق بازگردانی"),
) -> dict[str, Any]:
    sections = catalog()
    if section:
        section = section.strip().upper()
        sections = [s for s in sections if s["code"] == section]
        if not sections:
            raise HTTPException(status_code=404, detail=f"بخش {section} یافت نشد")

    if depth < 4:
        trimmed = []
        for sec in sections:
            sec_copy = {k: v for k, v in sec.items() if k != "modules"}
            if depth >= 2:
                sec_copy["modules"] = []
                for mod in sec["modules"]:
                    mod_copy = {k: v for k, v in mod.items() if k != "groups"}
                    if depth >= 3:
                        mod_copy["groups"] = [
                            {k: v for k, v in grp.items() if k != "items"} for grp in mod["groups"]
                        ]
                    sec_copy["modules"].append(mod_copy)
            trimmed.append(sec_copy)
        sections = trimmed

    return {"sections": sections, "stats": catalog_stats()}


@router.get("/catalog/stats")
def get_stats() -> dict[str, Any]:
    return catalog_stats()


@router.get("/catalog/search")
def search(q: str = Query(min_length=1), limit: int = Query(default=60, ge=1, le=300)) -> dict[str, Any]:
    results = catalog_search(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


def _module_dependencies(module_code: str) -> list[dict[str, Any]]:
    """وابستگی‌های یک ماژول: از زیرمجموعه‌های کاتالوگ و نگاشت پشتیبانی دامنه."""
    idx = index()
    module = idx.modules.get(module_code)
    if not module:
        return []

    found: dict[str, str] = {}
    for group in module["groups"]:
        for item in group["items"]:
            for dep in item.get("deps") or []:
                target = str(dep)
                while target and target not in idx.modules and "." in target:
                    target = target.rsplit(".", 1)[0]
                if target and target in idx.modules and target != module_code:
                    found.setdefault(target, f"وابستگی زیرمجموعه {item['code']}")

    for support in SUPPORT_MODULES.get(module_code, []):
        if support in idx.modules and support != module_code:
            found.setdefault(support, "ماژول پشتیبانی دامنه")

    return [
        {"code": code, "name": idx.modules[code]["name"], "reason": reason}
        for code, reason in sorted(found.items())
    ]


@router.get("/catalog/modules/{module_code}")
def get_module(module_code: str) -> dict[str, Any]:
    idx = index()
    code = module_code.strip().upper()
    mod = idx.modules.get(code)
    if not mod:
        raise HTTPException(status_code=404, detail=f"ماژول {module_code} یافت نشد")
    section_code = idx.section_of_module[code]
    spec = specs_for_modules([code])
    return {
        "module": mod,
        "section": idx.sections[section_code],
        "dependencies": _module_dependencies(code),
        "domain": {
            "entities": [
                {
                    "name": e["name"],
                    "table": e["table"],
                    "label_fa": e["label_fa"],
                    "fields": e["fields"],
                    "derived": bool(spec["modules"][0].get("derived")) if spec["modules"] else True,
                }
                for e in spec["entities"]
                if e.get("module_code") == code
            ],
        },
        "ai_points": [
            ai_points_detail([item["code"]])[0]
            for grp in mod["groups"]
            for item in grp["items"]
            if item["ai"]
        ],
    }


@router.get("/catalog/ai-points")
def get_ai_points(module: str | None = None, engine: str | None = None) -> dict[str, Any]:
    points = catalog_ai_points()
    caps = capability_catalog()
    by_code = {c["code"]: c for c in caps}
    result = []
    for point in points:
        cap = by_code.get(point["code"], {})
        merged = {**point, **{k: v for k, v in cap.items() if k not in point}}
        if module and not merged["module_code"].upper().startswith(module.upper()):
            continue
        if engine and merged.get("engine") != engine:
            continue
        result.append(merged)
    return {"count": len(result), "ai_points": result}


@router.get("/catalog/dependencies")
def get_dependencies() -> dict[str, Any]:
    """نگاشت وابستگی‌های صریح بین زیرمجموعه‌ها و ماژول‌ها."""
    idx = index()
    item_deps: dict[str, list[str]] = {}
    module_deps: dict[str, set[str]] = {}
    for item_code, item in idx.items.items():
        if item["deps"]:
            item_deps[item_code] = item["deps"]
            owner = idx.module_of_item[item_code]
            for dep in item["deps"]:
                target_module = dep[:2] if dep[:2] in idx.modules else dep[0]
                if target_module in idx.modules and target_module != owner:
                    module_deps.setdefault(owner, set()).add(target_module)
    return {
        "item_dependencies": item_deps,
        "module_dependencies": {k: sorted(v) for k, v in sorted(module_deps.items())},
        "system_modules": SYSTEM_MODULES,
    }


# --------------------------------------------------------------------------- #
# پریست‌ها
# --------------------------------------------------------------------------- #
@router.get("/presets")
def get_presets() -> dict[str, Any]:
    return {"presets": preset_list()}


def advisor_goals() -> list[str]:
    """اهداف کسب‌وکاری شناخته‌شده برای دستیار انتخاب ماژول."""
    return sorted(GOAL_MODULES)


@router.post("/presets/{preset_key}/apply")
def apply_preset_route(preset_key: str) -> dict[str, Any]:
    from ..presets import apply_preset

    try:
        payload = apply_preset(preset_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    resolution = resolve({"mode": "custom", "modules": payload["modules"]})
    return {**payload, "resolution": resolution}


# --------------------------------------------------------------------------- #
# حل وابستگی‌ها و تحلیل انتخاب
# --------------------------------------------------------------------------- #
@router.post("/resolve")
def resolve_selection(request: ResolveRequest) -> dict[str, Any]:
    selection = json.loads(request.selection.model_dump_json())
    return resolve(selection)


@router.post("/selection/expand")
def expand_route(request: ResolveRequest) -> dict[str, Any]:
    """بسط انتخاب بدون افزودن خودکار پیش‌نیازها (برای نمایش در UI)."""
    selection = json.loads(request.selection.model_dump_json())
    expanded = expand_selection(selection)
    idx = index()
    return {
        "expanded": expanded,
        "counts": {
            "sections": len(expanded["sections"]),
            "modules": len(expanded["modules"]),
            "groups": len(expanded["groups"]),
            "items": len(expanded["items"]),
            "ai_points": len(expanded["ai_points"]),
        },
        "coverage": coverage_by_section(expanded),
        "ai_engines": engine_summary(set(expanded["ai_points"])),
        "module_names": {m: idx.modules[m]["name"] for m in expanded["modules"]},
    }


@router.post("/advisor/recommend")
def advisor_recommend(request: AdvisorRequest) -> dict[str, Any]:
    settings = DEFAULT_FACTORY_SETTINGS
    result = advise(
        industry=request.industry,
        employees_count=request.employees_count,
        shifts_per_day=request.shifts_per_day,
        production_lines=request.production_lines,
        warehouses_count=request.warehouses_count,
        goals=request.goals,
        budget_level=request.budget_level,
        ai_appetite=request.ai_appetite,
        note=request.note,
        avalai_key=settings.get("avalai_api_key") or AVALAI_API_KEY,
        avalai_base_url=settings.get("avalai_base_url") or AVALAI_BASE_URL,
        avalai_model=settings.get("avalai_model") or AVALAI_MODEL,
    )
    return json.loads(json.dumps(result, ensure_ascii=False, default=lambda o: o.model_dump()))


@router.post("/advisor/recommend-fast")
def advisor_recommend_fast(request: AdvisorRequest) -> dict[str, Any]:
    """پیشنهاد سریع و صرفاً قاعده‌محور (بدون تماس با AvalAI)."""
    return recommend_modules(
        industry=request.industry,
        employees_count=request.employees_count,
        shifts_per_day=request.shifts_per_day,
        production_lines=request.production_lines,
        warehouses_count=request.warehouses_count,
        goals=request.goals,
        budget_level=request.budget_level,
        ai_appetite=request.ai_appetite,
    )


@router.post("/advisor/phases")
def advisor_phases(payload: dict[str, Any]) -> dict[str, Any]:
    modules = payload.get("modules") or []
    ai_points = payload.get("ai_points") or []
    if not modules:
        raise HTTPException(status_code=400, detail="فهرست ماژول‌ها خالی است")
    resolved = resolve_modules(modules)["resolved"]
    phases = build_phases(resolved, ai_points)
    return {
        "phases": [json.loads(p.model_dump_json()) for p in phases],
        "total_months": sum(p.duration_months for p in phases),
    }


# --------------------------------------------------------------------------- #
# پروژه‌ها
# --------------------------------------------------------------------------- #
@router.get("/projects")
def projects_list() -> dict[str, Any]:
    return {"projects": list_projects()}


@router.get("/projects/{project_id}")
def projects_get(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="پروژه یافت نشد")
    return json.loads(project.model_dump_json())


@router.post("/projects")
def projects_create(payload: ProjectConfig) -> dict[str, Any]:
    payload.id = None
    project = save_project(payload)
    return json.loads(project.model_dump_json())


@router.put("/projects/{project_id}")
def projects_update(project_id: str, payload: ProjectConfig) -> dict[str, Any]:
    payload.id = project_id
    project = save_project(payload)
    return json.loads(project.model_dump_json())


@router.delete("/projects/{project_id}")
def projects_delete(project_id: str) -> dict[str, Any]:
    if not delete_project(project_id):
        raise HTTPException(status_code=404, detail="پروژه یافت نشد")
    return {"deleted": project_id}


@router.post("/projects/{project_id}/phases")
def projects_build_phases(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="پروژه یافت نشد")
    selection = json.loads(project.selection.model_dump_json())
    resolution = resolve(selection)
    phases = build_phases(resolution["resolved_modules"], resolution["selection"]["ai_points"])
    project.phases = phases
    project = save_project(project)
    return {
        "project": json.loads(project.model_dump_json()),
        "phases": [json.loads(p.model_dump_json()) for p in phases],
        "total_months": sum(p.duration_months for p in phases),
    }


# --------------------------------------------------------------------------- #
# دستیار گفت‌وگو
# --------------------------------------------------------------------------- #
@router.post("/chat")
def chat_route(request: ChatRequest) -> dict[str, Any]:
    """گفت‌وگو با دستیار سازنده؛ در نبود AvalAI از پاسخ قاعده‌محور استفاده می‌شود."""
    idx = index()
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="پیام خالی است")

    api_key = (request.context.get("avalai_api_key") or AVALAI_API_KEY or "").strip()
    base_url = request.context.get("avalai_base_url") or AVALAI_BASE_URL
    model = request.context.get("avalai_model") or AVALAI_MODEL

    if is_configured(api_key):
        system = (
            "تو دستیار «سازنده ERP هوشمند کارخانه‌ای» هستی. به فارسی، دقیق و کوتاه پاسخ بده. "
            "کاربر در حال انتخاب ماژول‌های ERP برای کارخانه خود است. "
            f"کاتالوگ شامل {idx.counts()['sections']} بخش، {idx.counts()['modules']} ماژول، "
            f"{idx.counts()['items']} زیرمجموعه و {idx.counts()['ai_points']} نقطه هوش مصنوعی است. "
            "کدهای ماژول‌ها را با فرمت درست (مثل A1، B3، F9) ذکر کن."
        )
        history = [m for m in request.history if isinstance(m, dict) and m.get("role") and m.get("content")]
        result = chat(
            [{"role": "system", "content": system}] + history[-8:] + [{"role": "user", "content": message}],
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.3,
            max_tokens=900,
        )
        if result.used:
            return {"answer": result.text, "llm_used": True, "source": "avalai", "note": result.note}
        return {
            "answer": _heuristic_answer(message),
            "llm_used": False,
            "source": "heuristic",
            "note": result.note,
        }

    return {
        "answer": _heuristic_answer(message),
        "llm_used": False,
        "source": "heuristic",
        "note": "AvalAI فعال نیست؛ برای پاسخ‌های تحلیلی کلید API را در تنظیمات وارد کنید.",
    }


def _heuristic_answer(message: str) -> str:
    """پاسخ قاعده‌محور داخلی بر پایه جست‌وجو در کاتالوگ."""
    idx = index()
    hits = catalog_search(message, limit=8)
    lines: list[str] = []

    lowered = message.lower()
    if any(word in lowered for word in ("چطور", "چگونه", "how", "راهنما", "شروع")):
        lines.append(
            "برای شروع: ۱) از بخش «پریست‌ها» صنعت خود را انتخاب کنید یا دکمه «پیشنهاد هوشمند» را بزنید، "
            "۲) در «پیکربندگر» ماژول‌ها و زیرماژول‌ها را تیک بزنید، "
            "۳) در «تنظیمات کارخانه» پایگاه داده، AvalAI و روش استقرار را تعیین کنید، "
            "۴) در «تولید بسته» فایل آماده دیپلوی را دانلود کنید."
        )
    if "avalai" in lowered or "آوال" in lowered or "هوش مصنوعی" in lowered:
        lines.append(
            f"کاتالوگ {idx.counts()['ai_points']} نقطه هوش مصنوعی دارد که در {len(ENGINES)} موتور "
            "پیاده‌سازی می‌شوند. AvalAI یک لایه اختیاری برای قابلیت‌های زبانی (NLP، چت‌بات، خلاصه‌سازی، "
            "استخراج بند قرارداد و تولید بینش متنی) است و در تنظیمات کارخانه فعال می‌شود."
        )

    if hits:
        lines.append("نزدیک‌ترین قابلیت‌ها در کاتالوگ:")
        for hit in hits:
            lines.append(
                f"  • {hit['code']} — {hit['name']} "
                f"({hit['module_code']} {hit['module_name']} / بخش {hit['section_code']})"
            )
    else:
        lines.append(
            "مورد مشابهی در کاتالوگ یافت نشد. می‌توانید نام ماژول یا کلیدواژه فارسی/انگلیسی "
            "(مثل MRP، کالیبراسیون، مؤدیان، OEE) را جست‌وجو کنید."
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# تولید بسته استقرار
# --------------------------------------------------------------------------- #
@router.post("/generate")
def generate_package(request: GenerateRequest) -> dict[str, Any]:
    from ..generator.pipeline import generate_package as run_generate

    if request.save_project:
        save_project(request.project)
    try:
        result = run_generate(request.project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = json.loads(result.model_dump_json())
    # مسیرهای محلی سرور به کلاینت ارسال نمی‌شوند؛ فقط نام بسته/فایل zip
    payload["output_dir"] = Path(payload.get("output_dir") or "").name
    payload["zip_path"] = Path(payload.get("zip_path") or "").name
    return payload


def _package_summary(path: Path) -> dict[str, Any]:
    """خلاصه یک بسته تولیدشده برای فهرست و صفحه جزئیات."""
    manifest_path = path / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    counts = manifest.get("counts", {})
    zip_path = path.parent / f"{path.name}.zip"
    return {
        "package_id": path.name,
        "name": manifest.get("package_name", path.name),
        "created_at": manifest.get("created_at"),
        "created_at_jalali": manifest.get("created_at_jalali"),
        "preset_key": (manifest.get("project") or {}).get("preset_key"),
        "project_name": (manifest.get("project") or {}).get("name"),
        "modules": counts.get("modules"),
        "entities": counts.get("entities"),
        "ai_points": counts.get("ai_points"),
        "file_count": counts.get("files"),
        "line_count": counts.get("lines"),
        "zip_exists": zip_path.exists(),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "stats": manifest.get("stats", {}),
        "notes": manifest.get("notes", []),
    }


@router.get("/packages")
def packages_list() -> dict[str, Any]:
    packages = []
    if OUTPUT_DIR.exists():
        for path in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            packages.append(_package_summary(path))
    return {"packages": packages}


def _package_dir(package_id: str) -> Path:
    safe = Path(package_id).name
    path = OUTPUT_DIR / safe
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail=f"بسته {package_id} یافت نشد")
    return path


@router.get("/packages/{package_id}")
def package_detail(package_id: str) -> dict[str, Any]:
    """خلاصه + فهرست ماژول‌ها + ساختار ریشه یک بسته تولیدشده."""
    path = _package_dir(package_id)
    summary = _package_summary(path)
    manifest_path = path / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    summary["manifest_counts"] = manifest.get("counts", {})
    summary["modules"] = manifest.get("modules", [])
    summary["ai_engines"] = manifest.get("ai_engines", [])
    summary["selection"] = (manifest.get("reproduce") or {}).get("selection")
    summary["top_level"] = [
        {
            "name": node.get("name"),
            "path": node.get("path"),
            "type": node.get("type"),
            "size": node.get("size"),
            "children": len(node.get("children") or []),
        }
        for node in (manifest.get("tree") or [])
    ]
    return summary


@router.get("/packages/{package_id}/manifest")
def package_manifest(package_id: str) -> dict[str, Any]:
    path = _package_dir(package_id)
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="مانیفست بسته یافت نشد")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@router.get("/packages/{package_id}/tree")
def package_tree(package_id: str) -> dict[str, Any]:
    path = _package_dir(package_id)
    tree = _build_tree(path, path)
    return {"package_id": package_id, "tree": tree}


def _build_tree(root: Path, current: Path, max_depth: int = 8, depth: int = 0) -> list[dict[str, Any]]:
    if depth >= max_depth:
        return []
    entries = []
    for child in sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        node: dict[str, Any] = {
            "name": child.name,
            "path": str(child.relative_to(root)),
            "type": "dir" if child.is_dir() else "file",
        }
        if child.is_dir():
            node["children"] = _build_tree(root, child, max_depth, depth + 1)
            node["size"] = sum(
                f.stat().st_size for f in child.rglob("*") if f.is_file()
            )
        else:
            node["size"] = child.stat().st_size
            try:
                node["lines"] = len(child.read_text(encoding="utf-8").splitlines())
            except (UnicodeDecodeError, OSError):
                node["lines"] = 0
        entries.append(node)
    return entries


@router.get("/packages/{package_id}/file")
def package_file(package_id: str, path: str = Query(..., min_length=1)) -> Any:
    root = _package_dir(package_id)
    target = (root / path).resolve()
    if not str(target).startswith(str(root.resolve())):
        raise HTTPException(status_code=400, detail="مسیر نامعتبر")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="فایل یافت نشد")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return FileResponse(target, filename=target.name)
    return JSONResponse(
        {
            "path": str(target.relative_to(root)),
            "size": target.stat().st_size,
            "lines": len(content.splitlines()),
            "content": content,
        }
    )


@router.get("/packages/{package_id}/download")
def package_download(package_id: str) -> FileResponse:
    root = _package_dir(package_id)
    # فایل فشرده همیشه «کنار» پوشه بسته ساخته می‌شود؛ ساخت آن داخل پوشه
    # باعث می‌شد archive در حال رشد، خودش را دوباره بخواند و دیسک پر شود.
    zip_path = root.parent / f"{root.name}.zip"
    if not zip_path.exists():
        partial = zip_path.with_suffix(".zip.part")
        try:
            with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for path in sorted(root.rglob("*")):
                    if path.is_file():
                        archive.write(path, path.relative_to(root.parent))
            partial.replace(zip_path)
        except OSError as exc:
            partial.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"ساخت فایل zip ناموفق بود: {exc}") from exc
    if not zip_path.exists():
        raise HTTPException(status_code=500, detail="ساخت فایل zip ناموفق بود")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{package_id}.zip",
        headers={"Content-Disposition": f'attachment; filename="{package_id}.zip"'},
    )


@router.delete("/packages/{package_id}")
def package_delete(package_id: str) -> dict[str, Any]:
    path = _package_dir(package_id)
    shutil.rmtree(path, ignore_errors=True)
    (path.parent / f"{path.name}.zip").unlink(missing_ok=True)
    return {"deleted": package_id}
