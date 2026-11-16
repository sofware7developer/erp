# -*- coding: utf-8 -*-
"""
راستی‌آزمایی سرتاسری بسته تولیدشده
=====================================
یک بسته نمونه می‌سازد و هر چهار سطح بررسی را روی آن اجرا می‌کند:

  ۱. اعتبارسنجی ایستای همه فایل‌ها
  ۲. سازگاری manifest.json و docker-compose.yml
  ۳. آزمون‌های pytest سرویس AI تولیدشده
  ۴. ساخت واقعی فرانت‌اند با `npm install && npm run build`

    .venv/bin/python scripts/verify_generated.py [--no-build] [--preset smb_minimal]
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "builder" / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.generator import generate_package  # noqa: E402
from app.presets import apply_preset  # noqa: E402
from app.schemas import ProjectConfig, Selection  # noqa: E402

from package_checks import (  # noqa: E402
    build_frontend,
    check_compose_services,
    check_demo_data,
    check_manifest,
    check_policy_bindings,
    run_ai_tests,
    summarize,
    validate_package,
)


def build_project(preset_key: str) -> ProjectConfig:
    payload = apply_preset(preset_key)
    return ProjectConfig(
        id="verify-generated",
        name=payload["preset_name"],
        name_en=f"Verify {preset_key}",
        description="راستی‌آزمایی سرتاسری موتور تولید",
        preset_key=preset_key,
        selection=Selection(
            mode="preset",
            modules=payload["modules"],
            groups=payload["groups"],
            items=payload["items"],
            ai_points=payload["ai_points"],
        ),
        settings={
            **payload.get("settings", {}),
            "company_name": "صنایع راستی‌آزمایی",
            "db_driver": "mysql",
            "iot_enabled": True,
            "ai_enabled": True,
            "include_demo_data": True,
            "include_report_templates": True,
            "include_mobile_pwa": True,
            "include_docs": True,
            "generate_api_docs": True,
        },
    )


def main() -> int:
    do_build = "--no-build" not in sys.argv
    preset_key = "general_discrete"
    if "--preset" in sys.argv:
        preset_key = sys.argv[sys.argv.index("--preset") + 1]

    started = time.time()
    result = generate_package(build_project(preset_key))
    root = Path(result.output_dir)
    print(f"بسته: {result.package_id}")
    print(
        f"ماژول‌ها: {result.manifest['counts']['modules']} | جداول: {result.manifest['counts']['entities']}"
        f" | فیلدها: {result.manifest['counts']['fields']}"
        f" | نقاط AI: {result.manifest['counts']['ai_points']}"
    )
    print(f"فایل‌ها: {result.file_count} | خط‌ها: {result.line_count}"
          f" | zip: {result.zip_size_bytes / 1024 / 1024:.2f} MB | زمان: {time.time() - started:.1f}s")

    failures = 0

    print("\n۱) اعتبارسنجی ایستا")
    problems = validate_package(root)
    total, lines = summarize(problems)
    failures += 1 if total else 0
    print(f"   {'PASS' if not total else 'FAIL'}  {total} مشکل")
    for line in lines:
        print("  " + line)

    print("\n۲) مانیفست و پشته استقرار")
    for name, check in (
        ("manifest", check_manifest),
        ("docker-compose", check_compose_services),
        ("demo-data", check_demo_data),
        ("policy-bindings", check_policy_bindings),
    ):
        ok, detail = check(root)
        failures += 0 if ok else 1
        print(f"   {'PASS' if ok else 'FAIL'}  {name}: {detail}")

    print("\n۳) آزمون‌های سرویس AI")
    ok, detail = run_ai_tests(root)
    failures += 0 if ok else 1
    print(f"   {'PASS' if ok else 'FAIL'}  {detail}")

    print("\n۴) ساخت فرانت‌اند")
    if not do_build:
        print("   SKIP  (--no-build)")
    else:
        ok, detail = build_frontend(root)
        failures += 0 if ok else 1
        print(f"   {'PASS' if ok else 'FAIL'}")
        for line in detail.splitlines():
            print("   " + line)

    # پاکسازی خروجی حجیم (node_modules و dist) ولی نگه‌داشتن بسته برای مرور
    for junk in ("frontend/node_modules", "frontend/dist"):
        shutil.rmtree(root / junk, ignore_errors=True)

    print(f"\nfailures: {failures}")
    print(f"package: {root}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
