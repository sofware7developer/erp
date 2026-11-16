# -*- coding: utf-8 -*-
"""مدل‌های Pydantic برای API پلتفرم سازنده."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Selection(BaseModel):
    """انتخاب کاربر در چهار سطح کاتالوگ."""

    sections: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    items: list[str] = Field(default_factory=list)
    ai_points: list[str] = Field(default_factory=list)
    mode: str = Field(default="custom", description="custom | all | none | preset")


class PhasePlan(BaseModel):
    """یک فاز استقرار (برای برنامه‌ریزی پیاده‌سازی تدریجی)."""

    order: int = 1
    title: str = "فاز ۱"
    description: str = ""
    duration_months: int = 3
    modules: list[str] = Field(default_factory=list)
    ai_points: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """پیکربندی کامل یک پروژه کارخانه."""

    id: str | None = None
    name: str = "پروژه ERP کارخانه"
    name_en: str = "Factory ERP Project"
    description: str = ""
    preset_key: str | None = None
    selection: Selection = Field(default_factory=Selection)
    settings: dict[str, Any] = Field(default_factory=dict)
    phases: list[PhasePlan] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResolveRequest(BaseModel):
    """درخواست حل وابستگی‌ها برای یک انتخاب."""

    selection: Selection = Field(default_factory=Selection)


class ResolveResult(BaseModel):
    selection: Selection
    resolved_modules: list[str]
    auto_added: list[str]
    reasons: dict[str, str]
    invalid: list[str]
    counts: dict[str, int]
    sections: list[dict[str, Any]]
    ai_engines: list[dict[str, Any]]
    estimated_tables: int
    estimated_files: int


class GenerateRequest(BaseModel):
    """درخواست تولید بسته استقرار."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    save_project: bool = True


class GenerateResult(BaseModel):
    package_id: str
    package_name: str
    output_dir: str
    zip_path: str
    zip_size_bytes: int
    file_count: int
    line_count: int
    created_at: datetime
    stats: dict[str, Any]
    tree: list[dict[str, Any]]
    manifest: dict[str, Any]
    notes: list[str]


class AdvisorRequest(BaseModel):
    """درخواست دستیار هوشمند انتخاب ماژول."""

    industry: str = "general_discrete"
    employees_count: int = 150
    shifts_per_day: int = 2
    production_lines: int = 3
    warehouses_count: int = 2
    goals: list[str] = Field(default_factory=list)
    budget_level: str = "medium"   # low | medium | high
    ai_appetite: str = "medium"     # low | medium | high
    note: str = ""


class AdvisorResult(BaseModel):
    recommended_modules: list[str]
    recommended_ai_points: list[str]
    rationale: list[dict[str, Any]]
    phases: list[PhasePlan]
    coverage: dict[str, int]
    llm_used: bool = False
    llm_note: str = ""


class ChatRequest(BaseModel):
    """گفت‌وگو با دستیار سازنده (در صورت فعال بودن AvalAI)."""

    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, str]] = Field(default_factory=list)


class ChatResult(BaseModel):
    answer: str
    llm_used: bool = False
    source: str = "heuristic"
