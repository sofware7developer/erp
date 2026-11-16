# -*- coding: utf-8 -*-
"""
اعتبارسنجی ایستای یک بسته تولیدشده
====================================
    .venv/bin/python scripts/validate_package.py [مسیر بسته]

بدون آرگومان، تازه‌ترین بسته در `dist-packages/` بررسی می‌شود.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_checks import (  # noqa: E402
    REPO_ROOT,
    build_frontend,
    check_compose_services,
    check_manifest,
    run_ai_tests,
    summarize,
    validate_package,
)


def newest_package() -> Path:
    out = REPO_ROOT / "dist-packages"
    dirs = sorted((p for p in out.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime) if out.exists() else []
    if not dirs:
        raise SystemExit("بسته‌ای در dist-packages/ یافت نشد؛ ابتدا یک بسته تولید کنید.")
    return dirs[-1]


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else newest_package()
    print("بسته:", root)

    problems = validate_package(root)
    total, lines = summarize(problems)
    print(f"\nبررسی ایستا: {total} مشکل")
    for line in lines:
        print(line)

    checks = [
        ("manifest", *check_manifest(root)),
        ("docker-compose", *check_compose_services(root)),
        ("ai-service tests", *run_ai_tests(root)),
    ]
    failures = total
    print()
    for name, ok, detail in checks:
        failures += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")

    if "--build-frontend" in sys.argv:
        ok, detail = build_frontend(root)
        failures += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  frontend build:\n{detail}")

    print("\nfailures:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
