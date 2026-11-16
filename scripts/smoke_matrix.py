# -*- coding: utf-8 -*-
"""
ماتریس دود-تست موتور تولید
==============================
چند پیکربندی متفاوت (پایگاه داده، AI، IoT، سطح ماژول‌ها) را تولید و
اعتبارسنجی می‌کند تا شاخه‌های شرطی مولدها پوشش داده شود.

    .venv/bin/python scripts/smoke_matrix.py [quick]
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "builder" / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.config import OUTPUT_DIR  # noqa: E402
from app.generator import generate_package  # noqa: E402
from app.presets import apply_preset  # noqa: E402
from app.schemas import ProjectConfig, Selection  # noqa: E402

from package_checks import summarize, validate_package  # noqa: E402

CASES = [
    {
        "key": "small-mysql",
        "preset": None,
        "selection": {"modules": ["A1", "B1", "F9"]},
        "settings": {"db_driver": "mysql", "company_name": "کارخانه کوچک"},
    },
    {
        "key": "full-mysql-iot",
        "preset": "enterprise_full",
        "settings": {
            "db_driver": "mysql",
            "iot_enabled": True,
            "ai_enabled": True,
            "include_demo_data": True,
            "company_name": "هلدینگ بزرگ صنعتی",
            "industry": "enterprise_full",
        },
    },
    {
        "key": "sqlite-minimal",
        "preset": "smb_minimal",
        "settings": {
            "db_driver": "sqlite",
            "cache_driver": "file",
            "queue_driver": "sync",
            "session_driver": "file",
            "ai_enabled": False,
            "iot_enabled": False,
            "include_demo_data": False,
            "include_tests": False,
            "avalai_enabled": False,
            "company_name": "کارگاه کوچک",
        },
    },
    {
        "key": "pgsql-ai-avalai",
        "preset": "food_pharma",
        "settings": {
            "db_driver": "pgsql",
            "iot_enabled": True,
            "ai_enabled": True,
            "avalai_enabled": True,
            "avalai_api_key": "test-key-not-real",
            "deploy_target": "bare-metal",
            "include_demo_data": True,
            "company_name": "صنایع غذایی و دارویی البرز",
        },
    },
]


def build_project(case: dict) -> ProjectConfig:
    key = case["key"]
    if case.get("preset"):
        payload = apply_preset(case["preset"])
        return ProjectConfig(
            id=f"smoke-{key}",
            name=payload["preset_name"],
            name_en=f"Smoke {key}",
            description="دود-تست ماتریس تولید",
            preset_key=case["preset"],
            selection=Selection(
                mode="preset",
                modules=payload["modules"],
                groups=payload["groups"],
                items=payload["items"],
                ai_points=payload["ai_points"],
            ),
            settings={**payload.get("settings", {}), **case.get("settings", {})},
        )
    return ProjectConfig(
        id=f"smoke-{key}",
        name="پروژه نمونه",
        name_en=f"Smoke {key}",
        preset_key="general_discrete",
        selection=Selection(**case["selection"]),
        settings=case.get("settings", {}),
    )


def main() -> int:
    cases = CASES[:2] if "quick" in sys.argv else CASES
    failures = 0
    rows = []

    for position, case in enumerate(cases):
        key = case["key"]
        started = time.time()
        try:
            result = generate_package(build_project(case))
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"\n[FAIL] {key}: {type(exc).__name__}: {exc}")
            import traceback

            traceback.print_exc(limit=6)
            continue
        duration = time.time() - started

        root = Path(result.output_dir)
        problems = validate_package(root)
        total, lines = summarize(problems)
        failures += 1 if total else 0
        if total:
            print(f"\n[PROBLEMS] {key}")
            for line in lines:
                print(line)

        counts = result.manifest["counts"]
        rows.append(
            (
                key,
                counts["modules"],
                counts["entities"],
                counts["fields"],
                counts["ai_points"],
                result.file_count,
                result.line_count,
                round(result.zip_size_bytes / 1024 / 1024, 2),
                round(duration, 1),
                "ok" if not total else f"{total} problem",
            )
        )

        # فقط آخرین بسته نگه داشته می‌شود تا دیسک پر نشود
        if position != len(cases) - 1:
            shutil.rmtree(root, ignore_errors=True)
            root.parent.joinpath(root.name + ".zip").unlink(missing_ok=True)

    header = ("case", "mod", "ent", "fld", "ai", "files", "lines", "zipMB", "sec", "validation")
    widths = [18, 4, 5, 6, 5, 6, 8, 6, 5, 24]
    print("\n" + "  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    print("\nfailures:", failures)
    print("output dir:", OUTPUT_DIR)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
