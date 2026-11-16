# -*- coding: utf-8 -*-
"""
اعتبارسنجی کاتالوگ ERP
----------------------
بررسی‌ها:
  ۱. یکتایی و صحت کدها در هر چهار سطح
  ۲. صحت ارجاع وابستگی‌ها (deps) به کدهای موجود
  ۳. وجود نویسه‌های غیرمجاز (مثلاً CJK یا کاراکترهای کنترلی) در متن فارسی
  ۴. شمارش بخش / ماژول / زیرماژول / زیرمجموعه / نقاط AI
  ۵. خالی نبودن نام‌ها و حداقل طول متن

اجرا:
    python3 scripts/validate_catalog.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "builder" / "backend"))

from app.catalog.registry import catalog, index, stats  # noqa: E402

# نویسه‌های مجاز: فارسی/عربی، لاتین، ارقام، علائم رایج
FORBIDDEN_RANGES = [
    (0x3000, 0x9FFF),   # CJK
    (0xAC00, 0xD7AF),   # هانگول
    (0x0400, 0x04FF),   # سیریلیک
]

errors: list[str] = []
warnings: list[str] = []


def check_text(text: str, where: str) -> None:
    if not text or not text.strip():
        errors.append(f"{where}: متن خالی است")
        return
    if len(text.strip()) < 3:
        warnings.append(f"{where}: متن بسیار کوتاه است -> {text!r}")
    for ch in text:
        code = ord(ch)
        if any(start <= code <= end for start, end in FORBIDDEN_RANGES):
            errors.append(f"{where}: نویسه غیرمجاز U+{code:04X} ({unicodedata.name(ch, '?')}) در {text!r}")
        if unicodedata.category(ch) in {"Cc", "Cf"} and ch not in "\u200c\u200f":
            errors.append(f"{where}: نویسه کنترلی در {text!r}")
    if "  " in text:
        warnings.append(f"{where}: فاصله دوبل در {text!r}")
    if text != text.strip():
        warnings.append(f"{where}: فاصله ابتدا/انتها در {text!r}")


def main() -> int:
    idx = index()
    sections = catalog()
    all_codes: set[str] = set()

    for sec in sections:
        check_text(sec["name"], f"بخش {sec['code']}")
        if not re.fullmatch(r"[A-V]", sec["code"]):
            errors.append(f"کد بخش نامعتبر: {sec['code']}")

        expected_module_index = 0
        for mod in sec["modules"]:
            expected_module_index += 1
            expected_code = f"{sec['code']}{expected_module_index}"
            if mod["code"] != expected_code:
                errors.append(f"ترتیب ماژول نادرست: انتظار {expected_code} ولی {mod['code']}")
            if mod["code"] in all_codes:
                errors.append(f"کد تکراری: {mod['code']}")
            all_codes.add(mod["code"])
            check_text(mod["name"], f"ماژول {mod['code']}")
            check_text(mod["name_en"], f"نام انگلیسی ماژول {mod['code']}")
            if not mod["summary"]:
                warnings.append(f"ماژول {mod['code']} خلاصه ندارد")

            expected_group_index = 0
            for grp in mod["groups"]:
                expected_group_index += 1
                expected_group = f"{mod['code']}.{expected_group_index}"
                if grp["code"] != expected_group:
                    errors.append(f"کد زیرماژول نادرست: انتظار {expected_group} ولی {grp['code']}")
                if grp["code"] in all_codes:
                    errors.append(f"کد تکراری: {grp['code']}")
                all_codes.add(grp["code"])
                check_text(grp["name"], f"زیرماژول {grp['code']}")
                if not grp["items"]:
                    errors.append(f"زیرماژول {grp['code']} هیچ زیرمجموعه‌ای ندارد")

                expected_item_index = 0
                for item in grp["items"]:
                    expected_item_index += 1
                    expected_item = f"{grp['code']}.{expected_item_index}"
                    if item["code"] != expected_item:
                        errors.append(f"کد زیرمجموعه نادرست: انتظار {expected_item} ولی {item['code']}")
                    if item["code"] in all_codes:
                        errors.append(f"کد تکراری: {item['code']}")
                    all_codes.add(item["code"])
                    check_text(item["name"], f"آیتم {item['code']}")

    # اعتبار ارجاع وابستگی‌ها
    dangling = 0
    for item in idx.items.values():
        for dep in item["deps"]:
            if dep not in all_codes:
                dangling += 1
                if dangling <= 25:
                    errors.append(f"آیتم {item['code']}: وابستگی ناموجود -> {dep}")
    if dangling > 25:
        errors.append(f"... و {dangling - 25} وابستگی ناموجود دیگر")

    totals = stats()["totals"]
    per_section = {row["code"]: row for row in stats()["per_section"]}

    print("=" * 78)
    print("اعتبارسنجی کاتالوگ ERP")
    print("=" * 78)
    print(f"{'بخش':<6}{'ماژول':>7}{'زیرماژول':>11}{'زیرمجموعه':>12}{'نقطه AI':>10}")
    print("-" * 78)
    for code in sorted(per_section):
        row = per_section[code]
        print(f"{code:<6}{row['modules']:>7}{row['groups']:>11}{row['items']:>12}{row['ai_points']:>10}")
    print("-" * 78)
    print(
        f"{'جمع':<6}{totals['modules']:>7}{totals['groups']:>11}"
        f"{totals['items']:>12}{totals['ai_points']:>10}"
    )
    print("=" * 78)

    if warnings:
        print(f"\n⚠ {len(warnings)} هشدار:")
        for warning in warnings[:30]:
            print(f"   - {warning}")
        if len(warnings) > 30:
            print(f"   ... و {len(warnings) - 30} هشدار دیگر")

    if errors:
        print(f"\n✗ {len(errors)} خطا:")
        for error in errors[:60]:
            print(f"   - {error}")
        if len(errors) > 60:
            print(f"   ... و {len(errors) - 60} خطای دیگر")
        return 1

    print("\n✓ کاتالوگ معتبر است")

    # خروجی JSON برای مصرف فرانت‌اند و ژنراتور
    out = ROOT / "data" / "catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog(), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ خروجی JSON نوشته شد: {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
