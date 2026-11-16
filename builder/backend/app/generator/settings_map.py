# -*- coding: utf-8 -*-
"""
یکسان‌سازی تنظیمات کارخانه برای موتور تولید
===============================================
تنظیمات ذخیره‌شده در `config.DEFAULT_FACTORY_SETTINGS` (که رابط کاربری و
API همان کلیدها را می‌فرستند) نام‌هایی متفاوت از کلیدهایی دارند که
مولدهای کد می‌خوانند؛ مثلاً `base_currency` در برابر `currency` یا
`backup_schedule` در برابر `backup_cron`.

این ماژول یک نگاشت یک‌طرفه انجام می‌دهد:

  ۱. مقادیر پیش‌فرض پلتفرم
  ۲. تنظیمات کاربر (اولویت بالاتر)
  ۳. کلیدهای هم‌نام‌شده (alias) — فقط اگر کاربر مقدار صریح نداده باشد
  ۴. مقادیر مشتق (URL سرویس AI، دامنه‌های CORS، گذرواژه‌های تصادفی امن)

خروجی یک دیکشنری کامل است که همه مولدها بدون نگرانی از نبود کلید می‌خوانند.
"""

from __future__ import annotations

import re
import secrets
from typing import Any
from urllib.parse import urlparse

from ..config import DEFAULT_FACTORY_SETTINGS

CURRENCY_LABELS = {
    "IRR": "ریال",
    "IRT": "تومان",
    "Rial": "ریال",
    "Toman": "تومان",
    "USD": "دلار آمریکا",
    "EUR": "یورو",
    "AED": "درهم امارات",
    "TRY": "لیر ترکیه",
    "CNY": "یوان چین",
}

# کلید تنظیمات کارخانه -> کلید مورد انتظار مولدها
ALIASES: dict[str, str] = {
    "factory_name": "company_name",
    "factory_name_en": "company_name_en",
    "base_currency": "currency",
    "fiscal_year_start": "fiscal_year_start_month",
    "national_id": "company_national_id",
    "ai_service_enabled": "ai_enabled",
    "iot_mqtt_host": "mqtt_host",
    "iot_mqtt_port": "mqtt_port",
    "backup_schedule": "backup_cron",
    "storage_driver": "storage_disk",
}

DEFAULTS_EXTRA: dict[str, Any] = {
    "app_name": "",
    "app_name_fa": "",
    "company_name": "",
    "company_name_en": "",
    "company_legal_name": "",
    "company_national_id": "",
    "economic_code": "",
    "registration_no": "",
    "address": "",
    "postal_code": "",
    "phone": "",
    "website": "",
    "currency": "IRR",
    "currency_label": "ریال",
    "calendar": "jalali",
    "timezone": "Asia/Tehran",
    "week_start": "saturday",
    "weekend_days": ["thursday", "friday"],
    "fiscal_year_start_month": 1,
    "tax_rate_default": 0.10,
    "moadian_enabled": True,
    "costing_method": "weighted_average",
    "host_port": 8000,
    "db_driver": "mysql",
    "db_host": "mysql",
    "db_port": 3306,
    "db_host_port": 3306,
    "db_database": "smart_erp",
    "db_username": "erp_user",
    "db_password": "",
    "db_root_password": "",
    "cache_driver": "redis",
    "queue_driver": "redis",
    "session_driver": "database",
    "storage_disk": "local",
    "redis_host": "redis",
    "redis_port": 6379,
    "mail_driver": "smtp",
    "mail_host": "smtp.example.com",
    "mail_port": 587,
    "mail_username": "",
    "mail_password": "",
    "mail_from": "",
    "mail_from_name": "",
    "mail_encryption": "tls",
    "ai_enabled": True,
    "ai_human_approval": True,
    "ai_service_url": "http://ai-service:8001",
    "avalai_enabled": False,
    "avalai_api_key": "",
    "avalai_base_url": "https://api.avalai.ir/v1",
    "avalai_model": "gpt-4o-mini",
    "iot_enabled": False,
    "mqtt_host": "mosquitto",
    "mqtt_port": 1883,
    "mqtt_topic_prefix": "factory/",
    "iot_sampling_seconds": 30,
    "backup_cron": "0 2 * * *",
    "backup_keep_days": 30,
    "backup_disk": "local",
    "admin_name": "مدیر سامانه",
    "admin_email": "admin@factory.local",
    "admin_password": "",
    "include_demo_data": True,
    "include_tests": True,
    "include_docs": True,
    "include_mobile_pwa": True,
    "include_report_templates": True,
    "generate_api_docs": True,
    "deploy_target": "docker",
    "ssl_enabled": False,
    "multi_tenant": False,
    "cors_origins": "",
    "stateful_domains": "localhost:5173,localhost:3000",
    "app_env": "production",
    "app_debug": False,
    "employees_count": 150,
    "shifts_per_day": 2,
    "warehouses_count": 2,
    "production_lines": 3,
    "project_slug": "factory-erp",
    "project_description": "",
}


def _password(length: int = 24) -> str:
    """گذرواژه تصادفی امن بدون نویسه‌های مشکل‌ساز در env و shell."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            re.search(r"[A-Z]", candidate)
            and re.search(r"[a-z]", candidate)
            and re.search(r"[0-9]", candidate)
        ):
            return candidate


def _derive_urls(settings: dict[str, Any]) -> dict[str, str]:
    """استخراج دامنه/پورت از `app_url` برای CORS، Sanctum و پورت میزبان."""
    app_url = str(settings.get("app_url") or "http://erp.local").rstrip("/")
    parsed = urlparse(app_url if "://" in app_url else f"http://{app_url}")
    host = parsed.hostname or "erp.local"
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    origin = f"{parsed.scheme}://{host}" + ("" if port in (80, 443) else f":{port}")
    return {
        "app_url": origin,
        "app_host": host,
        "host_port": port,
        "cors_origins": ",".join([origin, "http://localhost:5173", "http://localhost:3000"]),
        "stateful_domains": ",".join([host, "localhost:5173", "localhost:3000"]),
    }


def normalize_settings(
    raw: dict[str, Any] | None = None,
    *,
    project_name: str = "",
    project_name_en: str = "",
    project_description: str = "",
    slug: str = "",
    generate_secrets: bool = True,
) -> dict[str, Any]:
    """ادغام و یکسان‌سازی تنظیمات؛ خروجی برای همه مولدها کامل است."""
    raw = dict(raw or {})

    settings: dict[str, Any] = {}
    settings.update(DEFAULTS_EXTRA)
    settings.update({k: v for k, v in DEFAULT_FACTORY_SETTINGS.items() if v is not None})
    settings.update({k: v for k, v in raw.items() if v is not None})

    # ۱) هم‌نام‌سازی کلیدها (مقدار صریح کاربر بر هم‌نام مقصد اولویت دارد)
    user_keys = set(raw)
    for source, target in ALIASES.items():
        if source not in settings:
            continue
        if target in user_keys and raw.get(target) not in (None, ""):
            continue
        settings[target] = settings[source]

    # ۲) مقادیر مشتق از app_url
    derived = _derive_urls(settings)
    for key, value in derived.items():
        if key == "host_port":
            if not raw.get("host_port") and int(value) not in (80, 443):
                settings["host_port"] = int(value)
            continue
        if key in ("cors_origins", "stateful_domains"):
            if not settings.get(key):
                settings[key] = value
        else:
            settings.setdefault(key, value)

    # ۳) نام‌ها و برچسب‌ها
    settings["company_name"] = (
        settings.get("company_name")
        or raw.get("factory_name")
        or project_name
        or "کارخانه"
    )
    settings["company_name_en"] = settings.get("company_name_en") or project_name_en or ""
    settings["project_description"] = project_description or settings.get("description", "")
    settings["app_name"] = settings.get("app_name") or slug or settings.get("project_slug") or "factory-erp"
    settings["app_name_fa"] = (
        settings.get("app_name_fa")
        or f"ERP {settings['company_name']}"
    )
    settings["currency_label"] = settings.get("currency_label") or CURRENCY_LABELS.get(
        str(settings.get("currency", "IRR")), "ریال"
    )
    settings["mail_from"] = settings.get("mail_from") or settings.get("admin_email") or f"erp@{derived['app_host']}"
    settings["mail_from_name"] = settings.get("mail_from_name") or settings["company_name"]
    settings["mqtt_topic_prefix"] = settings.get("mqtt_topic_prefix") or f"{slug or 'factory'}/"

    # ۴) سرویس AI
    if not settings.get("ai_service_url"):
        settings["ai_service_url"] = (
            f"http://{settings.get('ai_service_host', 'ai-service')}:{settings.get('ai_service_port', 8001)}"
        )

    # ۵) گذرواژه‌های امن تصادفی (فقط برای استقرار واقعی، نه sqlite)
    if generate_secrets:
        if settings.get("db_driver") != "sqlite":
            if not settings.get("db_password"):
                settings["db_password"] = _password()
            if not settings.get("db_root_password"):
                settings["db_root_password"] = _password()
        if not settings.get("admin_password"):
            settings["admin_password"] = _password(16)
        settings.setdefault("app_key", "")
        if not settings.get("app_key"):
            settings["app_key"] = "base64:" + secrets.token_urlsafe(32)

    # ۶) تطبیق انواع
    settings["include_demo_data"] = bool(settings.get("include_demo_data", True))
    settings["include_tests"] = bool(settings.get("include_tests", True))
    settings["ai_enabled"] = bool(settings.get("ai_enabled", True))
    settings["iot_enabled"] = bool(settings.get("iot_enabled", False))
    settings["ssl_enabled"] = bool(settings.get("ssl_enabled", False))
    settings["multi_tenant"] = bool(settings.get("multi_tenant", False))
    settings["app_debug"] = bool(settings.get("app_debug", False))
    for int_key in ("db_port", "db_host_port", "redis_port", "mail_port", "mqtt_port", "host_port", "iot_sampling_seconds"):
        try:
            settings[int_key] = int(settings.get(int_key) or 0)
        except (TypeError, ValueError):
            settings[int_key] = 0
    if not settings["db_host_port"]:
        settings["db_host_port"] = settings["db_port"] or 3306

    return settings
