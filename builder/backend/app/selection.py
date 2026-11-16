# -*- coding: utf-8 -*-
"""
موتور انتخاب و حل وابستگی‌ها
=============================
ورودی: انتخاب کاربر در چهار سطح (بخش، ماژول، زیرماژول، زیرمجموعه، نقاط AI)
خروجی: پیکربندی کامل قابل استقرار شامل

  * فهرست نهایی ماژول‌ها (منتخب + سیستمی + پیش‌نیازهای داده‌ای)
  * فهرست زیرماژول‌ها و زیرمجموعه‌های فعال
  * نقاط AI فعال به تفکیک موتور هوش مصنوعی
  * آمار پوشش به تفکیک ۲۲ بخش
  * برآورد تعداد جداول و فایل‌های بسته خروجی
"""

from __future__ import annotations

from typing import Any, Iterable

from .ai.registry import ENGINES, engine_for, engine_summary
from .catalog.registry import catalog, index
from .domain.registry import entity_table_map, resolve_modules, specs_for_modules

# برآورد فایل‌های تولیدشده به ازای هر موجودیت و هر زیرماژول
FILES_PER_ENTITY = 9      # migration, model, controller, request, resource, policy, routes, factory, seeder
FILES_PER_MODULE = 7      # react page + api client + menu + i18n + test + service + doc
FILES_PER_AI_POINT = 3    # python endpoint handler, laravel ai method, react widget
BASE_FILES = 96           # اسکلت پروژه (docker, env, scripts, config, layouts, ...)


def expand_selection(selection: dict[str, Any]) -> dict[str, Any]:
    """بسط انتخاب کاربر به فهرست کامل کدها با رعایت سلسله‌مراتب."""
    idx = index()

    selected_sections = set(selection.get("sections") or [])
    selected_modules = set(selection.get("modules") or [])
    selected_groups = set(selection.get("groups") or [])
    selected_items = set(selection.get("items") or [])
    selected_ai = set(selection.get("ai_points") or [])
    mode = selection.get("mode", "custom")

    all_modules = list(idx.modules)
    if mode == "all":
        selected_sections = set(idx.sections)
        selected_modules = set(all_modules)
        selected_groups = set(idx.groups)
        selected_items = set(idx.items)
        selected_ai = set(idx.ai_items)
    elif mode == "none":
        selected_sections, selected_modules = set(), set()
        selected_groups, selected_items, selected_ai = set(), set(), set()

    # بخش انتخاب‌شده -> همه ماژول‌های آن بخش
    for section_code in list(selected_sections):
        sec = idx.sections.get(section_code)
        if sec:
            selected_modules.update(m["code"] for m in sec["modules"])

    # ماژول انتخاب‌شده -> همه زیرماژول‌ها و زیرمجموعه‌های آن
    for module_code in list(selected_modules):
        mod = idx.modules.get(module_code)
        if not mod:
            continue
        for grp in mod["groups"]:
            selected_groups.add(grp["code"])
            for item in grp["items"]:
                selected_items.add(item["code"])
                if item["ai"]:
                    selected_ai.add(item["code"])

    # زیرماژول انتخاب‌شده -> همه زیرمجموعه‌های آن
    for group_code in list(selected_groups):
        grp = idx.groups.get(group_code)
        if not grp:
            continue
        for item in grp["items"]:
            selected_items.add(item["code"])
            if item["ai"]:
                selected_ai.add(item["code"])

    # حذف زیرمجموعه‌هایی که ماژول/زیرماژولشان انتخاب نشده
    selected_groups = {g for g in selected_groups if idx.module_of_group.get(g) in selected_modules}
    selected_items = {i for i in selected_items if idx.module_of_item.get(i) in selected_modules}
    selected_ai = {a for a in selected_ai if a in selected_items}

    return {
        "sections": sorted(selected_sections),
        "modules": sorted(selected_modules),
        "groups": sorted(selected_groups),
        "items": sorted(selected_items),
        "ai_points": sorted(selected_ai),
    }


def coverage_by_section(expanded: dict[str, Any]) -> list[dict[str, Any]]:
    """درصد پوشش هر بخش بر اساس انتخاب کاربر."""
    idx = index()
    selected_modules = set(expanded["modules"])
    selected_items = set(expanded["items"])
    selected_ai = set(expanded["ai_points"])

    rows = []
    for sec in catalog():
        modules = [m["code"] for m in sec["modules"]]
        chosen_modules = [m for m in modules if m in selected_modules]
        rows.append(
            {
                "code": sec["code"],
                "name": sec["name"],
                "name_en": sec["name_en"],
                "color": sec["color"],
                "icon": sec["icon"],
                "modules_total": len(modules),
                "modules_selected": len(chosen_modules),
                "items_total": sec["item_count"],
                "items_selected": len([i for i in selected_items if i.startswith(sec["code"])]),
                "ai_total": sec["ai_count"],
                "ai_selected": len([a for a in selected_ai if a.startswith(sec["code"])]),
                "percent": round(100 * len(chosen_modules) / max(len(modules), 1)),
            }
        )
    return rows


def ai_points_detail(codes: Iterable[str]) -> list[dict[str, Any]]:
    """جزئیات نقاط AI انتخاب‌شده همراه با موتور و اندپوینت."""
    idx = index()
    result = []
    for code in codes:
        item = idx.items.get(code)
        if not item or not item["ai"]:
            continue
        module_code = idx.module_of_item[code]
        mod = idx.modules[module_code]
        engine_key = engine_for(code, item["name"])
        engine = ENGINES[engine_key]
        result.append(
            {
                "code": code,
                "name": item["name"],
                "module_code": module_code,
                "module_name": mod["name"],
                "section_code": idx.section_of_module[module_code],
                "engine": engine_key,
                "engine_name_fa": engine.name_fa,
                "endpoint": engine.endpoint,
                "algorithms": engine.algorithms,
                "uses_llm": engine.uses_llm,
                "realtime": engine.realtime,
                "model_id": f"{engine_key}_{code.replace('.', '_').lower()}",
                "feature_flag": f"ai.{engine_key}.{code.lower().replace('.', '_')}",
            }
        )
    return result


def resolve(selection: dict[str, Any]) -> dict[str, Any]:
    """حل کامل وابستگی‌ها و آماده‌سازی آمار استقرار."""
    idx = index()
    expanded = expand_selection(selection)

    resolved = resolve_modules(expanded["modules"])
    final_modules = resolved["resolved"]

    # افزودن زیرماژول‌ها و آیتم‌های ماژول‌هایی که خودکار اضافه شده‌اند
    auto_added = resolved["auto_added"]
    groups = set(expanded["groups"])
    items = set(expanded["items"])
    ai_points = set(expanded["ai_points"])
    for code in auto_added:
        mod = idx.modules.get(code)
        if not mod:
            continue
        for grp in mod["groups"]:
            groups.add(grp["code"])
            for item in grp["items"]:
                items.add(item["code"])
                if item["ai"]:
                    ai_points.add(item["code"])

    expanded_final = {
        "sections": sorted({idx.section_of_module[m] for m in final_modules if m in idx.section_of_module}),
        "modules": final_modules,
        "groups": sorted(groups),
        "items": sorted(items),
        "ai_points": sorted(ai_points),
    }

    specs = specs_for_modules(final_modules)
    ai_engines = engine_summary(ai_points)

    counts = {
        "sections": len(expanded_final["sections"]),
        "modules": len(final_modules),
        "groups": len(expanded_final["groups"]),
        "items": len(expanded_final["items"]),
        "ai_points": len(expanded_final["ai_points"]),
        "tables": specs["counts"]["entities"],
        "fields": specs["counts"]["fields"],
        "ai_engines": len(ai_engines),
        "estimated_files": (
            BASE_FILES
            + specs["counts"]["entities"] * FILES_PER_ENTITY
            + len(final_modules) * FILES_PER_MODULE
            + len(ai_points) * FILES_PER_AI_POINT
        ),
    }

    return {
        "selection": expanded_final,
        "resolved_modules": final_modules,
        "auto_added": auto_added,
        "reasons": resolved["reasons"],
        "invalid": resolved["invalid"],
        "counts": counts,
        "sections": coverage_by_section(expanded_final),
        "ai_engines": ai_engines,
        "ai_points": ai_points_detail(ai_points),
        "estimated_tables": specs["counts"]["entities"],
        "estimated_files": counts["estimated_files"],
        "table_count": len(entity_table_map()),
    }


def selection_from_preset(preset_payload: dict[str, Any]) -> dict[str, Any]:
    """ساخت انتخاب از خروجی پریست."""
    return {
        "mode": "preset",
        "modules": preset_payload["modules"],
        "groups": preset_payload["groups"],
        "items": preset_payload["items"],
        "ai_points": preset_payload["ai_points"],
    }
