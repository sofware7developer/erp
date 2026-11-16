# -*- coding: utf-8 -*-
"""ذخیره‌سازی پروژه‌های پیکربندی (JSON محلی با قفل ساده)."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import PROJECTS_FILE
from .schemas import ProjectConfig

_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict[str, Any]:
    if not PROJECTS_FILE.exists():
        return {"projects": {}}
    try:
        data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "projects" not in data:
            return {"projects": {}}
        return data
    except (json.JSONDecodeError, OSError):
        return {"projects": {}}


def _save(data: dict[str, Any]) -> None:
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROJECTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(PROJECTS_FILE)


def list_projects() -> list[dict[str, Any]]:
    with _LOCK:
        data = _load()
    projects = list(data["projects"].values())
    projects.sort(key=lambda p: p.get("updated_at") or p.get("created_at") or "", reverse=True)
    return projects


def get_project(project_id: str) -> ProjectConfig | None:
    with _LOCK:
        data = _load()
    raw = data["projects"].get(project_id)
    if raw is None:
        return None
    return ProjectConfig(**raw)


def save_project(project: ProjectConfig) -> ProjectConfig:
    with _LOCK:
        data = _load()
        if not project.id:
            project.id = uuid.uuid4().hex[:12]
            project.created_at = datetime.fromisoformat(_now())
        project.updated_at = datetime.fromisoformat(_now())
        data["projects"][project.id] = json.loads(project.model_dump_json())
        _save(data)
    return project


def delete_project(project_id: str) -> bool:
    with _LOCK:
        data = _load()
        existed = data["projects"].pop(project_id, None) is not None
        if existed:
            _save(data)
    return existed
