# -*- coding: utf-8 -*-
"""
FastAPI — سرویس بک‌اند پلتفرم «سازنده ERP هوشمند کارخانه‌ای»

اجرا:
    cd builder/backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import APP_NAME, APP_NAME_FA, APP_VERSION, HOST, PORT, REPO_ROOT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
logger = logging.getLogger("builder")

FRONTEND_DIST = REPO_ROOT / "builder" / "frontend" / "dist"

app = FastAPI(
    title=APP_NAME,
    description=f"{APP_NAME_FA} — کاتالوگ کامل ماژول‌ها، پیکربندگر تعاملی و تولید بسته آماده استقرار",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# کاتالوگ کامل (depth=4) حدود ۴۰۰ کیلوبایت JSON است؛ فشرده‌سازی پاسخ‌ها
# حجم انتقال را به‌طور محسوس کاهش می‌دهد.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(router)


@app.get("/")
def root() -> JSONResponse:
    """در صورت نبود بیلد فرانت‌اند، اطلاعات سرویس برگردانده می‌شود."""
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {
            "app": APP_NAME,
            "app_fa": APP_NAME_FA,
            "version": APP_VERSION,
            "api_docs": "/api/docs",
            "endpoints": [
                "/api/health", "/api/meta", "/api/catalog", "/api/catalog/stats",
                "/api/catalog/search", "/api/presets", "/api/resolve",
                "/api/advisor/recommend", "/api/projects", "/api/generate", "/api/packages",
            ],
            "frontend_hint": "برای رابط کاربری: cd builder/frontend && npm install && npm run dev",
        }
    )


@app.get("/api/{_rest:path}", include_in_schema=False)
def api_fallback(_rest: str) -> JSONResponse:
    return JSONResponse({"detail": "مسیر API یافت نشد"}, status_code=404)


# سرو فایل‌های بیلد فرانت‌اند (در صورت وجود)
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
