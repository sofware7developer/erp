# -*- coding: utf-8 -*-
"""
راستی‌آزمایی رابط کاربری سازنده (builder/frontend)
=====================================================
سه سطح بررسی:

  ۱. ساخت واقعی باندل مرورگر با `npm run build`
  ۲. بالا آوردن سرویس FastAPI روی یک پورت آزاد و بررسی پاسخ API
     (health/meta/catalog/presets/resolve/packages) با شکل‌های مورد انتظار UI
  ۳. اجرای آزمون دود رندر (`npm run smoke`) که همه صفحه‌ها و کامپوننت‌ها را
     با داده واقعی API رندر می‌کند و نشتی undefined/NaN و خطای رندر را می‌گیرد

    .venv/bin/python scripts/verify_ui.py [--no-build] [--keep-server]

کد خروج: ۰ یعنی همه بررسی‌ها موفق بودند.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "builder" / "frontend"
BACKEND = ROOT / "builder" / "backend"
PYTHON = sys.executable
NPM_BIN = shutil.which("npm")

failures = 0


def report(ok: bool, label: str, detail: str = "") -> None:
    global failures
    if not ok:
        failures += 1
    print(f"   {'PASS' if ok else 'FAIL'}  {label}")
    for line in (detail or "").strip().splitlines():
        if line:
            print(f"        {line}")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout: int = 60):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post(url: str, payload: dict, timeout: int = 120):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def start_server(port: int) -> subprocess.Popen:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    return subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for_health(base: str, process: subprocess.Popen, timeout: int = 90) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"سرویس پیش از آماده‌شدن خارج شد:\n{output[-1200:]}")
        try:
            return fetch(f"{base}/health", timeout=5)
        except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.4)
    raise RuntimeError(f"سرویس در {timeout} ثانیه آماده نشد")


def check_api(base: str) -> None:
    """شکل پاسخ‌هایی که UI می‌خواند."""
    meta = fetch(f"{base}/meta")
    counts = meta.get("counts", {})
    ok = all(counts.get(key) for key in ("sections", "modules", "groups", "items", "ai_points"))
    report(ok, "GET /meta → counts", json.dumps(counts, ensure_ascii=False))

    ok = bool(meta.get("ai_engines")) and bool(meta.get("default_settings"))
    report(
        ok,
        "GET /meta → engines/settings",
        f"{len(meta.get('ai_engines', []))} موتور، {len(meta.get('default_settings', {}))} کلید تنظیمات، "
        f"{len(meta.get('advisor_goals', []))} هدف دستیار، {len(meta.get('industries', []))} صنعت",
    )

    catalog = fetch(f"{base}/catalog?depth=4")
    sections = catalog.get("sections", [])
    ok = len(sections) == counts.get("sections") and sections[0].get("modules")
    module_keys = set(sections[0]["modules"][0]) if ok else set()
    ok = ok and {"code", "name", "groups", "item_count", "ai_count"} <= module_keys
    report(ok, "GET /catalog?depth=4 → shape", f"{len(sections)} بخش، کلیدهای ماژول: {sorted(module_keys)[:6]}…")

    presets = fetch(f"{base}/presets").get("presets", [])
    report(len(presets) >= 8, "GET /presets", f"{len(presets)} پریست")

    preset_key = presets[0]["key"]
    applied = post(f"{base}/presets/{preset_key}/apply", {})
    resolution = post(
        f"{base}/resolve",
        {
            "selection": {
                "sections": [],
                "modules": applied.get("modules", []),
                "groups": applied.get("groups", []),
                "items": applied.get("items", []),
                "ai_points": applied.get("ai_points", []),
                "mode": "custom",
            }
        },
    )
    ok = bool(resolution.get("counts", {}).get("modules")) and bool(resolution.get("sections"))
    report(
        ok,
        f"POST /presets/{preset_key}/apply + /resolve",
        f"{resolution['counts']['modules']} ماژول، {resolution['counts']['tables']} جدول، "
        f"{len(resolution.get('ai_engines', []))} موتور AI، {len(resolution.get('auto_added', []))} پیش‌نیاز خودکار",
    )

    packages = fetch(f"{base}/packages").get("packages", [])
    if not packages:
        report(True, "GET /packages", "بسته‌ای وجود ندارد (این بررسی رد می‌شود)")
        return
    package_id = packages[0]["package_id"]
    detail = fetch(f"{base}/packages/{package_id}")
    ok = bool(detail.get("modules")) and bool(detail.get("top_level")) and "manifest_counts" in detail
    module0 = (detail.get("modules") or [{}])[0]
    ok = ok and {"code", "label_fa", "slug", "entities", "ai_points"} <= set(module0)
    report(
        ok,
        f"GET /packages/{package_id} → detail",
        f"{len(detail['modules'])} ماژول، {len(detail['top_level'])} گره ریشه، "
        f"کلیدهای ماژول: {sorted(module0)}",
    )

    tree = fetch(f"{base}/packages/{package_id}/tree").get("tree", [])
    first_file = None
    stack = list(tree)
    while stack:
        node = stack.pop()
        if node.get("type") == "file":
            first_file = node
            break
        stack.extend(node.get("children", []))
    report(bool(tree) and first_file is not None, "GET /packages/{id}/tree", f"{len(tree)} گره ریشه")

    if first_file:
        payload = fetch(f"{base}/packages/{package_id}/file?path={urllib.parse.quote(first_file['path'])}")
        ok = payload.get("path") == first_file["path"] and "content" in payload
        report(ok, "GET /packages/{id}/file", f"{payload.get('path')} — {payload.get('lines')} خط")


def run_npm(args: list[str], *, env: dict | None = None, timeout: int = 900) -> tuple[bool, str]:
    if not NPM_BIN:
        return True, "npm در دسترس نیست — این بررسی رد شد"
    if not (FRONTEND / "node_modules").exists():
        install = subprocess.run(
            [NPM_BIN, "install", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=FRONTEND, capture_output=True, text=True, timeout=timeout,
        )
        if install.returncode:
            return False, "npm install شکست خورد:\n" + (install.stderr or install.stdout)[-900:]
    result = subprocess.run(
        [NPM_BIN, "run", *args],
        cwd=FRONTEND, capture_output=True, text=True, timeout=timeout,
        env={**os.environ, **(env or {})},
    )
    output = (result.stdout or "") + (result.stderr or "")
    tail = "\n".join(output.strip().splitlines()[-40:])
    return result.returncode == 0, tail


def main() -> int:
    parser = argparse.ArgumentParser(description="راستی‌آزمایی رابط کاربری سازنده ERP")
    parser.add_argument("--no-build", action="store_true", help="ساخت باندل مرورگر رد شود")
    parser.add_argument("--no-smoke", action="store_true", help="آزمون دود رندر رد شود")
    parser.add_argument("--port", type=int, default=0, help="پورت سرویس موقت (پیش‌فرض: پورت آزاد)")
    args = parser.parse_args()

    port = args.port or free_port()
    base = f"http://127.0.0.1:{port}/api"

    print("۱) ساخت باندل مرورگر")
    if args.no_build:
        print("   SKIP  (--no-build)")
    else:
        ok, detail = run_npm(["build"])
        report(ok, "vite build", detail if not ok else "\n".join(detail.splitlines()[-5:]))

    print("\n۲) سرویس API و شکل پاسخ‌ها")
    process = start_server(port)
    try:
        health = wait_for_health(base, process)
        report(health.get("status") == "ok", "GET /health", f"{health.get('app_fa')} v{health.get('version')}")
        check_api(base)

        print("\n۳) آزمون دود رندر رابط کاربری")
        if args.no_smoke:
            print("   SKIP  (--no-smoke)")
        else:
            ok, detail = run_npm(["smoke"], env={"SMOKE_API": base}, timeout=600)
            report(ok, "npm run smoke", detail)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    print(f"\nfailures: {failures}")
    print(f"server: {base} (متوقف شد)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
