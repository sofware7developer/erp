"""
DSL تعریف کاتالوگ ماژول‌های ERP
================================
ساختار سلسله‌مراتبی چهار سطحی:

    بخش (Section)  ->  ماژول (Module)  ->  زیرماژول (Group)  ->  زیرمجموعه (Item)
        A                A1                  A1.1                 A1.1.1

قواعد نویسه‌گذاری آیتم‌ها (Item) برای کاهش خطا و تضمین شماره‌گذاری خودکار:

    "متن ساده"                     -> یک زیرمجموعه معمولی
    "🤖 متن"                       -> یک نقطه هوش مصنوعی (AI Capability)
    "متن @@dep=A1.2,A2.1"          -> دارای وابستگی صریح به ماژول/زیرماژول دیگر
    "متن @@ent=work_orders"        -> مرتبط با موجودیت داده‌ای مشخص (برای تولید کد)
    "متن @@role=planner"           -> نقش سازمانی مسئول این قابلیت

شماره آیتم‌ها (A1.1.3 و ...) به‌صورت خودکار و بر اساس ترتیب تولید می‌شود،
بنابراین نویسنده کاتالوگ هرگز نیازی به نوشتن دستی شماره‌ها ندارد.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

AI_MARKER = "🤖"


# --------------------------------------------------------------------------- #
# تجزیه برچسب‌های متادیتا
# --------------------------------------------------------------------------- #
def _parse_meta(raw: str) -> tuple[str, dict[str, list[str]]]:
    """متن آیتم را به (نام تمیز، متادیتا) تبدیل می‌کند."""
    meta: dict[str, list[str]] = {}
    name = raw
    if "@@" in raw:
        name, _, tail = raw.partition("@@")
        for chunk in tail.split("@@"):
            chunk = chunk.strip()
            if not chunk or "=" not in chunk:
                continue
            key, _, value = chunk.partition("=")
            meta[key.strip()] = [v.strip() for v in value.split(",") if v.strip()]
    return name.strip(), meta


def _build_item(raw: str, code: str) -> dict[str, Any]:
    text, meta = _parse_meta(raw)
    is_ai = text.startswith(AI_MARKER)
    if is_ai:
        text = text[len(AI_MARKER):].strip()
        if text.upper().startswith("AI:"):
            text = text[3:].strip()
    return {
        "code": code,
        "name": text,
        "ai": is_ai,
        "deps": meta.get("dep", []),
        "entity": (meta.get("ent") or [None])[0],
        "role": (meta.get("role") or [None])[0],
        "level": 4,
    }


def group(code: str, name: str, items: list[str], name_en: str | None = None) -> dict[str, Any]:
    """تعریف یک زیرماژول (سطح سوم) همراه با زیرمجموعه‌های آن (سطح چهارم)."""
    built = [_build_item(text, f"{code}.{index}") for index, text in enumerate(items, start=1)]
    return {
        "code": code,
        "name": name,
        "name_en": name_en or "",
        "level": 3,
        "items": built,
        "ai_count": sum(1 for it in built if it["ai"]),
        "item_count": len(built),
    }


def module(
    code: str,
    name: str,
    name_en: str,
    groups: list[dict[str, Any]],
    *,
    icon: str = "cube",
    summary: str = "",
    color: str = "#6366f1",
) -> dict[str, Any]:
    """تعریف یک ماژول (سطح دوم)."""
    return {
        "code": code,
        "name": name,
        "name_en": name_en,
        "level": 2,
        "icon": icon,
        "summary": summary,
        "color": color,
        "groups": groups,
        "group_count": len(groups),
        "item_count": sum(g["item_count"] for g in groups),
        "ai_count": sum(g["ai_count"] for g in groups),
    }


def section(
    code: str,
    name: str,
    name_en: str,
    modules: list[dict[str, Any]],
    *,
    icon: str = "layers",
    color: str = "#6366f1",
    description: str = "",
) -> dict[str, Any]:
    """تعریف یک بخش (سطح اول)."""
    return {
        "code": code,
        "name": name,
        "name_en": name_en,
        "level": 1,
        "icon": icon,
        "color": color,
        "description": description,
        "modules": modules,
        "module_count": len(modules),
        "item_count": sum(m["item_count"] for m in modules),
        "ai_count": sum(m["ai_count"] for m in modules),
    }


# --------------------------------------------------------------------------- #
# ابزارهای کمکی روی کاتالوگ assembled شده
# --------------------------------------------------------------------------- #
@dataclass
class CatalogIndex:
    """ایندکس سریع برای جست‌وجو و حل وابستگی‌ها."""

    sections: dict[str, dict[str, Any]] = field(default_factory=dict)
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    items: dict[str, dict[str, Any]] = field(default_factory=dict)
    ai_items: dict[str, dict[str, Any]] = field(default_factory=dict)
    module_of_group: dict[str, str] = field(default_factory=dict)
    module_of_item: dict[str, str] = field(default_factory=dict)
    section_of_module: dict[str, str] = field(default_factory=dict)
    search_blob: dict[str, str] = field(default_factory=dict)

    @classmethod
    def build(cls, catalog: list[dict[str, Any]]) -> "CatalogIndex":
        index = cls()
        for sec in catalog:
            index.sections[sec["code"]] = sec
            for mod in sec["modules"]:
                index.modules[mod["code"]] = mod
                index.section_of_module[mod["code"]] = sec["code"]
                for grp in mod["groups"]:
                    index.groups[grp["code"]] = grp
                    index.module_of_group[grp["code"]] = mod["code"]
                    for item in grp["items"]:
                        index.items[item["code"]] = item
                        index.module_of_item[item["code"]] = mod["code"]
                        if item["ai"]:
                            index.ai_items[item["code"]] = item
                        index.search_blob[item["code"]] = " ".join(
                            [
                                item["code"],
                                item["name"],
                                grp["code"],
                                grp["name"],
                                mod["code"],
                                mod["name"],
                                mod["name_en"],
                                sec["code"],
                                sec["name"],
                                sec["name_en"],
                            ]
                        ).lower()
        return index

    def counts(self) -> dict[str, int]:
        return {
            "sections": len(self.sections),
            "modules": len(self.modules),
            "groups": len(self.groups),
            "items": len(self.items),
            "ai_points": len(self.ai_items),
        }
