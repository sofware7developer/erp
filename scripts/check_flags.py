# -*- coding: utf-8 -*-
"""
بررسی رعایت پرچم‌های قابلیت در بسته تولیدشده
==============================================
هر پرچم تنظیمات باید واقعاً روی خروجی اثر بگذارد؛ این اسکریپت دو بسته
(پرچم فعال / غیرفعال) می‌سازد و وجود یا نبود فایل‌های مرتبط را می‌سنجد.

    .venv/bin/python scripts/check_flags.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "builder" / "backend"))

from app.generator import generate_package  # noqa: E402
from app.schemas import ProjectConfig, Selection  # noqa: E402

MODULES = ["A1", "B1", "F9"]

CHECKS = [
    {
        "flag": "ai_enabled",
        "present_when_true": ["ai-service/app/main.py", "deploy/systemd/erp-ai.service"],
        "absent_when_false": ["ai-service/app/main.py", "deploy/systemd/erp-ai.service"],
        "text_when_false": [("docker-compose.yml", "سرویس هوش مصنوعی غیرفعال است")],
        "text_when_true": [("docker-compose.yml", "ai-service:")],
    },
    {
        "flag": "include_docs",
        "present_when_true": ["docs/01-architecture.md", "docs/04-data-model.md"],
        "absent_when_false": ["docs/01-architecture.md", "docs/04-data-model.md"],
        "text_when_false": [],
        "text_when_true": [],
        "always_present": ["README-fa.md", "LICENSE", "CHANGELOG.md"],
    },
    {
        "flag": "generate_api_docs",
        "present_when_true": ["docs/06-api-reference.md"],
        "absent_when_false": ["docs/06-api-reference.md"],
        "text_when_false": [],
        "text_when_true": [],
    },
    {
        "flag": "include_mobile_pwa",
        "present_when_true": [
            "frontend/public/manifest.webmanifest",
            "frontend/public/sw.js",
            "frontend/public/icon.svg",
        ],
        "absent_when_false": ["frontend/public/sw.js"],
        "text_when_false": [("frontend/src/main.jsx", None)],
        "text_when_true": [
            ("frontend/src/main.jsx", "serviceWorker"),
            ("frontend/index.html", "manifest.webmanifest"),
        ],
    },
    {
        "flag": "include_report_templates",
        "present_when_true": ["backend/config/reports.php"],
        "absent_when_false": ["backend/config/reports.php"],
        "text_when_false": [],
        "text_when_true": [],
    },
    {
        "flag": "include_demo_data",
        "present_when_true": [
            "backend/database/seeders/DemoDataSeeder.php",
            "backend/database/seeders/Demo/DemoDataSpec.php",
            "backend/database/seeders/Demo/DemoHistorySeeder.php",
        ],
        "absent_when_false": [
            "backend/database/seeders/DemoDataSeeder.php",
            "backend/database/seeders/Demo/DemoDataSpec.php",
            "backend/database/seeders/Demo/DemoHistorySeeder.php",
        ],
        "text_when_true": [
            ("backend/database/seeders/DemoDataSeeder.php", "DemoHistorySeeder"),
            ("backend/database/seeders/ManufacturingA1Seeder.php", "داده نمونه فعال است"),
        ],
        "text_when_false": [
            ("backend/database/seeders/ManufacturingA1Seeder.php", "داده نمونه غیرفعال است"),
        ],
    },
    {
        "flag": "include_tests",
        "present_when_true": ["backend/phpunit.xml"],
        "absent_when_false": [],
        "text_when_false": [],
        "text_when_true": [],
        "count_when_true": [("backend/tests/Feature", 10)],
        "count_when_false": [("backend/tests/Feature", 0)],
    },
    {
        "flag": "iot_enabled",
        "present_when_true": ["deploy/mosquitto/config/mosquitto.conf"],
        "absent_when_false": ["deploy/mosquitto/config/mosquitto.conf"],
        "text_when_false": [("docker-compose.yml", "سرویس MQTT غیرفعال است")],
        "text_when_true": [("docker-compose.yml", "mosquitto")],
    },
    {
        "flag": "db_driver",
        "values": {
            "sqlite": {
                "absent": ["deploy/mosquitto/config/mosquitto.conf"],
                "text": [("docker-compose.yml", "DB_CONNECTION: sqlite")],
            },
            "pgsql": {
                "text": [
                    ("docker-compose.yml", "postgres:16-alpine"),
                    ("backend/.env", "DB_CONNECTION=pgsql"),
                ],
            },
            "mysql": {"text": [("docker-compose.yml", "mysql:8.4")]},
        },
    },
]


def build(settings: dict, key: str) -> Path:
    project = ProjectConfig(
        id=f"flag-{key}",
        name="پروژه پرچم‌ها",
        name_en=f"Flag Check {key}",
        preset_key="general_discrete",
        selection=Selection(modules=MODULES),
        settings=settings,
    )
    result = generate_package(project)
    return Path(result.output_dir)


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(("  PASS  " if ok else "  FAIL  ") + name + (f" — {detail}" if detail and not ok else ""))
    return ok


def main() -> int:
    failures = 0
    for spec in CHECKS:
        flag = spec["flag"]

        if "values" in spec:
            print(f"\n[{flag}] (حالت‌های مختلف)")
            for value, expectation in spec["values"].items():
                root = build({"db_driver": value, "project_slug": f"flag-{flag}-{value}"}, f"{flag}-{value}")
                for rel, needle in expectation.get("text", []):
                    text = (root / rel).read_text(encoding="utf-8") if (root / rel).exists() else ""
                    failures += 0 if check(f"{flag}={value}: {rel} شامل «{needle}»", needle in text, rel) else 1
                for rel in expectation.get("absent", []):
                    failures += 0 if check(f"{flag}={value}: نبود {rel}", not (root / rel).exists()) else 1
                shutil.rmtree(root, ignore_errors=True)
                root.parent.joinpath(root.name + ".zip").unlink(missing_ok=True)
            continue

        print(f"\n[{flag}]")
        root_on = build({flag: True, "project_slug": f"flag-{flag}-on"}, f"{flag}-on")
        root_off = build({flag: False, "project_slug": f"flag-{flag}-off"}, f"{flag}-off")

        for rel in spec.get("present_when_true", []):
            failures += 0 if check(f"{flag}=true → وجود {rel}", (root_on / rel).exists()) else 1
        for rel in spec.get("absent_when_false", []):
            failures += 0 if check(f"{flag}=false → نبود {rel}", not (root_off / rel).exists()) else 1
        for rel, needle in spec.get("text_when_true", []):
            path = root_on / rel
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if needle is None:
                continue
            failures += 0 if check(f"{flag}=true → {rel} شامل «{needle}»", needle in text, rel) else 1
        for rel, needle in spec.get("text_when_false", []):
            path = root_off / rel
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            if needle is None:
                continue
            failures += 0 if check(f"{flag}=false → {rel} شامل «{needle}»", needle in text, rel) else 1
        for rel in spec.get("always_present", []):
            for label, root in (("on", root_on), ("off", root_off)):
                failures += 0 if check(f"{flag}={label} → وجود همیشگی {rel}", (root / rel).exists()) else 1
        for rel, minimum in spec.get("count_when_true", []):
            found = len(list((root_on / rel).rglob("*.php"))) if (root_on / rel).exists() else 0
            failures += 0 if check(f"{flag}=true → ≥{minimum} فایل در {rel}", found >= minimum, f"{found}") else 1
        for rel, maximum in spec.get("count_when_false", []):
            found = len(list((root_off / rel).rglob("*.php"))) if (root_off / rel).exists() else 0
            failures += 0 if check(f"{flag}=false → ≤{maximum} فایل در {rel}", found <= maximum, f"{found}") else 1

        for root in (root_on, root_off):
            shutil.rmtree(root, ignore_errors=True)
            root.parent.joinpath(root.name + ".zip").unlink(missing_ok=True)

    print(f"\nfailures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
