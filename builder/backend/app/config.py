# -*- coding: utf-8 -*-
"""پیکربندی مرکزی پلتفرم سازنده ERP."""

from __future__ import annotations

import os
from pathlib import Path

# مسیرهای اصلی
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = Path(os.getenv("ERP_OUTPUT_DIR") or (REPO_ROOT / "dist-packages"))
PROJECTS_FILE = DATA_DIR / "projects.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "Smart Factory ERP Builder"
APP_NAME_FA = "سازنده ERP هوشمند کارخانه‌ای"
APP_VERSION = "1.0.0"
CATALOG_VERSION = "1.0.0"

# AvalAI — API سازگار با OpenAI (اختیاری)
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
AVALAI_MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")

# سرویس
HOST = os.getenv("BUILDER_HOST", "0.0.0.0")
PORT = int(os.getenv("BUILDER_PORT", "8000"))

# گزینه‌های پیش‌فرض استقرار قابل انتخاب در رابط کاربری
DB_DRIVERS = [
    {"id": "mysql", "label": "MySQL / MariaDB", "default": True,
     "note": "گزینه پیشنهادی برای استقرار با Docker Compose"},
    {"id": "pgsql", "label": "PostgreSQL", "default": False,
     "note": "مناسب حجم داده بالا و تحلیل"},
    {"id": "sqlite", "label": "SQLite", "default": False,
     "note": "برای آزمایش سریع و استقرار تک‌کاربره"},
    {"id": "sqlsrv", "label": "SQL Server", "default": False,
     "note": "برای زیرساخت‌های مایکروسافتی موجود"},
]

QUEUE_DRIVERS = [
    {"id": "redis", "label": "Redis", "default": True, "note": "صف و کش با کارایی بالا"},
    {"id": "database", "label": "Database", "default": False, "note": "بدون نیاز به سرویس جانبی"},
    {"id": "sync", "label": "Sync", "default": False, "note": "اجرای همزمان (فقط محیط آزمون)"},
]

STORAGE_DRIVERS = [
    {"id": "local", "label": "فضای محلی سرور", "default": True, "note": "ذخیره فایل‌ها روی دیسک سرور"},
    {"id": "s3", "label": "S3 / MinIO", "default": False, "note": "ذخیره‌سازی شیء برای مقیاس‌پذیری"},
]

DEPLOY_TARGETS = [
    {"id": "docker", "label": "Docker Compose (پیشنهادی)", "default": True,
     "note": "بسته کامل با docker-compose، Nginx، MySQL، Redis و سرویس AI"},
    {"id": "baremetal", "label": "سرور فیزیکی / VM بدون داکر", "default": False,
     "note": "اسکریپت نصب با PHP-FPM، Nginx و systemd"},
    {"id": "k8s", "label": "Kubernetes", "default": False,
     "note": "مانیفست‌های K8s همراه با Helm-like values"},
]

AI_ENGINES_MIN_VERSION = {
    "python": "3.11",
    "php": "8.2",
    "node": "20",
}

DEFAULT_FACTORY_SETTINGS: dict = {
    # --- هویت کارخانه و پروژه --------------------------------------------- #
    "company_name": "کارخانه نمونه",
    "company_name_en": "Sample Factory",
    "company_legal_name": "",
    "company_national_id": "",
    "economic_code": "",
    "registration_no": "",
    "province": "",
    "city": "",
    "address": "",
    "postal_code": "",
    "phone": "",
    "website": "",
    "industry": "general_discrete",
    "project_slug": "factory-erp",
    "project_description": "",
    "app_name": "factory-erp",
    "app_name_fa": "ERP کارخانه نمونه",

    # --- مقیاس عملیاتی (ورودی دستیار هوشمند) ------------------------------- #
    "employees_count": 150,
    "shifts_per_day": 2,
    "warehouses_count": 2,
    "production_lines": 3,

    # --- تقویم، پول و قوانین مالی ایران ------------------------------------ #
    "calendar": "jalali",
    "language": "fa",
    "timezone": "Asia/Tehran",
    "currency": "IRR",
    "currency_label": "ریال",
    "week_start": "saturday",
    "weekend_days": ["thursday", "friday"],
    "fiscal_year_start_month": 1,
    "tax_rate_default": 0.10,
    "moadian_enabled": True,
    "costing_method": "weighted_average",

    # --- سرویس و شبکه ------------------------------------------------------ #
    "app_url": "http://erp.local",
    "app_env": "production",
    "app_debug": False,
    "host_port": 8000,
    "cors_origins": "",
    "stateful_domains": "localhost:5173,localhost:3000",
    "ssl_enabled": False,
    "multi_tenant": False,
    "deploy_target": "docker",

    # --- پایگاه داده و زیرساخت --------------------------------------------- #
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

    # --- هوش مصنوعی -------------------------------------------------------- #
    "ai_enabled": True,
    "ai_human_approval": True,
    "ai_service_host": "ai-service",
    "ai_service_port": 8001,
    "ai_service_url": "http://ai-service:8001",
    "avalai_enabled": False,
    "avalai_api_key": "",
    "avalai_base_url": "https://api.avalai.ir/v1",
    "avalai_model": "gpt-4o-mini",

    # --- IoT و MQTT -------------------------------------------------------- #
    "iot_enabled": False,
    "mqtt_host": "mosquitto",
    "mqtt_port": 1883,
    "mqtt_topic_prefix": "factory/",
    "iot_sampling_seconds": 30,

    # --- ایمیل و پیامک ----------------------------------------------------- #
    "mail_enabled": True,
    "mail_driver": "smtp",
    "mail_host": "smtp.example.com",
    "mail_port": 587,
    "mail_username": "",
    "mail_password": "",
    "mail_from": "",
    "mail_from_name": "",
    "mail_encryption": "tls",
    "sms_enabled": False,
    "sms_provider": "kavenegar",
    "sms_api_key": "",

    # --- کاربر مدیر و پشتیبان‌گیری ------------------------------------------ #
    "admin_name": "مدیر سامانه",
    "admin_email": "admin@factory.local",
    "admin_password": "",
    "backup_enabled": True,
    "backup_cron": "0 2 * * *",
    "backup_keep_days": 30,
    "backup_disk": "local",

    # --- محتوای بسته خروجی ------------------------------------------------- #
    "include_demo_data": True,
    "include_tests": True,
    "include_docs": True,
    "include_mobile_pwa": True,
    "include_report_templates": True,
    "generate_api_docs": True,
}
