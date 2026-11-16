# -*- coding: utf-8 -*-
"""
تولید خودکار مشخصات دامنه (Derived Specs)
=========================================
برای هر ماژولی که مشخصات دست‌نویس ندارد، از روی زیرماژول‌های کاتالوگ
یک موجودیت CRUD استاندارد ساخته می‌شود تا بسته خروجی «کامل» باشد:

  * هر زیرماژول (مثلاً B1.1 بازرسی ورودی) یک جدول می‌گیرد
  * فیلدهای پایه (کد، عنوان، وضعیت، تاریخ، مسئول، پیوست، ویژگی‌ها)
  * فیلدهای تخصصی بر پایه کلیدواژه‌های نام انگلیسی زیرماژول
  * ارجاع به موجودیت‌های پایه (کاربر، واحد سازمانی، کالا، تجهیز و ...)

این مکانیزم تضمین می‌کند که حتی اگر کاربر ماژولی کم‌تر شناخته‌شده را
انتخاب کند، مایگریشن/مدل/کنترلر/روت/صفحه UI مربوطه در بسته وجود دارد.
"""

from __future__ import annotations

import re
from typing import Any

from ..catalog.registry import index
from .dsl import entity, module_spec, pascal_case, pluralize, snake_case

BASE_FIELDS = [
    "code|string|کد|unique,index",
    "title|string|عنوان|required,searchable",
    "ref_no|string|شماره مرجع|nullable,index",
    "description|text|شرح|nullable",
    "category|string|دسته‌بندی|nullable,index",
    "priority|enum(low,medium,high,critical)|اولویت|default=medium,index",
    "occurred_at|datetime|تاریخ رخداد|nullable,index",
    "due_date|date|سررسید|nullable,index",
    "quantity|decimal|مقدار|default=0",
    "amount|decimal|مبلغ|default=0",
    "currency|string|ارز|default=IRR",
    "owner_id|foreign(users)|مسئول|nullable,index",
    "department_id|foreign(departments)|واحد سازمانی|nullable,index",
    "attachments|json|پیوست‌ها|nullable",
    "attributes|json|ویژگی‌های تکمیلی|nullable",
    "status|enum(draft,submitted,in_progress,reviewed,completed,closed,cancelled)|وضعیت|default=draft,index",
]

# کلیدواژه -> فیلدهای تخصصی افزوده
KEYWORD_FIELDS: list[tuple[tuple[str, ...], list[str]]] = [
    (("report", "record", "log", "reading", "tracking", "monitoring", "measurement"), [
        "value|decimal|مقدار اندازه‌گیری‌شده|default=0",
        "uom|string|واحد اندازه‌گیری|nullable",
        "period_label|string|دوره گزارش|nullable,index",
        "measured_by|foreign(employees)|ثبت‌کننده|nullable,index",
    ]),
    (("plan", "schedule", "budget", "program", "forecast", "roster"), [
        "start_date|date|تاریخ شروع|nullable,index",
        "end_date|date|تاریخ پایان|nullable,index",
        "planned_qty|decimal|مقدار برنامه|default=0",
        "actual_qty|decimal|مقدار واقعی|default=0",
        "progress_percent|integer|درصد پیشرفت|default=0",
    ]),
    (("audit", "inspection", "check", "assessment", "evaluation", "review", "test"), [
        "score|decimal|امتیاز|nullable,index",
        "result|enum(pass,fail,conditional,pending)|نتیجه|nullable,index",
        "findings|json|یافته‌ها|nullable",
        "inspector_id|foreign(employees)|ارزیاب|nullable,index",
        "checked_at|datetime|زمان ارزیابی|nullable,index",
    ]),
    (("cost", "price", "invoice", "payment", "fee", "expense", "budget", "financial", "commission"), [
        "unit_price|decimal|بهای واحد|default=0",
        "total_amount|decimal|مبلغ کل|default=0,index",
        "tax_amount|decimal|مالیات|default=0",
        "journal_entry_id|foreign(journal_entries)|سند حسابداری|nullable,index",
        "cost_center_id|foreign(cost_centers)|مرکز هزینه|nullable,index",
    ]),
    (("request", "approval", "workflow", "requisition", "order", "permit", "claim"), [
        "requested_by|foreign(users)|درخواست‌کننده|nullable,index",
        "requested_at|datetime|زمان درخواست|nullable,index",
        "approved_by|foreign(users)|تأییدکننده|nullable,index",
        "approved_at|datetime|زمان تأیید|nullable,index",
        "approval_status|enum(pending,approved,rejected)|وضعیت تأیید|default=pending,index",
    ]),
    (("equipment", "machine", "asset", "vehicle", "sensor", "device", "tool", "robot"), [
        "equipment_id|foreign(equipments)|تجهیز مرتبط|nullable,index",
        "serial_no|string|شماره سریال|nullable,index",
        "location|string|محل استقرار|nullable,index",
        "maintenance_due|date|سررسید نگهداری|nullable,index",
    ]),
    (("employee", "personnel", "staff", "training", "skill", "shift", "attendance", "recruit", "interview"), [
        "employee_id|foreign(employees)|کارمند مرتبط|nullable,index",
        "shift_id|foreign(shifts)|شیفت|nullable,index",
    ]),
    (("customer", "supplier", "contractor", "lead", "account", "vendor", "client"), [
        "customer_id|foreign(customers)|مشتری مرتبط|nullable,index",
        "supplier_id|foreign(suppliers)|تأمین‌کننده مرتبط|nullable,index",
        "contractor_id|foreign(contractors)|پیمانکار مرتبط|nullable,index",
    ]),
    (("product", "item", "material", "bom", "inventory", "stock", "batch", "lot", "spare"), [
        "item_id|foreign(items)|کالا مرتبط|nullable,index",
        "warehouse_id|foreign(warehouses)|انبار|nullable,index",
        "lot_batch_no|string|شماره لات یا بچ|nullable,index",
    ]),
    (("production", "work order", "operation", "routing", "assembly", "line"), [
        "work_order_id|foreign(work_orders)|دستور کار|nullable,index",
        "work_center_id|foreign(work_centers)|ایستگاه کاری|nullable,index",
    ]),
    (("meeting", "session", "event", "incident", "accident", "alert", "alarm"), [
        "scheduled_at|datetime|زمان برنامه‌ریزی‌شده|nullable,index",
        "severity|enum(low,medium,high,critical)|شدت|default=medium,index",
    ]),
    (("document", "file", "record", "certificate", "standard", "policy"), [
        "document_id|foreign(documents)|سند مرتبط|nullable,index",
        "version|string|نسخه|default=1.0",
        "valid_until|date|اعتبار تا|nullable,index",
    ]),
    (("risk", "hazard", "safety", "compliance", "ncr", "non-conformance", "complaint"), [
        "severity|enum(low,medium,high,critical)|شدت|default=medium,index",
        "risk_level|enum(low,medium,high,critical)|سطح ریسک|default=medium,index",
        "corrective_action|text|اقدام اصلاحی|nullable",
    ]),
    (("energy", "water", "waste", "emission", "environment", "carbon"), [
        "meter_id|foreign(energy_meters)|کنتور مرتبط|nullable,index",
        "consumption|decimal|مقدار مصرف|default=0",
        "uom|string|واحد مصرف|nullable",
    ]),
    (("kpi", "indicator", "metric", "dashboard", "scorecard"), [
        "kpi_id|foreign(kpi_definitions)|شاخص مرتبط|nullable,index",
        "target_value|decimal|مقدار هدف|nullable",
        "actual_value|decimal|مقدار واقعی|nullable",
        "variance_percent|decimal|انحراف درصدی|nullable",
    ]),
    (("project", "wbs", "milestone", "task", "activity"), [
        "project_id|foreign(projects)|پروژه مرتبط|nullable,index",
        "progress_percent|integer|درصد پیشرفت|default=0",
    ]),
]

# نام‌های رزروشده پایتون/PHP که نباید به عنوان نام کلاس استفاده شوند
RESERVED_NAMES = {"Class", "Abstract", "Interface", "Trait", "List", "Array", "Object", "Function", "Return"}


def _dedupe_fields(fields: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for field in fields:
        name = field.split("|", 1)[0]
        if name in seen:
            continue
        seen.add(name)
        result.append(field)
    return result


def _extra_fields(name_en: str) -> list[str]:
    lowered = name_en.lower()
    extra: list[str] = []
    for keywords, fields in KEYWORD_FIELDS:
        if any(keyword in lowered for keyword in keywords):
            extra.extend(fields)
    return extra


def _clean_class_name(raw: str, fallback: str) -> str:
    """ساخت نام کلاس معتبر از نام انگلیسی زیرماژول."""
    text = re.sub(r"\(.*?\)", " ", raw)          # حذف عبارت‌های داخل پرانتز
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", text)  # حذف علائم
    text = re.sub(r"\b(and|or|the|of|for|in|to|with|management|system)\b", " ", text, flags=re.I)
    words = [w for w in text.split() if len(w) > 1][:4]
    name = pascal_case(" ".join(words)) if words else pascal_case(fallback)
    if not name:
        name = pascal_case(fallback)
    if name[0].isdigit():
        name = "M" + name
    if name in RESERVED_NAMES:
        name = name + "Record"
    return name


def _unique_class_name(
    base_name: str,
    module_name_en: str,
    module_code: str,
    used_tables: set[str],
    used_names: set[str],
) -> str:
    """ساخت نام کلاس یکتا با پیشوند نام ماژول در صورت برخورد نام جدول."""
    prefix_words = [
        w for w in re.split(r"[^A-Za-z]+", module_name_en)
        if len(w) > 2 and w.lower() not in {"management", "and", "the", "system", "with", "for"}
    ]
    candidates = [base_name]
    for word in prefix_words[:2]:
        candidates.append(pascal_case(word) + base_name)
    candidates.append(pascal_case(" ".join(prefix_words[:2])) + base_name)
    candidates.append(f"M{module_code.replace('.', '')}{base_name}")

    for candidate in candidates:
        table = pluralize(snake_case(candidate))
        if table not in used_tables and candidate not in used_names:
            return candidate

    counter = 2
    while True:
        candidate = f"{candidates[-1]}{counter}"
        table = pluralize(snake_case(candidate))
        if table not in used_tables and candidate not in used_names:
            return candidate
        counter += 1


def derive_module_spec(
    module_code: str,
    module_data: dict[str, Any],
    used_tables: set[str] | None = None,
    used_names: set[str] | None = None,
) -> dict[str, Any]:
    """ساخت مشخصات دامنه خودکار برای یک ماژول."""
    entities: list[dict[str, Any]] = []
    used_tables = used_tables if used_tables is not None else set()
    used_names = used_names if used_names is not None else set()

    for group in module_data["groups"]:
        raw_name = _clean_class_name(group["name_en"] or group["name"], f"{module_code}Record")
        class_name = _unique_class_name(
            raw_name, module_data.get("name_en", ""), module_code, used_tables, used_names
        )
        used_names.add(class_name)
        used_tables.add(pluralize(snake_case(class_name)))

        fields = _dedupe_fields(BASE_FIELDS + _extra_fields(group["name_en"] or ""))
        entities.append(
            entity(
                class_name,
                group["name"],
                fields,
                label_en=group["name_en"] or class_name,
                icon="layers",
                notes=(
                    "موجودیت استاندارد تولیدشده برای زیرماژول "
                    f"{group['code']} — قابل گسترش با فیلدهای سفارشی از ماژول Low-Code."
                ),
            )
        )

    return module_spec(
        module_code,
        module_data["name_en"],
        module_data["name"],
        entities,
        menu_group=_menu_group(module_code),
        description=module_data.get("summary", ""),
        ai_endpoints=["/api/ai/classify"],
        priority=4,
    ) | {"derived": True}


SECTION_MENU = {
    "A": "تولید", "B": "کیفیت", "C": "نت", "D": "زنجیره تأمین", "E": "فروش",
    "F": "مالی", "G": "منابع انسانی", "H": "مهندسی", "I": "پروژه", "J": "IoT",
    "K": "هوش مصنوعی", "L": "هوش تجاری", "M": "HSE", "N": "انرژی", "O": "حاکمیت",
    "P": "اسناد و فرآیند", "Q": "لجستیک داخلی", "R": "استراتژی", "S": "مدیریت سیستم",
    "T": "صنایع تخصصی", "U": "پیمانکاران", "V": "پایش عملکرد",
}


def _menu_group(module_code: str) -> str:
    return SECTION_MENU.get(module_code[:1], "سایر")


def derive_all(
    covered_codes: set[str],
    used_tables: set[str] | None = None,
    used_names: set[str] | None = None,
) -> list[dict[str, Any]]:
    """تولید مشخصات دامنه خودکار برای همه ماژول‌های پوشش‌داده‌نشده."""
    idx = index()
    shared_tables = set(used_tables or set())
    shared_names = set(used_names or set())
    derived: list[dict[str, Any]] = []
    for code in sorted(idx.modules, key=lambda c: (c[0], len(c), c)):
        if code in covered_codes:
            continue
        derived.append(derive_module_spec(code, idx.modules[code], shared_tables, shared_names))
    return derived
