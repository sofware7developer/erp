# -*- coding: utf-8 -*-
"""
خط لوله تولید بسته استقرار
============================
یک پروژه (انتخاب ماژول‌ها + تنظیمات کارخانه) را به یک پوشه کامل و
قابل استقرار تبدیل می‌کند:

    dist-packages/<package_id>/
    ├── backend/    لاراول ۱۱
    ├── frontend/   React 18 + Vite (RTL)
    ├── ai-service/ FastAPI + numpy/pandas/scikit-learn
    ├── deploy/     nginx، systemd، cron، اسکریپت‌ها
    ├── docs/       مستندات فارسی
    ├── docker-compose.yml، deploy.sh، Makefile، manifest.json
    └── <package_id>.zip

خروجی: `GenerateResult` با آمار، درخت فایل‌ها و مانیفست.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..ai.registry import ENGINES
from ..catalog.registry import index as catalog_index
from ..config import APP_NAME_FA, APP_VERSION, CATALOG_VERSION, OUTPUT_DIR
from ..domain.derived import SECTION_MENU
from ..domain.registry import (
    PLATFORM_ENTITY,
    SYSTEM_MODULES,
    specs_for_modules,
    topological_order,
    validate_foreign_keys,
)
from ..schemas import GenerateResult, ProjectConfig
from ..selection import ai_points_detail, resolve
from .ai_service import generate_ai_service
from .deploy import generate_deploy_files
from .docs import generate_docs
from .frontend import generate_frontend
from .laravel_core import generate_core_files
from .laravel_domain import generate_domain_files
from .laravel_routes import generate_routes, generate_seeders
from .laravel_system import generate_system_files
from .settings_map import CURRENCY_LABELS, normalize_settings
from .writers import Package, pascal, slugify

INDUSTRY_LABELS = {
    "general_discrete": "تولید گسسته عمومی",
    "process_general": "فرآیندی عمومی",
    "food_pharma": "صنایع غذایی، دارویی و بهداشتی",
    "automotive": "خودروسازی و قطعه‌سازی",
    "metals_foundry": "فلزات، ریخته‌گری و فولاد",
    "textile": "نساجی، پوشاک و فرش",
    "electronics": "الکترونیک و نیمه‌هادی",
    "petrochemical": "پتروشیمی، پالایشگاه و شیمیایی",
    "packaging_print": "بسته‌بندی و چاپ",
    "smb_minimal": "کسب‌وکار کوچک و متوسط",
    "enterprise_full": "هلدینگ و بنگاه بزرگ چندکارخانه‌ای",
}


def jalali_now() -> tuple[str, str]:
    """تاریخ میلادی و شمسی اکنون (برای مانیفست و مستندات)."""
    now = datetime.now(timezone.utc)
    g_days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy, gm, gd = now.year, now.month, now.day
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
        + gd + g_days[gm - 1]
    )
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return (
        now.replace(microsecond=0).isoformat(),
        f"{jy:04d}/{jm:02d}/{jd:02d} — {now.hour:02d}:{now.minute:02d} UTC",
    )


def _normalize_endpoint(endpoint: str) -> str:
    """اندپوینت‌های رجیستری با پیشوند /api/ai هستند؛ سرویس AI مسیر /ai دارد."""
    return endpoint.replace("/api/ai/", "/ai/").replace("/api/", "/")


def _merged_settings(project: ProjectConfig) -> dict[str, Any]:
    """تنظیمات کاربر + پیش‌فرض‌ها + هم‌نام‌سازی کلیدها برای مولدها."""
    raw = {k: v for k, v in (project.settings or {}).items() if v is not None}
    slug = slugify(raw.get("project_slug") or project.name_en or project.name, "factory-erp")
    settings = normalize_settings(
        raw,
        project_name=project.name,
        project_name_en=project.name_en,
        project_description=project.description,
        slug=slug,
    )
    settings["project_slug"] = slug
    return settings


def build_context(
    project: ProjectConfig,
    settings: dict[str, Any],
    resolution: dict[str, Any],
    modules: list[dict[str, Any]],
    package_id: str,
) -> dict[str, Any]:
    """ساخت زمینه مشترک همه مولدها."""
    idx = catalog_index()
    generated_at, generated_at_jalali = jalali_now()

    slug = settings.get("project_slug") or slugify(project.name_en or project.name, "erp-factory")
    slug = slugify(slug, "erp-factory")

    section_meta = {}
    for section in idx.sections.values():
        code = section["code"]
        section_meta[code] = {
            "name": section["name"],
            "name_en": section["name_en"],
            "icon": section["icon"],
            "color": section["color"],
            "menu": SECTION_MENU.get(code, "سایر"),
        }

    module_stats = {}
    for module in modules:
        catalog_module = idx.modules.get(module["code"])
        module_stats[module["code"]] = {
            "groups": catalog_module["group_count"] if catalog_module else 0,
            "items": catalog_module["item_count"] if catalog_module else 0,
            "ai": catalog_module["ai_count"] if catalog_module else 0,
        }

    industry = str(settings.get("industry", project.preset_key or "general_discrete"))
    app_name_fa = settings.get("app_name_fa") or f"ERP {settings.get('company_name') or 'کارخانه'}"

    return {
        "slug": slug,
        "pascal": pascal(slug, "Erp"),
        "app_name": settings.get("app_name") or slug,
        "app_name_fa": app_name_fa,
        "app_url": settings.get("app_url") or "http://localhost",
        "preview_origin": settings.get("cors_origins") or "*",
        "version": APP_VERSION,
        "catalog_version": CATALOG_VERSION,
        "package_id": package_id,
        "generated_at": generated_at,
        "generated_at_jalali": generated_at_jalali,
        "section_meta": section_meta,
        "module_stats": module_stats,
        "sections": {code: meta for code, meta in section_meta.items()},
        "counts": resolution["counts"],
        "system_modules": SYSTEM_MODULES,
        "preset": project.preset_key,
        "industry": industry,
        "industry_label": INDUSTRY_LABELS.get(industry, INDUSTRY_LABELS.get(project.preset_key or "", "تولید صنعتی")),
        "tagline": f"ERP یکپارچه کارخانه با {resolution['counts']['modules']} ماژول و "
                   f"{resolution['counts']['ai_points']} قابلیت هوش مصنوعی",
        "file_count": 0,
        "line_count": 0,
        "counters": {},
        "topological_order": [],
        "platform_name": APP_NAME_FA,
    }


def _catalog_items(selection: dict[str, Any], modules: list[str]) -> list[dict[str, Any]]:
    """زیرمجموعه‌های انتخاب‌شده با متادیتای لازم برای رجیستری قابلیت‌ها."""
    idx = catalog_index()
    engine_by_code = {cap["code"]: cap for cap in _capability_index()}
    module_names = {m: idx.modules[m]["name"] for m in modules if m in idx.modules}

    items: list[dict[str, Any]] = []
    for code in selection["items"]:
        item = idx.items.get(code)
        if not item:
            continue
        module_code = idx.module_of_item.get(code, "")
        if module_code not in module_names:
            continue
        group_code = code.rsplit(".", 1)[0]
        group = idx.groups.get(group_code, {})
        capability = engine_by_code.get(code, {})
        items.append(
            {
                "code": code,
                "name": item["name"],
                "level": item.get("level", 4),
                "ai": bool(item.get("ai")),
                "deps": item.get("deps", []),
                "roles": [item["role"]] if item.get("role") else [],
                "entity": item.get("entity"),
                "module_code": module_code,
                "module_name": module_names.get(module_code, ""),
                "section_code": module_code[:1],
                "section_name": idx.sections.get(module_code[:1], {}).get("name", ""),
                "group_code": group_code,
                "group_name": group.get("name", ""),
                "engine": capability.get("engine"),
            }
        )
    return items


def _capability_index() -> list[dict[str, Any]]:
    from ..ai.registry import capability_catalog

    return capability_catalog()


def _ai_points(selection: dict[str, Any]) -> list[dict[str, Any]]:
    points = ai_points_detail(selection["ai_points"])
    for point in points:
        point["endpoint"] = _normalize_endpoint(point["endpoint"])
    return points


def _ai_engines(ai_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    engines: list[dict[str, Any]] = []
    used = {point["engine"] for point in ai_points}
    for key in sorted(used | {"mlops"}):
        engine = ENGINES.get(key)
        if engine is None:
            continue
        engines.append(
            {
                "key": engine.key,
                "engine": engine.key,
                "name_fa": engine.name_fa,
                "name_en": engine.name_en,
                "category": engine.category,
                "endpoint": _normalize_endpoint(engine.endpoint),
                "model_dir": engine.model_dir,
                "algorithms": engine.algorithms,
                "pip_packages": engine.pip_packages,
                "uses_llm": engine.uses_llm,
                "realtime": engine.realtime,
                "retraining": engine.retraining,
                "metrics": engine.metrics,
                "description": engine.description,
                "input_hint": "؛ ".join(engine.inputs),
                "output_hint": "؛ ".join(engine.outputs),
                "count": sum(1 for point in ai_points if point["engine"] == key),
            }
        )
    return engines


def _zip_package(root: Path) -> Path:
    zip_path = root.parent / f"{root.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root.parent))
    return zip_path


def generate_package(project: ProjectConfig, *, keep_previous: bool = False) -> GenerateResult:
    """تولید کامل بسته استقرار از روی پیکربندی پروژه."""
    settings = _merged_settings(project)
    resolution = resolve(json.loads(project.selection.model_dump_json()))

    if resolution["counts"]["modules"] == 0:
        raise ValueError("هیچ ماژولی انتخاب نشده است؛ دست‌کم یک ماژول را در پیکربندگر انتخاب کنید.")

    module_codes = resolution["resolved_modules"]
    idx = catalog_index()

    # ۱) مشخصات دامنه (موجودیت‌ها، جداول، فیلدها)
    specs = specs_for_modules(module_codes)
    fk_errors = validate_foreign_keys()
    notes: list[str] = []
    if fk_errors:
        notes.append(f"{len(fk_errors)} وابستگی خارجی بی‌مقصد در مدل داده یافت شد و به‌صورت ستون ساده تولید می‌شود.")

    entities = specs["entities"]
    tables = specs["tables"]
    topo = [ent["table"] for ent in topological_order(entities)]

    # ۲) ماژول‌ها با متادیتای کاتالوگ
    modules: list[dict[str, Any]] = []
    for spec in specs["modules"]:
        catalog_module = idx.modules.get(spec["code"], {})
        modules.append(
            {
                **spec,
                "name": catalog_module.get("name", spec["label_fa"]),
                "name_en": spec.get("name_en") or catalog_module.get("name_en", ""),
                "icon": catalog_module.get("icon", "box"),
                "color": catalog_module.get("color", "#4f46e5"),
                "groups": catalog_module.get("groups", []),
            }
        )
    modules.sort(key=lambda m: m["code"])

    ai_points = _ai_points(resolution["selection"])
    ai_engines = _ai_engines(ai_points)
    ai_by_module: dict[str, list[dict[str, Any]]] = {}
    for point in ai_points:
        ai_by_module.setdefault(point["module_code"], []).append(point)

    # ۳) شناسه و پوشه بسته
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = settings.get("project_slug") or slugify(project.name_en or project.name, "erp-factory")
    package_id = f"{slugify(slug, 'erp')}-{stamp}"
    output_root = OUTPUT_DIR / package_id

    if output_root.exists() and not keep_previous:
        shutil.rmtree(output_root, ignore_errors=True)
    output_root.mkdir(parents=True, exist_ok=True)

    context = build_context(project, settings, resolution, modules, package_id)
    context["topological_order"] = topo
    package = Package(root=output_root, name=package_id)

    catalog_items = _catalog_items(resolution["selection"], module_codes)
    groups = [
        {**group, "module_code": code, "module_name": idx.modules[code]["name"]}
        for code in module_codes
        for group in (idx.modules.get(code, {}).get("groups") or [])
    ]

    # ۴) تولید لایه‌ها ----------------------------------------------------- #
    generate_core_files(
        package,
        settings=settings,
        modules=modules,
        ai_engines=ai_engines,
        ai_points=ai_points,
        context=context,
    )

    domain_result = generate_domain_files(
        package,
        modules,
        specs,
        settings=settings,
        ai_points_by_module=ai_by_module,
    )
    counters = dict(domain_result["counters"])

    generate_system_files(
        package,
        settings=settings,
        modules=modules,
        entities=entities,
        ai_engines=ai_engines,
        ai_points=ai_points,
        catalog_items=catalog_items,
        context=context,
    )

    generate_routes(
        package,
        settings=settings,
        modules=modules,
        entities=entities,
        module_stats=context["module_stats"],
        context=context,
    )

    generate_seeders(
        package,
        modules=modules,
        entities=entities,
        include_demo_data=bool(settings.get("include_demo_data", False)),
        context=context,
    )

    # سرویس هوش مصنوعی فقط وقتی نقطه AI انتخاب شده و پرچم آن فعال باشد
    settings["ai_enabled"] = bool(settings.get("ai_enabled", True)) and bool(ai_points)
    if settings["ai_enabled"]:
        generate_ai_service(
            package,
            settings=settings,
            ai_engines=ai_engines,
            ai_points=ai_points,
            context=context,
        )
    else:
        notes.append(
            "هوش مصنوعی در این بسته تولید نشد (ai_enabled=false یا نبود نقطه AI)؛ "
            "با فعال‌سازی گزینه AI و انتخاب نقاط هوشمند، بسته را دوباره بسازید."
        )

    generate_frontend(
        package,
        settings=settings,
        modules=modules,
        entities=entities,
        ai_points=ai_points,
        context=context,
    )

    generate_deploy_files(package, settings=settings, context=context)

    # ۵) مستندات (دو بار: با آمار میانی و سپس آمار نهایی) ------------------- #
    include_docs = bool(settings.get("include_docs", True))
    include_api_docs = bool(settings.get("generate_api_docs", True))
    counters["backend_files"] = sum(
        1 for path in package.files if path.startswith("backend/")
    )
    context["counters"] = counters
    context["file_count"] = package.file_count + 12
    context["line_count"] = package.line_count

    sections_meta = {
        code: {
            "name": meta["name"],
            "name_en": meta["name_en"],
            "icon": meta["icon"],
            "color": meta["color"],
        }
        for code, meta in context["section_meta"].items()
    }

    generate_docs(
        package,
        settings=settings,
        modules=modules,
        entities=entities,
        ai_engines=ai_engines,
        ai_points=ai_points,
        sections=sections_meta,
        groups=groups,
        items=catalog_items,
        context=context,
        include_docs=include_docs,
        include_api_docs=include_api_docs,
    )

    # آمار نهایی و بازنویسی README و CHANGELOG با اعداد دقیق
    context["file_count"] = package.file_count
    context["line_count"] = package.line_count
    generate_docs(
        package,
        settings=settings,
        modules=modules,
        entities=entities,
        ai_engines=ai_engines,
        ai_points=ai_points,
        sections=sections_meta,
        groups=groups,
        items=catalog_items,
        context=context,
        include_docs=include_docs,
        include_api_docs=include_api_docs,
    )

    # ۶) مانیفست ------------------------------------------------------------ #
    stats = package.stats()
    manifest = {
        "package_id": package_id,
        "package_name": f"{context['app_name_fa']} — {context['industry_label']}",
        "generator": {
            "name": APP_NAME_FA,
            "version": APP_VERSION,
            "catalog_version": CATALOG_VERSION,
        },
        "created_at": context["generated_at"],
        "created_at_jalali": context["generated_at_jalali"],
        "project": {
            "id": project.id,
            "name": project.name,
            "name_en": project.name_en,
            "description": project.description,
            "preset_key": project.preset_key,
        },
        "settings": settings,
        "counts": {
            **resolution["counts"],
            "files": package.file_count,
            "lines": package.line_count,
            "bytes": package.byte_count,
            "tables": len(tables),
            "entities": len(entities),
            "fields": sum(len(e["fields"]) for e in entities),
        },
        "modules": [
            {
                "code": m["code"],
                "slug": m["slug"],
                "label_fa": m["label_fa"],
                "name_en": m.get("name_en", ""),
                "menu_group": m.get("menu_group", ""),
                "derived": bool(m.get("derived")),
                "priority": m.get("priority", 3),
                "entities": len([e for e in entities if e["module_code"] == m["code"]]),
                "ai_points": len(ai_by_module.get(m["code"], [])),
                "groups": context["module_stats"].get(m["code"], {}).get("groups", 0),
                "items": context["module_stats"].get(m["code"], {}).get("items", 0),
            }
            for m in modules
        ],
        "auto_added": resolution["auto_added"],
        "dependency_reasons": resolution["reasons"],
        "ai_engines": ai_engines,
        "ai_points": ai_points,
        "platform_entities": [PLATFORM_ENTITY["name"]],
        "system_modules": SYSTEM_MODULES,
        "foreign_key_warnings": fk_errors[:50],
        "stats": stats,
        "counters": counters,
        "tree": package.tree(max_depth=4),
        "notes": notes,
        "reproduce": {
            "selection": resolution["selection"],
            "settings": settings,
        },
    }

    package.add("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", area="manifest")

    # فایل انتخاب سریع برای بازتولید
    package.add(
        "erp-selection.json",
        json.dumps(
            {
                "selection": resolution["selection"],
                "settings": settings,
                "preset_key": project.preset_key,
                "generated_at": context["generated_at"],
                "generator_version": APP_VERSION,
                "catalog_version": CATALOG_VERSION,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        area="manifest",
    )

    # ۷) نوشتن روی دیسک و فشرده‌سازی ---------------------------------------- #
    package.write()
    zip_path = _zip_package(output_root)

    final_stats = package.stats()
    if notes:
        notes.append("")
    notes.extend(
        [
            f"بسته در `{output_root.name}` نوشته شد و فایل فشرده `{zip_path.name}` ساخته شد.",
            "برای استقرار: `./deploy.sh` (یا `make install`) — سپس با کاربر مدیر وارد شوید.",
            f"مستندات: `README-fa.md` و پوشه `docs/` ({final_stats['areas'].get('docs', {}).get('files', 0)} فایل).",
        ]
    )
    if fk_errors:
        notes.insert(0, f"هشدار: {len(fk_errors)} کلید خارجی بدون مقصد — فهرست کامل در manifest.json.")
    if not settings.get("avalai_api_key"):
        notes.append("کلید AvalAI تنظیم نشده: قابلیت‌های زبانی از موتور داخلی استفاده می‌کنند (اختیاری).")

    return GenerateResult(
        package_id=package_id,
        package_name=manifest["package_name"],
        output_dir=str(output_root),
        zip_path=str(zip_path),
        zip_size_bytes=zip_path.stat().st_size,
        file_count=package.file_count,
        line_count=package.line_count,
        created_at=datetime.fromisoformat(context["generated_at"]),
        stats=final_stats,
        tree=manifest["tree"],
        manifest=manifest,
        notes=[note for note in notes if note],
    )


def package_dirs() -> list[Path]:
    """فهرست بسته‌های تولیدشده."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted((p for p in OUTPUT_DIR.iterdir() if p.is_dir()), reverse=True)
