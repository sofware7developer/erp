# -*- coding: utf-8 -*-
"""
کلاینت AvalAI (سازگار با OpenAI Chat Completions)
==================================================
استفاده از این کلاینت کاملاً اختیاری است: اگر کلید API تنظیم نشده باشد یا
خطایی رخ دهد، سامانه به‌صورت خودکار به موتور قاعده‌محور داخلی بازمی‌گردد
و هرگز جریان کار کاربر متوقف نمی‌شود.

این همان الگویی است که در بسته خروجی نیز برای کارخانه تولید می‌شود
(کلاس `AvalAiClient` در لاراول و `avalai_client.py` در سرویس پایتون).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import urllib.error
import urllib.request

from ..config import AVALAI_API_KEY, AVALAI_BASE_URL, AVALAI_MODEL

logger = logging.getLogger("builder.ai")

DEFAULT_TIMEOUT = 45


@dataclass
class LlmResult:
    text: str
    used: bool
    note: str = ""
    raw: dict[str, Any] | None = None


def is_configured(api_key: str | None = None, base_url: str | None = None) -> bool:
    key = (api_key or AVALAI_API_KEY or "").strip()
    return bool(key)


def chat(
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 1500,
    json_mode: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
) -> LlmResult:
    """ارسال درخواست گفت‌وگو به AvalAI و بازگرداندن پاسخ."""
    key = (api_key or AVALAI_API_KEY or "").strip()
    if not key:
        return LlmResult("", False, "کلید AvalAI تنظیم نشده است؛ از موتور قاعده‌محور استفاده شد.")

    url = f"{(base_url or AVALAI_BASE_URL).rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": model or AVALAI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover - وابسته به شبکه
        detail = exc.read().decode("utf-8", "ignore")[:300]
        logger.warning("AvalAI HTTP %s: %s", exc.code, detail)
        return LlmResult("", False, f"خطای HTTP {exc.code} از AvalAI؛ از موتور قاعده‌محور استفاده شد.")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:  # pragma: no cover
        logger.warning("AvalAI error: %s", exc)
        return LlmResult("", False, f"خطای اتصال به AvalAI ({exc}); از موتور قاعده‌محور استفاده شد.")

    try:
        text = body["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return LlmResult("", False, "پاسخ AvalAI قالب معتبر نداشت.")
    return LlmResult(text.strip(), True, "پاسخ از AvalAI دریافت شد.", body)


def parse_json_answer(text: str) -> dict[str, Any] | list[Any] | None:
    """استخراج JSON از پاسخ مدل (تحمل بلوک‌های کد و متن اضافی)."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # تلاش برای یافتن اولین بلوک JSON معتبر
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start: end + 1])
            except json.JSONDecodeError:
                continue
    return None
