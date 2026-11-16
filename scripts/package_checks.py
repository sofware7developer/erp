# -*- coding: utf-8 -*-
"""
ابزارهای بررسی بسته تولیدشده
==============================
سه سطح بررسی برای هر بسته خروجی موتور تولید:

۱. `validate_package` — بررسی ایستا: جای‌گذار جامانده، نویسه‌های غیرمجاز
   (CJK/سیریلیک/کنترلی)، ساختار Python/JSON/YAML، توازن پرانتز PHP،
   `bash -n` برای اسکریپت‌ها و `node --check` برای JS.
۲. `run_ai_tests` — اجرای pytest روی `ai-service/tests` بسته تولیدشده.
۳. `build_frontend` — اجرای `npm install && npm run build` روی فرانت‌اند
   تولیدشده (نیاز به شبکه و node دارد).

این ماژول توسط `scripts/validate_package.py`، `scripts/smoke_matrix.py` و
`scripts/verify_generated.py` استفاده می‌شود.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
NODE_BIN = shutil.which("node")
NPM_BIN = shutil.which("npm")

PLACEHOLDER = re.compile(r"@@[a-z_]+@@")
BAD_CHARS = re.compile(
    r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0000-\u0008\u000b\u000c\u000e-\u001f]"
)
SKIP_NAMES = (".gitkeep", "__init__.py")


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and "node_modules" not in path.parts and "dist" not in path.parts:
            yield path


def validate_package(root: Path) -> dict[str, list[str]]:
    """بررسی ایستای همه فایل‌های بسته؛ خروجی: دسته -> فهرست مشکلات."""
    problems: dict[str, list[str]] = {
        "placeholders": [],
        "bad_chars": [],
        "py_syntax": [],
        "json": [],
        "yaml": [],
        "php_structure": [],
        "sh": [],
        "js_syntax": [],
        "empty": [],
    }
    try:
        import yaml  # type: ignore
    except ImportError:  # pragma: no cover
        yaml = None

    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        if rel.endswith(SKIP_NAMES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if not text.strip():
            problems["empty"].append(rel)

        for match in PLACEHOLDER.finditer(text):
            problems["placeholders"].append(f"{rel}: {match.group(0)}")
        for match in BAD_CHARS.finditer(text):
            problems["bad_chars"].append(f"{rel}: {match.group(0)!r}")

        if rel.endswith(".py"):
            try:
                ast.parse(text)
            except SyntaxError as exc:
                problems["py_syntax"].append(f"{rel}:{exc.lineno}: {exc.msg}")

        if rel.endswith((".json", ".webmanifest")):
            try:
                json.loads(text)
            except Exception as exc:  # noqa: BLE001
                problems["json"].append(f"{rel}: {exc}")

        if rel.endswith((".yml", ".yaml")) and yaml is not None:
            try:
                yaml.safe_load(text)
            except Exception as exc:  # noqa: BLE001
                problems["yaml"].append(f"{rel}: {exc}")

        if rel.endswith(".php"):
            if text.count("{") - text.count("}"):
                problems["php_structure"].append(f"{rel}: آکولاد نابرابر")
            if text.count("(") - text.count(")"):
                problems["php_structure"].append(f"{rel}: پرانتز نابرابر")
            if not text.lstrip().startswith("<?php"):
                problems["php_structure"].append(f"{rel}: بدون <?php")
            class_match = re.search(r"^\s*(?:final\s+|abstract\s+)?class\s+(\w+)", text, re.M)
            if class_match and not rel.endswith(class_match.group(1) + ".php"):
                problems["php_structure"].append(
                    f"{rel}: نام کلاس {class_match.group(1)} با نام فایل نمی‌خواند"
                )
            namespace = re.search(r"^namespace\s+([^;]+);", text, re.M)
            if namespace:
                expected = _namespace_from_path(root, rel)
                if expected and namespace.group(1).strip() != expected:
                    problems["php_structure"].append(
                        f"{rel}: namespace «{namespace.group(1)}» ≠ انتظار «{expected}»"
                    )

        if rel.endswith(".sh"):
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                problems["sh"].append(f"{rel}: {result.stderr.strip()[:140]}")

        if rel.endswith(".js") and NODE_BIN:
            result = subprocess.run([NODE_BIN, "--check", str(path)], capture_output=True, text=True)
            if result.returncode and "Cannot use import statement" not in result.stderr:
                problems["js_syntax"].append(f"{rel}: {result.stderr.strip()[:140]}")

    return problems


def _namespace_from_path(root: Path, rel: str) -> str:
    """استخراج namespace انتظار از مسیر فایل PHP (فقط برای پوشه‌های استاندارد)."""
    parts = Path(rel).parts
    if parts[0] != "backend" or len(parts) < 3:
        return ""
    sub = parts[1]
    if sub in ("database", "tests"):
        return ""
    body = list(parts[2:-1])
    if sub == "app":
        if body and body[0] == "Http":
            return "App\\Http\\" + "\\".join(body[1:])
        return "App\\" + "\\".join(body) if body else "App"
    return ""


def summarize(problems: dict[str, list[str]], *, verbose: int = 6) -> tuple[int, list[str]]:
    """خلاصه مشکلات؛ خروجی: (تعداد کل، خطوط گزارش)."""
    lines: list[str] = []
    total = 0
    for kind, items in problems.items():
        total += len(items)
        if items:
            lines.append(f"  {kind}: {len(items)}")
            for item in items[:verbose]:
                lines.append(f"    - {item}")
            if len(items) > verbose:
                lines.append(f"    … و {len(items) - verbose} مورد دیگر")
    return total, lines


def run_ai_tests(root: Path, *, timeout: int = 600) -> tuple[bool, str]:
    """اجرای آزمون‌های سرویس AI تولیدشده با pytest."""
    service = root / "ai-service"
    if not (service / "tests").exists():
        return True, "سرویس AI در این بسته تولید نشده (ai_enabled=false)"

    env = {**os.environ, "PYTHONPATH": str(service)}
    try:
        result = subprocess.run(
            [PYTHON, "-m", "pytest", "tests", "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=service,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return True, "pytest نصب نیست — آزمون‌های سرویس AI اجرا نشد"
    except subprocess.TimeoutExpired:
        return False, f"آزمون‌های سرویس AI بیش از {timeout} ثانیه طول کشید"

    tail = "\n".join((result.stdout or result.stderr).strip().splitlines()[-6:])
    return result.returncode == 0, tail


def build_frontend(root: Path, *, timeout: int = 900, install: bool = True) -> tuple[bool, str]:
    """اجرای `npm install` و `npm run build` روی فرانت‌اند تولیدشده."""
    frontend = root / "frontend"
    if not (frontend / "package.json").exists():
        return True, "فرانت‌اندی در این بسته نیست"
    if not NPM_BIN:
        return True, "npm در دسترس نیست — ساخت فرانت‌اند بررسی نشد"

    if install and not (frontend / "node_modules").exists():
        result = subprocess.run(
            [NPM_BIN, "install", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=frontend, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode:
            return False, "npm install شکست خورد:\n" + (result.stderr or result.stdout)[-800:]

    result = subprocess.run(
        [NPM_BIN, "run", "build"],
        cwd=frontend, capture_output=True, text=True, timeout=timeout,
    )
    tail = "\n".join((result.stdout or "").strip().splitlines()[-10:])
    if result.returncode:
        return False, "vite build شکست خورد:\n" + (result.stderr or tail)[-1200:]
    return True, tail


def check_compose_services(root: Path) -> tuple[bool, str]:
    """بررسی اینکه سرویس‌های docker-compose با تنظیمات بسته هم‌خوان باشند."""
    compose_path = root / "docker-compose.yml"
    if not compose_path.exists():
        return True, "docker-compose.yml وجود ندارد"
    try:
        import yaml  # type: ignore
    except ImportError:
        return True, "pyyaml نصب نیست"

    data = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
    services = set((data.get("services") or {}).keys())
    env_text = (root / "backend" / ".env").read_text(encoding="utf-8") if (root / "backend" / ".env").exists() else ""

    problems: list[str] = []
    if "DB_CONNECTION=sqlite" not in env_text and "db" not in services:
        problems.append("پایگاه داده غیر sqlite است اما سرویس db در compose نیست")
    if "DB_CONNECTION=sqlite" in env_text and "db" in services:
        problems.append("sqlite انتخاب شده اما سرویس db در compose آمده است")
    if "ERP_IOT_ENABLED=\"true\"" in (compose_path.read_text(encoding="utf-8")) and "mqtt" not in services:
        problems.append("IoT فعال است اما سرویس mqtt در compose نیست")
    if "ai-service" in services and not (root / "ai-service" / "app" / "main.py").exists():
        problems.append("سرویس ai-service در compose است اما پوشه ai-service ساخته نشده")
    if "redis" in services and "REDIS_HOST=redis" not in env_text:
        problems.append("سرویس redis هست اما REDIS_HOST به آن اشاره نمی‌کند")

    return (not problems), "; ".join(problems) or f"{len(services)} سرویس: {', '.join(sorted(services))}"


def check_manifest(root: Path) -> tuple[bool, str]:
    """بررسی سازگاری manifest.json با فایل‌های واقعی بسته."""
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return False, "manifest.json وجود ندارد"
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = manifest.get("counts", {})
    actual = sum(1 for _ in iter_files(root))
    problems: list[str] = []
    if abs(int(counts.get("files", 0)) - actual) > 2:
        problems.append(f"شمار فایل‌ها: manifest={counts.get('files')} واقعی={actual}")
    for module in manifest.get("modules", []):
        if not module.get("slug"):
            problems.append(f"ماژول {module.get('code')} بدون slug")
    if not manifest.get("reproduce", {}).get("selection"):
        problems.append("manifest بخش reproduce.selection ندارد")
    return (not problems), "; ".join(problems) or f"{actual} فایل، {len(manifest.get('modules', []))} ماژول"
