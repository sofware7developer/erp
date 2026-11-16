# -*- coding: utf-8 -*-
"""
رجیستری دامنه داده
==================
* تجمیع مشخصات دست‌نویس و خودکار همه ۱۳۰ ماژول
* اعتبارسنجی ارجاع‌های خارجی (هر foreign(...) باید به جدول موجود اشاره کند)
* مرتب‌سازی توپولوژیک جداول برای تولید مایگریشن‌ها به ترتیب درست
* تعیین ماژول‌های «پیش‌نیاز سیستمی» که همیشه در بسته خروجی ساخته می‌شوند
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from ..catalog.registry import index
from . import base_specs, core_specs_business, core_specs_ops, core_specs_quality, core_specs_supply
from .derived import derive_all
from .dsl import entity

# ماژول‌هایی که زیرساخت داده‌ای کل سامانه‌اند و همیشه ساخته می‌شوند
SYSTEM_MODULES = [
    "S1",  # کاربران، نقش‌ها، دسترسی‌ها، ردیابی حسابرسی
    "G1",  # ساختار سازمانی و کارکنان (مالک داده اصلی پرسنل)
    "D4",  # کالا و موجودی (قلب داده‌ای همه ماژول‌های عملیاتی)
    "D3",  # انبار و محل‌های انبارش
    "F1",  # دفتر کل و دوره‌های مالی (زیرساخت همه اسناد مالی)
    "P1",  # مدیریت اسناد (پیوست همه ماژول‌ها)
    "V3",  # KPI و هشدارها (زیرساخت پایش و مرکز فرماندهی)
    "K7",  # رجیستری مدل‌ها و قابلیت‌های AI
    "P2",  # موتور گردش‌کار (زیرساخت همه تأییدها)
]

# ماژول‌های پشتیبانی که در صورت انتخاب ماژول‌های مشخص اضافه می‌شوند
SUPPORT_MODULES: dict[str, list[str]] = {
    "A2": ["A4", "D4"],
    "A1": ["A3", "A4", "D4"],
    "A3": ["D4"],
    "A5": ["A3", "D4"],
    "A6": ["A3", "A4", "E1"],
    "A7": ["C1", "C4"],
    "A8": ["A2", "A4"],
    "B1": ["D4", "B7"],
    "B2": ["B1", "B4"],
    "B3": ["B1"],
    "B4": ["B1"],
    "B5": ["C1", "B6"],
    "B6": ["D4"],
    "B7": ["D4", "A2"],
    "C1": ["C3", "C4"],
    "C2": ["C1", "J5"],
    "C3": ["C4"],
    "C4": ["D4", "D1"],
    "C5": ["C3"],
    "C6": ["C1", "C3", "I1"],
    "D1": ["D2", "D4", "F3"],
    "D2": ["D1"],
    "D5": ["D3"],
    "D6": ["D4", "D3"],
    "D7": ["D1", "F5"],
    "D8": ["D4", "D1"],
    "E1": ["E2", "D4", "F2"],
    "E2": ["E1"],
    "E3": ["E2"],
    "E4": ["E1", "E6"],
    "E5": ["E2"],
    "E6": ["E2"],
    "E7": ["E1", "E2"],
    "F2": ["E1"],
    "F3": ["D1"],
    "F4": ["F1", "F5"],
    "F5": ["F1"],
    "F6": ["F1", "A2"],
    "F7": ["F1", "F6"],
    "F8": ["F1"],
    "F9": ["F1", "E1", "D1"],
    "F10": ["F1", "I1"],
    "F11": ["F1"],
    "F12": ["F1"],
    "G2": ["G1"],
    "G3": ["G1", "G4"],
    "G4": ["G1"],
    "G5": ["G1", "G3", "F1"],
    "G6": ["G1", "V3"],
    "G7": ["G1"],
    "G8": ["G1", "G6"],
    "G9": ["G1", "G5"],
    "G10": ["G1", "G5"],
    "G11": ["G1"],
    "G12": ["G1"],
    "H1": ["A3"],
    "H2": ["H1", "A3"],
    "H3": ["H1"],
    "H4": ["H1", "I1"],
    "H5": ["P1"],
    "I1": ["P1"],
    "I2": ["I1", "G1"],
    "I3": ["I1", "F10"],
    "I4": ["I1", "O1"],
    "I5": ["I1"],
    "J1": ["J5"],
    "J2": ["J1", "J5"],
    "J3": ["J2", "A2"],
    "J4": ["J2", "J3"],
    "J6": ["J1", "Q2"],
    "L1": ["V3", "L4"],
    "L2": ["L1", "L4"],
    "L3": ["L4"],
    "L4": ["S2"],
    "M1": ["G1", "O1"],
    "M2": ["M1", "G1"],
    "M3": ["M1", "N1"],
    "M4": ["M1"],
    "M5": ["M3", "D4"],
    "N1": ["J2", "F6"],
    "N2": ["C1", "N1"],
    "N3": ["N1", "M3"],
    "O1": ["V3"],
    "O2": ["O1", "P1"],
    "O3": ["O2", "P1"],
    "O4": ["S1", "P1"],
    "P3": ["P1", "P2"],
    "P4": ["P1"],
    "Q1": ["D5", "C1"],
    "Q2": ["D3", "A2"],
    "Q3": ["D4", "A3"],
    "R1": ["V3", "L1"],
    "R2": ["V3", "R1"],
    "R3": ["R1", "H4"],
    "R4": ["P1"],
    "S2": ["S1"],
    "S3": ["F9", "G5", "D7"],
    "S4": ["S1"],
    "S5": ["S1"],
    "S6": ["S1"],
    "S7": ["P2", "L2"],
    "U1": ["D2", "U3"],
    "U2": ["D1", "A4", "U1"],
    "U3": ["P1", "F5"],
    "V1": ["V3", "L1"],
    "V2": ["V3", "J3"],
}

# ماژول‌های بخش K (هسته AI) که انتخاب هر کدام، K7 را لازم می‌کند
for _k in ("K1", "K2", "K3", "K4", "K5", "K6"):
    SUPPORT_MODULES[_k] = ["K7"]

# بخش‌های تخصصی صنایع به هسته تولید و کیفیت وابسته‌اند
for _t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7"):
    SUPPORT_MODULES[_t] = ["A5" if _t in {"T1", "T6"} else "A2", "B1", "B7", "D4"]


PLATFORM_ENTITY = entity(
    "SystemFeature",
    "قابلیت فعال سامانه",
    [
        "code|string|کد زیرمجموعه کاتالوگ|unique,index",
        "title|string|نام قابلیت|required,searchable",
        "section_code|string|کد بخش|required,index",
        "module_code|string|کد ماژول|required,index",
        "group_code|string|کد زیرماژول|required,index",
        "feature_level|enum(section,module,group,item)|سطح قابلیت|required,index",
        "is_ai_capability|boolean|نقطه هوش مصنوعی|default=false,index",
        "ai_engine|string|موتور AI|nullable,index",
        "is_enabled|boolean|فعال در این کارخانه|default=true,index",
        "license_scope|string|دامنه مجوز|nullable",
        "enabled_at|datetime|زمان فعال‌سازی|nullable,index",
        "config|json|پیکربندی قابلیت|nullable",
    ],
    table="system_features",
    icon="toggle-right",
    notes="رجیستری قابلیت‌های فعال‌شده در این کارخانه؛ مبنای منوی پویا و کنترل دسترسی.",
)


def _collect_core_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for source in (base_specs, core_specs_ops, core_specs_quality, core_specs_supply, core_specs_business):
        for spec in source.MODULE_SPECS:
            code = spec["code"]
            if code in specs:
                # ادغام موجودیت‌ها در صورت تعریف دوباره یک ماژول
                existing_tables = {e["table"] for e in specs[code]["entities"]}
                for ent in spec["entities"]:
                    if ent["table"] not in existing_tables:
                        specs[code]["entities"].append(ent)
                        existing_tables.add(ent["table"])
                for key in ("ai_endpoints",):
                    merged = list(dict.fromkeys(specs[code].get(key, []) + spec.get(key, [])))
                    specs[code][key] = merged
            else:
                specs[code] = spec
    return specs


@lru_cache(maxsize=1)
def all_specs() -> dict[str, dict[str, Any]]:
    """مشخصات دامنه همه ۱۳۰ ماژول (دست‌نویس + خودکار)."""
    specs = _collect_core_specs()
    idx = index()
    unknown_codes = set(specs) - set(idx.modules)
    if unknown_codes:
        raise ValueError(f"کد ماژول نامعتبر در مشخصات دامنه: {sorted(unknown_codes)}")
    core_tables: set[str] = set()
    core_names: set[str] = set()
    for spec in specs.values():
        for ent in spec["entities"]:
            core_tables.add(ent["table"])
            core_names.add(ent["name"])
    for derived in derive_all(set(specs), core_tables, core_names):
        specs[derived["code"]] = derived
    return specs


@lru_cache(maxsize=1)
def entity_table_map() -> dict[str, dict[str, Any]]:
    """نگاشت نام جدول -> مشخصات موجودیت (برای اعتبارسنجی FK)."""
    table_map: dict[str, dict[str, Any]] = {"system_features": PLATFORM_ENTITY}
    duplicates: list[str] = []
    for code, spec in all_specs().items():
        for ent in spec["entities"]:
            if ent["table"] in table_map:
                duplicates.append(f"{ent['table']} (در {table_map[ent['table']].get('_owner', '?')} و {code})")
                continue
            ent = dict(ent)
            ent["_owner"] = code
            table_map[ent["table"]] = ent
    if duplicates:
        raise ValueError("نام جدول تکراری در مشخصات دامنه:\n  - " + "\n  - ".join(sorted(duplicates)))
    return table_map


def validate_foreign_keys() -> list[str]:
    """اعتبارسنجی همه ارجاع‌های خارجی؛ فهرست خطاها را برمی‌گرداند."""
    table_map = entity_table_map()
    problems: list[str] = []
    for table, ent in table_map.items():
        for field in ent["fields"]:
            if field["type"] != "foreign":
                continue
            target = field["references_table"]
            if target not in table_map:
                problems.append(f"{table}.{field['name']} -> جدول ناموجود `{target}`")
    return problems


def resolve_modules(selected: Iterable[str]) -> dict[str, Any]:
    """
    حل وابستگی‌های ماژول‌ها.

    خروجی شامل: فهرست نهایی ماژول‌ها (منتخب + سیستمی + پشتیبانی)،
    ماژول‌های افزوده‌شده خودکار با ذکر دلیل، و ماژول‌های نامعتبر.
    """
    idx = index()
    selected_set = {code for code in selected if code in idx.modules}
    invalid = sorted({code for code in selected if code not in idx.modules})

    final: dict[str, str] = {code: "selected" for code in sorted(selected_set)}
    for code in SYSTEM_MODULES:
        if code in idx.modules:
            final.setdefault(code, "system")

    # گسترش انتقالی ماژول‌های پشتیبانی
    queue = list(final)
    while queue:
        code = queue.pop(0)
        for support in SUPPORT_MODULES.get(code, []):
            if support in idx.modules and support not in final:
                final[support] = f"dependency-of-{code}"
                queue.append(support)

    return {
        "selected": sorted(selected_set),
        "resolved": sorted(final),
        "auto_added": sorted(c for c, reason in final.items() if reason != "selected"),
        "reasons": final,
        "invalid": invalid,
    }


def topological_order(entities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """مرتب‌سازی توپولوژیک جداول بر اساس وابستگی خارجی (برای ترتیب مایگریشن)."""
    items = list(entities)
    by_table = {ent["table"]: ent for ent in items}
    graph: dict[str, set[str]] = {ent["table"]: set() for ent in items}
    for ent in items:
        for field in ent["fields"]:
            if field["type"] == "foreign":
                target = field["references_table"]
                if target in by_table and target != ent["table"]:
                    graph[ent["table"]].add(target)

    ordered: list[dict[str, Any]] = []
    visited: set[str] = set()
    in_progress: set[str] = set()

    def visit(table: str) -> None:
        if table in visited:
            return
        if table in in_progress:  # چرخه خودارجاع یا متقابل -> شکستن چرخه
            return
        in_progress.add(table)
        for dep in sorted(graph[table]):
            visit(dep)
        in_progress.discard(table)
        visited.add(table)
        ordered.append(by_table[table])

    for table in sorted(by_table):
        visit(table)
    return ordered


def specs_for_modules(module_codes: Iterable[str]) -> dict[str, Any]:
    """مشخصات دامنه کامل برای مجموعه‌ای از ماژول‌ها."""
    specs = all_specs()
    table_map = entity_table_map()
    chosen = [specs[code] for code in dict.fromkeys(module_codes) if code in specs]

    entities: list[dict[str, Any]] = [PLATFORM_ENTITY]
    seen_tables = {PLATFORM_ENTITY["table"]}
    for spec in chosen:
        for ent in spec["entities"]:
            if ent["table"] in seen_tables:
                continue
            seen_tables.add(ent["table"])
            owner = table_map[ent["table"]]["_owner"]
            entities.append({**ent, "module_code": owner})

    ordered = topological_order(entities)
    for ent in ordered:
        ent.setdefault("module_code", ent.get("_owner", ""))

    return {
        "modules": chosen,
        "entities": ordered,
        "tables": [ent["table"] for ent in ordered],
        "counts": {
            "modules": len(chosen),
            "entities": len(ordered),
            "fields": sum(len(e["fields"]) for e in ordered),
        },
    }


def coverage_report() -> dict[str, Any]:
    """گزارش پوشش مشخصات دامنه (دست‌نویس در برابر خودکار)."""
    specs = all_specs()
    handwritten = [c for c, s in specs.items() if not s.get("derived")]
    derived = [c for c, s in specs.items() if s.get("derived")]
    return {
        "total_modules": len(specs),
        "handwritten": sorted(handwritten),
        "handwritten_count": len(handwritten),
        "derived": sorted(derived),
        "derived_count": len(derived),
        "entities_total": sum(len(s["entities"]) for s in specs.values()) + 1,
        "fields_total": sum(len(e["fields"]) for s in specs.values() for e in s["entities"]),
    }
