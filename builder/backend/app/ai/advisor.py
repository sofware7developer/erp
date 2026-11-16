# -*- coding: utf-8 -*-
"""
دستیار هوشمند پیکربندی
=======================
دو لایه تصمیم‌گیری:

  ۱) موتور قاعده‌محور داخلی (همیشه در دسترس، بدون اینترنت)
     بر پایه صنعت، اندازه سازمان، تعداد شیفت، اهداف و سطح بودجه
  ۲) لایه AvalAI (اختیاری) برای تولید استدلال متنی فارسی و بازبینی پیشنهادها

خروجی: ماژول‌های پیشنهادی، نقاط AI پیشنهادی، استدلال‌ها و برنامه فازبندی استقرار.
"""

from __future__ import annotations

from typing import Any

from ..catalog.registry import index
from ..domain.registry import resolve_modules
from ..schemas import PhasePlan
from .llm import chat, is_configured, parse_json_answer

# --------------------------------------------------------------------------- #
# قواعد پیشنهاد ماژول بر اساس اهداف کسب‌وکاری
# --------------------------------------------------------------------------- #
GOAL_MODULES: dict[str, list[str]] = {
    "کاهش ضایعات": ["B1", "B3", "B4", "A2", "K3", "K6", "V2"],
    "بهبود کیفیت": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "K3"],
    "کاهش توقفات": ["C1", "C2", "C3", "C4", "C5", "J1", "J2", "J3", "K1"],
    "نگهداری و تعمیرات": ["C1", "C2", "C3", "C4", "C5", "C6", "J5"],
    "بهینه‌سازی موجودی": ["D3", "D4", "D6", "K2", "A1", "L3"],
    "زنجیره تأمین": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "K2"],
    "خرید و تدارکات": ["D1", "D2", "U3", "F3", "K5"],
    "افزایش فروش": ["E1", "E2", "E3", "E5", "E7", "K4", "K5"],
    "رضایت مشتری": ["E2", "E4", "E6", "K4", "L1"],
    "خدمات پس از فروش": ["E4", "B7", "C4", "D8", "S5"],
    "دقت مالی": ["F1", "F2", "F3", "F4", "F6", "F9", "F12", "K6"],
    "بهای تمام شده": ["F6", "A3", "A4", "F7", "L3"],
    "بودجه‌ریزی": ["F7", "F12", "L1", "L3", "R2"],
    "مالیات و مؤدیان": ["F9", "S3", "F1", "E1", "D1"],
    "منابع انسانی": ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G12"],
    "حقوق و دستمزد": ["G1", "G3", "G4", "G5", "F1", "S3"],
    "بهره‌وری نیرو": ["G3", "G4", "G6", "V2", "V3", "L1"],
    "آموزش و مهارت": ["G7", "G8", "G6", "R4", "B2"],
    "مهندسی و طراحی": ["H1", "H2", "H3", "H4", "H5", "A3", "A6"],
    "مدیریت پروژه": ["I1", "I2", "I3", "I4", "I5", "F10"],
    "اتوماسیون و IoT": ["J1", "J2", "J3", "J4", "J5", "J6", "K6"],
    "هوش مصنوعی": ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "L3", "L4"],
    "گزارش و داشبورد": ["L1", "L2", "L3", "L4", "V1", "V3"],
    "ایمنی و HSE": ["M1", "M2", "M3", "M4", "M5", "K3", "O3"],
    "انرژی و محیط زیست": ["N1", "N2", "N3", "M3", "J2", "K2"],
    "ریسک و انطباق": ["O1", "O2", "O3", "O4", "F11", "L1"],
    "اسناد و مکاتبات": ["P1", "P2", "P3", "P4", "K4"],
    "گردش کار و فرآیند": ["P2", "P3", "S7", "L4", "K5"],
    "لجستیک داخلی": ["Q1", "Q2", "Q3", "D3", "D5", "K2"],
    "استراتژی و اهداف": ["R1", "R2", "R3", "R4", "V3", "L1"],
    "امنیت اطلاعات": ["S1", "O4", "S6", "K6", "F11"],
    "یکپارچه‌سازی": ["S2", "S3", "L4", "D1", "E1"],
    "موبایل و دسترسی": ["S5", "S4", "L1", "G12"],
    "پیمانکاران": ["U1", "U2", "U3", "C6", "F3"],
    "پایش عملکرد": ["V1", "V2", "V3", "L1", "J3", "R2"],
    "ردیابی و رهگیری": ["B7", "D4", "A2", "J2", "Q3"],
    "تولید و برنامه‌ریزی": ["A1", "A2", "A3", "A4", "A6", "A8", "D4", "K2"],
}

INDUSTRY_EXTRA: dict[str, list[str]] = {
    "food_pharma": ["T1", "A5", "B6", "B7", "M5", "N3", "O3", "B5"],
    "automotive": ["T2", "A8", "B2", "B3", "S2", "D6", "H1", "H2", "J3", "K3"],
    "metals": ["T3", "A5", "J1", "J2", "N1", "M4", "C6", "B6"],
    "textile": ["T4", "A6", "A8", "E7", "Q3", "G9"],
    "electronics": ["T5", "A7", "A8", "B3", "H1", "J1", "K3"],
    "petrochemical": ["T6", "A5", "J1", "J4", "M4", "M5", "N1", "N3", "D7"],
    "packaging_print": ["T7", "A7", "Q3", "E7", "B1"],
    "general_discrete": ["A6", "A7", "A8", "H1", "H5", "J3"],
    "process": ["A5", "B6", "J2", "N1"],
    "smb": [],
    "enterprise": [],
}

# اندازه سازمان -> سطح پوشش ماژول‌های پشتیبانی
SIZE_PROFILES = {
    "small": {"max_modules": 45, "ai_level": "essential"},
    "medium": {"max_modules": 85, "ai_level": "recommended"},
    "large": {"max_modules": 130, "ai_level": "advanced"},
}

AI_LEVEL_ENGINES = {
    "essential": ["forecasting", "classification"],
    "recommended": ["forecasting", "classification", "optimization", "anomaly"],
    "advanced": ["forecasting", "classification", "optimization", "anomaly",
                 "quality_spc", "reliability", "recommendation"],
    "all": None,
}

# --------------------------------------------------------------------------- #
# فازبندی استاندارد استقرار
# --------------------------------------------------------------------------- #
PHASE_TEMPLATE = [
    {
        "title": "فاز ۱ — زیرساخت، داده اصلی و امنیت",
        "description": "راه‌اندازی هسته سامانه، کاربران و دسترسی‌ها، داده اصلی کالا و انبار، "
                       "دفتر کل، اسناد و موتور گردش‌کار.",
        "modules": ["S1", "S2", "S6", "G1", "D4", "D3", "F1", "P1", "P2", "V3", "L4", "O4"],
        "duration_months": 2,
        "milestones": [
            "استقرار زیرساخت (Docker، پایگاه داده، صف، پشتیبان‌گیری)",
            "تعریف ساختار سازمانی، کاربران، نقش‌ها و دسترسی‌ها",
            "بارگذاری داده اصلی کالا، انبار و چارت حساب‌ها",
            "آماده‌سازی موتور گردش‌کار و مخزن اسناد",
        ],
        "deliverables": [
            "محیط عملیاتی و محیط آزمون",
            "داده اصلی پاک‌سازی‌شده",
            "راهنمای کاربری مدیریت سیستم",
        ],
    },
    {
        "title": "فاز ۲ — زنجیره تأمین و تولید",
        "description": "خرید، تأمین‌کنندگان، انبارگردانی، برنامه‌ریزی تولید، دستور کار، BOM و مسیر تولید.",
        "modules": ["D1", "D2", "D5", "D8", "A1", "A2", "A3", "A4", "A6", "U1", "U2"],
        "duration_months": 3,
        "milestones": [
            "اجرای چرخه کامل خرید تا رسید کالا",
            "اجرای MRP و صدور دستور کار تولید",
            "عملیاتی‌شدن انبار و بارکدگذاری",
        ],
        "deliverables": [
            "فرآیندهای خرید و انبار عملیاتی",
            "گزارش‌های موجودی و خرید",
            "ترمینال کف کارخانه",
        ],
    },
    {
        "title": "فاز ۳ — فروش، مالی و منابع انسانی",
        "description": "سفارش فروش و قیمت‌گذاری، دریافتنی و پرداختنی، اسناد مالی، مالیات و مؤدیان، "
                       "حضور و غیاب و حقوق و دستمزد.",
        "modules": ["E1", "E2", "E4", "E6", "F2", "F3", "F4", "F5", "F9", "F12", "G3", "G4", "G5", "S3"],
        "duration_months": 3,
        "milestones": [
            "صدور فاکتور و اتصال به سامانه مؤدیان",
            "بستن دوره مالی ماهانه در سامانه",
            "اجرای اولین دوره حقوق و دستمزد",
        ],
        "deliverables": [
            "گردش کامل فروش تا وصول مطالبات",
            "گزارش‌های مالی قانونی",
            "فیش حقوقی و فهرست بیمه",
        ],
    },
    {
        "title": "فاز ۴ — کیفیت، نت و هوش تجاری",
        "description": "کنترل و تضمین کیفیت، SPC، کالیبراسیون، آزمایشگاه، ردیابی، نگهداری پیشگیرانه و "
                       "پیش‌بینانه، بهای تمام‌شده و داشبوردها.",
        "modules": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "C1", "C2", "C3", "C4", "C5",
                    "F6", "F7", "F8", "L1", "L2", "L3", "V1", "V2"],
        "duration_months": 4,
        "milestones": [
            "عملیاتی‌شدن بازرسی‌ها و ثبت عدم انطباق",
            "اجرای برنامه نگهداری پیشگیرانه",
            "راه‌اندازی داشبوردهای مدیریتی و گزارش‌ساز",
            "محاسبه بهای تمام‌شده واقعی",
        ],
        "deliverables": [
            "پرونده کیفیت محصول و ردیابی لات",
            "شاخص‌های نت (MTBF، MTTR، دسترس‌پذیری)",
            "داشبورد مدیریتی روزانه",
        ],
    },
    {
        "title": "فاز ۵ — هوش مصنوعی، IoT و ماژول‌های تخصصی",
        "description": "اتصال تجهیزات و سنسورها، موتورهای هوش مصنوعی، ماژول‌های تخصصی صنعت، HSE، "
                       "انرژی، استراتژی و پلتفرم کم‌کد.",
        "modules": ["J1", "J2", "J3", "J4", "J5", "J6", "K1", "K2", "K3", "K4", "K5", "K6", "K7",
                    "T1", "T2", "T3", "T4", "T5", "T6", "T7", "M1", "M2", "M3", "M4", "M5",
                    "N1", "N2", "N3", "O1", "O2", "O3", "H1", "H2", "H3", "H4", "H5",
                    "I1", "I2", "I3", "I4", "I5", "R1", "R2", "R3", "R4", "Q1", "Q2", "Q3",
                    "E3", "E5", "E7", "G2", "G6", "G7", "G8", "G9", "G10", "G11", "G12",
                    "P3", "P4", "S4", "S5", "S7", "U3", "F10", "F11", "C6", "D6", "D7", "A5", "A7", "A8"],
        "duration_months": 5,
        "milestones": [
            "اتصال تجهیزات و جمع‌آوری داده بلادرنگ",
            "استقرار مدل‌های هوش مصنوعی و پایش آن‌ها",
            "فعال‌سازی ماژول تخصصی صنعت",
            "راه‌اندازی مرکز فرماندهی و پایش عملکرد",
        ],
        "deliverables": [
            "سرویس AI عملیاتی با پایش مدل",
            "داشبورد بلادرنگ مرکز فرماندهی",
            "مستندات آموزش و مدیریت تغییر",
        ],
    },
]


def _size_bucket(employees: int) -> str:
    if employees <= 60:
        return "small"
    if employees <= 400:
        return "medium"
    return "large"


def _ai_level(budget_level: str, ai_appetite: str, size_bucket: str) -> str:
    score = {"low": 0, "medium": 1, "high": 2}
    total = score.get(budget_level, 1) + score.get(ai_appetite, 1) + score.get(
        {"small": 0, "medium": 1, "large": 2}[size_bucket], 1
    )
    if total <= 1:
        return "essential"
    if total <= 3:
        return "recommended"
    if total <= 4:
        return "advanced"
    return "all"


def recommend_modules(
    industry: str = "general_discrete",
    employees_count: int = 150,
    shifts_per_day: int = 2,
    production_lines: int = 3,
    warehouses_count: int = 2,
    goals: list[str] | None = None,
    budget_level: str = "medium",
    ai_appetite: str = "medium",
) -> dict[str, Any]:
    """پیشنهاد قاعده‌محور ماژول‌ها بر اساس مشخصات کارخانه."""
    from ..presets import PRESETS, apply_preset

    idx = index()
    goals = goals or []
    size_bucket = _size_bucket(employees_count)
    ai_level = _ai_level(budget_level, ai_appetite, size_bucket)

    # ۱) پایه از نزدیک‌ترین پریست صنعتی
    preset_key = industry if any(p["key"] == industry for p in PRESETS) else "general_discrete"
    base = apply_preset(preset_key)
    modules: set[str] = set(base["modules"])

    # ۲) افزودن ماژول‌های تخصصی صنعت
    modules.update(m for m in INDUSTRY_EXTRA.get(industry, []) if m in idx.modules)

    # ۳) افزودن ماژول‌های مرتبط با اهداف اعلام‌شده
    goal_hits: list[tuple[str, list[str]]] = []
    for goal in goals:
        matched_key = None
        for key in GOAL_MODULES:
            if key in goal or goal in key:
                matched_key = key
                break
        if matched_key is None:
            # تطبیق نرم‌تر: اشتراک کلمات
            words = [w for w in goal.replace("،", " ").split() if len(w) > 2]
            for key in GOAL_MODULES:
                if any(word in key for word in words):
                    matched_key = key
                    break
        if matched_key:
            added = [m for m in GOAL_MODULES[matched_key] if m in idx.modules]
            goal_hits.append((matched_key, added))
            modules.update(added)

    # ۴) تنظیم بر اساس اندازه سازمان
    profile = SIZE_PROFILES[size_bucket]
    if len(modules) > profile["max_modules"]:
        # حذف ماژول‌های کم‌اولویت‌تر بر اساس تعداد زیرمجموعه (کوچک‌تر = تخصصی‌تر)
        ranked = sorted(
            modules,
            key=lambda m: (idx.modules[m]["priority"] if "priority" in idx.modules[m] else 3,
                           -idx.modules[m]["item_count"]),
        )
        modules = set(ranked[: profile["max_modules"]])

    # سازمان‌های بزرگ‌تر نیاز به ماژول‌های حاکمیتی و چندشیفتی دارند
    if shifts_per_day >= 3:
        modules.update({"G4", "C1", "J3", "V2"})
    if production_lines >= 4:
        modules.update({"A8", "J3", "V2", "Q2"})
    if warehouses_count >= 3:
        modules.update({"D3", "D4", "D6", "Q2"})
    if employees_count >= 250:
        modules.update({"G2", "G6", "G7", "G11", "G12", "F7", "O1", "O2"})
    if employees_count >= 800:
        modules.update({"R1", "R2", "F11", "O3", "O4", "S6", "L3"})

    # ۵) حل وابستگی‌ها
    resolved = resolve_modules(sorted(modules))
    final_modules = resolved["resolved"]

    # ۶) نقاط AI بر اساس سطح اشتیاق به هوش مصنوعی
    allowed_engines = AI_LEVEL_ENGINES.get(ai_level)
    ai_points: list[str] = []
    for code in final_modules:
        for grp in idx.modules[code]["groups"]:
            for item in grp["items"]:
                if not item["ai"]:
                    continue
                from .registry import engine_for

                if allowed_engines is None or engine_for(item["code"], item["name"]) in allowed_engines:
                    ai_points.append(item["code"])

    rationale: list[dict[str, str]] = [
        {
            "type": "industry",
            "title": f"پریست صنعتی «{base['preset_name']}» اعمال شد",
            "detail": f"{len(base['modules'])} ماژول پایه متناسب با صنعت انتخابی.",
        },
        {
            "type": "size",
            "title": f"اندازه سازمان: {profile['max_modules']} ماژول (سطح {size_bucket})",
            "detail": f"با {employees_count} نیروی انسانی و {shifts_per_day} شیفت کاری در روز.",
        },
    ]
    for goal, added in goal_hits:
        rationale.append(
            {
                "type": "goal",
                "title": f"هدف «{goal}» پوشش داده شد",
                "detail": f"ماژول‌های افزوده: {', '.join(added) if added else '—'}",
            }
        )
    if shifts_per_day >= 3:
        rationale.append({
            "type": "shift",
            "title": "کار چندشیفتی",
            "detail": "ماژول‌های شیفت‌بندی، پایش OEE و بهره‌وری نیرو افزوده شد.",
        })
    rationale.append({
        "type": "dependencies",
        "title": f"{len(resolved['auto_added'])} ماژول پیش‌نیاز به‌صورت خودکار افزوده شد",
        "detail": ", ".join(resolved["auto_added"][:18]) or "—",
    })
    rationale.append({
        "type": "ai",
        "title": f"سطح هوش مصنوعی: {ai_level}",
        "detail": f"{len(ai_points)} نقطه AI متناسب با بودجه و اشتیاق سازمان فعال شد.",
    })

    return {
        "modules": final_modules,
        "ai_points": sorted(ai_points),
        "rationale": rationale,
        "ai_level": ai_level,
        "size_bucket": size_bucket,
        "preset_key": preset_key,
        "auto_added": resolved["auto_added"],
    }


def build_phases(modules: list[str], ai_points: list[str] | None = None) -> list[PhasePlan]:
    """ساخت برنامه فازبندی استقرار بر اساس ماژول‌های انتخاب‌شده."""
    idx = index()
    ai_points = ai_points or []
    module_set = set(modules)
    assigned: set[str] = set()
    phases: list[PhasePlan] = []

    for order, template in enumerate(PHASE_TEMPLATE, start=1):
        phase_modules = [m for m in template["modules"] if m in module_set and m not in assigned]
        assigned.update(phase_modules)
        if order == len(PHASE_TEMPLATE):
            leftovers = sorted(module_set - assigned)
            phase_modules.extend(leftovers)
            assigned.update(leftovers)
        phase_ai = [a for a in ai_points if idx.module_of_item.get(a) in set(phase_modules)]
        item_count = sum(idx.modules[m]["item_count"] for m in phase_modules)
        duration = max(1, template["duration_months"])
        if len(phase_modules) <= 4:
            duration = max(1, duration - 1)
        elif len(phase_modules) >= 18:
            duration += 1

        phases.append(
            PhasePlan(
                order=order,
                title=template["title"],
                description=template["description"],
                duration_months=duration,
                modules=phase_modules,
                ai_points=phase_ai,
                milestones=template["milestones"],
                deliverables=template["deliverables"] + [
                    f"فعال‌سازی {len(phase_modules)} ماژول و {item_count} زیرمجموعه",
                ] if phase_modules else template["deliverables"],
            )
        )

    return [p for p in phases if p.modules]


def advise(
    industry: str,
    employees_count: int,
    shifts_per_day: int,
    production_lines: int,
    warehouses_count: int,
    goals: list[str],
    budget_level: str,
    ai_appetite: str,
    note: str = "",
    avalai_key: str = "",
    avalai_base_url: str = "",
    avalai_model: str = "",
    use_llm: bool = True,
) -> dict[str, Any]:
    """پیشنهاد نهایی ماژول‌ها با امکان بازبینی توسط AvalAI."""
    base = recommend_modules(
        industry=industry,
        employees_count=employees_count,
        shifts_per_day=shifts_per_day,
        production_lines=production_lines,
        warehouses_count=warehouses_count,
        goals=goals,
        budget_level=budget_level,
        ai_appetite=ai_appetite,
    )

    llm_used = False
    llm_note = ""
    modules = base["modules"]
    rationale = base["rationale"]

    if use_llm and is_configured(avalai_key):
        idx = index()
        module_lines = "\n".join(
            f"{code}: {idx.modules[code]['name']} ({idx.modules[code]['item_count']} زیرمجموعه، "
            f"{idx.modules[code]['ai_count']} نقطه AI)"
            for code in sorted(idx.modules)
        )
        prompt = (
            "شما مشاور ارشد پیاده‌سازی ERP کارخانه‌ای هستید. بر اساس مشخصات کارخانه، "
            "فهرست ماژول‌های پیشنهادی زیر را بازبینی کنید و خروجی را فقط به‌صورت JSON با کلیدهای "
            'add (کدهای ماژول برای افزودن)، remove (کدهای ماژول برای حذف) و rationale '
            "(فهرست دلیل‌های کوتاه فارسی) برگردانید.\n\n"
            f"مشخصات کارخانه: صنعت={industry}، تعداد کارکنان={employees_count}، "
            f"شیفت در روز={shifts_per_day}، خطوط تولید={production_lines}، "
            f"انبارها={warehouses_count}، سطح بودجه={budget_level}، "
            f"اشتیاق به هوش مصنوعی={ai_appetite}\n"
            f"اهداف: {', '.join(goals) or 'اعلام نشده'}\n"
            f"یادداشت کاربر: {note or '—'}\n\n"
            f"ماژول‌های پیشنهادی فعلی: {', '.join(modules)}\n\n"
            f"فهرست کامل ماژول‌ها:\n{module_lines}\n"
        )
        result = chat(
            [
                {"role": "system", "content": "تو یک مشاور ERP صنعتی هستی و فقط JSON معتبر برمی‌گردانی."},
                {"role": "user", "content": prompt},
            ],
            api_key=avalai_key,
            base_url=avalai_base_url or None,
            model=avalai_model or None,
            json_mode=True,
            temperature=0.1,
        )
        llm_note = result.note
        llm_used = result.used
        if result.used:
            parsed = parse_json_answer(result.text)
            if isinstance(parsed, dict):
                add = [m for m in parsed.get("add", []) if m in idx.modules]
                remove = [m for m in parsed.get("remove", []) if m in idx.modules]
                # ماژول‌های سیستمی هرگز حذف نمی‌شوند
                from ..domain.registry import SYSTEM_MODULES

                remove = [m for m in remove if m not in SYSTEM_MODULES]
                modules = sorted((set(modules) | set(add)) - set(remove))
                extra = parsed.get("rationale")
                if isinstance(extra, list):
                    for text in extra[:8]:
                        if isinstance(text, str) and text.strip():
                            rationale.append({"type": "ai", "title": "بازبینی AvalAI", "detail": text.strip()})
                modules = resolve_modules(modules)["resolved"]

    phases = build_phases(modules, base["ai_points"])
    idx = index()
    coverage = {
        "modules": len(modules),
        "items": sum(idx.modules[m]["item_count"] for m in modules),
        "ai_points": len(base["ai_points"]),
        "sections": len({idx.section_of_module[m] for m in modules if m in idx.section_of_module}),
    }

    return {
        "recommended_modules": modules,
        "recommended_ai_points": base["ai_points"],
        "rationale": rationale,
        "phases": phases,
        "coverage": coverage,
        "llm_used": llm_used,
        "llm_note": llm_note or ("AvalAI غیرفعال است؛ پیشنهادها از موتور قاعده‌محور داخلی است."),
        "ai_level": base["ai_level"],
        "size_bucket": base["size_bucket"],
    }
