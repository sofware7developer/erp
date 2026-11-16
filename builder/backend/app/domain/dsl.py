# -*- coding: utf-8 -*-
"""
DSL تعریف موجودیت‌های داده‌ای
=============================
برای تولید خودکار مایگریشن، مدل Eloquent، کنترلر، روت و صفحه ری‌اکت،
هر موجودیت با یک رشته فشرده تعریف می‌شود:

    نام_فیلد|نوع|برچسب فارسی|پرچم‌ها

انواع پشتیبانی‌شده:
    string, text, integer, bigint, decimal, boolean, date, datetime,
    time, json, uuid, enum(گزینه۱,گزینه۲,...), foreign(جدول_مقصد)

پرچم‌ها (اختیاری، با کاما جدا می‌شوند):
    unique, nullable, index, indexed, default=..., unsigned, hidden,
    soft (فقط در سطح موجودیت), searchable, required

نمونه:
    entity("WorkOrder", "دستور کار تولید", [
        "code|string|شماره دستور کار|unique,index",
        "product_id|foreign(items)|کالا|required,index",
        "planned_qty|decimal|مقدار برنامه‌ریزی‌شده|default=0",
        "status|enum(draft,released,started,done,closed)|وضعیت|default=draft",
        "notes|text|توضیحات|nullable",
    ])
"""

from __future__ import annotations

import re
from typing import Any

SIMPLE_TYPES = {
    "string": "string",
    "text": "text",
    "integer": "integer",
    "bigint": "bigInteger",
    "decimal": "decimal",
    "boolean": "boolean",
    "date": "date",
    "datetime": "dateTime",
    "time": "time",
    "json": "json",
    "uuid": "uuid",
}

DEFAULT_DECIMAL_PRECISION = (18, 4)


def snake_case(text: str) -> str:
    """تبدیل متن انگلیسی به snake_case."""
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip()
    words = []
    for token in text.split():
        parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+|\d+", token)
        words.extend(p.lower() for p in parts)
    return "_".join(words) or "item"


IRREGULAR_PLURALS = {
    "analysis": "analyses",
    "basis": "bases",
    "datum": "data",
    "index": "indices",
    "matrix": "matrices",
    "status": "statuses",
    "address": "addresses",
    "process": "processes",
    "series": "series",
}


def pluralize(word: str) -> str:
    """جمع‌سازی انگلیسی برای نام جدول (با پشتیبانی از بی‌قاعده‌ها)."""
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    # کلمات ختم‌شده به «is» مانند analysis -> analyses
    if word.endswith("is") and len(word) > 3:
        return word[:-2] + "es"
    if word.endswith("fe"):
        return word[:-2] + "ves"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if word.endswith("f") and not word.endswith("ff"):
        return word[:-1] + "ves"
    return word + "s"


def pascal_case(text: str) -> str:
    """تبدیل متن به PascalCase برای نام کلاس."""
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip()
    return "".join(part[:1].upper() + part[1:] for part in text.split()) or "Item"


def singularize(word: str) -> str:
    """مفردسازی ساده برای ساخت نام کلاس از نام جدول."""
    if word.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"
    if word.endswith(("ses", "xes", "zes", "ches", "shes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def parse_field(spec: str) -> dict[str, Any]:
    """تجزیه تعریف یک فیلد."""
    parts = [p.strip() for p in spec.split("|")]
    if len(parts) < 2:
        raise ValueError(f"تعریف فیلد نامعتبر (حداقل نام و نوع لازم است): {spec!r}")

    name = parts[0]
    raw_type = parts[1]
    label = parts[2] if len(parts) > 2 and parts[2] else name
    flags_raw = parts[3] if len(parts) > 3 else ""
    flags = {f.strip() for f in flags_raw.split(",") if f.strip()}

    field: dict[str, Any] = {
        "name": name,
        "label": label,
        "nullable": "nullable" in flags,
        "unique": "unique" in flags,
        "index": "index" in flags or "indexed" in flags,
        "searchable": "searchable" in flags,
        "hidden": "hidden" in flags,
        "required": "required" in flags,
    }

    for flag in flags:
        if flag.startswith("default="):
            field["default"] = flag.split("=", 1)[1]

    if raw_type.startswith("enum(") and raw_type.endswith(")"):
        field["type"] = "enum"
        field["options"] = [o.strip() for o in raw_type[5:-1].split(",") if o.strip()]
    elif raw_type.startswith("foreign(") and raw_type.endswith(")"):
        field["type"] = "foreign"
        field["references_table"] = raw_type[8:-1]
        field["index"] = True
        if "nullable" not in flags:
            field["nullable"] = False
    else:
        if raw_type not in SIMPLE_TYPES:
            raise ValueError(f"نوع فیلد ناشناخته در {spec!r}: {raw_type}")
        field["type"] = raw_type

    return field


def entity(
    name: str,
    label_fa: str,
    fields: list[str],
    *,
    table: str | None = None,
    label_en: str | None = None,
    soft_deletes: bool = True,
    timestamps: bool = True,
    has_code: bool = True,
    icon: str = "file-text",
    notes: str = "",
    owner: str = "tenant",
) -> dict[str, Any]:
    """تعریف یک موجودیت (جدول دیتابیس)."""
    parsed = [parse_field(spec) for spec in fields]
    names = [f["name"] for f in parsed]
    if len(names) != len(set(names)):
        duplicates = {n for n in names if names.count(n) > 1}
        raise ValueError(f"فیلد تکراری در موجودیت {name}: {sorted(duplicates)}")

    table_name = table or pluralize(snake_case(name))
    return {
        "name": name,
        "label_fa": label_fa,
        "label_en": label_en or name,
        "table": table_name,
        "fields": parsed,
        "soft_deletes": soft_deletes,
        "timestamps": timestamps,
        "has_code": has_code and any(f["name"] == "code" for f in parsed),
        "icon": icon,
        "notes": notes,
        "owner": owner,
    }


def module_spec(
    code: str,
    name_en: str,
    label_fa: str,
    entities: list[dict[str, Any]],
    *,
    menu_group: str = "",
    description: str = "",
    ai_endpoints: list[str] | None = None,
    priority: int = 3,
) -> dict[str, Any]:
    """تعریف مشخصات فنی یک ماژول برای تولید کد."""
    slug = snake_case(name_en)
    return {
        "code": code,
        "name_en": name_en,
        "slug": slug,
        "label_fa": label_fa,
        "menu_group": menu_group,
        "description": description,
        "entities": entities,
        "ai_endpoints": ai_endpoints or [],
        "priority": priority,
        "derived": False,
    }
