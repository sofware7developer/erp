"""مدل دامنه داده: موجودیت‌ها، ماژول‌ها و حل وابستگی‌ها."""

from .registry import (
    SYSTEM_MODULES,
    all_specs,
    coverage_report,
    resolve_modules,
    specs_for_modules,
    topological_order,
    validate_foreign_keys,
)

__all__ = [
    "SYSTEM_MODULES",
    "all_specs",
    "coverage_report",
    "resolve_modules",
    "specs_for_modules",
    "topological_order",
    "validate_foreign_keys",
]
