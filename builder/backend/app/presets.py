# -*- coding: utf-8 -*-
"""
پریست‌های صنعتی و اندازه سازمان
================================
هر پریست یک بسته پیشنهادی از ماژول‌ها + تنظیمات کارخانه است تا کاربر
به‌جای انتخاب دستی ۱۳۰ ماژول، با یک کلیک پیکربندی متناسب صنعت خود را
دریافت کند و سپس آن را ویرایش نماید.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------- #
# بسته‌های پایه که در همه پریست‌ها مشترک‌اند
# --------------------------------------------------------------------------- #
BACKBONE = [
    # تولید
    "A1", "A2", "A3", "A4",
    # کیفیت
    "B1", "B4", "B7",
    # نت
    "C1", "C3", "C4",
    # زنجیره تأمین
    "D1", "D2", "D3", "D4",
    # فروش
    "E1", "E2",
    # مالی
    "F1", "F2", "F3", "F5", "F9", "F12",
    # منابع انسانی
    "G1", "G3", "G5",
    # زیرساخت
    "S1", "S2", "S4", "P1", "P2", "P3", "V3",
]

PRESETS: list[dict[str, Any]] = [
    {
        "key": "general_discrete",
        "name": "کارخانه تولیدی عمومی (گره‌ای)",
        "name_en": "General Discrete Manufacturing",
        "icon": "factory",
        "color": "#4f46e5",
        "description": "پیکربندی متوازن برای کارخانه‌های تولید قطعه و مونتاژ با تمرکز بر برنامه‌ریزی تولید، "
                       "کیفیت، نت و زنجیره تأمین.",
        "modules": BACKBONE + [
            "A6", "A7", "A8",
            "B2", "B3", "B5", "B6",
            "C2", "C5",
            "D5", "D8",
            "E4", "E6",
            "F4", "F6", "F7", "F8", "F11",
            "G2", "G4", "G6", "G7", "G11", "G12",
            "H1", "H2", "H5",
            "I1", "I2", "I3",
            "J3",
            "K1", "K2", "K6", "K7",
            "L1", "L2", "L4",
            "M1", "M3",
            "N1",
            "O1", "O2", "O3",
            "P4",
            "Q1", "Q2", "Q3",
            "R1", "R2",
            "S3", "S5", "S6",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "general_discrete", "shifts_per_day": 2},
        "ai_focus": ["forecasting", "optimization", "anomaly", "classification"],
    },
    {
        "key": "process_general",
        "name": "صنایع فرآیندی عمومی",
        "name_en": "General Process Industry",
        "icon": "flask",
        "color": "#0891b2",
        "description": "برای صنایع شیمیایی، رنگ، رزین و مواد ساختمانی با محوریت فرمولاسیون، بچ و ردیابی.",
        "modules": BACKBONE + [
            "A5", "A6",
            "B2", "B3", "B5", "B6",
            "C2", "C5",
            "D5", "D7", "D8",
            "E4", "E6",
            "F4", "F6", "F7", "F8",
            "G4", "G7", "G11", "G12",
            "H1", "H5",
            "J1", "J2", "J3", "J5",
            "K1", "K2", "K6", "K7",
            "L1", "L2", "L4",
            "M1", "M2", "M3", "M4", "M5",
            "N1", "N2", "N3",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q1", "Q2", "Q3",
            "S3", "S5", "S6",
            "U1", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "process", "shifts_per_day": 3},
        "ai_focus": ["forecasting", "optimization", "anomaly", "quality_spc"],
    },
    {
        "key": "food_pharma",
        "name": "صنایع غذایی و دارویی",
        "name_en": "Food & Pharmaceutical",
        "icon": "apple",
        "color": "#16a34a",
        "description": "تمرکز بر GMP، ردیابی لات و انقضا، آزمایشگاه (LIMS)، HACCP و مستندسازی کامل.",
        "modules": BACKBONE + [
            "A5", "A6",
            "B2", "B3", "B5", "B6",
            "C2", "C5",
            "D5", "D8",
            "E4", "E6",
            "F4", "F6", "F7", "F8", "F11",
            "G2", "G4", "G6", "G7", "G11", "G12",
            "H1", "H5",
            "I1", "I3",
            "J2", "J3", "J5",
            "K1", "K2", "K6", "K7",
            "L1", "L2", "L4",
            "M1", "M2", "M3", "M5",
            "N1", "N2", "N3",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q1", "Q3",
            "R1", "R2", "R4",
            "S3", "S5", "S6",
            "T1",
            "U1", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "food_pharma", "shifts_per_day": 3},
        "ai_focus": ["forecasting", "quality_spc", "anomaly", "reliability"],
    },
    {
        "key": "automotive",
        "name": "خودروسازی و قطعه‌سازی",
        "name_en": "Automotive & Tier Suppliers",
        "icon": "car",
        "color": "#dc2626",
        "description": "IATF 16949، APQP/PPAP، FMEA، JIT/JIS، EDI با خودروساز و بالانس خط مونتاژ.",
        "modules": BACKBONE + [
            "A5", "A6", "A7", "A8",
            "B2", "B3", "B5", "B6",
            "C2", "C5", "C6",
            "D5", "D6", "D7", "D8",
            "E3", "E4", "E6", "E7",
            "F4", "F6", "F7", "F8", "F10", "F11",
            "G2", "G4", "G6", "G7", "G8", "G9", "G11", "G12",
            "H1", "H2", "H3", "H4", "H5",
            "I1", "I2", "I3", "I4",
            "J1", "J2", "J3", "J5", "J6",
            "K1", "K2", "K3", "K4", "K5", "K6", "K7",
            "L1", "L2", "L3", "L4",
            "M1", "M2", "M3", "M4",
            "N1", "N2",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q1", "Q2", "Q3",
            "R1", "R2", "R3", "R4",
            "S3", "S5", "S6", "S7",
            "T2",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "automotive", "shifts_per_day": 3, "production_lines": 5},
        "ai_focus": ["optimization", "quality_spc", "reliability", "computer_vision"],
    },
    {
        "key": "metals_foundry",
        "name": "فلزی، ذوب و ریخته‌گری",
        "name_en": "Metals & Foundry",
        "icon": "flame",
        "color": "#b45309",
        "description": "مدیریت شماره ذوب، کوره، نورد، گواهی مواد (MTC)، انرژی و ایمنی سنگین.",
        "modules": BACKBONE + [
            "A5", "A7",
            "B2", "B3", "B5", "B6",
            "C2", "C5", "C6",
            "D5", "D7", "D8",
            "E4", "E6",
            "F4", "F6", "F7", "F8", "F10", "F11",
            "G2", "G4", "G6", "G7", "G11",
            "H1", "H3", "H5",
            "I1", "I2", "I3",
            "J1", "J2", "J3", "J4", "J5",
            "K1", "K2", "K6", "K7",
            "L1", "L2", "L3", "L4",
            "M1", "M2", "M3", "M4", "M5",
            "N1", "N2", "N3",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q1", "Q2", "Q3",
            "R1", "R2",
            "S3", "S5", "S6",
            "T3",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "metals", "shifts_per_day": 3},
        "ai_focus": ["optimization", "reliability", "anomaly", "forecasting"],
    },
    {
        "key": "textile",
        "name": "نساجی و پوشاک",
        "name_en": "Textile & Apparel",
        "icon": "shirt",
        "color": "#db2777",
        "description": "استایل و ماتریس سایز-رنگ، برنامه برش، مدیریت پارچه و راندمان خطوط خیاطی.",
        "modules": BACKBONE + [
            "A6", "A8",
            "B1", "B3", "B4", "B7",
            "C1", "C3", "C4",
            "D5", "D7", "D8",
            "E3", "E4", "E5", "E6", "E7",
            "F4", "F6", "F7", "F8",
            "G2", "G4", "G6", "G7", "G9", "G11", "G12",
            "H1", "H3", "H5",
            "J3",
            "K1", "K2", "K5", "K7",
            "L1", "L2",
            "M1", "M2", "M3",
            "N1",
            "O1", "O2", "O3",
            "Q2", "Q3",
            "R1", "R2",
            "S5", "S6",
            "T4",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "textile", "shifts_per_day": 2, "employees_count": 400},
        "ai_focus": ["optimization", "forecasting", "classification"],
    },
    {
        "key": "electronics",
        "name": "الکترونیک و SMT",
        "name_en": "Electronics Manufacturing",
        "icon": "cpu",
        "color": "#0891b2",
        "description": "چرخه عمر قطعات، انطباق RoHS، خطوط SMT، آزمون ICT/FCT و ردیابی سریال.",
        "modules": BACKBONE + [
            "A6", "A7", "A8",
            "B2", "B3", "B5", "B6",
            "C2", "C5",
            "D5", "D6", "D7", "D8",
            "E4", "E6", "E7",
            "F4", "F6", "F7", "F8",
            "G2", "G4", "G6", "G7", "G8", "G11", "G12",
            "H1", "H2", "H3", "H4", "H5",
            "I1", "I2", "I3",
            "J1", "J2", "J3", "J5",
            "K1", "K2", "K3", "K4", "K6", "K7",
            "L1", "L2", "L3", "L4",
            "M1", "M3", "M5",
            "N1",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q2", "Q3",
            "R1", "R2", "R3",
            "S3", "S5", "S6", "S7",
            "T5",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "electronics", "shifts_per_day": 2},
        "ai_focus": ["computer_vision", "quality_spc", "anomaly", "forecasting"],
    },
    {
        "key": "petrochemical",
        "name": "پتروشیمی و انرژی",
        "name_en": "Petrochemical & Energy",
        "icon": "droplet",
        "color": "#ea580c",
        "description": "مخازن، خطوط لوله، اختلاط، HSE پیشرفته، انرژی و نگهداری پیش‌بینانه.",
        "modules": BACKBONE + [
            "A5",
            "B2", "B3", "B5", "B6",
            "C2", "C5", "C6",
            "D5", "D7", "D8",
            "E4", "E6",
            "F4", "F6", "F7", "F8", "F10", "F11",
            "G2", "G4", "G6", "G7", "G11",
            "H1", "H3", "H4", "H5",
            "I1", "I2", "I3", "I4",
            "J1", "J2", "J3", "J4", "J5", "J6",
            "K1", "K2", "K6", "K7",
            "L1", "L2", "L3", "L4",
            "M1", "M2", "M3", "M4", "M5",
            "N1", "N2", "N3",
            "O1", "O2", "O3", "O4",
            "P4",
            "Q1", "Q2", "Q3",
            "R1", "R2",
            "S3", "S5", "S6",
            "T6",
            "U1", "U2", "U3",
            "V1", "V2",
        ],
        "settings": {"industry": "petrochemical", "shifts_per_day": 4},
        "ai_focus": ["reliability", "optimization", "anomaly", "simulation"],
    },
    {
        "key": "packaging_print",
        "name": "بسته‌بندی و چاپ",
        "name_en": "Packaging & Printing",
        "icon": "printer",
        "color": "#7c3aed",
        "description": "سفارش چاپ، مدیریت زینک و رنگ، کنترل ضایعات و برنامه‌ریزی ماشین‌های چاپ.",
        "modules": BACKBONE + [
            "A6", "A7",
            "B1", "B3", "B4", "B7",
            "C1", "C3", "C4",
            "D5", "D8",
            "E1", "E2", "E4", "E6", "E7",
            "F4", "F6", "F7", "F8",
            "G4", "G7", "G11", "G12",
            "H5",
            "J2", "J3",
            "K1", "K2", "K7",
            "L1", "L2",
            "M1", "M3", "M5",
            "N1",
            "O2", "O3",
            "Q2", "Q3",
            "S5", "S6",
            "T7",
            "U1", "U2", "U3",
            "V2", "V3",
        ],
        "settings": {"industry": "packaging_print", "shifts_per_day": 2},
        "ai_focus": ["optimization", "forecasting", "computer_vision"],
    },
    {
        "key": "smb_minimal",
        "name": "کارخانه کوچک (حداقلی)",
        "name_en": "Small Factory (Minimal)",
        "icon": "zap",
        "color": "#f59e0b",
        "description": "کم‌هزینه و سریع برای راه‌اندازی: تولید، موجودی، خرید، فروش، مالی پایه و حقوق.",
        "modules": [
            "A1", "A2", "A3", "A4",
            "B1", "B4",
            "C1", "C3", "C4",
            "D1", "D3", "D4",
            "E1", "E2",
            "F1", "F2", "F3", "F5", "F9", "F12",
            "G1", "G3", "G5",
            "K1", "K7",
            "L1", "L2",
            "P1", "P3",
            "S1", "S4",
            "V3",
        ],
        "settings": {
            "industry": "smb", "shifts_per_day": 1, "employees_count": 40,
            "production_lines": 1, "warehouses_count": 1, "db_driver": "mysql",
            "ai_service_enabled": True, "include_demo_data": True,
        },
        "ai_focus": ["forecasting", "classification"],
    },
    {
        "key": "enterprise_full",
        "name": "فول ماژول سازمانی (همه ۲۲ بخش)",
        "name_en": "Enterprise Full Suite",
        "icon": "layers",
        "color": "#111827",
        "description": "همه ۱۳۰ ماژول و تمام نقاط هوش مصنوعی؛ مناسب هلدینگ‌ها و کارخانه‌های بزرگ "
                       "با استقرار فازبندی‌شده.",
        "modules": "__ALL__",
        "settings": {"industry": "enterprise", "shifts_per_day": 3, "multi_tenant": True},
        "ai_focus": ["__ALL__"],
    },
]


def preset_list() -> list[dict[str, Any]]:
    """فهرست پریست‌ها با شمارش ماژول‌ها."""
    from .catalog.registry import index

    idx = index()
    result = []
    for preset in PRESETS:
        modules = list(idx.modules) if preset["modules"] == "__ALL__" else preset["modules"]
        modules = sorted({m for m in modules if m in idx.modules})
        ai_count = sum(idx.modules[m]["ai_count"] for m in modules)
        item_count = sum(idx.modules[m]["item_count"] for m in modules)
        result.append(
            {
                "key": preset["key"],
                "name": preset["name"],
                "name_en": preset["name_en"],
                "icon": preset["icon"],
                "color": preset["color"],
                "description": preset["description"],
                "module_count": len(modules),
                "item_count": item_count,
                "ai_count": ai_count,
                "sections": sorted({m[0] for m in modules}),
                "ai_focus": preset["ai_focus"],
            }
        )
    return result


def apply_preset(key: str) -> dict[str, Any]:
    """اعمال پریست: فهرست ماژول‌ها + تنظیمات پیشنهادی کارخانه."""
    from .catalog.registry import index
    from .config import DEFAULT_FACTORY_SETTINGS

    idx = index()
    preset = next((p for p in PRESETS if p["key"] == key), None)
    if preset is None:
        raise KeyError(f"پریست ناشناخته: {key}")

    modules = list(idx.modules) if preset["modules"] == "__ALL__" else preset["modules"]
    modules = sorted({m for m in modules if m in idx.modules})

    settings = dict(DEFAULT_FACTORY_SETTINGS)
    settings.update(preset.get("settings", {}))

    # فعال‌سازی همه نقاط AI ماژول‌های انتخاب‌شده
    ai_codes = [
        item["code"]
        for code in modules
        for group in idx.modules[code]["groups"]
        for item in group["items"]
        if item["ai"]
    ]

    return {
        "preset_key": key,
        "preset_name": preset["name"],
        "modules": modules,
        "groups": [g["code"] for m in modules for g in idx.modules[m]["groups"]],
        "items": [
            i["code"] for m in modules for g in idx.modules[m]["groups"] for i in g["items"]
        ],
        "ai_points": ai_codes,
        "settings": settings,
        "ai_focus": preset["ai_focus"],
    }
