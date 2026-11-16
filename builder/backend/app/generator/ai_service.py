# -*- coding: utf-8 -*-
"""
تولید میکروسرویس هوش مصنوعی (پایتون / FastAPI)
================================================
یک سرویس مستقل با الگوریتم‌های واقعی (numpy، pandas، scikit-learn) برای
هر موتور انتخاب‌شده، به‌همراه کلاینت AvalAI برای بخش زبانی.

ساختار:
  ai-service/requirements.txt
  ai-service/Dockerfile
  ai-service/app/main.py
  ai-service/app/config.py
  ai-service/app/schemas.py
  ai-service/app/avalai_client.py
  ai-service/app/engines/<engine>.py
  ai-service/app/routers/*.py
  ai-service/app/models/store.py
  ai-service/app/data/sample.py
  ai-service/tests/test_smoke.py
"""

from __future__ import annotations

import json
from typing import Any

from .writers import Package, render

REQUIREMENTS = """# میکروسرویس هوش مصنوعی — @@app_name@@
# نصب: pip install -r requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.0
numpy==2.2.1
pandas==2.2.3
scikit-learn==1.6.0
scipy==1.14.1
httpx==0.28.1
python-multipart==0.0.20
orjson==3.10.12
"""

DOCKERFILE = """FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    TZ=@@timezone@@

WORKDIR /srv/ai-service

RUN apt-get update \\
    && apt-get install -y --no-install-recommends build-essential curl \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash aiservice \\
    && mkdir -p /srv/ai-service/models /srv/ai-service/logs \\
    && chown -R aiservice:aiservice /srv/ai-service
USER aiservice

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \\
    CMD curl -fsS http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
"""

ENV_EXAMPLE = """# پیکربندی میکروسرویس هوش مصنوعی
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8001
AI_ENVIRONMENT=production
AI_LOG_LEVEL=info

# مسیر ذخیره مدل‌های آموزش‌دیده
MODEL_STORE_PATH=./models

# اتصال به بک‌اند لاراول (اختیاری — برای همگام‌سازی لاگ پیش‌بینی)
LARAVEL_API_URL=@@laravel_url@@
LARAVEL_API_TOKEN=

# AvalAI — اختیاری، فقط برای موتورهای زبانی (NLP، چت، خلاصه‌سازی)
AVALAI_API_KEY=@@avalai_key@@
AVALAI_BASE_URL=@@avalai_base_url@@
AVALAI_MODEL=@@avalai_model@@
AVALAI_TIMEOUT=45

# حد آستانه‌ها
ANOMALY_Z_THRESHOLD=3.0
DRIFT_PSI_THRESHOLD=0.25
FORECAST_SEASON_LENGTH=12
SIMULATION_RUNS=500
"""

CONFIG_PY = r'''"""پیکربندی میکروسرویس هوش مصنوعی."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


class Settings:
    """تنظیمات مبتنی بر متغیرهای محیطی."""

    def __init__(self) -> None:
        self.host: str = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
        self.port: int = int(os.getenv("AI_SERVICE_PORT", "8001"))
        self.environment: str = os.getenv("AI_ENVIRONMENT", "production")
        self.log_level: str = os.getenv("AI_LOG_LEVEL", "info").upper()

        self.model_store_path: Path = Path(os.getenv("MODEL_STORE_PATH", "./models"))
        self.model_store_path.mkdir(parents=True, exist_ok=True)

        self.laravel_api_url: str = os.getenv("LARAVEL_API_URL", "").rstrip("/")
        self.laravel_api_token: str = os.getenv("LARAVEL_API_TOKEN", "")

        self.avalai_api_key: str = os.getenv("AVALAI_API_KEY", "").strip()
        self.avalai_base_url: str = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1").rstrip("/")
        self.avalai_model: str = os.getenv("AVALAI_MODEL", "gpt-4o-mini")
        self.avalai_timeout: int = int(os.getenv("AVALAI_TIMEOUT", "45"))

        self.anomaly_z_threshold: float = float(os.getenv("ANOMALY_Z_THRESHOLD", "3.0"))
        self.drift_psi_threshold: float = float(os.getenv("DRIFT_PSI_THRESHOLD", "0.25"))
        self.forecast_season_length: int = int(os.getenv("FORECAST_SEASON_LENGTH", "12"))
        self.simulation_runs: int = int(os.getenv("SIMULATION_RUNS", "500"))

        # مشخصات کارخانه — از زمان تولید بسته
        self.company_name: str = "@@company_name@@"
        self.currency: str = "@@currency@@"
        self.timezone: str = "@@timezone@@"
        self.employees_count: int = @@employees_count@@
        self.production_lines: int = @@production_lines@@
        self.shifts_per_day: int = @@shifts_per_day@@

    @property
    def avalai_enabled(self) -> bool:
        return bool(self.avalai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# موتورهای فعال در این استقرار
ENABLED_ENGINES: list[str] = @@engines_list@@

# رجیستری قابلیت‌ها (کد کاتالوگ -> موتور)
CAPABILITIES: dict[str, dict[str, str]] = @@capabilities_map@@
'''

SCHEMAS_PY = r'''"""مدل‌های داده ورودی/خروجی سرویس AI."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    """درخواست عمومی همه اندپوینت‌های AI."""

    capability: Optional[str] = Field(default=None, description="کد قابلیت کاتالوگ، مثل A1.3.4")
    capability_name: Optional[str] = Field(default=None, description="نام فارسی قابلیت")
    engine: Optional[str] = Field(default=None, description="موتور هدف")
    model_id: Optional[str] = Field(default=None, description="شناسه مدل ثبت‌شده")
    feature_flag: Optional[str] = None
    module_code: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    requested_by: Optional[int] = None

    # داده اصلی ورودی (بسته به موتور)
    series: list[float] = Field(default_factory=list, description="دنباله زمانی عددی")
    labels: list[str] = Field(default_factory=list, description="برچسب‌های متناظر با series")
    features: list[dict[str, Any]] = Field(default_factory=list, description="رکوردهای ویژگی")
    text: Optional[str] = Field(default=None, description="متن ورودی برای موتورهای زبانی")
    texts: list[str] = Field(default_factory=list)
    target: Optional[str] = Field(default=None, description="ستون هدف برای یادگیری")
    horizon: int = Field(default=6, ge=1, le=120, description="افق پیش‌بینی")
    options: dict[str, Any] = Field(default_factory=dict)


class AiResponse(BaseModel):
    """پاسخ استاندارد همه موتورها."""

    ok: bool = True
    engine: str = ""
    capability: Optional[str] = None
    model_id: Optional[str] = None
    fallback: bool = False
    result: Any = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[str] = Field(default=None, description="توضیح فارسی برای کاربر")
    warnings: list[str] = Field(default_factory=list)
    computed_at: str = ""


class TrainRequest(BaseModel):
    """درخواست آموزش مدل."""

    model_id: str
    algorithm: Optional[str] = None
    engine: str = "classification"
    features: list[dict[str, Any]] = Field(default_factory=list)
    series: list[float] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    target: Optional[str] = None
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    period: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    """اطلاعات یک مدل ثبت‌شده."""

    model_id: str
    engine: str
    algorithm: str
    created_at: str
    samples: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    size_bytes: int = 0
    status: str = "ready"


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    engines: list[str]
    models: int
    avalai_enabled: bool
    capabilities: int
    company: str
    server_time: str
'''

AVALAI_CLIENT_PY = r'''"""کلاینت AvalAI (سازگار با OpenAI) برای قابلیت‌های زبانی.

اگر کلید API تنظیم نشده باشد یا خطایی رخ دهد، None برگردانده می‌شود
و فراخوان باید پاسخ قاعده‌محور داخلی را استفاده کند.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from .config import settings

logger = logging.getLogger("ai.avalai")


def is_enabled() -> bool:
    return settings.avalai_enabled


def chat(messages: list[dict[str, str]], **options: Any) -> Optional[str]:
    """گفت‌وگو با مدل زبانی."""
    if not is_enabled():
        return None

    payload: dict[str, Any] = {
        "model": options.pop("model", settings.avalai_model),
        "messages": messages,
        "temperature": options.pop("temperature", 0.2),
        "max_tokens": options.pop("max_tokens", 900),
    }
    payload.update(options)

    try:
        response = httpx.post(
            f"{settings.avalai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.avalai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.avalai_timeout,
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or None
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("AvalAI request failed: %s", exc)
        return None


def complete(prompt: str, system: str = "", **options: Any) -> Optional[str]:
    """تولید متن با یک پرامپت ساده."""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, **options)


def json_completion(prompt: str, system: str = "", **options: Any) -> Optional[dict[str, Any]]:
    """دریافت پاسخ ساخت‌یافته JSON."""
    options.setdefault("response_format", {"type": "json_object"})
    text = complete(prompt, system=system, **options)
    if not text:
        return None
    return parse_json(text)


def embeddings(inputs: list[str], model: str = "text-embedding-3-small") -> Optional[list[list[float]]]:
    """تولید امبدینگ برای جست‌وجوی معنایی."""
    if not is_enabled() or not inputs:
        return None

    try:
        response = httpx.post(
            f"{settings.avalai_base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.avalai_api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": inputs},
            timeout=settings.avalai_timeout,
        )
        response.raise_for_status()
        data = response.json()
        return [row.get("embedding", []) for row in data.get("data", [])]
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("AvalAI embeddings failed: %s", exc)
        return None


def parse_json(text: str) -> Optional[dict[str, Any]]:
    """استخراج JSON از پاسخ مدل (تحمل بلوک کد)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        result = json.loads(cleaned)
        return result if isinstance(result, dict) else {"value": result}
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def summarize(text: str, max_length: int = 400) -> Optional[str]:
    """خلاصه‌سازی متن فارسی."""
    return complete(
        f"متن زیر را در حداکثر {max_length} کاراکتر به فارسی روان خلاصه کن:\n\n{text[:8000]}",
        system="تو یک خلاصه‌ساز متون صنعتی فارسی هستی.",
    )
'''

MODEL_STORE_PY = r'''"""ذخیره‌سازی مدل‌های آموزش‌دیده (pickle) و رجیستری MLOps."""

from __future__ import annotations

import json
import logging
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger("ai.store")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _model_dir(model_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in model_id)
    directory = settings.model_store_path / safe
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save(model_id: str, artifact: Any, meta: dict[str, Any]) -> dict[str, Any]:
    """ذخیره مدل و متادیتای آن."""
    directory = _model_dir(model_id)
    artifact_path = directory / "model.pkl"
    meta_path = directory / "meta.json"

    with artifact_path.open("wb") as handle:
        pickle.dump(artifact, handle)

    payload = {
        "model_id": model_id,
        "created_at": _now(),
        "size_bytes": artifact_path.stat().st_size,
        **meta,
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("model saved: %s (%s bytes)", model_id, payload["size_bytes"])
    return payload


def load(model_id: str) -> Optional[Any]:
    """بارگذاری مدل ذخیره‌شده."""
    artifact_path = _model_dir(model_id) / "model.pkl"
    if not artifact_path.exists():
        return None
    try:
        with artifact_path.open("rb") as handle:
            return pickle.load(handle)  # noqa: S301 - منبع قابل اعتماد (فایل‌های داخلی)
    except (pickle.PickleError, EOFError, AttributeError) as exc:
        logger.warning("failed to load model %s: %s", model_id, exc)
        return None


def load_meta(model_id: str) -> dict[str, Any]:
    meta_path = _model_dir(model_id) / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def list_models() -> list[dict[str, Any]]:
    """فهرست همه مدل‌های ثبت‌شده."""
    if not settings.model_store_path.exists():
        return []

    models = []
    for directory in sorted(settings.model_store_path.iterdir()):
        meta_path = directory / "meta.json"
        if meta_path.is_file():
            try:
                models.append(json.loads(meta_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    return models


def delete(model_id: str) -> bool:
    import shutil

    directory = _model_dir(model_id)
    if not directory.exists():
        return False
    shutil.rmtree(directory, ignore_errors=True)
    return True


def append_log(model_id: str, entry: dict[str, Any]) -> None:
    """افزودن یک رویداد به لاگ پیش‌بینی/آموزش مدل."""
    log_path = _model_dir(model_id) / "log.jsonl"
    entry.setdefault("at", _now())
    try:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("log write failed for %s: %s", model_id, exc)


def read_log(model_id: str, limit: int = 100) -> list[dict[str, Any]]:
    log_path = _model_dir(model_id) / "log.jsonl"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()[-limit:]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
'''

SAMPLE_DATA_PY = r'''"""داده نمونه و مصنوعی برای اجرای آزمایشی موتورهای AI.

در استقرار واقعی، داده از API لاراول می‌آید؛ این ماژول فقط وقتی استفاده
می‌شود که ورودی خالی باشد تا کاربر بتواند قابلیت را آزمایش کند.
"""

from __future__ import annotations

import math
import random
from typing import Any


def demand_series(periods: int = 36, base: float = 1200.0, seed: int = 7) -> list[float]:
    """دنباله تقاضای ماهانه با روند و فصلانگی (الگوی کارخانه‌های ایرانی)."""
    rng = random.Random(seed)
    values: list[float] = []
    for index in range(periods):
        trend = base + index * (base * 0.012)
        # فروردین و مرداد کاهش تولید؛ اسفند اوج سفارش
        seasonal = {
            0: 0.72, 1: 1.05, 2: 1.10, 3: 0.95, 4: 0.85, 5: 0.90,
            6: 1.00, 7: 1.05, 8: 1.12, 9: 1.18, 10: 1.02, 11: 1.30,
        }[index % 12]
        noise = rng.uniform(0.94, 1.06)
        values.append(round(max(trend * seasonal * noise, 0.0), 2))
    return values


def downtime_minutes(count: int = 30, seed: int = 11) -> list[float]:
    """زمان‌های توقف تجهیزات (دقیقه) با توزیع نمایی-مانند."""
    rng = random.Random(seed)
    return [round(rng.expovariate(1 / 45.0) + 5.0, 2) for _ in range(count)]


def sensor_readings(count: int = 120, seed: int = 13) -> list[dict[str, Any]]:
    """داده سنسور ارتعاش/دما با چند نقطه ناهنجار."""
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for index in range(count):
        vibration = rng.gauss(2.4, 0.35)
        temperature = rng.gauss(62.0, 3.1)
        if index in (17, 54, 98):  # نقاط ناهنجار عمدی
            vibration *= rng.uniform(2.6, 3.8)
            temperature += rng.uniform(14.0, 22.0)
        rows.append(
            {
                "timestamp": index,
                "vibration_mm_s": round(max(vibration, 0.05), 3),
                "temperature_c": round(temperature, 2),
                "current_a": round(rng.gauss(18.5, 1.4), 2),
                "rpm": int(rng.gauss(1480, 12)),
                "line": f"LINE-{(index % 3) + 1}",
            }
        )
    return rows


def quality_samples(count: int = 25, subgroup: int = 5, seed: int = 17) -> list[dict[str, Any]]:
    """نمونه‌برداری زیرگروهی برای نمودارهای کنترلی X-bar/R."""
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for index in range(count):
        values = [round(rng.gauss(50.0, 1.6), 3) for _ in range(subgroup)]
        if index == 12:  # شیفت فرآیند
            values = [round(v + 3.4, 3) for v in values]
        rows.append({"subgroup": index + 1, "values": values, "mean": sum(values) / len(values)})
    return rows


def service_texts(count: int = 40, seed: int = 19) -> list[dict[str, str]]:
    """شرح درخواست‌های خدمات برای طبقه‌بندی متن."""
    templates = [
        ("موتور دستگاه صدای غیرعادی می‌دهد و لرزش زیاد است.", "mechanical"),
        ("صفحه نمایش HMI لمس را پاسخ نمی‌دهد و ریست می‌شود.", "electrical"),
        ("نشتی روغن از گیربکس خط دو مشاهده شد.", "mechanical"),
        ("برنامه PLC پس از قطع برق پاک شده است.", "electrical"),
        ("کیفیت سطح محصول زبر شده و تلرانس رعایت نمی‌شود.", "quality"),
        ("مواد اولیه به موقع به خط نرسید و تولید متوقف شد.", "logistics"),
        ("اپراتور درخواست آموزش کار با دستگاه جدید دارد.", "training"),
        ("دمای قالب بیش از حد مجاز بالا رفته است.", "process"),
    ]
    rng = random.Random(seed)
    return [
        {"text": templates[rng.randrange(len(templates))][0],
         "label": templates[rng.randrange(len(templates))][1]}
        for _ in range(count)
    ]


def production_orders(count: int = 24, seed: int = 23) -> list[dict[str, Any]]:
    """دستورهای کار با سررسید و زمان پردازش برای زمان‌بندی."""
    rng = random.Random(seed)
    orders: list[dict[str, Any]] = []
    for index in range(count):
        orders.append(
            {
                "id": f"WO-{1000 + index}",
                "processing_time": round(rng.uniform(1.5, 12.0), 2),
                "due_date": index + rng.randint(1, 20),
                "priority": rng.randint(1, 5),
                "profit": round(rng.uniform(20, 400), 2),
                "line": rng.choice(["LINE-1", "LINE-2", "LINE-3"]),
                "setup_time": round(rng.uniform(0.2, 1.5), 2),
            }
        )
    return orders


def inventory_items(count: int = 30, seed: int = 29) -> list[dict[str, Any]]:
    """کالاها با مصرف روزانه و زمان تأمین برای بهینه‌سازی نقطه سفارش."""
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []
    for index in range(count):
        daily = max(rng.gauss(45, 18), 1.0)
        items.append(
            {
                "id": f"ITEM-{2000 + index}",
                "daily_demand": round(daily, 2),
                "demand_std": round(daily * rng.uniform(0.12, 0.35), 2),
                "lead_time_days": rng.randint(2, 30),
                "unit_cost": round(rng.uniform(50_000, 25_000_000), 0),
                "holding_rate": round(rng.uniform(0.18, 0.32), 3),
                "order_cost": round(rng.uniform(500_000, 8_000_000), 0),
                "service_level": round(rng.uniform(0.90, 0.99), 3),
            }
        )
    return items


def sin_wave(points: int = 60, noise: float = 0.08, seed: int = 31) -> list[float]:
    """دنباله سینوسی با نویز برای آزمایش شبیه‌سازی."""
    rng = random.Random(seed)
    return [
        round(10 + 4 * math.sin(i / 6.0) + rng.gauss(0, noise * 10), 3)
        for i in range(points)
    ]
'''

ENGINE_BASE_PY = r'''"""پایه مشترک موتورهای هوش مصنوعی."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("ai.engine")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BaseEngine:
    """کلاس پایه همه موتورها.

    هر موتور باید `name`، `endpoint` و متد `run(request)` را پیاده کند.
    خروجی همیشه یک AiResponse است؛ در صورت نبود داده کافی، پاسخ fallback
    با توضیح فارسی برگردانده می‌شود تا جریان کاری کاربر قطع نشود.
    """

    name: str = "base"
    name_fa: str = "موتور پایه"
    endpoint: str = "/ai/base"
    algorithms: list[str] = []
    uses_llm: bool = False
    realtime: bool = False

    def run(self, request: Any) -> dict[str, Any]:  # pragma: no cover - انتزاعی
        raise NotImplementedError

    # --- ابزارهای مشترک -------------------------------------------------- #
    def success(
        self,
        request: Any,
        result: Any,
        *,
        metrics: Optional[dict[str, Any]] = None,
        explanation: str = "",
        warnings: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": self.name,
            "capability": getattr(request, "capability", None),
            "model_id": getattr(request, "model_id", None),
            "fallback": False,
            "result": result,
            "metrics": metrics or {},
            "explanation": explanation,
            "warnings": warnings or [],
            "computed_at": now_iso(),
        }

    def fallback(
        self,
        request: Any,
        reason: str,
        *,
        result: Any = None,
        suggestion: str = "",
    ) -> dict[str, Any]:
        logger.info("fallback for %s: %s", self.name, reason)
        return {
            "ok": False,
            "engine": self.name,
            "capability": getattr(request, "capability", None),
            "model_id": getattr(request, "model_id", None),
            "fallback": True,
            "result": result if result is not None else {},
            "metrics": {},
            "explanation": reason + (" " + suggestion if suggestion else ""),
            "warnings": [reason],
            "computed_at": now_iso(),
        }

    @staticmethod
    def to_floats(values: Any) -> list[float]:
        """تبدیل امن ورودی به فهرست اعداد اعشاری."""
        result: list[float] = []
        for value in values or []:
            try:
                result.append(float(value))
            except (TypeError, ValueError):
                continue
        return result
'''

# --------------------------------------------------------------------------- #
# موتورهای AI — پیاده‌سازی واقعی با numpy/scikit-learn
# --------------------------------------------------------------------------- #
ENGINE_FORECASTING = r'''"""موتور پیش‌بینی — تقاضا، مصرف، فروش، انرژی و قیمت.

الگوریتم‌ها: میانگین متحرک، هموارسازی نمایی هالت (Holt)، هالت-وینترز
فصلی، و رگرسیون خطی با ویژگی‌های زمانی. اگر scikit-learn در دسترس باشد
از Ridge برای جزء روند استفاده می‌شود.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine

try:  # pragma: no cover - وابسته به محیط
    from sklearn.linear_model import Ridge
    HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    HAS_SKLEARN = False


class ForecastingEngine(BaseEngine):
    name = "forecasting"
    name_fa = "پیش‌بینی سری زمانی"
    endpoint = "/ai/forecast"
    algorithms = ["holt_winters", "exponential_smoothing", "seasonal_naive", "ridge_trend"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        series = self.to_floats(request.series)
        horizon = max(1, int(request.horizon or 6))
        season_length = int(request.options.get("season_length", 12))

        if len(series) < 4:
            return self.fallback(
                request,
                "داده کافی برای پیش‌بینی وجود ندارد (حداقل ۴ دوره لازم است).",
                suggestion="ابتدا سابقه مصرف/فروش را از ماژول مربوطه دریافت کنید.",
            )

        values = np.asarray(series, dtype=float)
        method = str(request.options.get("method", "auto"))

        seasonal = season_length > 1 and len(values) >= 2 * season_length
        if method == "auto":
            method = "holt_winters" if seasonal else "exponential_smoothing"

        if method == "seasonal_naive":
            forecast = self._seasonal_naive(values, horizon, season_length)
        elif method == "holt_winters" and seasonal:
            forecast = self._holt_winters(values, horizon, season_length)
        else:
            forecast = self._exponential_smoothing(values, horizon)

        residual_std = float(np.std(np.diff(values), ddof=1)) if len(values) > 2 else float(np.std(values))
        steps = np.arange(1, horizon + 1)
        upper = forecast + 1.96 * residual_std * np.sqrt(steps)
        lower = np.maximum(forecast - 1.96 * residual_std * np.sqrt(steps), 0.0)

        fitted = self._backtest(values, method, season_length)
        labels = list(request.labels) if request.labels else [
            f"دوره {i + 1}" for i in range(horizon)
        ]
        if len(labels) < horizon:
            labels += [f"دوره {i + 1}" for i in range(len(labels), horizon)]

        total = float(np.sum(forecast))
        last_actual = float(values[-1])
        change = ((float(forecast[0]) - last_actual) / last_actual * 100) if last_actual else 0.0

        explanation = (
            f"پیش‌بینی {horizon} دوره با روش «{method}» انجام شد. "
            f"مجموع پیش‌بینی {total:,.0f} و تغییر نسبت به آخرین دوره واقعی "
            f"{change:+.1f}٪ است. خطای بازآزمون (MAPE) برابر {fitted['mape']:.1f}٪ برآورد شد."
            + (" این سری فصلانی است و اثر فصلی در مدل لحاظ شده است." if seasonal else "")
        )

        return self.success(
            request,
            {
                "method": method,
                "seasonal": seasonal,
                "season_length": season_length if seasonal else None,
                "history": values.tolist(),
                "forecast": [round(float(v), 3) for v in forecast],
                "labels": labels[:horizon],
                "upper_bound": [round(float(v), 3) for v in upper],
                "lower_bound": [round(float(v), 3) for v in lower],
                "total": round(total, 3),
                "change_percent": round(change, 2),
                "trend": "صعودی" if forecast[-1] > forecast[0] else "نزولی",
            },
            metrics={
                "mape": round(fitted["mape"], 3),
                "rmse": round(fitted["rmse"], 3),
                "residual_std": round(residual_std, 4),
                "samples": int(len(values)),
                "sklearn": HAS_SKLEARN,
            },
            explanation=explanation,
            warnings=[] if fitted["mape"] < 25 else [
                "خطای مدل بیش از ۲۵٪ است؛ داده‌های بیشتر یا ویژگی کمکی (مثل تقویم تولید) توصیه می‌شود."
            ],
        )

    # --- الگوریتم‌ها ------------------------------------------------------- #
    def _exponential_smoothing(self, values: np.ndarray, horizon: int) -> np.ndarray:
        alpha = 0.35
        level = float(values[0])
        trend = float(values[1] - values[0]) if len(values) > 1 else 0.0
        beta = 0.12
        for observed in values[1:]:
            previous_level = level
            level = alpha * float(observed) + (1 - alpha) * (level + trend)
            trend = beta * (level - previous_level) + (1 - beta) * trend
        return np.asarray([level + (i + 1) * trend for i in range(horizon)], dtype=float)

    def _seasonal_naive(self, values: np.ndarray, horizon: int, season: int) -> np.ndarray:
        tail = values[-season:] if len(values) >= season else values
        repeats = int(np.ceil(horizon / max(len(tail), 1)))
        return np.tile(tail, repeats)[:horizon]

    def _holt_winters(self, values: np.ndarray, horizon: int, season: int) -> np.ndarray:
        alpha, beta, gamma = 0.32, 0.10, 0.22

        # مقداردهی اولیه فصلی با میانگین نسبت به میانگین کل
        initial_mean = float(np.mean(values[:season])) or 1.0
        seasonal = [float(values[i]) / initial_mean for i in range(season)]
        level = initial_mean
        trend = float((np.mean(values[season : 2 * season]) - initial_mean) / season)

        for index, observed in enumerate(values):
            season_value = seasonal[index % season] or 1.0
            previous_level = level
            level = alpha * (float(observed) / season_value) + (1 - alpha) * (level + trend)
            trend = beta * (level - previous_level) + (1 - beta) * trend
            seasonal[index % season] = gamma * (float(observed) / (level or 1.0)) + (1 - gamma) * season_value

        forecast = []
        for step in range(1, horizon + 1):
            season_value = seasonal[(len(values) + step - 1) % season] or 1.0
            forecast.append((level + step * trend) * season_value)
        return np.asarray(forecast, dtype=float)

    def _backtest(self, values: np.ndarray, method: str, season: int) -> dict[str, float]:
        if len(values) < 6:
            return {"mape": 0.0, "rmse": 0.0}

        split = len(values) - max(2, len(values) // 5)
        train, test = values[:split], values[split:]

        if method == "seasonal_naive":
            predicted = self._seasonal_naive(train, len(test), season)
        elif method == "holt_winters" and len(train) >= 2 * season > 1:
            predicted = self._holt_winters(train, len(test), season)
        else:
            predicted = self._exponential_smoothing(train, len(test))

        if HAS_SKLEARN and len(train) > 5:
            features = np.arange(len(train)).reshape(-1, 1)
            model = Ridge(alpha=1.0).fit(features, train)
            ridge = model.predict(np.arange(len(train), len(train) + len(test)).reshape(-1, 1))
            if float(np.mean(np.abs((ridge - test) / np.where(test == 0, 1, test)))) < float(
                np.mean(np.abs((predicted - test) / np.where(test == 0, 1, test)))
            ):
                predicted = ridge

        errors = predicted - test
        mape = float(np.mean(np.abs(errors / np.where(test == 0, 1, test))) * 100)
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        return {"mape": mape, "rmse": rmse}
'''

ENGINE_ANOMALY = r'''"""موتور تشخیص ناهنجاری — سنسور، کیفیت، مالی و رفتار کاربر.

الگوریتم‌ها: Z-score چندمتغیره، IQR، IsolationForest و مرز فاصله ماهالانوبیس.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine

try:  # pragma: no cover
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    HAS_SKLEARN = False


class AnomalyEngine(BaseEngine):
    name = "anomaly"
    name_fa = "تشخیص ناهنجاری"
    endpoint = "/ai/anomaly"
    algorithms = ["isolation_forest", "zscore", "iqr", "mahalanobis"]
    realtime = True

    def run(self, request: Any) -> dict[str, Any]:
        from ..config import settings

        rows: list[dict[str, Any]] = list(request.features or [])
        series = self.to_floats(request.series)

        if rows:
            return self._detect_tabular(request, rows, float(settings.anomaly_z_threshold))
        if len(series) >= 8:
            return self._detect_series(request, np.asarray(series, dtype=float), float(settings.anomaly_z_threshold))

        return self.fallback(
            request,
            "داده ورودی کافی برای تشخیص ناهنجاری نیست.",
            suggestion="حداقل ۸ نمونه یا یک دنباله عددی ارسال کنید.",
        )

    def _numeric_matrix(self, rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
        keys: list[str] = []
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (int, float)) and key not in keys:
                    keys.append(key)
        matrix = np.asarray(
            [[float(row.get(key, 0.0)) for key in keys] for row in rows], dtype=float
        )
        return matrix, keys

    def _detect_tabular(self, request: Any, rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
        matrix, keys = self._numeric_matrix(rows)
        if matrix.size == 0 or len(keys) == 0:
            return self.fallback(request, "ستون عددی در داده‌ها یافت نشد.")

        mean = matrix.mean(axis=0)
        std = np.where(matrix.std(axis=0) == 0, 1.0, matrix.std(axis=0))
        z = np.abs((matrix - mean) / std)
        z_scores = z.max(axis=1)

        anomalies: list[dict[str, Any]] = []
        iso_scores = None
        if HAS_SKLEARN and len(rows) >= 12:
            forest = IsolationForest(random_state=42, contamination="auto")
            labels = forest.fit_predict(matrix)
            iso_scores = -forest.score_samples(matrix)
            z_scores = np.maximum(z_scores * 0.6, (labels == -1) * threshold)

        for index, row in enumerate(rows):
            score = float(z_scores[index])
            is_anomaly = bool(score >= threshold or (iso_scores is not None and iso_scores[index] > 0.18))
            if is_anomaly:
                drivers = [
                    {
                        "feature": key,
                        "value": float(row.get(key, 0.0)),
                        "mean": round(float(mean[i]), 4),
                        "std": round(float(std[i]), 4),
                        "z": round(float(z[index][i]), 3),
                    }
                    for i, key in enumerate(keys)
                    if z[index][i] >= 2.0
                ]
                anomalies.append(
                    {
                        "index": index,
                        "row": {k: row[k] for k in list(row)[:8]},
                        "score": round(score, 4),
                        "severity": "بحرانی" if score >= threshold * 1.5 else "هشدار",
                        "drivers": sorted(drivers, key=lambda d: -d["z"])[:5],
                    }
                )

        ratio = len(anomalies) / max(len(rows), 1) * 100
        explanation = (
            f"از {len(rows)} رکورد، {len(anomalies)} مورد ({ratio:.1f}٪) ناهنجار تشخیص داده شد. "
            f"معیار: بیشینه Z-score با آستانه {threshold} "
            + ("و IsolationForest." if HAS_SKLEARN and len(rows) >= 12 else ".")
        )

        return self.success(
            request,
            {
                "total": len(rows),
                "anomaly_count": len(anomalies),
                "anomaly_ratio_percent": round(ratio, 2),
                "features": keys,
                "anomalies": anomalies[:100],
                "threshold": threshold,
                "method": "isolation_forest+zscore" if HAS_SKLEARN and len(rows) >= 12 else "zscore",
            },
            metrics={
                "samples": len(rows),
                "features": len(keys),
                "anomalies": len(anomalies),
                "max_z": round(float(z_scores.max()), 4) if len(z_scores) else 0.0,
                "sklearn": HAS_SKLEARN,
            },
            explanation=explanation,
            warnings=[] if ratio < 15 else [
                "نسبت ناهنجاری بالاست؛ ممکن است آستانه سخت‌گیرانه یا داده ورودی نادرست باشد."
            ],
        )

    def _detect_series(self, request: Any, values: np.ndarray, threshold: float) -> dict[str, Any]:
        mean, std = float(values.mean()), float(values.std() or 1.0)
        z = np.abs((values - mean) / std)

        q1, q3 = np.percentile(values, [25, 75])
        iqr = float(q3 - q1)
        iqr_flags = (values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)

        points = [
            {
                "index": int(i),
                "value": round(float(values[i]), 4),
                "z": round(float(z[i]), 3),
                "iqr_outlier": bool(iqr_flags[i]),
                "severity": "بحرانی" if z[i] >= threshold * 1.4 else "هشدار",
            }
            for i in range(len(values))
            if z[i] >= threshold or iqr_flags[i]
        ]

        explanation = (
            f"در دنباله‌ای به طول {len(values)}، {len(points)} نقطه ناهنجار یافت شد "
            f"(میانگین {mean:.2f}، انحراف معیار {std:.2f}، آستانه Z={threshold})."
        )

        return self.success(
            request,
            {
                "total": int(len(values)),
                "anomaly_count": len(points),
                "anomalies": points[:100],
                "statistics": {
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                    "q1": round(float(q1), 4),
                    "q3": round(float(q3), 4),
                    "iqr": round(iqr, 4),
                    "min": round(float(values.min()), 4),
                    "max": round(float(values.max()), 4),
                },
            },
            metrics={"samples": int(len(values)), "anomalies": len(points), "max_z": round(float(z.max()), 4)},
            explanation=explanation,
        )
'''

ENGINE_QUALITY_SPC = r'''"""موتور کنترل کیفیت آماری (SPC).

نمودارهای کنترلی X-bar/R، p و np به‌همراه قواعد غربال الکتریکی (Nelson).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine

# ضرایب استاندارد X-bar/R بر اساس اندازه زیرگروه
A2 = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
D3 = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
D4 = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}


class QualitySpcEngine(BaseEngine):
    name = "quality_spc"
    name_fa = "کنترل کیفیت آماری"
    endpoint = "/ai/spc"
    algorithms = ["xbar_r_chart", "p_chart", "np_chart", "nelson_rules", "cpk"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        options = request.options or {}
        chart = str(options.get("chart", "auto"))

        subgroups = self._extract_subgroups(request)
        if subgroups:
            return self._xbar_r(request, subgroups, options)

        counts = self._extract_defectives(request)
        if counts:
            if chart in ("auto", "p", "np"):
                return self._p_chart(request, counts, options)

        series = self.to_floats(request.series)
        if len(series) >= 5:
            return self._xbar_r(request, [[v] for v in series], options)

        return self.fallback(
            request,
            "داده کیفیت برای رسم نمودار کنترلی کافی نیست.",
            suggestion="زیرگروه‌های نمونه (values) یا تعداد معیوبی (defectives) را ارسال کنید.",
        )

    # --- استخراج داده ------------------------------------------------------ #
    def _extract_subgroups(self, request: Any) -> list[list[float]]:
        groups: list[list[float]] = []
        for row in request.features or []:
            if isinstance(row, dict):
                values = row.get("values") or row.get("samples")
                if isinstance(values, list):
                    numeric = [float(v) for v in values if isinstance(v, (int, float))]
                    if numeric:
                        groups.append(numeric)
                    continue
                numeric = [float(v) for v in row.values() if isinstance(v, (int, float))]
                if numeric:
                    groups.append(numeric)
        if not groups and request.series:
            season = int((request.options or {}).get("subgroup_size", 5))
            values = self.to_floats(request.series)
            groups = [values[i : i + season] for i in range(0, len(values), season) if len(values[i : i + season]) > 1]
        return groups

    def _extract_defectives(self, request: Any) -> list[dict[str, float]]:
        rows = []
        for row in request.features or []:
            if not isinstance(row, dict):
                continue
            sample_size = row.get("sample_size") or row.get("n")
            defectives = row.get("defectives") or row.get("defective_count")
            if sample_size and defectives is not None:
                rows.append({"n": float(sample_size), "d": float(defectives)})
        return rows

    # --- نمودارها ---------------------------------------------------------- #
    def _xbar_r(self, request: Any, subgroups: list[list[float]], options: dict[str, Any]) -> dict[str, Any]:
        size = int(np.median([len(g) for g in subgroups]))
        size_key = min(max(size, 2), 10)

        means = np.asarray([float(np.mean(g)) for g in subgroups])
        ranges = np.asarray([float(np.max(g) - np.min(g)) for g in subgroups])

        x_double_bar = float(means.mean())
        r_bar = float(ranges.mean())

        ucl_x = x_double_bar + A2[size_key] * r_bar
        lcl_x = x_double_bar - A2[size_key] * r_bar
        ucl_r = D4[size_key] * r_bar
        lcl_r = D3[size_key] * r_bar

        sigma_within = r_bar / D2[size_key] if D2[size_key] else 0.0

        violations = self._nelson_rules(means, x_double_bar, sigma_within or 1e-9)

        lsl = options.get("lsl")
        usl = options.get("usl")
        capability: dict[str, Any] = {}
        if lsl is not None and usl is not None and sigma_within > 0:
            cp = (float(usl) - float(lsl)) / (6 * sigma_within)
            cpu = (float(usl) - x_double_bar) / (3 * sigma_within)
            cpl = (x_double_bar - float(lsl)) / (3 * sigma_within)
            cpk = min(cpu, cpl)
            capability = {
                "cp": round(cp, 3),
                "cpk": round(cpk, 3),
                "cpu": round(cpu, 3),
                "cpl": round(cpl, 3),
                "sigma_within": round(sigma_within, 4),
                "ppm_estimate": round(self._ppm(cpk), 2),
                "verdict": self._capability_verdict(cpk),
            }

        out_of_control = [
            {"subgroup": int(i + 1), "mean": round(float(means[i]), 4), "range": round(float(ranges[i]), 4),
             "reason": "خارج از حد میانگین" if (means[i] > ucl_x or means[i] < lcl_x) else "خارج از حد دامنه"}
            for i in range(len(subgroups))
            if means[i] > ucl_x or means[i] < lcl_x or ranges[i] > ucl_r or ranges[i] < lcl_r
        ]

        explanation = (
            f"نمودار X-bar/R با {len(subgroups)} زیرگروه (اندازه {size}) رسم شد. "
            f"میانگین کل {x_double_bar:.3f} و حدود کنترلی [{lcl_x:.3f}, {ucl_x:.3f}] است. "
            + (f"{len(out_of_control)} زیرگروه خارج از کنترل و {len(violations)} نقض قاعده نلسون مشاهده شد. "
               if out_of_control or violations else "فرآیند در کنترل آماری است. ")
            + (f"شاخص قابلیت CpK برابر {capability['cpk']} ({capability['verdict']})." if capability else "")
        )

        return self.success(
            request,
            {
                "chart": "xbar_r",
                "subgroup_size": size,
                "center_line": round(x_double_bar, 4),
                "ucl": round(ucl_x, 4),
                "lcl": round(lcl_x, 4),
                "r_center": round(r_bar, 4),
                "r_ucl": round(ucl_r, 4),
                "r_lcl": round(lcl_r, 4),
                "means": [round(float(v), 4) for v in means],
                "ranges": [round(float(v), 4) for v in ranges],
                "out_of_control": out_of_control,
                "nelson_violations": violations,
                "capability": capability,
            },
            metrics={
                "subgroups": len(subgroups),
                "x_double_bar": round(x_double_bar, 4),
                "r_bar": round(r_bar, 4),
                "sigma_within": round(sigma_within, 4),
                "out_of_control": len(out_of_control),
                **({"cpk": capability["cpk"]} if capability else {}),
            },
            explanation=explanation,
            warnings=[v["rule"] for v in violations[:5]],
        )

    def _p_chart(self, request: Any, counts: list[dict[str, float]], options: dict[str, Any]) -> dict[str, Any]:
        n = np.asarray([row["n"] for row in counts])
        d = np.asarray([row["d"] for row in counts])
        p = d / np.where(n == 0, 1, n)
        p_bar = float(d.sum() / max(n.sum(), 1))

        sigma = np.sqrt(p_bar * (1 - p_bar) / np.where(n == 0, 1, n))
        ucl = np.minimum(p_bar + 3 * sigma, 1.0)
        lcl = np.maximum(p_bar - 3 * sigma, 0.0)

        out_of_control = [
            {"sample": int(i + 1), "p": round(float(p[i]), 4), "n": int(n[i]), "defectives": int(d[i])}
            for i in range(len(counts))
            if p[i] > ucl[i] or p[i] < lcl[i]
        ]

        explanation = (
            f"نمودار p با {len(counts)} نمونه رسم شد؛ نسبت معیوب میانگین {p_bar * 100:.2f}٪ "
            f"و {len(out_of_control)} نمونه خارج از کنترل است."
        )

        return self.success(
            request,
            {
                "chart": "p",
                "p_bar": round(p_bar, 5),
                "proportions": [round(float(v), 5) for v in p],
                "ucl": [round(float(v), 5) for v in ucl],
                "lcl": [round(float(v), 5) for v in lcl],
                "out_of_control": out_of_control,
            },
            metrics={"samples": len(counts), "p_bar": round(p_bar, 5), "out_of_control": len(out_of_control)},
            explanation=explanation,
        )

    # --- قواعد نلسون ------------------------------------------------------- #
    def _nelson_rules(self, means: np.ndarray, center: float, sigma: float) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []

        for i, value in enumerate(means):
            if abs(value - center) > 3 * sigma:
                violations.append({"rule": "قاعده ۱: نقطه خارج از ۳ سیگما", "subgroup": int(i + 1)})

        if len(means) >= 9:
            for start in range(len(means) - 8):
                window = means[start : start + 9]
                if np.all(window > center) or np.all(window < center):
                    violations.append({
                        "rule": "قاعده ۲: ۹ نقطه متوالی در یک سمت میانگین",
                        "subgroup": int(start + 9),
                    })
                    break

        if len(means) >= 6:
            for start in range(len(means) - 5):
                window = means[start : start + 6]
                diffs = np.diff(window)
                if np.all(diffs > 0) or np.all(diffs < 0):
                    violations.append({
                        "rule": "قاعده ۳: ۶ نقطه متوالی صعودی یا نزولی",
                        "subgroup": int(start + 6),
                    })
                    break

        if len(means) >= 14:
            for start in range(len(means) - 13):
                window = means[start : start + 14]
                diffs = np.diff(window)
                alternating = np.all(diffs[:-1] * diffs[1:] < 0)
                if alternating:
                    violations.append({
                        "rule": "قاعده ۴: ۱۴ نقطه متناوب (نوسان سیستماتیک)",
                        "subgroup": int(start + 14),
                    })
                    break

        if len(means) >= 5:
            for start in range(len(means) - 4):
                window = means[start : start + 5]
                beyond_2 = np.sum(np.abs(window - center) > 2 * sigma)
                if beyond_2 >= 4 and np.all((window - center) * np.sign(window[0] - center) > 0):
                    violations.append({
                        "rule": "قاعده ۵: ۴ نقطه از ۵ فراتر از ۲ سیگما در یک سمت",
                        "subgroup": int(start + 5),
                    })
                    break

        return violations[:10]

    @staticmethod
    def _ppm(cpk: float) -> float:
        """برآورد PPM معیوب بر اساس CpK (تقریب نرمال)."""
        if cpk <= 0:
            return 500_000.0
        z = 3 * cpk
        # تقریب دم نرمال
        ppm = 1_000_000 * np.exp(-0.5 * z * z) / (z * np.sqrt(2 * np.pi))
        return float(min(ppm, 1_000_000.0))

    @staticmethod
    def _capability_verdict(cpk: float) -> str:
        if cpk >= 1.67:
            return "عالی — فرآیند بسیار قادر"
        if cpk >= 1.33:
            return "قابل قبول — فرآیند قادر"
        if cpk >= 1.0:
            return "لب مرز — نیازمند پایش دقیق"
        if cpk >= 0.67:
            return "ضعیف — نیازمند بهبود"
        return "بحرانی — فرآیند قادر نیست"
'''

ENGINE_RELIABILITY = r'''"""موتور قابلیت اطمینان و نگهداری پیش‌بینانه (PdM).

برازش توزیع وایبول، محاسبه MTBF/MTTR، تخمین عمر باقی‌مانده (RUL)
و امتیازدهی ریسک خرابی تجهیزات.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .base import BaseEngine


class ReliabilityEngine(BaseEngine):
    name = "reliability"
    name_fa = "قابلیت اطمینان و PdM"
    endpoint = "/ai/reliability"
    algorithms = ["weibull_mle", "mtbf", "rul_regression", "risk_scoring"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        times = self.to_floats(request.series)
        if not times:
            times = [
                float(row.get("time_to_failure") or row.get("ttf") or 0.0)
                for row in (request.features or [])
                if isinstance(row, dict)
            ]
            times = [t for t in times if t > 0]

        if len(times) < 3:
            return self.fallback(
                request,
                "برای تحلیل قابلیت اطمینان حداقل ۳ زمان تا خرابی لازم است.",
                suggestion="سابقه خرابی‌ها را از ماژول نت دریافت کنید.",
            )

        values = np.asarray([t for t in times if t > 0], dtype=float)
        shape, scale = self._weibull_mle(values)

        mtbf = float(scale * math.gamma(1 + 1 / shape)) if shape > 0 else float(values.mean())
        repair_times = [
            float(row.get("repair_time") or row.get("mttr") or 0.0)
            for row in (request.features or [])
            if isinstance(row, dict) and (row.get("repair_time") or row.get("mttr"))
        ]
        repair_times = [t for t in repair_times if t > 0]
        if repair_times:
            mttr = float(np.mean(repair_times))
        else:
            mttr = float(request.options.get("mttr", 4.0) or 4.0)
        if not mttr > 0:
            mttr = 4.0

        availability = mtbf / (mtbf + mttr) if (mtbf + mttr) > 0 else 0.0
        b10 = scale * (-math.log(0.90)) ** (1 / shape) if shape > 0 else float(np.percentile(values, 10))
        b50 = scale * (-math.log(0.50)) ** (1 / shape) if shape > 0 else float(np.percentile(values, 50))

        current_age = float(request.options.get("current_age", values.mean() * 0.6))
        rul = self._remaining_useful_life(shape, scale, current_age)
        hazard_now = self._hazard(shape, scale, current_age)

        risk_score = min(100.0, (hazard_now * mtbf * 100) if mtbf else 0.0)
        risk_level = (
            "بحرانی" if risk_score >= 70 else "بالا" if risk_score >= 45 else "متوسط" if risk_score >= 20 else "پایین"
        )

        curve = [
            {
                "time": round(float(t), 2),
                "reliability": round(self._reliability(shape, scale, float(t)), 4),
                "hazard": round(self._hazard(shape, scale, float(t)), 6),
            }
            for t in np.linspace(float(values.min()) * 0.5, float(values.max()) * 1.5, 24)
        ]

        explanation = (
            f"برازش وایبول: شکل β={shape:.2f} و مقیاس η={scale:.1f}. "
            + ("خرابی از نوع فرسودگی است (β>۱) و با افزایش سن، نرخ خرابی بالا می‌رود. "
               if shape > 1.2 else
               "خرابی تصادفی است (β≈۱) و نرخ خرابی تقریباً ثابت است. "
               if 0.8 <= shape <= 1.2 else
               "خرابی از نوع زودهنگام/مرگ نوزادی است (β<۱). ")
            + f"MTBF برآوردی {mtbf:,.0f} و دسترس‌پذیری {availability * 100:.2f}٪ است. "
            f"عمر باقی‌مانده در سن فعلی {rul:,.0f} واحد و سطح ریسک «{risk_level}» ارزیابی شد."
        )

        recommendations = self._recommendations(shape, availability, risk_score, mttr, mtbf)

        return self.success(
            request,
            {
                "weibull": {"shape_beta": round(shape, 4), "scale_eta": round(scale, 3)},
                "failure_mode": "فرسودگی" if shape > 1.2 else "تصادفی" if shape >= 0.8 else "زودهنگام",
                "mtbf": round(mtbf, 3),
                "mttr": round(mttr, 3),
                "availability": round(availability, 5),
                "availability_percent": round(availability * 100, 2),
                "b10_life": round(float(b10), 2),
                "b50_life": round(float(b50), 2),
                "current_age": round(current_age, 2),
                "remaining_useful_life": round(rul, 2),
                "hazard_now": round(hazard_now, 6),
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "reliability_curve": curve,
                "samples": int(len(values)),
                "recommendations": recommendations,
            },
            metrics={
                "samples": int(len(values)),
                "shape": round(shape, 4),
                "scale": round(scale, 3),
                "mtbf": round(mtbf, 2),
                "availability": round(availability, 4),
                "log_likelihood": round(self._log_likelihood(values, shape, scale), 3),
            },
            explanation=explanation,
            warnings=[] if availability > 0.9 else [
                "دسترس‌پذیری کمتر از ۹۰٪ است؛ برنامه نت پیشگیرانه باید بازنگری شود."
            ],
        )

    # --- محاسبات وایبول ---------------------------------------------------- #
    def _weibull_mle(self, values: np.ndarray) -> tuple[float, float]:
        """برازش وایبول دوپارامتری با روش بیشینه درستنمایی (Newton-Raphson)."""
        logs = np.log(values)
        shape = 1.2
        for _ in range(80):
            powered = values ** shape
            numerator = np.sum(powered * logs) / np.sum(powered) - 1.0 / shape - float(logs.mean())
            denominator = (
                np.sum(powered * logs * logs) / np.sum(powered)
                - (np.sum(powered * logs) / np.sum(powered)) ** 2
                + 1.0 / (shape ** 2)
            )
            if abs(denominator) < 1e-12:
                break
            step = numerator / denominator
            new_shape = shape - step
            if new_shape <= 0.01:
                new_shape = shape / 2
            if abs(new_shape - shape) < 1e-7:
                shape = new_shape
                break
            shape = new_shape
        scale = float((np.sum(values ** shape) / len(values)) ** (1.0 / shape))
        return float(max(shape, 0.05)), float(max(scale, 1e-6))

    @staticmethod
    def _reliability(shape: float, scale: float, t: float) -> float:
        if t <= 0:
            return 1.0
        return float(math.exp(-((t / scale) ** shape)))

    @staticmethod
    def _hazard(shape: float, scale: float, t: float) -> float:
        if t <= 0:
            return 0.0
        return float((shape / scale) * ((t / scale) ** (shape - 1)))

    def _remaining_useful_life(self, shape: float, scale: float, age: float, threshold: float = 0.5) -> float:
        """عمر باقی‌مانده تا رسیدن قابلیت اطمینان به آستانه."""
        target = scale * (-math.log(threshold)) ** (1 / shape) if shape > 0 else scale
        return float(max(target - age, 0.0))

    @staticmethod
    def _log_likelihood(values: np.ndarray, shape: float, scale: float) -> float:
        n = len(values)
        return float(
            n * math.log(shape / scale)
            + (shape - 1) * float(np.sum(np.log(values)))
            - float(np.sum((values / scale) ** shape))
        )

    @staticmethod
    def _recommendations(shape: float, availability: float, risk: float, mttr: float, mtbf: float) -> list[str]:
        items: list[str] = []
        if shape > 1.5:
            items.append("الگوی فرسودگی غالب است: جایگزینی دوره‌ای قطعات بر اساس B10 زندگی توصیه می‌شود.")
        elif shape < 0.9:
            items.append("خرابی‌های زودهنگام غالب است: کیفیت نصب، راه‌اندازی و دریافت کالا بررسی شود.")
        if availability < 0.9:
            items.append("دسترس‌پذیری پایین است؛ تمرکز بر کاهش MTTR (آمادگی قطعات یدکی و تیم شیفت).")
        if mttr > 6:
            items.append("MTTR بیش از ۶ ساعت است: استانداردسازی عیب‌یابی و کیت ابزار فوری پیشنهاد می‌شود.")
        if risk >= 70:
            items.append("ریسک بحرانی: پایش وضعیت (ارتعاش/دما) به‌صورت برخط فعال و بازدید فوری انجام شود.")
        if not items:
            items.append("وضعیت پایدار است؛ برنامه نت پیشگیرانه فعلی ادامه یابد و شاخص‌ها پایش شود.")
        return items
'''

ENGINE_OPTIMIZATION = r'''"""موتور بهینه‌سازی — زمان‌بندی تولید، نقطه سفارش، سبد و تخصیص.

الگوریتم‌ها: EOQ/نقطه سفارش، زمان‌بندی با قواعد اولویت‌دهی + جست‌وجوی محلی،
و تخصیص منابع با روش حریصانه بهینه‌شده.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .base import BaseEngine


class OptimizationEngine(BaseEngine):
    name = "optimization"
    name_fa = "بهینه‌سازی و تجویز"
    endpoint = "/ai/optimize"
    algorithms = ["eoq_reorder_point", "priority_scheduling", "local_search", "greedy_allocation"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        problem = str((request.options or {}).get("problem", "auto"))
        items = [row for row in (request.features or []) if isinstance(row, dict)]

        if problem in ("auto", "inventory") and items and any("daily_demand" in row for row in items):
            return self._inventory(request, items)
        if problem in ("auto", "scheduling") and items and any("processing_time" in row for row in items):
            return self._scheduling(request, items)
        if problem == "allocation" and items:
            return self._allocation(request, items)

        if request.series:
            return self._inventory_from_series(request)

        return self.fallback(
            request,
            "نوع مسئله بهینه‌سازی از ورودی قابل تشخیص نیست.",
            suggestion="فیلدهای daily_demand/lead_time_days (موجودی) یا processing_time/due_date (زمان‌بندی) را ارسال کنید.",
        )

    # --- بهینه‌سازی موجودی ------------------------------------------------- #
    def _inventory(self, request: Any, items: list[dict[str, Any]]) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        total_saving = 0.0

        for row in items:
            demand = float(row.get("daily_demand") or 0.0)
            std = float(row.get("demand_std") or demand * 0.2)
            lead_time = float(row.get("lead_time_days") or 7.0)
            unit_cost = float(row.get("unit_cost") or 0.0)
            holding_rate = float(row.get("holding_rate") or 0.25)
            order_cost = float(row.get("order_cost") or 1_000_000.0)
            service_level = float(row.get("service_level") or 0.95)

            if demand <= 0:
                continue

            annual_demand = demand * 365
            holding_cost = max(unit_cost * holding_rate, 1.0)
            eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost)
            z = self._service_z(service_level)
            safety_stock = z * std * math.sqrt(lead_time)
            reorder_point = demand * lead_time + safety_stock

            cycles = annual_demand / eoq if eoq else 0
            annual_cost = (cycles * order_cost) + ((eoq / 2 + safety_stock) * holding_cost)

            # مقایسه با سیاست فعلی (در صورت ارائه)
            current_stock = float(row.get("current_stock") or 0.0)
            current_policy_cost = float(row.get("current_annual_cost") or annual_cost * 1.12)
            saving = max(current_policy_cost - annual_cost, 0.0)
            total_saving += saving

            results.append(
                {
                    "id": row.get("id") or row.get("code") or row.get("item_id"),
                    "eoq": round(eoq, 2),
                    "safety_stock": round(safety_stock, 2),
                    "reorder_point": round(reorder_point, 2),
                    "max_stock": round(eoq + safety_stock, 2),
                    "order_cycles_per_year": round(cycles, 2),
                    "annual_cost": round(annual_cost, 2),
                    "estimated_saving": round(saving, 2),
                    "service_level": service_level,
                    "z_factor": round(z, 3),
                    "current_stock": current_stock,
                    "action": self._action(current_stock, reorder_point, eoq),
                }
            )

        if not results:
            return self.fallback(request, "هیچ کالایی با داده کافی برای محاسبه نقطه سفارش یافت نشد.")

        results.sort(key=lambda r: -r["annual_cost"])
        urgent = [r for r in results if r["action"] == "سفارش فوری"]

        explanation = (
            f"برای {len(results)} کالا EOQ، ذخیره اطمینان و نقطه سفارش محاسبه شد. "
            f"{len(urgent)} کالا نیاز به سفارش فوری دارد و برآورد صرفه‌جویی سالانه "
            f"{total_saving:,.0f} است."
        )

        return self.success(
            request,
            {
                "problem": "inventory_policy",
                "items": results[:200],
                "urgent": urgent[:50],
                "total_annual_cost": round(sum(r["annual_cost"] for r in results), 2),
                "total_saving": round(total_saving, 2),
                "service_levels": sorted({r["service_level"] for r in results}),
            },
            metrics={
                "items": len(results),
                "urgent": len(urgent),
                "total_saving": round(total_saving, 2),
            },
            explanation=explanation,
        )

    def _inventory_from_series(self, request: Any) -> dict[str, Any]:
        values = np.asarray(self.to_floats(request.series), dtype=float)
        if len(values) < 3:
            return self.fallback(request, "دنباله مصرف برای محاسبه نقطه سفارش کوتاه است.")

        mean, std = float(values.mean()), float(values.std(ddof=1))
        lead_time = float((request.options or {}).get("lead_time_days", 7.0))
        service_level = float((request.options or {}).get("service_level", 0.95))
        z = self._service_z(service_level)

        safety_stock = z * std * math.sqrt(lead_time)
        reorder_point = mean * lead_time + safety_stock

        return self.success(
            request,
            {
                "problem": "inventory_policy_from_series",
                "daily_demand_mean": round(mean, 3),
                "daily_demand_std": round(std, 3),
                "lead_time_days": lead_time,
                "service_level": service_level,
                "safety_stock": round(safety_stock, 2),
                "reorder_point": round(reorder_point, 2),
            },
            metrics={"samples": int(len(values)), "cv": round(std / mean if mean else 0, 4)},
            explanation=(
                f"میانگین مصرف روزانه {mean:.2f} و انحراف معیار {std:.2f} است؛ "
                f"با سطح خدمت {service_level * 100:.0f}٪، نقطه سفارش {reorder_point:.0f} محاسبه شد."
            ),
        )

    # --- زمان‌بندی تولید --------------------------------------------------- #
    def _scheduling(self, request: Any, items: list[dict[str, Any]]) -> dict[str, Any]:
        rules = {
            "spt": lambda job: job["processing_time"],
            "lpt": lambda job: -job["processing_time"],
            "edd": lambda job: job["due_date"],
            "cr": lambda job: max(job["due_date"] - job["elapsed"], 0.001) / max(job["processing_time"], 0.001),
            "priority": lambda job: (-job["priority"], job["due_date"]),
        }

        jobs: list[dict[str, Any]] = []
        for index, row in enumerate(items):
            jobs.append(
                {
                    "id": row.get("id") or f"JOB-{index + 1}",
                    "processing_time": float(row.get("processing_time") or 1.0),
                    "due_date": float(row.get("due_date") or (index + 1) * 2),
                    "priority": int(row.get("priority") or 3),
                    "profit": float(row.get("profit") or 0.0),
                    "setup_time": float(row.get("setup_time") or 0.0),
                    "line": row.get("line") or "LINE-1",
                    "elapsed": float(row.get("elapsed") or 0.0),
                }
            )

        evaluations: dict[str, dict[str, Any]] = {}
        for rule_name, key_fn in rules.items():
            schedule = self._simulate(sorted(jobs, key=key_fn))
            evaluations[rule_name] = schedule

        # جست‌وجوی محلی: جابه‌جایی جفتی روی بهترین قاعده
        best_rule = min(evaluations, key=lambda name: evaluations[name]["objective"])
        improved = self._local_search(jobs, evaluations[best_rule]["sequence"])

        evaluations["local_search"] = improved
        best = min(evaluations.items(), key=lambda kv: kv[1]["objective"])

        explanation = (
            f"{len(rules)} قاعده اولویت‌دهی ارزیابی شد و جست‌وجوی محلی نیز انجام گرفت. "
            f"بهترین برنامه با روش «{best[0]}» به دست آمد: میانگین تأخیر "
            f"{best[1]['average_tardiness']:.2f}، بیشینه تأخیر {best[1]['max_tardiness']:.2f} و "
            f"میانگین زمان جریان {best[1]['average_flow_time']:.2f}."
        )

        return self.success(
            request,
            {
                "problem": "single_machine_scheduling",
                "best_method": best[0],
                "best_schedule": best[1],
                "comparison": {
                    name: {
                        "objective": round(data["objective"], 3),
                        "average_tardiness": round(data["average_tardiness"], 3),
                        "max_tardiness": round(data["max_tardiness"], 3),
                        "average_flow_time": round(data["average_flow_time"], 3),
                        "on_time_percent": round(data["on_time_percent"], 2),
                        "sequence": data["sequence"][:40],
                    }
                    for name, data in evaluations.items()
                },
                "jobs_count": len(jobs),
            },
            metrics={
                "jobs": len(jobs),
                "best_objective": round(best[1]["objective"], 3),
                "methods_evaluated": len(evaluations),
                "improvement_percent": round(
                    (evaluations[best_rule]["objective"] - best[1]["objective"])
                    / evaluations[best_rule]["objective"] * 100
                    if evaluations[best_rule]["objective"]
                    else 0.0,
                    2,
                ),
            },
            explanation=explanation,
        )

    def _simulate(self, jobs: list[dict[str, Any]]) -> dict[str, Any]:
        clock = 0.0
        flow_times: list[float] = []
        tardiness: list[float] = []
        sequence: list[str] = []

        for job in jobs:
            start = clock + job["setup_time"]
            clock = start + job["processing_time"]
            flow_times.append(clock)
            tardiness.append(max(clock - job["due_date"], 0.0))
            sequence.append(job["id"])

        on_time = sum(1 for t in tardiness if t <= 0) / max(len(jobs), 1) * 100
        avg_tard = float(np.mean(tardiness)) if tardiness else 0.0
        objective = avg_tard + 0.35 * float(np.mean(flow_times) if flow_times else 0.0)

        return {
            "sequence": sequence,
            "makespan": round(clock, 3),
            "average_flow_time": float(np.mean(flow_times)) if flow_times else 0.0,
            "average_tardiness": avg_tard,
            "max_tardiness": float(np.max(tardiness)) if tardiness else 0.0,
            "tardy_jobs": sum(1 for t in tardiness if t > 0),
            "on_time_percent": on_time,
            "objective": objective,
            "start_times": [],
        }

    def _local_search(self, jobs: list[dict[str, Any]], sequence: list[str], iterations: int = 120) -> dict[str, Any]:
        by_id = {job["id"]: job for job in jobs}
        best_sequence = list(sequence)
        best = self._simulate([by_id[job_id] for job_id in best_sequence if job_id in by_id])

        rng = np.random.default_rng(42)
        for _ in range(iterations):
            if len(best_sequence) < 2:
                break
            i, j = sorted(rng.choice(len(best_sequence), size=2, replace=False).tolist())
            candidate = list(best_sequence)
            candidate[i], candidate[j] = candidate[j], candidate[i]
            result = self._simulate([by_id[job_id] for job_id in candidate if job_id in by_id])
            if result["objective"] < best["objective"]:
                best_sequence, best = candidate, result

        best["sequence"] = best_sequence
        return best

    # --- تخصیص منابع ------------------------------------------------------- #
    def _allocation(self, request: Any, items: list[dict[str, Any]]) -> dict[str, Any]:
        capacity = float((request.options or {}).get("capacity", 100.0))
        weight_key = str((request.options or {}).get("weight", "profit"))
        cost_key = str((request.options or {}).get("cost", "processing_time"))

        scored = []
        for row in items:
            weight = float(row.get(weight_key) or 0.0)
            cost = float(row.get(cost_key) or 1.0)
            scored.append((weight / cost if cost else 0.0, row))

        scored.sort(key=lambda pair: -pair[0])

        chosen: list[dict[str, Any]] = []
        used = 0.0
        total_weight = 0.0
        for ratio, row in scored:
            cost = float(row.get(cost_key) or 1.0)
            if used + cost <= capacity:
                used += cost
                total_weight += float(row.get(weight_key) or 0.0)
                chosen.append({"id": row.get("id"), "cost": cost, "weight": float(row.get(weight_key) or 0.0),
                               "ratio": round(ratio, 4)})

        return self.success(
            request,
            {
                "problem": "resource_allocation",
                "capacity": capacity,
                "used": round(used, 3),
                "utilization_percent": round(used / capacity * 100 if capacity else 0, 2),
                "selected": chosen,
                "total_value": round(total_weight, 3),
                "rejected": [row.get("id") for _, row in scored if row.get("id") not in {c["id"] for c in chosen}],
            },
            metrics={"selected": len(chosen), "utilization": round(used / capacity if capacity else 0, 4)},
            explanation=(
                f"از {len(items)} گزینه، {len(chosen)} مورد با روش حریصانه نسبت ارزش/هزینه انتخاب شد؛ "
                f"مصرف ظرفیت {used / capacity * 100 if capacity else 0:.1f}٪ و ارزش کل {total_weight:,.2f}."
            ),
        )

    @staticmethod
    def _service_z(service_level: float) -> float:
        """تقریب معکوس نرمال برای سطح خدمت."""
        table = {
            0.80: 0.842, 0.85: 1.036, 0.90: 1.282, 0.92: 1.405, 0.95: 1.645,
            0.96: 1.751, 0.97: 1.881, 0.98: 2.054, 0.99: 2.326, 0.995: 2.576, 0.999: 3.090,
        }
        closest = min(table, key=lambda level: abs(level - service_level))
        return table[closest]

    @staticmethod
    def _action(current_stock: float, reorder_point: float, eoq: float) -> str:
        if current_stock <= 0:
            return "سفارش فوری"
        if current_stock <= reorder_point:
            return "سفارش فوری"
        if current_stock <= reorder_point * 1.25:
            return "آماده‌سازی سفارش"
        if current_stock > reorder_point + eoq * 1.5:
            return "کاهش موجودی (اضافه‌موجودی)"
        return "وضعیت مناسب"
'''

ENGINE_CLASSIFICATION = r'''"""موتور طبقه‌بندی — عمومی، متنی و عددی.

خط لوله: پیش‌پردازش -> TF-IDF یا نرمال‌سازی عددی -> LogisticRegression/RandomForest
با گزارش دقت، F1، ماتریس درهم‌آمیگی و اهمیت ویژگی‌ها.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine

try:  # pragma: no cover
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    HAS_SKLEARN = False


class ClassificationEngine(BaseEngine):
    name = "classification"
    name_fa = "طبقه‌بندی"
    endpoint = "/ai/classify"
    algorithms = ["tfidf_logistic", "random_forest", "naive_frequency", "knn_numeric"]
    realtime = True

    def run(self, request: Any) -> dict[str, Any]:
        rows = [row for row in (request.features or []) if isinstance(row, dict)]
        target = request.target

        if rows and target and any(target in row for row in rows):
            return self._train_tabular(request, rows, target)

        if request.texts and request.labels and len(request.texts) == len(request.labels):
            return self._train_text(request, request.texts, request.labels)

        if rows and any("label" in row or "class" in row for row in rows):
            label_key = "label" if "label" in rows[0] else "class"
            return self._train_tabular(request, rows, label_key)

        return self.fallback(
            request,
            "داده برچسب‌دار برای طبقه‌بندی یافت نشد.",
            suggestion="فیلدهای features به‌همراه target (نام ستون برچسب) را ارسال کنید.",
        )

    # --- داده جدولی -------------------------------------------------------- #
    def _train_tabular(self, request: Any, rows: list[dict[str, Any]], target: str) -> dict[str, Any]:
        feature_keys: list[str] = []
        for row in rows:
            for key, value in row.items():
                if key != target and isinstance(value, (int, float)) and key not in feature_keys:
                    feature_keys.append(key)

        if not feature_keys:
            return self.fallback(request, "ویژگی عددی در داده‌ها یافت نشد.")

        X = np.asarray([[float(row.get(key, 0.0)) for key in feature_keys] for row in rows], dtype=float)
        y = np.asarray([str(row.get(target, "")) for row in rows])
        classes = sorted(set(y.tolist()))

        if len(classes) < 2:
            return self.fallback(request, "فقط یک کلاس در داده‌ها وجود دارد؛ طبقه‌بندی ممکن نیست.")

        if not HAS_SKLEARN:
            return self._frequency_fallback(request, rows, target, classes)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y if min(np.bincount(
                np.unique(y, return_inverse=True)[1])) >= 2 else None
        )

        scaler = StandardScaler()
        model = RandomForestClassifier(n_estimators=160, max_depth=12, random_state=42, n_jobs=-1)
        model.fit(scaler.fit_transform(X_train), y_train)

        predicted = model.predict(scaler.transform(X_test))
        accuracy = float(accuracy_score(y_test, predicted))
        macro_f1 = float(f1_score(y_test, predicted, average="macro", zero_division=0))
        report = classification_report(y_test, predicted, output_dict=True, zero_division=0)
        matrix = confusion_matrix(y_test, predicted, labels=classes).tolist()

        importances = sorted(
            ({"feature": key, "importance": round(float(value), 4)}
             for key, value in zip(feature_keys, model.feature_importances_)),
            key=lambda item: -item["importance"],
        )

        cv_scores = []
        if len(rows) >= 20:
            try:
                cv_scores = cross_val_score(model, scaler.transform(X), y, cv=min(5, len(classes) * 3), scoring="accuracy").tolist()
            except ValueError:
                cv_scores = []

        explanation = (
            f"مدل جنگل تصادفی روی {len(rows)} نمونه و {len(feature_keys)} ویژگی آموزش دید. "
            f"دقت {accuracy * 100:.1f}٪ و F1 ماکرو {macro_f1:.3f} است. "
            f"مهم‌ترین ویژگی‌ها: {', '.join(item['feature'] for item in importances[:3])}."
        )

        return self.success(
            request,
            {
                "model": "random_forest",
                "classes": classes,
                "features": feature_keys,
                "feature_importance": importances[:20],
                "confusion_matrix": matrix,
                "report": {name: {k: round(float(v), 4) for k, v in metrics.items() if isinstance(v, (int, float))}
                           for name, metrics in report.items() if isinstance(metrics, dict)},
                "cv_accuracy_mean": round(float(np.mean(cv_scores)), 4) if cv_scores else None,
                "sample_size": len(rows),
            },
            metrics={"accuracy": round(accuracy, 4), "f1_macro": round(macro_f1, 4), "samples": len(rows)},
            explanation=explanation,
            warnings=[] if accuracy >= 0.75 else [
                "دقت مدل پایین است؛ ویژگی‌های بیشتر یا داده تمیزتر لازم است."
            ],
        )

    # --- داده متنی --------------------------------------------------------- #
    def _train_text(self, request: Any, texts: list[str], labels: list[str]) -> dict[str, Any]:
        classes = sorted(set(labels))
        if len(classes) < 2:
            return self.fallback(request, "متن‌ها فقط یک برچسب دارند.")

        if not HAS_SKLEARN:
            counts: dict[str, int] = {}
            for label in labels:
                counts[label] = counts.get(label, 0) + 1
            return self.success(
                request,
                {"model": "frequency", "distribution": counts, "dominant": max(counts, key=counts.get)},
                metrics={"samples": len(labels)},
                explanation="scikit-learn در دسترس نیست؛ توزیع فراوانی برچسب‌ها برگردانده شد.",
                warnings=["مدل واقعی آموزش داده نشد."],
            )

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.25, random_state=42,
            stratify=labels if min(np.bincount(np.unique(labels, return_inverse=True)[1])) >= 2 else None,
        )

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)),
        ])
        pipeline.fit(X_train, y_train)

        predicted = pipeline.predict(X_test)
        accuracy = float(accuracy_score(y_test, predicted))
        macro_f1 = float(f1_score(y_test, predicted, average="macro", zero_division=0))

        explanation = (
            f"طبقه‌بند متن با TF-IDF و رگرسیون لجستیک روی {len(texts)} نمونه آموزش دید؛ "
            f"دقت {accuracy * 100:.1f}٪ و F1 ماکرو {macro_f1:.3f} برای {len(classes)} کلاس."
        )

        return self.success(
            request,
            {
                "model": "tfidf_logistic",
                "classes": classes,
                "distribution": {label: labels.count(label) for label in classes},
                "sample_size": len(texts),
                "report": classification_report(y_test, predicted, output_dict=True, zero_division=0),
            },
            metrics={"accuracy": round(accuracy, 4), "f1_macro": round(macro_f1, 4), "samples": len(texts)},
            explanation=explanation,
        )

    def _frequency_fallback(self, request: Any, rows: list[dict[str, Any]], target: str, classes: list[str]) -> dict[str, Any]:
        counts = {label: sum(1 for row in rows if str(row.get(target, "")) == label) for label in classes}
        dominant = max(counts, key=lambda key: counts[key])
        accuracy = counts[dominant] / max(len(rows), 1)

        return self.success(
            request,
            {"model": "frequency_baseline", "classes": classes, "distribution": counts, "dominant": dominant},
            metrics={"accuracy": round(accuracy, 4), "samples": len(rows), "sklearn": False},
            explanation=f"خط پایه فراوانی: کلاس غالب «{dominant}» با سهم {accuracy * 100:.1f}٪.",
            warnings=["scikit-learn نصب نیست؛ فقط خط پایه محاسبه شد."],
        )
'''

ENGINE_NLP = r'''"""موتور پردازش زبان طبیعی فارسی.

لایه اول: پیش‌پردازش بومی (نرمال‌سازی ارقام/حروف، حذف توقف‌واژه‌ها، ریشه‌یابی ساده)
و TF-IDF داخلی. لایه دوم (اختیاری): AvalAI برای خلاصه‌سازی، استخراج و چت.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from .base import BaseEngine

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

STOPWORDS = {
    "و", "در", "به", "از", "که", "این", "آن", "یک", "را", "با", "برای", "تا", "بر",
    "هم", "نیز", "شد", "شده", "است", "بود", "های", "ها", "کرد", "کردند", "دارد",
    "دارند", "ما", "شما", "او", "آنها", "من", "خود", "بین", "پس", "قبل", "بعد",
    "مورد", "صورت", "طریق", "روی", "زیر", "بالا", "هر", "چه", "کدام", "اگر",
    "اما", "یا", "بلکه", "ضمن", "هنگام", "مدت", "روز", "ساعت", "بسیار", "کم",
}

SUFFIXES = ("ها", "های", "تر", "ترین", "ای", "یی", "شان", "مان", "تان")


class NlpEngine(BaseEngine):
    name = "nlp"
    name_fa = "پردازش زبان طبیعی"
    endpoint = "/ai/nlp"
    algorithms = ["tfidf", "keyword_extraction", "text_similarity", "sentiment_lexicon", "avalai_llm"]
    uses_llm = True
    realtime = True

    def run(self, request: Any) -> dict[str, Any]:
        task = str((request.options or {}).get("task", "auto"))
        texts = [text for text in (request.texts or []) if isinstance(text, str) and text.strip()]

        if request.text and not texts:
            texts = [request.text]

        if not texts:
            return self.fallback(request, "متنی برای پردازش ارسال نشد.")

        if task == "auto":
            task = "keywords" if len(texts) == 1 else "similarity"

        if task == "keywords":
            return self._keywords(request, texts)
        if task == "similarity":
            return self._similarity(request, texts)
        if task == "sentiment":
            return self._sentiment(request, texts)
        if task == "summary":
            return fallback_summary(self, request, texts)

        return self.fallback(request, f"وظیفه «{task}» پشتیبانی نمی‌شود.",
                             suggestion="وظایف موجود: keywords، similarity، sentiment، summary.")

    # --- ابزارهای زبانی ---------------------------------------------------- #
    @staticmethod
    def normalize(text: str) -> str:
        text = text.translate(PERSIAN_DIGITS)
        text = text.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه")
        text = re.sub(r"\u200c", " ", text)
        text = re.sub(r"[^\w\s.%/-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def tokenize(self, text: str) -> list[str]:
        tokens = [word for word in self.normalize(text).split() if len(word) > 1]
        cleaned: list[str] = []
        for token in tokens:
            if token in STOPWORDS or token.isdigit():
                continue
            stem = token
            for suffix in SUFFIXES:
                if stem.endswith(suffix) and len(stem) - len(suffix) > 2:
                    stem = stem[: -len(suffix)]
                    break
            cleaned.append(stem)
        return cleaned

    def tfidf_vectors(self, documents: list[str]) -> tuple[list[dict[str, float]], list[str]]:
        tokenized = [self.tokenize(document) for document in documents]
        vocab = sorted({token for tokens in tokenized for token in tokens})
        document_frequency = Counter()
        for tokens in tokenized:
            document_frequency.update(set(tokens))

        total = max(len(tokenized), 1)
        idf = {
            term: math.log((1 + total) / (1 + count)) + 1.0
            for term, count in document_frequency.items()
        }

        vectors: list[dict[str, float]] = []
        for tokens in tokenized:
            counts = Counter(tokens)
            length = max(len(tokens), 1)
            vector = {term: (count / length) * idf.get(term, 1.0) for term, count in counts.items()}
            norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
            vectors.append({term: value / norm for term, value in vector.items()})

        return vectors, vocab

    # --- وظایف ------------------------------------------------------------- #
    def _keywords(self, request: Any, texts: list[str]) -> dict[str, Any]:
        top_n = int((request.options or {}).get("top_n", 12))
        vectors, vocab = self.tfidf_vectors(texts + [" ".join(texts)])
        main_vector = vectors[-1]

        keywords = sorted(main_vector.items(), key=lambda item: -item[1])[:top_n]
        sentences = [s.strip() for s in re.split(r"[.!؟?\n]+", texts[0]) if len(s.strip()) > 20][:8]

        scored_sentences = []
        for sentence in sentences:
            tokens = set(self.tokenize(sentence))
            score = sum(main_vector.get(token, 0.0) for token in tokens) / max(len(tokens), 1)
            scored_sentences.append({"text": sentence, "score": round(score, 5)})

        # تلاش برای استفاده از AvalAI در خلاصه‌سازی
        llm_summary = None
        try:
            from .. import avalai_client

            if avalai_client.is_enabled() and len(texts[0]) > 400:
                llm_summary = avalai_client.summarize(texts[0], 350)
        except Exception:  # pragma: no cover - وابسته به شبکه
            llm_summary = None

        explanation = (
            f"{len(keywords)} کلیدواژه از متن استخراج شد (واژگان: {len(vocab)}). "
            + (f"خلاصه با AvalAI تولید شد." if llm_summary else "خلاصه با روش استخراجی (TF-IDF) ساخته شد.")
        )

        return self.success(
            request,
            {
                "task": "keywords",
                "keywords": [{"term": term, "score": round(score, 5)} for term, score in keywords],
                "vocabulary_size": len(vocab),
                "char_count": len(texts[0]),
                "word_count": len(self.tokenize(texts[0])),
                "key_sentences": sorted(scored_sentences, key=lambda s: -s["score"])[:3],
                "summary": llm_summary or " ".join(
                    s["text"] for s in sorted(scored_sentences, key=lambda s: -s["score"])[:2]
                ),
                "llm_used": bool(llm_summary),
            },
            metrics={"keywords": len(keywords), "vocabulary": len(vocab), "llm": bool(llm_summary)},
            explanation=explanation,
        )

    def _similarity(self, request: Any, texts: list[str]) -> dict[str, Any]:
        vectors, vocab = self.tfidf_vectors(texts)
        pairs: list[dict[str, Any]] = []

        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                common = set(vectors[i]) & set(vectors[j])
                score = sum(vectors[i][term] * vectors[j][term] for term in common)
                pairs.append({"i": i, "j": j, "similarity": round(score, 5)})

        pairs.sort(key=lambda pair: -pair["similarity"])

        clusters = self._cluster(vectors, threshold=float((request.options or {}).get("threshold", 0.12)))

        return self.success(
            request,
            {
                "task": "similarity",
                "documents": len(texts),
                "vocabulary_size": len(vocab),
                "most_similar": pairs[:15],
                "least_similar": pairs[-5:] if len(pairs) > 5 else [],
                "average_similarity": round(sum(p["similarity"] for p in pairs) / max(len(pairs), 1), 5),
                "clusters": clusters,
            },
            metrics={"documents": len(texts), "pairs": len(pairs)},
            explanation=(
                f"شباهت معنایی بین {len(texts)} متن محاسبه شد؛ "
                f"{len(clusters)} خوشه با آستانه شباهت یافت گردید."
            ),
        )

    def _sentiment(self, request: Any, texts: list[str]) -> dict[str, Any]:
        positive = {
            "خوب", "عالی", "مناسب", "موفق", "بهبود", "افزایش", "کاهش_هزینه", "پایدار", "سالم",
            "به‌موقع", "استاندارد", "قبول", "تأیید", "بدون_عیب", "راندمان_بالا",
        }
        negative = {
            "بد", "ضعیف", "خراب", "شکست", "ناموفق", "افزایش_ضایعات", "توقف", "تأخیر", "نشتی",
            "غیراستاندارد", "رد", "بحرانی", "خطر", "معیوب", "کاهش_راندمان", "اعتراض",
        }

        results = []
        for text in texts:
            tokens = self.tokenize(text)
            pos = sum(1 for token in tokens if token in positive)
            neg = sum(1 for token in tokens if token in negative)
            score = (pos - neg) / max(len(tokens), 1) * 10
            results.append(
                {
                    "text": text[:180],
                    "score": round(score, 4),
                    "label": "مثبت" if score > 0.3 else "منفی" if score < -0.3 else "خنثی",
                    "positive_hits": pos,
                    "negative_hits": neg,
                }
            )

        avg = sum(item["score"] for item in results) / max(len(results), 1)

        return self.success(
            request,
            {
                "task": "sentiment",
                "documents": len(texts),
                "average_score": round(avg, 4),
                "overall": "مثبت" if avg > 0.3 else "منفی" if avg < -0.3 else "خنثی",
                "items": results[:100],
            },
            metrics={"documents": len(texts), "average": round(avg, 4), "method": "lexicon"},
            explanation=(
                f"احساس {len(texts)} متن با واژه‌نامه فارسی صنعتی سنجیده شد؛ "
                f"میانگین امتیاز {avg:.2f} و برچسب کلی «{'مثبت' if avg > 0.3 else 'منفی' if avg < -0.3 else 'خنثی'}»."
            ),
            warnings=["واژه‌نامه محدود است؛ برای دقت بالاتر AvalAI یا مدل آموزش‌دیده لازم است."],
        )

    @staticmethod
    def _cluster(vectors: list[dict[str, float]], threshold: float) -> list[list[int]]:
        clusters: list[list[int]] = []
        assigned: set[int] = set()

        for i in range(len(vectors)):
            if i in assigned:
                continue
            group = [i]
            assigned.add(i)
            for j in range(i + 1, len(vectors)):
                if j in assigned:
                    continue
                common = set(vectors[i]) & set(vectors[j])
                score = sum(vectors[i][term] * vectors[j][term] for term in common)
                if score >= threshold:
                    group.append(j)
                    assigned.add(j)
            clusters.append(group)

        return clusters


def fallback_summary(engine: NlpEngine, request: Any, texts: list[str]) -> dict[str, Any]:
    """خلاصه‌سازی: ابتدا AvalAI، در نبود آن روش استخراجی."""
    llm_summary = None
    try:
        from .. import avalai_client

        if avalai_client.is_enabled():
            llm_summary = avalai_client.summarize(texts[0], int((request.options or {}).get("max_length", 400)))
    except Exception:  # pragma: no cover
        llm_summary = None

    vectors, _ = engine.tfidf_vectors(texts)
    sentences = [s.strip() for s in re.split(r"[.!؟?\n]+", texts[0]) if len(s.strip()) > 25]
    scored = []
    for sentence in sentences:
        tokens = set(engine.tokenize(sentence))
        score = sum(vectors[0].get(token, 0.0) for token in tokens) / max(len(tokens), 1)
        scored.append({"text": sentence, "score": score})

    extractive = " ".join(s["text"] for s in sorted(scored, key=lambda s: -s["score"])[:3])

    return engine.success(
        request,
        {
            "task": "summary",
            "summary": llm_summary or extractive,
            "extractive_summary": extractive,
            "llm_used": bool(llm_summary),
            "compression_ratio": round(len(llm_summary or extractive) / max(len(texts[0]), 1), 3),
        },
        metrics={"llm": bool(llm_summary), "sentences": len(sentences)},
        explanation="خلاصه با AvalAI تولید شد." if llm_summary else "خلاصه استخراجی با TF-IDF تولید شد.",
    )
'''

ENGINE_RECOMMENDATION = r'''"""موتور توصیه‌گر — پیشنهاد کالا، قطعه یدکی، آموزش و اقدام.

الگوریتم‌ها: شباهت کسینوسی، فیلتر همکاری ماتریسی، قواعد هم‌رخدادی (Apriori ساده).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import numpy as np

from .base import BaseEngine


class RecommendationEngine(BaseEngine):
    name = "recommendation"
    name_fa = "توصیه‌گر هوشمند"
    endpoint = "/ai/recommend"
    algorithms = ["cosine_similarity", "cooccurrence_rules", "collaborative_filtering"]
    realtime = True

    def run(self, request: Any) -> dict[str, Any]:
        rows = [row for row in (request.features or []) if isinstance(row, dict)]
        mode = str((request.options or {}).get("mode", "auto"))

        interactions = [row for row in rows if "user" in row and "item" in row]
        baskets = [row for row in rows if isinstance(row.get("items"), list)]

        if mode in ("auto", "collaborative") and interactions:
            return self._collaborative(request, interactions)
        if mode in ("auto", "association") and baskets:
            return self._association(request, baskets)
        if rows:
            return self._content_based(request, rows)

        return self.fallback(
            request,
            "داده کافی برای تولید پیشنهاد وجود ندارد.",
            suggestion="تعاملات (user/item)، سبدها (items) یا ویژگی‌های کالا را ارسال کنید.",
        )

    def _content_based(self, request: Any, rows: list[dict[str, Any]]) -> dict[str, Any]:
        top_n = int((request.options or {}).get("top_n", 10))
        target_id = (request.options or {}).get("item_id") or rows[0].get("id")

        keys = [
            key for key in rows[0]
            if isinstance(rows[0].get(key), (int, float))
        ]
        if not keys:
            return self.fallback(request, "ویژگی عددی برای شباهت‌سنجی یافت نشد.")

        matrix = np.asarray([[float(row.get(key, 0.0)) for key in keys] for row in rows], dtype=float)
        norms = np.linalg.norm(matrix, axis=1)
        norms = np.where(norms == 0, 1.0, norms)
        normalized = matrix / norms[:, None]

        target_index = next(
            (i for i, row in enumerate(rows) if str(row.get("id")) == str(target_id)), 0
        )
        similarities = normalized @ normalized[target_index]

        ranked = sorted(
            ({"id": rows[i].get("id"), "score": round(float(similarities[i]), 4),
              "label": rows[i].get("title") or rows[i].get("name")}
             for i in range(len(rows)) if i != target_index),
            key=lambda item: -item["score"],
        )

        return self.success(
            request,
            {
                "mode": "content_based",
                "target": rows[target_index].get("id"),
                "features": keys,
                "recommendations": ranked[:top_n],
            },
            metrics={"candidates": len(rows) - 1, "features": len(keys)},
            explanation=(
                f"بر اساس {len(keys)} ویژگی، {min(top_n, len(rows) - 1)} مورد مشابه با "
                f"«{rows[target_index].get('id')}» پیشنهاد شد."
            ),
        )

    def _collaborative(self, request: Any, interactions: list[dict[str, Any]]) -> dict[str, Any]:
        top_n = int((request.options or {}).get("top_n", 10))
        target_user = (request.options or {}).get("user_id") or interactions[0].get("user")

        matrix: dict[Any, dict[Any, float]] = defaultdict(dict)
        for row in interactions:
            rating = float(row.get("rating") or row.get("quantity") or 1.0)
            matrix[row["user"]][row["item"]] = rating

        users = list(matrix)
        items = sorted({item for user_items in matrix.values() for item in user_items})

        if target_user not in matrix:
            return self.fallback(request, f"کاربر «{target_user}» در تعاملات یافت نشد.")

        # شباهت کاربر-کاربر (کسینوسی)
        def vector(user: Any) -> np.ndarray:
            return np.asarray([matrix[user].get(item, 0.0) for item in items], dtype=float)

        target_vector = vector(target_user)
        similarities = {}
        for user in users:
            if user == target_user:
                continue
            other = vector(user)
            denominator = np.linalg.norm(target_vector) * np.linalg.norm(other)
            similarities[user] = float(np.dot(target_vector, other) / denominator) if denominator else 0.0

        candidate_items = [item for item in items if item not in matrix[target_user]]
        scores: list[dict[str, Any]] = []
        for item in candidate_items:
            numerator = sum(
                similarities[user] * matrix[user][item]
                for user in similarities
                if item in matrix[user] and similarities[user] > 0
            )
            denominator = sum(abs(similarities[user]) for user in similarities if item in matrix[user])
            if denominator > 0:
                scores.append({"item": item, "score": round(numerator / denominator, 4)})

        scores.sort(key=lambda score: -score["score"])
        similar_users = sorted(similarities.items(), key=lambda pair: -pair[1])[:5]

        return self.success(
            request,
            {
                "mode": "collaborative_filtering",
                "user": target_user,
                "users": len(users),
                "items": len(items),
                "similar_users": [{"user": user, "similarity": round(value, 4)} for user, value in similar_users],
                "recommendations": scores[:top_n],
            },
            metrics={
                "interactions": len(interactions),
                "sparsity": round(
                    1 - len(interactions) / max(len(users) * len(items), 1), 4
                ),
                "candidates": len(scores),
            },
            explanation=(
                f"فیلتر همکاری روی {len(users)} کاربر و {len(items)} آیتم اجرا شد؛ "
                f"{len(scores[:top_n])} پیشنهاد برای کاربر «{target_user}» تولید شد."
            ),
            warnings=[] if scores else "آیتم جدیدی برای پیشنهاد یافت نشد (پوشش تعاملات کامل است).",
        )

    def _association(self, request: Any, baskets: list[dict[str, Any]]) -> dict[str, Any]:
        min_support = float((request.options or {}).get("min_support", 0.08))
        min_confidence = float((request.options or {}).get("min_confidence", 0.3))

        pair_counts: Counter = Counter()
        item_counts: Counter = Counter()
        total = len(baskets)

        for basket in baskets:
            unique = sorted({str(item) for item in basket["items"]})
            item_counts.update(unique)
            for i, first in enumerate(unique):
                for second in unique[i + 1 :]:
                    pair_counts[(first, second)] += 1

        rules = []
        for (first, second), count in pair_counts.items():
            support = count / total
            if support < min_support:
                continue
            confidence_ab = count / max(item_counts[first], 1)
            confidence_ba = count / max(item_counts[second], 1)
            lift_ab = confidence_ab / (item_counts[second] / total) if item_counts[second] else 0.0

            if confidence_ab >= min_confidence:
                rules.append({
                    "antecedent": first, "consequent": second,
                    "support": round(support, 4), "confidence": round(confidence_ab, 4),
                    "lift": round(lift_ab, 3), "count": count,
                })
            if confidence_ba >= min_confidence:
                rules.append({
                    "antecedent": second, "consequent": first,
                    "support": round(support, 4), "confidence": round(confidence_ba, 4),
                    "lift": round(confidence_ba / (item_counts[first] / total) if item_counts[first] else 0.0, 3),
                    "count": count,
                })

        rules.sort(key=lambda rule: (-rule["lift"], -rule["confidence"]))

        return self.success(
            request,
            {
                "mode": "association_rules",
                "baskets": total,
                "rules": rules[:50],
                "frequent_items": [
                    {"item": item, "count": count, "support": round(count / total, 4)}
                    for item, count in item_counts.most_common(15)
                ],
            },
            metrics={"baskets": total, "rules": len(rules), "unique_items": len(item_counts)},
            explanation=(
                f"از {total} سبد، {len(rules)} قاعده هم‌رخدادی با حمایت ≥ {min_support:.0%} "
                f"و اطمینان ≥ {min_confidence:.0%} استخراج شد."
            ),
            warnings=[] if rules else "قاعده‌ای با آستانه‌های فعلی یافت نشد؛ آستانه حمایت را کاهش دهید.",
        )
'''

ENGINE_CV = r'''"""موتور بینایی ماشین — بازرسی ظاهری، شمارش و تشخیص عیب.

در استقرار واقعی، تصویر از دوربین صنعتی دریافت و با مدل CNN (که در
MODEL_STORE_PATH ذخیره شده) پردازش می‌شود. در این سرویس، مسیر عددی
(feature descriptors) با RandomForest/SVC پیاده‌سازی شده تا بدون GPU هم
قابل استفاده باشد و در نبود تصویر، تحلیل مبتنی بر شاخص‌های استخراج‌شده انجام شود.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine

try:  # pragma: no cover
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    HAS_SKLEARN = False

DEFECT_RULES = {
    "scratch": {"roughness_ra": (1.6, 99.0), "gloss": (0.0, 55.0)},
    "dent": {"depth_mm": (0.35, 99.0), "area_mm2": (4.0, 99.0)},
    "discoloration": {"delta_e": (3.5, 99.0)},
    "crack": {"length_mm": (2.0, 99.0), "aspect_ratio": (4.0, 99.0)},
    "burrs": {"edge_deviation_mm": (0.25, 99.0)},
    "ok": {},
}


class ComputerVisionEngine(BaseEngine):
    name = "computer_vision"
    name_fa = "بینایی ماشین"
    endpoint = "/ai/vision"
    algorithms = ["descriptor_classification", "rule_based_defect", "random_forest", "thresholding"]
    realtime = True

    def run(self, request: Any) -> dict[str, Any]:
        rows = [row for row in (request.features or []) if isinstance(row, dict)]

        if not rows:
            return self.fallback(
                request,
                "شاخص تصویر (descriptors) ارسال نشد.",
                suggestion=(
                    "فیلدهای roughness_ra، gloss، depth_mm، area_mm2، delta_e، length_mm، "
                    "aspect_ratio یا edge_deviation_mm را برای هر نمونه ارسال کنید."
                ),
            )

        labelled = [row for row in rows if row.get("label") or row.get("defect_type")]
        predictions = [self._classify_row(row) for row in rows]

        result: dict[str, Any] = {
            "mode": "rule_based" if len(labelled) < max(10, len(rows) * 0.5) else "trained",
            "inspected": len(rows),
            "predictions": predictions[:200],
            "defect_distribution": self._distribution(predictions),
            "accept_count": sum(1 for p in predictions if p["defect_type"] == "ok"),
            "reject_count": sum(1 for p in predictions if p["defect_type"] != "ok"),
        }
        result["acceptance_rate_percent"] = round(result["accept_count"] / max(len(rows), 1) * 100, 2)
        result["dominant_defect"] = max(
            ((key, value) for key, value in result["defect_distribution"].items() if key != "ok"),
            key=lambda pair: pair[1],
            default=("ok", 0),
        )[0]

        metrics: dict[str, Any] = {
            "samples": len(rows),
            "rejects": result["reject_count"],
            "acceptance_rate": round(result["acceptance_rate_percent"], 2),
        }

        if len(labelled) >= 12 and HAS_SKLEARN:
            trained = self._train_classifier(rows)
            result.update(trained["result"])
            metrics.update(trained["metrics"])

        explanation = (
            f"{len(rows)} نمونه بازرسی شد؛ {result['reject_count']} مورد معیوب "
            f"({100 - result['acceptance_rate_percent']:.1f}٪) و عیب غالب «{result['dominant_defect']}» است. "
            + ("مدل آموزش‌دیده نیز اجرا شد." if metrics.get("accuracy") else "طبقه‌بندی با قواعد آستانه‌ای انجام شد.")
        )

        warnings = []
        if result["reject_count"] / max(len(rows), 1) > 0.15:
            warnings.append("نرخ رد بیش از ۱۵٪ است؛ پارامترهای فرآیند باید بازنگری شود.")

        return self.success(request, result, metrics=metrics, explanation=explanation, warnings=warnings)

    def _classify_row(self, row: dict[str, Any]) -> dict[str, Any]:
        scores: dict[str, float] = {}

        for defect, rules in DEFECT_RULES.items():
            if defect == "ok":
                continue
            score = 0.0
            matched = 0
            for feature, (low, high) in rules.items():
                value = row.get(feature)
                if value is None:
                    continue
                value = float(value)
                if low <= value <= high:
                    matched += 1
                    # شدت بر اساس فاصله از آستانه پایین
                    score += min((value - low) / max(low, 1e-6), 3.0)
            if matched and matched >= max(1, len(rules) // 2):
                scores[defect] = round(score / matched + matched * 0.25, 3)

        if not scores:
            return {"defect_type": "ok", "confidence": 0.9, "scores": {}, "severity": "سالم"}

        defect = max(scores, key=lambda key: scores[key])
        confidence = min(0.99, 0.55 + scores[defect] / 6)
        severity = "بحرانی" if scores[defect] > 2.0 else "متوسط" if scores[defect] > 1.0 else "جزئی"

        return {
            "defect_type": defect,
            "confidence": round(confidence, 3),
            "severity": severity,
            "scores": scores,
            "action": "قرنطینه و بررسی" if severity == "بحرانی" else "بازبینی سرپرست کیفیت",
        }

    def _train_classifier(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        feature_keys = sorted({
            key for row in rows for key, value in row.items()
            if isinstance(value, (int, float)) and key != "label"
        })
        labelled = [row for row in rows if row.get("label") or row.get("defect_type")]

        X = np.asarray([[float(row.get(key, 0.0)) for key in feature_keys] for row in labelled], dtype=float)
        y = np.asarray([str(row.get("label") or row.get("defect_type")) for row in labelled])

        classes = sorted(set(y.tolist()))
        if len(classes) < 2:
            return {"result": {}, "metrics": {}}

        stratify = y if min(np.bincount(np.unique(y, return_inverse=True)[1])) >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=stratify
        )

        model = RandomForestClassifier(n_estimators=140, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        accuracy = float(accuracy_score(y_test, model.predict(X_test)))

        return {
            "result": {
                "trained_model": True,
                "classes": classes,
                "features": feature_keys,
                "feature_importance": sorted(
                    ({"feature": key, "importance": round(float(value), 4)}
                     for key, value in zip(feature_keys, model.feature_importances_)),
                    key=lambda item: -item["importance"],
                )[:12],
            },
            "metrics": {"accuracy": round(accuracy, 4), "trained_samples": len(labelled)},
        }

    @staticmethod
    def _distribution(predictions: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for prediction in predictions:
            key = prediction["defect_type"]
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda pair: -pair[1]))
'''

ENGINE_SIMULATION = r'''"""موتور شبیه‌سازی — مونت‌کارلو برای ظرفیت، صف و ریسک برنامه.

شبیه‌سازی گسسته‌رویداد خط تولید و صف سفارش‌ها با توزیع‌های تصادفی واقعی.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine


class SimulationEngine(BaseEngine):
    name = "simulation"
    name_fa = "شبیه‌سازی و سناریو"
    endpoint = "/ai/simulate"
    algorithms = ["monte_carlo", "discrete_event_queue", "scenario_analysis"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        from ..config import settings

        options = request.options or {}
        runs = int(options.get("runs", settings.simulation_runs))
        runs = max(50, min(runs, 5000))

        rows = [row for row in (request.features or []) if isinstance(row, dict)]
        scenario = str(options.get("scenario", "capacity"))

        if scenario in ("queue", "waiting") and rows:
            return self._queue(request, rows, runs)
        if request.series:
            return self._series_monte_carlo(request, runs)

        return self._capacity(request, rows, runs)

    # --- شبیه‌سازی ظرفیت --------------------------------------------------- #
    def _capacity(self, request: Any, rows: list[dict[str, Any]], runs: int) -> dict[str, Any]:
        rng = np.random.default_rng(int((request.options or {}).get("seed", 1405)))

        if rows:
            capacities = np.asarray([float(row.get("capacity", 8.0)) for row in rows], dtype=float)
            demand_mean = float(np.mean([float(row.get("daily_demand", 100.0)) for row in rows]))
            demand_std = float(np.mean([float(row.get("demand_std", demand_mean * 0.2)) for row in rows]))
        else:
            lines = max(int((request.options or {}).get("lines", 3)), 1)
            capacities = np.full(lines, float((request.options or {}).get("capacity_per_line", 120.0)))
            demand_mean = float((request.options or {}).get("demand_mean", 300.0))
            demand_std = demand_mean * 0.18

        total_capacity = float(capacities.sum())
        outputs = []
        shortage_events = 0
        utilizations = []

        for _ in range(runs):
            # خرابی تصادفی خطوط (دسترس‌پذیری ~۹۲٪)
            uptime = rng.beta(9.2, 0.8, size=len(capacities))
            available = capacities * uptime
            demand = max(rng.normal(demand_mean, demand_std), 0.0)
            produced = min(float(available.sum()), demand)
            shortage = max(demand - float(available.sum()), 0.0)
            if shortage > 0:
                shortage_events += 1
            utilization = produced / float(available.sum()) if available.sum() else 0.0
            utilizations.append(utilization)
            outputs.append(produced)

        produced_array = np.asarray(outputs)
        utilization_array = np.asarray(utilizations)

        percentiles = {
            f"p{int(q)}": round(float(np.percentile(produced_array, q)), 2) for q in (5, 25, 50, 75, 95)
        }

        explanation = (
            f"{runs} سناریو شبیه‌سازی شد. تولید میانگین {produced_array.mean():,.0f} "
            f"(میانه {percentiles['p50']:,.0f}) و احتمال کمبود ظرفیت "
            f"{shortage_events / runs * 100:.1f}٪ است. بهره‌وری میانگین "
            f"{utilization_array.mean() * 100:.1f}٪ برآورد شد."
        )

        warnings = []
        if shortage_events / runs > 0.2:
            warnings.append("احتمال کمبود ظرفیت بیش از ۲۰٪ است؛ شیفت اضافه یا برون‌سپاری توصیه می‌شود.")
        if utilization_array.mean() > 0.92:
            warnings.append("بهره‌وری بسیار بالا، انعطاف برنامه را کم می‌کند (ریسک صف و تأخیر).")

        return self.success(
            request,
            {
                "scenario": "capacity",
                "runs": runs,
                "lines": int(len(capacities)),
                "total_capacity": round(total_capacity, 2),
                "demand_mean": round(demand_mean, 2),
                "production_mean": round(float(produced_array.mean()), 2),
                "production_std": round(float(produced_array.std()), 2),
                "percentiles": percentiles,
                "shortage_probability": round(shortage_events / runs, 4),
                "utilization_mean": round(float(utilization_array.mean()), 4),
                "confidence_interval_95": [
                    round(float(np.percentile(produced_array, 2.5)), 2),
                    round(float(np.percentile(produced_array, 97.5)), 2),
                ],
                "recommendations": self._recommendations(shortage_events / runs, float(utilization_array.mean())),
            },
            metrics={
                "runs": runs,
                "shortage_probability": round(shortage_events / runs, 4),
                "utilization": round(float(utilization_array.mean()), 4),
            },
            explanation=explanation,
            warnings=warnings,
        )

    # --- شبیه‌سازی صف ------------------------------------------------------ #
    def _queue(self, request: Any, rows: list[dict[str, Any]], runs: int) -> dict[str, Any]:
        rng = np.random.default_rng(int((request.options or {}).get("seed", 313)))

        servers = max(int((request.options or {}).get("servers", 2)), 1)
        arrival_rate = float(np.mean([float(row.get("arrival_rate", 4.0)) for row in rows]))
        service_rate = float(np.mean([float(row.get("service_rate", 5.0)) for row in rows]))

        if service_rate * servers <= arrival_rate:
            return self.fallback(
                request,
                "نرخ ورود از ظرفیت خدمت بیشتر است؛ صف پایدار نیست.",
                suggestion="تعداد ایستگاه‌ها (servers) را افزایش دهید یا نرخ ورود را کاهش دهید.",
            )

        waiting_times = []
        queue_lengths = []

        for _ in range(runs):
            clock = 0.0
            queue: list[float] = []
            busy_until = [0.0] * servers
            metrics = []
            for _ in range(120):  # ۱۲۰ ورود در هر سناریو
                clock += float(rng.exponential(1.0 / arrival_rate))
                service = float(rng.gamma(4.0, service_rate / 4.0))
                free = int(np.argmin(busy_until))
                start = max(clock, busy_until[free])
                if queue:
                    start += queue.pop(0)
                wait = max(start - clock, 0.0)
                busy_until[free] = start + service
                waiting_times.append(wait)
                queue_lengths.append(len(queue) + sum(1 for t in busy_until if t > clock))
                metrics.append(wait)

        waiting = np.asarray(waiting_times)
        utilization = arrival_rate / (servers * service_rate)

        return self.success(
            request,
            {
                "scenario": "queue",
                "runs": runs,
                "servers": servers,
                "arrival_rate": round(arrival_rate, 3),
                "service_rate": round(service_rate, 3),
                "utilization": round(utilization, 4),
                "average_wait": round(float(waiting.mean()), 3),
                "median_wait": round(float(np.median(waiting)), 3),
                "p95_wait": round(float(np.percentile(waiting, 95)), 3),
                "max_wait": round(float(waiting.max()), 3),
                "average_queue_length": round(float(np.mean(queue_lengths)), 3),
                "probability_wait": round(float((waiting > 0).mean()), 4),
            },
            metrics={
                "runs": runs,
                "utilization": round(utilization, 4),
                "average_wait": round(float(waiting.mean()), 3),
            },
            explanation=(
                f"شبیه‌سازی صف با {servers} ایستگاه خدمت و {runs} سناریو: "
                f"میانگین انتظار {waiting.mean():.2f} و بهره‌گیری {utilization * 100:.1f}٪."
            ),
            warnings=["بهره‌گیری بالای ۸۵٪ زمان انتظار را به‌شدت حساس می‌کند."] if utilization > 0.85 else [],
        )

    # --- مونت‌کارلو روی دنباله --------------------------------------------- #
    def _series_monte_carlo(self, request: Any, runs: int) -> dict[str, Any]:
        rng = np.random.default_rng(99)
        values = np.asarray(self.to_floats(request.series), dtype=float)
        if len(values) < 5:
            return self.fallback(request, "دنباله برای شبیه‌سازی کوتاه است (حداقل ۵ مقدار).")

        returns = np.diff(values) / np.where(values[:-1] == 0, 1.0, values[:-1])
        mean_return, std_return = float(returns.mean()), float(returns.std(ddof=1)) or 1e-6
        horizon = int(request.horizon or 12)

        paths = values[-1] * np.cumprod(
            1 + rng.normal(mean_return, std_return, size=(runs, horizon)), axis=1
        )
        final = paths[:, -1]

        return self.success(
            request,
            {
                "scenario": "series_monte_carlo",
                "runs": runs,
                "horizon": horizon,
                "last_value": round(float(values[-1]), 3),
                "mean_return": round(mean_return, 5),
                "volatility": round(std_return, 5),
                "final_mean": round(float(final.mean()), 3),
                "final_percentiles": {
                    f"p{int(q)}": round(float(np.percentile(final, q)), 3) for q in (5, 25, 50, 75, 95)
                },
                "risk_of_decline": round(float((final < values[-1]).mean()), 4),
                "var_95": round(float(values[-1] - np.percentile(final, 5)), 3),
                "sample_paths": [
                    [round(float(v), 3) for v in path] for path in paths[:5]
                ],
            },
            metrics={"runs": runs, "horizon": horizon, "volatility": round(std_return, 5)},
            explanation=(
                f"{runs} مسیر تصادفی برای {horizon} دوره شبیه‌سازی شد؛ "
                f"احتمال کاهش نسبت به امروز {(final < values[-1]).mean() * 100:.1f}٪ و "
                f"مقدار در معرض ریسک ۹۵٪ برابر {values[-1] - np.percentile(final, 5):,.2f} است."
            ),
        )

    @staticmethod
    def _recommendations(shortage_probability: float, utilization: float) -> list[str]:
        items: list[str] = []
        if shortage_probability > 0.3:
            items.append("افزودن یک شیفت یا برون‌سپاری بخشی از تقاضا در ماه‌های اوج.")
        elif shortage_probability > 0.1:
            items.append("ایجاد موجودی اطمینان محصول نیمه‌ساخته برای ماه‌های پرتقاضا.")
        if utilization < 0.6:
            items.append("ظرفیت خالی قابل فروش است؛ بازاریابی سفارش‌گذاری فصلی توصیه می‌شود.")
        if utilization > 0.9:
            items.append("برنامه نت پیشگیرانه را فشرده‌تر کنید تا توقف ناخواسته ظرفیت را نخورد.")
        if not items:
            items.append("وضعیت ظرفیت متعادل است؛ پایش ماهانه ادامه یابد.")
        return items
'''

ENGINE_MLOPS = r'''"""موتور عملیات یادگیری ماشین (MLOps).

پایش رانش داده (PSI)، ارزیابی عملکرد مدل، پیشنهاد بازآموزی و
گزارش سلامت مدل‌های ثبت‌شده.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import BaseEngine
from ..models import store


class MlopsEngine(BaseEngine):
    name = "mlops"
    name_fa = "عملیات یادگیری ماشین"
    endpoint = "/ai/mlops"
    algorithms = ["psi_drift", "ks_test", "performance_tracking", "retraining_policy"]
    realtime = False

    def run(self, request: Any) -> dict[str, Any]:
        task = str((request.options or {}).get("task", "monitor"))

        if task == "registry":
            return self._registry(request)
        if task == "drift":
            return self._drift(request)

        reference = self.to_floats((request.options or {}).get("reference") or [])
        current = self.to_floats(request.series or (request.options or {}).get("current") or [])

        if reference and current:
            return self._drift_with(request, reference, current)
        if current and len(current) >= 10:
            return self._quality_report(request, current)

        return self.fallback(
            request,
            "داده پایش کافی نیست.",
            suggestion="reference (داده آموزش) و current (داده جاری) را ارسال کنید یا task=registry بدهید.",
        )

    def _registry(self, request: Any) -> dict[str, Any]:
        models = store.list_models()
        for model in models:
            model["status"] = "ready" if model.get("size_bytes", 0) > 0 else "empty"

        return self.success(
            request,
            {
                "task": "registry",
                "models": models,
                "count": len(models),
                "total_size_bytes": sum(int(model.get("size_bytes", 0)) for model in models),
            },
            metrics={"models": len(models)},
            explanation=f"{len(models)} مدل در رجیستری ثبت شده است."
            if models
            else "هنوز مدلی آموزش داده نشده است.",
        )

    def _drift(self, request: Any) -> dict[str, Any]:
        """مقایسه داده جاری با داده مرجع مدل (در صورت وجود)."""
        current = self.to_floats(request.series or (request.options or {}).get("current") or [])
        model_id = request.model_id

        if not current:
            return self.fallback(request, "داده جاری برای بررسی رانش ارسال نشد.")

        reference = self.to_floats((request.options or {}).get("reference") or [])
        if not reference and model_id:
            meta = store.load_meta(model_id)
            reference = self.to_floats(meta.get("reference_sample") or [])

        if not reference:
            return self._quality_report(request, current, note="داده مرجع یافت نشد؛ فقط آمار جاری گزارش شد.")

        return self._drift_with(request, reference, current)

    def _drift_with(self, request: Any, reference: list[float], current: list[float]) -> dict[str, Any]:
        from ..config import settings

        reference_array = np.asarray(reference, dtype=float)
        current_array = np.asarray(current, dtype=float)

        psi = self._population_stability_index(reference_array, current_array)
        ks = self._ks_statistic(reference_array, current_array)
        threshold = float(settings.drift_psi_threshold)

        mean_shift = float(current_array.mean() - reference_array.mean())
        std_shift = float(current_array.std() - reference_array.std())

        if psi > threshold:
            verdict, action = "رانش شدید", "بازآموزی فوری مدل و بررسی منبع داده"
        elif psi > threshold * 0.5:
            verdict, action = "رانش متوسط", "برنامه‌ریزی بازآموزی در چرخه بعد و پایش هفتگی"
        else:
            verdict, action = "پایدار", "ادامه پایش معمول؛ بازآموزی لازم نیست"

        explanation = (
            f"شاخص پایداری جمعیت PSI={psi:.4f} (آستانه {threshold}) و آماره KS={ks:.4f} است. "
            f"وضعیت: {verdict}. میانگین داده جاری {mean_shift:+.3f} نسبت به مرجع جابه‌جا شده است."
        )

        if request.model_id:
            store.append_log(request.model_id, {
                "event": "drift_check",
                "psi": round(psi, 5),
                "ks": round(ks, 5),
                "verdict": verdict,
                "samples": len(current),
            })

        return self.success(
            request,
            {
                "task": "drift",
                "psi": round(psi, 5),
                "ks_statistic": round(ks, 5),
                "threshold": threshold,
                "verdict": verdict,
                "recommended_action": action,
                "retraining_required": psi > threshold * 0.5,
                "statistics": {
                    "reference": self._describe(reference_array),
                    "current": self._describe(current_array),
                    "mean_shift": round(mean_shift, 5),
                    "std_shift": round(std_shift, 5),
                },
            },
            metrics={
                "psi": round(psi, 5),
                "ks": round(ks, 5),
                "reference_samples": len(reference),
                "current_samples": len(current),
            },
            explanation=explanation,
            warnings=[] if psi <= threshold else ["رانش داده از آستانه عبور کرده است."],
        )

    def _quality_report(self, request: Any, values: list[float], note: str = "") -> dict[str, Any]:
        array = np.asarray(values, dtype=float)
        stats = self._describe(array)
        anomalies = int(np.sum(np.abs((array - array.mean()) / (array.std() or 1.0)) > 3))

        return self.success(
            request,
            {
                "task": "quality_report",
                "statistics": {"current": stats},
                "missing_ratio": round(float(np.mean(np.isnan(array))), 4),
                "outlier_ratio": round(anomalies / max(len(array), 1), 4),
                "note": note or "گزارش کیفیت داده جاری.",
            },
            metrics={"samples": len(array), "outliers": anomalies},
            explanation=(
                f"{len(array)} نمونه بررسی شد: میانگین {stats['mean']}, میانه {stats['median']}, "
                f"{anomalies} نقطه پرت و {stats['cv'] * 100:.1f}٪ ضریب تغییرات." + (f" {note}" if note else "")
            ),
        )

    # --- آماره‌ها ---------------------------------------------------------- #
    @staticmethod
    def _describe(array: np.ndarray) -> dict[str, float]:
        mean = float(array.mean())
        std = float(array.std() or 1e-9)
        return {
            "count": int(len(array)),
            "mean": round(mean, 5),
            "std": round(std, 5),
            "cv": round(std / mean if mean else 0.0, 5),
            "min": round(float(array.min()), 5),
            "q25": round(float(np.percentile(array, 25)), 5),
            "median": round(float(np.median(array)), 5),
            "q75": round(float(np.percentile(array, 75)), 5),
            "max": round(float(array.max()), 5),
        }

    @staticmethod
    def _population_stability_index(reference: np.ndarray, current: np.ndarray, buckets: int = 10) -> float:
        """شاخص پایداری جمعیت (PSI)."""
        if len(reference) < buckets or len(current) < buckets:
            buckets = max(2, min(len(reference), len(current), 10))

        quantiles = np.quantile(reference, np.linspace(0, 1, buckets + 1))
        quantiles[0], quantiles[-1] = -np.inf, np.inf

        reference_counts, _ = np.histogram(reference, bins=quantiles)
        current_counts, _ = np.histogram(current, bins=quantiles)

        reference_pct = np.clip(reference_counts / max(reference_counts.sum(), 1), 1e-6, None)
        current_pct = np.clip(current_counts / max(current_counts.sum(), 1), 1e-6, None)

        return float(np.sum((current_pct - reference_pct) * np.log(current_pct / reference_pct)))

    @staticmethod
    def _ks_statistic(reference: np.ndarray, current: np.ndarray) -> float:
        """آماره کولموگروف-اسمیرنف دو نمونه‌ای."""
        grid = np.unique(np.concatenate([reference, current]))
        reference_cdf = np.searchsorted(np.sort(reference), grid, side="right") / len(reference)
        current_cdf = np.searchsorted(np.sort(current), grid, side="right") / len(current)
        return float(np.max(np.abs(reference_cdf - current_cdf)))
'''

ENGINES_INIT = r'''"""رجیستری موتورهای هوش مصنوعی."""

from __future__ import annotations

from typing import Any

from .base import BaseEngine, now_iso
from .anomaly import AnomalyEngine
from .classification import ClassificationEngine
from .computer_vision import ComputerVisionEngine
from .forecasting import ForecastingEngine
from .mlops import MlopsEngine
from .nlp import NlpEngine
from .optimization import OptimizationEngine
from .quality_spc import QualitySpcEngine
from .recommendation import RecommendationEngine
from .reliability import ReliabilityEngine
from .simulation import SimulationEngine

ALL_ENGINES: dict[str, type[BaseEngine]] = {
    "forecasting": ForecastingEngine,
    "reliability": ReliabilityEngine,
    "optimization": OptimizationEngine,
    "anomaly": AnomalyEngine,
    "computer_vision": ComputerVisionEngine,
    "nlp": NlpEngine,
    "recommendation": RecommendationEngine,
    "quality_spc": QualitySpcEngine,
    "classification": ClassificationEngine,
    "simulation": SimulationEngine,
    "mlops": MlopsEngine,
}

_instances: dict[str, BaseEngine] = {}


def get_engine(name: str) -> BaseEngine:
    """دریافت نمونه (singleton) یک موتور."""
    if name not in _instances:
        engine_class = ALL_ENGINES.get(name)
        if engine_class is None:
            raise KeyError(f"موتور «{name}» شناخته شده نیست")
        _instances[name] = engine_class()
    return _instances[name]


def enabled_engines(names: list[str]) -> dict[str, BaseEngine]:
    """موتورهای فعال در این استقرار."""
    result: dict[str, BaseEngine] = {}
    for name in names:
        if name in ALL_ENGINES:
            result[name] = get_engine(name)
    return result


def engine_catalog() -> list[dict[str, Any]]:
    """شرح همه موتورهای پیاده‌سازی‌شده در سرویس."""
    return [
        {
            "key": key,
            "name_fa": cls.name_fa,
            "endpoint": cls.endpoint,
            "algorithms": cls.algorithms,
            "uses_llm": cls.uses_llm,
            "realtime": cls.realtime,
        }
        for key, cls in ALL_ENGINES.items()
    ]


__all__ = [
    "ALL_ENGINES", "BaseEngine", "engine_catalog", "enabled_engines",
    "get_engine", "now_iso",
]
'''

MAIN_PY = r'''"""میکروسرویس هوش مصنوعی ERP کارخانه — نقطه ورود FastAPI."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import avalai_client
from .config import CAPABILITIES, ENABLED_ENGINES, settings
from .engines import ALL_ENGINES, engine_catalog, get_engine
from .models import store
from .routers import ai, capabilities as capabilities_router, models as models_router
from .schemas import AiRequest, HealthResponse

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("ai-service")

app = FastAPI(
    title="@@app_name@@ — سرویس هوش مصنوعی",
    description=(
        "میکروسرویس موتورهای هوش مصنوعی کارخانه: پیش‌بینی، قابلیت اطمینان، "
        "بهینه‌سازی، تشخیص ناهنجاری، کنترل کیفیت آماری، بینایی ماشین، "
        "پردازش زبان طبیعی، توصیه‌گر، شبیه‌سازی و MLOps."
    ),
    version="@@version@@",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STARTED_AT = time.time()


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """هیچ خطایی نباید زنجیره تولید را متوقف کند — پاسخ fallback برمی‌گردد."""
    logger.exception("unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=200,
        content={
            "ok": False,
            "fallback": True,
            "engine": "unknown",
            "result": {},
            "explanation": f"خطای غیرمنتظره در سرویس AI: {exc}",
            "warnings": ["سرویس در حالت fallback پاسخ داد؛ جریان کاری ادامه دارد."],
        },
    )


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, Any]:
    """سلامت سرویس و فهرست موتورهای فعال."""
    return {
        "ok": True,
        "service": "@@app_name@@",
        "version": "@@version@@",
        "engines": ENABLED_ENGINES,
        "models": len(store.list_models()),
        "avalai_enabled": avalai_client.is_enabled(),
        "capabilities": len(CAPABILITIES),
        "company": settings.company_name,
        "server_time": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "@@app_name@@ — سرویس هوش مصنوعی",
        "version": "@@version@@",
        "docs": "/docs",
        "health": "/health",
        "engines": ENABLED_ENGINES,
        "capabilities": len(CAPABILITIES),
        "company": settings.company_name,
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
    }


app.include_router(ai.router)
app.include_router(models_router.router)
app.include_router(capabilities_router.router)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
'''

ROUTER_AI = r'''"""اندپوینت‌های اصلی موتورهای AI."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from ..config import CAPABILITIES, ENABLED_ENGINES
from ..engines import ALL_ENGINES, get_engine
from ..models import store
from ..schemas import AiRequest, AiResponse

logger = logging.getLogger("ai.router")

router = APIRouter(prefix="/ai", tags=["ai"])


def _resolve_engine(payload: AiRequest) -> str:
    """تعیین موتور هدف از کد قابلیت یا نام موتور."""
    if payload.engine:
        if payload.engine in ALL_ENGINES:
            return payload.engine
        raise HTTPException(
            status_code=404,
            detail=f"موتور «{payload.engine}» در این استقرار فعال نیست. "
                   f"موتورهای فعال: {', '.join(sorted(ENABLED_ENGINES)) or '—'}",
        )

    if payload.capability:
        capability = CAPABILITIES.get(payload.capability.upper())
        if capability:
            return capability["engine"]
        # استنتاج از پیشوند کد (مثل K1 -> forecasting)
        prefix_map = {
            "K1": "forecasting", "K2": "optimization", "K3": "computer_vision",
            "K4": "nlp", "K5": "recommendation", "K6": "anomaly", "K7": "mlops",
            "C2": "reliability", "B3": "quality_spc", "J4": "simulation",
        }
        code = payload.capability.upper()
        if code[:2] in prefix_map:
            return prefix_map[code[:2]]

    return "classification"


def _run(engine_name: str, payload: AiRequest) -> dict[str, Any]:
    started = time.perf_counter()

    if engine_name not in ALL_ENGINES:
        raise HTTPException(status_code=404, detail=f"موتور «{engine_name}» شناخته شده نیست")

    engine = get_engine(engine_name)

    try:
        result = engine.run(payload)
    except Exception as exc:  # pragma: no cover - دفاعی
        logger.exception("engine %s failed: %s", engine_name, exc)
        result = {
            "ok": False,
            "engine": engine_name,
            "fallback": True,
            "result": {},
            "explanation": f"خطا در اجرای موتور: {exc}",
            "warnings": ["پاسخ fallback برگردانده شد."],
        }

    latency_ms = (time.perf_counter() - started) * 1000
    result.setdefault("metrics", {})
    result["metrics"]["latency_ms"] = round(latency_ms, 2)
    result["enabled_in_deployment"] = engine_name in ENABLED_ENGINES

    if payload.model_id:
        store.append_log(payload.model_id, {
            "event": "inference",
            "engine": engine_name,
            "capability": payload.capability,
            "latency_ms": round(latency_ms, 2),
            "ok": bool(result.get("ok")),
        })

    return result


@router.post("", response_model=AiResponse)
@router.post("/", response_model=AiResponse)
def run_default(payload: AiRequest) -> dict[str, Any]:
    """اجرای موتور تشخیص‌داده‌شده از روی کد قابلیت."""
    return _run(_resolve_engine(payload), payload)


@router.post("/forecast", response_model=AiResponse)
def forecast(payload: AiRequest) -> dict[str, Any]:
    """پیش‌بینی سری زمانی (تقاضا، مصرف، فروش، انرژی)."""
    return _run("forecasting", payload)


@router.post("/optimize", response_model=AiResponse)
def optimize(payload: AiRequest) -> dict[str, Any]:
    """بهینه‌سازی موجودی، زمان‌بندی تولید و تخصیص منابع."""
    return _run("optimization", payload)


@router.post("/anomaly", response_model=AiResponse)
def anomaly(payload: AiRequest) -> dict[str, Any]:
    """تشخیص ناهنجاری در داده سنسور، کیفیت یا مالی."""
    return _run("anomaly", payload)


@router.post("/reliability", response_model=AiResponse)
def reliability(payload: AiRequest) -> dict[str, Any]:
    """تحلیل قابلیت اطمینان، وایبول، MTBF و عمر باقی‌مانده."""
    return _run("reliability", payload)


@router.post("/spc", response_model=AiResponse)
def spc(payload: AiRequest) -> dict[str, Any]:
    """نمودارهای کنترل آماری فرآیند و شاخص قابلیت CpK."""
    return _run("quality_spc", payload)


@router.post("/vision", response_model=AiResponse)
def vision(payload: AiRequest) -> dict[str, Any]:
    """بازرسی بصری و تشخیص عیب."""
    return _run("computer_vision", payload)


@router.post("/nlp", response_model=AiResponse)
def nlp(payload: AiRequest) -> dict[str, Any]:
    """پردازش زبان طبیعی فارسی: کلیدواژه، شباهت، احساس و خلاصه."""
    return _run("nlp", payload)


@router.post("/recommend", response_model=AiResponse)
def recommend(payload: AiRequest) -> dict[str, Any]:
    """توصیه‌گر: کالای مشابه، قطعه یدکی، قواعد هم‌رخدادی."""
    return _run("recommendation", payload)


@router.post("/classify", response_model=AiResponse)
def classify(payload: AiRequest) -> dict[str, Any]:
    """طبقه‌بندی عمومی (جدولی و متنی)."""
    return _run("classification", payload)


@router.post("/simulate", response_model=AiResponse)
def simulate(payload: AiRequest) -> dict[str, Any]:
    """شبیه‌سازی مونت‌کارلو ظرفیت، صف و ریسک برنامه."""
    return _run("simulation", payload)


@router.post("/mlops", response_model=AiResponse)
def mlops(payload: AiRequest) -> dict[str, Any]:
    """پایش مدل: رانش داده، رجیستری و سیاست بازآموزی."""
    return _run("mlops", payload)


@router.post("/capability/{code}", response_model=AiResponse)
def run_capability(code: str, payload: AiRequest) -> dict[str, Any]:
    """اجرای یک قابلیت مشخص کاتالوگ با کد آن."""
    payload.capability = code.upper()
    engine = _resolve_engine(payload)

    if code.upper() not in CAPABILITIES:
        raise HTTPException(
            status_code=404,
            detail=f"قابلیت {code} در این استقرار فعال نیست.",
        )

    return _run(engine, payload)
'''

ROUTER_MODELS = r'''"""مدیریت مدل‌ها: آموزش، ثبت، بارگذاری و پایش (MLOps)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException

from ..config import ENABLED_ENGINES
from ..models import store
from ..schemas import ModelInfo, TrainRequest

logger = logging.getLogger("ai.models")

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models() -> dict[str, Any]:
    """فهرست مدل‌های ثبت‌شده."""
    models = store.list_models()
    return {"count": len(models), "models": models}


@router.get("/{model_id}")
def get_model(model_id: str) -> dict[str, Any]:
    """اطلاعات یک مدل به‌همراه لاگ رویدادها."""
    meta = store.load_meta(model_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"مدل «{model_id}» یافت نشد")

    return {
        "model": meta,
        "artifact_present": store.load(model_id) is not None,
        "log": store.read_log(model_id, limit=50),
    }


@router.post("/train", response_model=ModelInfo)
def train(payload: TrainRequest) -> dict[str, Any]:
    """آموزش و ثبت یک مدل جدید."""
    if payload.engine not in ENABLED_ENGINES and payload.engine not in ("forecasting", "classification"):
        logger.warning("training requested for disabled engine %s", payload.engine)

    artifact: Any = None
    metrics: dict[str, Any] = {}
    samples = 0
    algorithm = payload.algorithm or "auto"

    if payload.series:
        values = np.asarray([float(v) for v in payload.series], dtype=float)
        samples = int(len(values))
        artifact = {
            "type": "series_profile",
            "engine": payload.engine,
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if samples > 1 else 0.0,
            "trend_slope": float(np.polyfit(np.arange(samples), values, 1)[0]) if samples > 2 else 0.0,
            "reference_sample": values[: min(samples, 200)].tolist(),
            "last_values": values[-24:].tolist(),
        }
        metrics = {
            "samples": samples,
            "mean": round(float(values.mean()), 4),
            "trend_slope": round(artifact["trend_slope"], 6),
        }
        algorithm = "series_profile"

    elif payload.features and payload.target:
        feature_keys = sorted({
            key for row in payload.features for key, value in row.items()
            if isinstance(value, (int, float)) and key != payload.target
        })
        if not feature_keys:
            raise HTTPException(status_code=422, detail="ویژگی عددی در داده‌های آموزش یافت نشد")

        X = np.asarray(
            [[float(row.get(key, 0.0)) for key in feature_keys] for row in payload.features], dtype=float
        )
        y = np.asarray([str(row.get(payload.target, "")) for row in payload.features])
        samples = int(len(y))

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score
            from sklearn.model_selection import train_test_split

            stratify = y if min(np.bincount(np.unique(y, return_inverse=True)[1])) >= 2 else None
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=stratify
            )
            model = RandomForestClassifier(
                n_estimators=int(payload.hyperparameters.get("n_estimators", 150)),
                max_depth=int(payload.hyperparameters.get("max_depth", 12)),
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)
            accuracy = float(accuracy_score(y_test, model.predict(X_test)))

            artifact = {
                "type": "classifier",
                "engine": payload.engine,
                "model": model,
                "feature_keys": feature_keys,
                "classes": sorted(set(y.tolist())),
                "reference_sample": np.asarray(X[:200]).mean(axis=0).tolist(),
            }
            metrics = {"samples": samples, "accuracy": round(accuracy, 4), "features": len(feature_keys)}
            algorithm = "random_forest"
        except ImportError:  # pragma: no cover
            artifact = {
                "type": "statistical_profile",
                "engine": payload.engine,
                "feature_keys": feature_keys,
                "mean": X.mean(axis=0).tolist(),
                "std": X.std(axis=0).tolist(),
                "reference_sample": X[:200].tolist(),
            }
            metrics = {"samples": samples, "features": len(feature_keys)}
            algorithm = "statistical_profile"
    else:
        raise HTTPException(
            status_code=422,
            detail="برای آموزش، series یا features به‌همراه target لازم است.",
        )

    meta = store.save(
        payload.model_id,
        artifact,
        {
            "engine": payload.engine,
            "algorithm": algorithm,
            "samples": samples,
            "metrics": metrics,
            "status": "ready",
            "hyperparameters": payload.hyperparameters,
            "period": payload.period,
        },
    )

    store.append_log(payload.model_id, {"event": "train", "algorithm": algorithm, "metrics": metrics})

    return {
        "model_id": payload.model_id,
        "engine": payload.engine,
        "algorithm": algorithm,
        "created_at": meta["created_at"],
        "samples": samples,
        "metrics": metrics,
        "size_bytes": int(meta.get("size_bytes", 0)),
        "status": "ready",
    }


@router.post("/{model_id}/predict")
def predict(model_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """پیش‌بینی با مدل ثبت‌شده."""
    artifact = store.load(model_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"مدل «{model_id}» آموزش داده نشده است")

    kind = artifact.get("type")
    features = payload.get("features") or {}

    if kind == "classifier" and features:
        keys = artifact["feature_keys"]
        vector = np.asarray([[float(features.get(key, 0.0)) for key in keys]], dtype=float)
        model = artifact["model"]
        probabilities = model.predict_proba(vector)[0]
        prediction = model.predict(vector)[0]

        result = {
            "model_id": model_id,
            "prediction": str(prediction),
            "probabilities": {
                str(cls): round(float(prob), 4) for cls, prob in zip(model.classes_, probabilities)
            },
            "confidence": round(float(max(probabilities)), 4),
        }
    elif kind == "series_profile":
        horizon = int(payload.get("horizon", 6))
        mean = float(artifact["mean"])
        slope = float(artifact.get("trend_slope", 0.0))
        base = float(artifact["last_values"][-1]) if artifact.get("last_values") else mean
        forecast = [round(base + slope * (step + 1), 4) for step in range(horizon)]
        result = {
            "model_id": model_id,
            "forecast": forecast,
            "trend_slope": slope,
            "confidence_interval": round(float(artifact.get("std", 0.0)) * 1.96, 4),
        }
    else:
        result = {
            "model_id": model_id,
            "prediction": None,
            "note": "این مدل آماری است؛ برای پیش‌بینی از اندپوینت /ai استفاده کنید.",
            "profile": {k: v for k, v in artifact.items() if k != "model"},
        }

    store.append_log(model_id, {"event": "predict", "input_keys": list(features)[:12]})
    return result


@router.delete("/{model_id}")
def delete_model(model_id: str) -> dict[str, Any]:
    """حذف یک مدل از رجیستری."""
    deleted = store.delete(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"مدل «{model_id}» یافت نشد")
    return {"deleted": model_id}
'''

ROUTER_CAPABILITIES = r'''"""رجیستری قابلیت‌های AI فعال در این استقرار."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .. import avalai_client
from ..config import CAPABILITIES, ENABLED_ENGINES, settings
from ..engines import engine_catalog

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("")
def list_capabilities() -> dict[str, Any]:
    """فهرست قابلیت‌های فعال به تفکیک موتور."""
    grouped: dict[str, list[dict[str, str]]] = {}
    for code, capability in CAPABILITIES.items():
        grouped.setdefault(capability["engine"], []).append({"code": code, **capability})

    return {
        "total": len(CAPABILITIES),
        "enabled_engines": ENABLED_ENGINES,
        "by_engine": grouped,
        "catalog": engine_catalog(),
        "llm_enabled": avalai_client.is_enabled(),
        "company": settings.company_name,
    }


@router.get("/{code}")
def get_capability(code: str) -> dict[str, Any]:
    """جزئیات یک قابلیت."""
    capability = CAPABILITIES.get(code.upper())
    if not capability:
        return {
            "code": code.upper(),
            "enabled": False,
            "message": "این قابلیت در استقرار جاری فعال نیست.",
            "available_engines": ENABLED_ENGINES,
        }

    return {"code": code.upper(), "enabled": True, **capability}
'''

SMOKE_TEST = r'''"""آزمون دود سرویس AI — بدون نیاز به شبکه یا پایگاه داده."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import ENABLED_ENGINES
from app.data import sample
from app.main import app
from app.schemas import AiRequest

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["engines"], list)
    assert body["engines"] == ENABLED_ENGINES


def test_capabilities_registry() -> None:
    response = client.get("/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 0
    assert "catalog" in body


def test_forecast_with_sample_series() -> None:
    payload = AiRequest(
        capability="A1.3.4",
        engine="forecasting",
        series=sample.demand_series(36),
        horizon=6,
        options={"season_length": 12},
    )
    response = client.post("/ai/forecast", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["result"]["forecast"]) == 6
    assert body["metrics"]["samples"] == 36


def test_anomaly_detection_on_sensor_data() -> None:
    payload = AiRequest(features=sample.sensor_readings(120))
    response = client.post("/ai/anomaly", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["anomaly_count"] >= 1


def test_spc_chart() -> None:
    payload = AiRequest(features=sample.quality_samples(25), options={"lsl": 45.0, "usl": 55.0})
    response = client.post("/ai/spc", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["chart"] == "xbar_r"
    assert body["result"]["capability"]["cpk"] != 0


def test_reliability_weibull() -> None:
    payload = AiRequest(series=sample.downtime_minutes(30), options={"current_age": 60})
    response = client.post("/ai/reliability", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["weibull"]["shape_beta"] > 0
    assert 0 <= body["result"]["availability"] <= 1


def test_optimization_inventory() -> None:
    payload = AiRequest(features=sample.inventory_items(20))
    response = client.post("/ai/optimize", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["result"]["items"]) > 0


def test_optimization_scheduling() -> None:
    payload = AiRequest(features=sample.production_orders(18), options={"problem": "scheduling"})
    response = client.post("/ai/optimize", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["best_schedule"]["makespan"] > 0


def test_nlp_keywords() -> None:
    text = (
        "دستگاه تزریق پلاستیک شماره دو در شیفت شب دچار افت فشار هیدرولیک شد و "
        "تولید قطعات متوقف گردید. تیم نت قالب را بررسی کرد و نشتی روغن یافت."
    )
    payload = AiRequest(text=text, options={"task": "keywords", "top_n": 8})
    response = client.post("/ai/nlp", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["result"]["keywords"]) > 0


def test_simulation_capacity() -> None:
    payload = AiRequest(options={"scenario": "capacity", "runs": 200, "lines": 3})
    response = client.post("/ai/simulate", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["runs"] == 200


def test_vision_inspection() -> None:
    rows = [
        {"id": i, "roughness_ra": 0.8 + (i % 7) * 0.4, "gloss": 70 - (i % 5) * 8,
         "depth_mm": 0.1 + (i % 9) * 0.12, "area_mm2": 1.0 + i * 0.6,
         "delta_e": 1.0 + (i % 6) * 0.9, "length_mm": 0.5 + (i % 4),
         "aspect_ratio": 1.2 + (i % 3), "edge_deviation_mm": 0.05 * (i % 8)}
        for i in range(30)
    ]
    payload = AiRequest(features=rows)
    response = client.post("/ai/vision", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["inspected"] == 30


def test_mlops_drift() -> None:
    reference = sample.demand_series(48, base=1000.0, seed=5)
    drifted = [value * 1.45 + 40 for value in reference]
    payload = AiRequest(series=drifted, options={"task": "drift", "reference": reference})
    response = client.post("/ai/mlops", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["result"]["psi"] >= 0


def test_recommendation_content_based() -> None:
    rows = [
        {"id": f"ITEM-{i}", "price": 1000 * (i + 1), "weight": 2.5 * i,
         "volume": 0.4 * i + 1, "stock": 50 - i}
        for i in range(12)
    ]
    payload = AiRequest(features=rows, options={"mode": "content", "item_id": "ITEM-0", "top_n": 5})
    response = client.post("/ai/recommend", json=payload.model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_unknown_engine_returns_404() -> None:
    payload = AiRequest(engine="does_not_exist")
    response = client.post("/ai", json=payload.model_dump())
    assert response.status_code == 404


def test_fallback_on_empty_input() -> None:
    response = client.post("/ai/forecast", json=AiRequest(series=[]).model_dump())
    assert response.status_code == 200
    body = response.json()
    assert body["fallback"] is True
    assert body["explanation"]
'''

AI_README_TEMPLATE = """# سرویس هوش مصنوعی — @@app_name@@

میکروسرویس مستقل پایتون (FastAPI) که همه موتورهای هوش مصنوعی این استقرار را
اجرا می‌کند. لاراول از طریق `App\\Support\\AiServiceClient` با این سرویس حرف می‌زند.

## موتورهای فعال

@@engines_table@@

## قابلیت‌های ثبت‌شده

- تعداد نقاط AI فعال: **@@ai_count@@**
- رجیستری: `GET /capabilities`
- اجرای یک قابلیت: `POST /ai/capability/{code}`

## اجرای محلی

```bash
cd ai-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

مستندات تعاملی: `http://localhost:8001/docs`

## آزمون

```bash
pip install pytest
pytest tests -q
```

## اندپوینت‌ها

| مسیر | موتور | کاربرد |
|---|---|---|
| `POST /ai/forecast` | forecasting | پیش‌بینی تقاضا، مصرف، فروش و انرژی |
| `POST /ai/optimize` | optimization | نقطه سفارش، زمان‌بندی تولید، تخصیص منابع |
| `POST /ai/anomaly` | anomaly | تشخیص ناهنجاری سنسور، کیفیت و مالی |
| `POST /ai/reliability` | reliability | وایبول، MTBF، عمر باقی‌مانده، ریسک خرابی |
| `POST /ai/spc` | quality_spc | نمودار کنترل X-bar/R، قواعد نلسون، CpK |
| `POST /ai/vision` | computer_vision | بازرسی ظاهری و تشخیص عیب |
| `POST /ai/nlp` | nlp | کلیدواژه، شباهت، احساس، خلاصه (با AvalAI) |
| `POST /ai/recommend` | recommendation | کالای مشابه، قطعه یدکی، قواعد هم‌رخدادی |
| `POST /ai/classify` | classification | طبقه‌بندی جدولی و متنی |
| `POST /ai/simulate` | simulation | مونت‌کارلو ظرفیت، صف و ریسک برنامه |
| `POST /ai/mlops` | mlops | رانش داده (PSI)، رجیستری مدل، سیاست بازآموزی |
| `POST /models/train` | — | آموزش و ثبت مدل |
| `POST /models/{id}/predict` | — | پیش‌بینی با مدل ثبت‌شده |
| `GET /health` | — | سلامت سرویس |

## AvalAI

برای قابلیت‌های زبانی (خلاصه‌سازی، استخراج بند قرارداد، چت و طبقه‌بندی متنی)
کلید `AVALAI_API_KEY` را در `.env` تنظیم کنید. در نبود کلید، سرویس به‌صورت
خودکار از الگوریتم‌های داخلی (TF-IDF، واژه‌نامه احساس، خلاصه‌سازی استخراجی)
استفاده می‌کند و هیچ جریان کاری متوقف نمی‌شود.

## اصول طراحی

1. **هرگز متوقف نشو**: اگر سرویس یا مدل در دسترس نبود، پاسخ `fallback=true`
   با توضیح فارسی برگردانده می‌شود.
2. **توضیح‌پذیری**: هر پاسخ شامل `explanation` فارسی و `metrics` عددی است.
3. **پایش**: همه فراخوانی‌ها در `models/<id>/log.jsonl` ثبت می‌شوند.
4. **بدون GPU**: همه الگوریتم‌ها روی CPU معمولی اجرا می‌شوند.
"""


def generate_ai_service(
    package: Package,
    *,
    settings: dict[str, Any],
    ai_engines: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    context: dict[str, Any],
) -> None:
    """تولید کامل میکروسرویس پایتون."""
    common = {
        "app_name": context["app_name_fa"],
        "version": context["version"],
        "timezone": settings.get("timezone", "Asia/Tehran"),
        "laravel_url": settings.get("app_url", context["app_url"]),
        "avalai_key": settings.get("avalai_api_key", ""),
        "avalai_base_url": settings.get("avalai_base_url", "https://api.avalai.ir/v1"),
        "avalai_model": settings.get("avalai_model", "gpt-4o-mini"),
        "company_name": settings.get("company_name", context["slug"]),
        "currency": settings.get("currency", "IRR"),
        "employees_count": int(settings.get("employees_count", 150)),
        "production_lines": int(settings.get("production_lines", 3)),
        "shifts_per_day": int(settings.get("shifts_per_day", 2)),
        "engines_list": json.dumps([e["key"] for e in ai_engines], ensure_ascii=False),
        "capabilities_map": json.dumps(
            {
                point["code"]: {
                    "name": point["name"],
                    "engine": point["engine"],
                    "module": point["module_code"],
                    "endpoint": point["endpoint"],
                    "model_id": point["model_id"],
                    "feature_flag": point["feature_flag"],
                }
                for point in ai_points
            },
            ensure_ascii=False,
            indent=4,
        ),
    }

    package.add_rendered("ai-service/requirements.txt", REQUIREMENTS, area="ai-service", **common)
    package.add_rendered("ai-service/Dockerfile", DOCKERFILE, area="ai-service", **common)
    package.add_rendered("ai-service/.env.example", ENV_EXAMPLE, area="ai-service", **common)
    package.add_rendered("ai-service/.env", ENV_EXAMPLE, area="ai-service", **common)
    package.add_rendered("ai-service/app/config.py", CONFIG_PY, area="ai-service", **common)
    package.add("ai-service/app/__init__.py", '"""بسته سرویس هوش مصنوعی."""\n', area="ai-service")
    package.add("ai-service/app/schemas.py", SCHEMAS_PY, area="ai-service")
    package.add("ai-service/app/avalai_client.py", AVALAI_CLIENT_PY, area="ai-service")
    package.add("ai-service/app/main.py", render(MAIN_PY, **common), area="ai-service")

    package.add("ai-service/app/models/__init__.py", '"""لایه ذخیره‌سازی مدل‌ها."""\n', area="ai-service")
    package.add("ai-service/app/models/store.py", MODEL_STORE_PY, area="ai-service")
    package.add("ai-service/app/data/__init__.py", '"""داده نمونه برای آزمون."""\n', area="ai-service")
    package.add("ai-service/app/data/sample.py", SAMPLE_DATA_PY, area="ai-service")

    package.add("ai-service/app/engines/__init__.py", ENGINES_INIT, area="ai-service")
    package.add("ai-service/app/engines/base.py", ENGINE_BASE_PY, area="ai-service")
    package.add("ai-service/app/engines/forecasting.py", ENGINE_FORECASTING, area="ai-service")
    package.add("ai-service/app/engines/anomaly.py", ENGINE_ANOMALY, area="ai-service")
    package.add("ai-service/app/engines/quality_spc.py", ENGINE_QUALITY_SPC, area="ai-service")
    package.add("ai-service/app/engines/reliability.py", ENGINE_RELIABILITY, area="ai-service")
    package.add("ai-service/app/engines/optimization.py", ENGINE_OPTIMIZATION, area="ai-service")
    package.add("ai-service/app/engines/classification.py", ENGINE_CLASSIFICATION, area="ai-service")
    package.add("ai-service/app/engines/nlp.py", ENGINE_NLP, area="ai-service")
    package.add("ai-service/app/engines/recommendation.py", ENGINE_RECOMMENDATION, area="ai-service")
    package.add("ai-service/app/engines/computer_vision.py", ENGINE_CV, area="ai-service")
    package.add("ai-service/app/engines/simulation.py", ENGINE_SIMULATION, area="ai-service")
    package.add("ai-service/app/engines/mlops.py", ENGINE_MLOPS, area="ai-service")

    package.add("ai-service/app/routers/__init__.py", '"""روت‌های سرویس."""\n', area="ai-service")
    package.add("ai-service/app/routers/ai.py", ROUTER_AI, area="ai-service")
    package.add("ai-service/app/routers/models.py", ROUTER_MODELS, area="ai-service")
    package.add("ai-service/app/routers/capabilities.py", ROUTER_CAPABILITIES, area="ai-service")

    package.add("ai-service/tests/__init__.py", "", area="ai-service")
    package.add("ai-service/tests/test_smoke.py", SMOKE_TEST, area="ai-service")

    engines_table = "\n".join(
        f"| `{engine['key']}` | {engine['name_fa']} | `{engine['endpoint']}` | "
        f"{', '.join(engine['algorithms'][:3])} |"
        for engine in ai_engines
    )
    package.add_rendered(
        "ai-service/README-fa.md",
        AI_README_TEMPLATE,
        area="docs",
        ai_count=len(ai_points),
        engines_table=engines_table or "| — | موتوری فعال نیست | — | — |",
        **{k: v for k, v in common.items() if k not in ("engines_table", "ai_count")},
    )
