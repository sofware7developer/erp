# -*- coding: utf-8 -*-
"""
موتور تولید کد (Generation Engine)
====================================
هر مولد یک لایه از بسته خروجی را می‌سازد و همه از یک `Package` مشترک
و یک `context` واحد تغذیه می‌شوند تا نام‌ها، اسلاگ‌ها و تنظیمات در
کل بسته سازگار بماند.

    pipeline.generate_package(project)  ->  GenerateResult

لایه‌ها:
    laravel_core     اسکلت لاراول ۱۱ (composer، config، env، public، Docker)
    laravel_domain   مایگریشن/مدل/کنترلر/درخواست/منبع/سیاست/تست/سیدر/سرویس
    laravel_system   پشتیبانی فارسی و جلالی، میان‌افزار، کنترلرهای سامانه، دستورهای artisan
    laravel_routes   مسیرهای API/وب/کنسول و سیدرهای پایگاه داده
    ai_service       میکروسرویس FastAPI با ۱۱ موتور هوش مصنوعی
    frontend         SPA ری‌اکت + ویت (RTL، بدون کتابخانه UI)
    deploy           docker-compose، nginx، systemd، cron، اسکریپت‌ها، Makefile
    docs             README فارسی و ۹ سند عملیاتی/فنی
"""

from __future__ import annotations

from .pipeline import (
    INDUSTRY_LABELS,
    build_context,
    generate_package,
    jalali_now,
    package_dirs,
)
from .writers import Package, WrittenFile, php_value, render, slugify

__all__ = [
    "INDUSTRY_LABELS",
    "Package",
    "WrittenFile",
    "build_context",
    "generate_package",
    "jalali_now",
    "package_dirs",
    "php_value",
    "render",
    "slugify",
]
