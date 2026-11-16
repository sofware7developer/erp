"""لایه هوش مصنوعی پلتفرم سازنده (رجیستری موتورها، دستیار انتخاب، کلاینت AvalAI)."""

from .advisor import advise, build_phases, recommend_modules
from .llm import chat, is_configured
from .registry import ENGINES, capability_catalog, engine_summary

__all__ = [
    "ENGINES", "advise", "build_phases", "capability_catalog", "chat",
    "engine_summary", "is_configured", "recommend_modules",
]
