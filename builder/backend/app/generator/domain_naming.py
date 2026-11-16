# -*- coding: utf-8 -*-
"""
قراردادهای نام‌گذاری مشترک بین کد تولیدشده
============================================
این توابع در چند مولد (مسیرها، کنترلرها، فرانت‌اند، سرویس AI) استفاده می‌شوند
تا نام پارامتر مسیر، نام کلاس و نام فیلد همیشه یکسان بماند.
"""

from __future__ import annotations

import re

from ..domain.dsl import pascal_case, singularize


def singular_route_param(table: str) -> str:
    """نام پارامتر مسیر برای یک جدول (snake_case مفرد).

    مثال: production_plans -> production_plan
    """
    return singularize(table)


def camel_case(text: str) -> str:
    """تبدیل snake_case به camelCase."""
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", text) if p]
    if not parts:
        return "item"
    return parts[0].lower() + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def pascal(text: str) -> str:
    """تبدیل snake_case به PascalCase."""
    return pascal_case(text)


def dasherize(text: str) -> str:
    """تبدیل snake_case به kebab-case (برای مسیرهای فرانت‌اند)."""
    return re.sub(r"[_\s]+", "-", text.strip().lower())


def js_identifier(text: str) -> str:
    """ساخت شناسه معتبر JavaScript از متن دلخواه."""
    cleaned = re.sub(r"[^A-Za-z0-9_$]", "_", text)
    if cleaned and cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned or "_item"


def route_param_for(table: str) -> str:
    """نام پارامتر مسیر به صورت camelCase — همان چیزی که در کنترلر استفاده می‌شود."""
    return camel_case(singular_route_param(table))
