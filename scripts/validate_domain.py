# -*- coding: utf-8 -*-
"""اعتبارسنجی مدل دامنه: FKها، نام جداول، مرتب‌سازی توپولوژیک."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "builder" / "backend"))

from app.catalog.registry import index  # noqa: E402
from app.domain.registry import (  # noqa: E402
    SYSTEM_MODULES, all_specs, coverage_report, resolve_modules,
    specs_for_modules, validate_foreign_keys,
)


def main() -> int:
    errors: list[str] = []

    specs = all_specs()
    idx = index()
    missing = sorted(set(idx.modules) - set(specs))
    if missing:
        errors.append(f"ماژول‌های بدون مشخصات دامنه: {missing}")

    fk_problems = validate_foreign_keys()
    if fk_problems:
        errors.extend([f"FK نامعتبر: {p}" for p in fk_problems])

    report = coverage_report()
    print("=" * 74)
    print("اعتبارسنجی مدل دامنه")
    print("=" * 74)
    print(f"ماژول‌های دارای مشخصات دامنه : {report['total_modules']} / {len(idx.modules)}")
    print(f"  - دست‌نویس (غنی)           : {report['handwritten_count']}")
    print(f"  - خودکار (از کاتالوگ)      : {report['derived_count']}")
    print(f"کل موجودیت‌ها (جداول)        : {report['entities_total']}")
    print(f"کل فیلدها                    : {report['fields_total']}")
    print(f"ماژول‌های سیستمی همیشه‌ساخته : {', '.join(SYSTEM_MODULES)}")

    # نمونه: انتخاب کل بخش A و F و بررسی خروجی
    sel = resolve_modules(["A1", "A2", "A3", "F1", "F2", "E1"])
    spec = specs_for_modules(sel["resolved"])
    print("\nنمونه حل وابستگی برای [A1, A2, A3, F1, F2, E1]:")
    print(f"  ماژول‌های نهایی : {len(sel['resolved'])} -> {', '.join(sel['resolved'])}")
    print(f"  خودکار افزوده   : {len(sel['auto_added'])} -> {', '.join(sel['auto_added'])}")
    print(f"  جداول تولیدشده  : {spec['counts']['entities']}")
    print(f"  فیلدها            : {spec['counts']['fields']}")

    # سناریوی حداکثری: همه ماژول‌ها
    full = resolve_modules(list(idx.modules))
    full_spec = specs_for_modules(full["resolved"])
    print("\nسناریوی کامل (همه ۱۳۰ ماژول):")
    print(f"  جداول            : {full_spec['counts']['entities']}")
    print(f"  فیلدها           : {full_spec['counts']['fields']}")
    print(f"  اولین جداول      : {', '.join(full_spec['tables'][:6])}")

    if errors:
        print(f"\n✗ {len(errors)} خطا:")
        for error in errors[:40]:
            print(f"   - {error}")
        if len(errors) > 40:
            print(f"   ... و {len(errors) - 40} خطای دیگر")
        return 1
    print("\n✓ مدل دامنه معتبر است")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
