# -*- coding: utf-8 -*-
"""
ابزارهای نوشتن بسته خروجی
==========================
* کلاس `Package` برای جمع‌آوری فایل‌ها، آمارگیری و نوشتن روی دیسک + zip
* تابع `render` برای جای‌گذاری متغیرها با الگوی `@@name@@`
  (این الگو عمداً انتخاب شده تا با `{}` در PHP/JS و `{{ }}` در Blade تداخل نکند)
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

PLACEHOLDER = re.compile(r"@@([A-Za-z0-9_]+)@@")


def render(template: str, **values: Any) -> str:
    """جای‌گذاری `@@نام@@` با مقدار متناظر."""
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in values:
            return str(values[key])
        return match.group(0)

    return PLACEHOLDER.sub(replace, template)


def indent(text: str, prefix: str = "    ") -> str:
    """فرورفتگی همه خطوط غیرخالی."""
    return "\n".join(prefix + line if line.strip() else line for line in text.splitlines())


def php_value(value: Any) -> str:
    """تبدیل مقدار پایتون به معادل PHP برای فایل‌های config و seeder."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, dict):
        items = []
        for key, val in value.items():
            items.append(f"        {_php_key(key)} => {php_value(val)},")
        return "[\n" + "\n".join(items) + "\n    ]"
    if isinstance(value, (list, tuple)):
        items = [f"        {php_value(v)}," for v in value]
        return "[\n" + "\n".join(items) + "\n    ]"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def _php_key(key: Any) -> str:
    if isinstance(key, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"'{key}'"
    return php_value(key)


def php_array(data: Any, level: int = 0) -> str:
    """رندر آرایه PHP با فرورفتگی درست و بازگشتی (برای config و رجیستری‌ها)."""
    pad = "    " * level
    inner = "    " * (level + 1)

    if isinstance(data, dict):
        if not data:
            return "[]"
        lines = ["["]
        for key, value in data.items():
            lines.append(f"{inner}{_php_key(key)} => {php_array(value, level + 1)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    if isinstance(data, (list, tuple)):
        if not data:
            return "[]"
        if all(not isinstance(value, (dict, list, tuple)) for value in data):
            rendered = ", ".join(php_value(value) for value in data)
            if len(rendered) + len(pad) < 100:
                return f"[{rendered}]"
        lines = ["["]
        for value in data:
            lines.append(f"{inner}{php_array(value, level + 1)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    return php_value(data)


def php_array_literal(mapping: dict[str, Any], level: int = 2) -> str:
    """ساخت آرایه PHP با فرورفتگی مناسب."""
    pad = "    " * level
    lines = ["["]
    for key, value in mapping.items():
        rendered = php_value(value)
        if "\n" in rendered:
            rendered = rendered.replace("\n    ", "\n" + pad)
        lines.append(f"{pad}    {_php_key(key)} => {rendered},")
    lines.append(f"{pad}]")
    return "\n".join(lines)


def json_pretty(data: Any, indent_size: int = 2) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=indent_size)


@dataclass
class WrittenFile:
    path: str
    lines: int
    bytes: int
    area: str
    kind: str = "text"


@dataclass
class Package:
    """مجموعه فایل‌های بسته خروجی."""

    root: Path
    name: str
    files: dict[str, bytes] = field(default_factory=dict)
    meta: dict[str, WrittenFile] = field(default_factory=dict)
    area_of: dict[str, str] = field(default_factory=dict)

    # -- افزودن فایل -------------------------------------------------------- #
    def add(self, rel_path: str, content: str, area: str = "misc", *, executable: bool = False) -> None:
        rel_path = rel_path.strip("/")
        if not rel_path:
            raise ValueError("مسیر فایل خالی است")
        data = content.encode("utf-8")
        self.files[rel_path] = data
        self.area_of[rel_path] = area
        self.meta[rel_path] = WrittenFile(
            path=rel_path,
            lines=len(content.splitlines()),
            bytes=len(data),
            area=area,
        )
        if executable:
            self.executables.add(rel_path)

    def add_binary(self, rel_path: str, data: bytes, area: str = "assets") -> None:
        rel_path = rel_path.strip("/")
        self.files[rel_path] = data
        self.area_of[rel_path] = area
        self.meta[rel_path] = WrittenFile(
            path=rel_path, lines=0, bytes=len(data), area=area, kind="binary"
        )

    def add_rendered(self, rel_path: str, template: str, area: str = "misc", **values: Any) -> None:
        self.add(rel_path, render(template, **values), area=area)

    def add_many(self, items: Iterable[tuple[str, str]], area: str = "misc") -> None:
        for rel_path, content in items:
            self.add(rel_path, content, area=area)

    executables: set[str] = field(default_factory=set)

    # -- آمار -------------------------------------------------------------- #
    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def line_count(self) -> int:
        return sum(meta.lines for meta in self.meta.values())

    @property
    def byte_count(self) -> int:
        return sum(len(data) for data in self.files.values())

    def stats(self) -> dict[str, Any]:
        areas: dict[str, dict[str, int]] = {}
        kinds: dict[str, int] = {}
        for meta in self.meta.values():
            bucket = areas.setdefault(meta.area, {"files": 0, "lines": 0, "bytes": 0})
            bucket["files"] += 1
            bucket["lines"] += meta.lines
            bucket["bytes"] += meta.bytes
            extension = Path(meta.path).suffix.lstrip(".").lower() or "no-ext"
            kinds[extension] = kinds.get(extension, 0) + 1
        return {
            "files": self.file_count,
            "lines": self.line_count,
            "bytes": self.byte_count,
            "areas": areas,
            "extensions": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
        }

    # -- نوشتن روی دیسک ----------------------------------------------------- #
    def write(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        for rel_path, data in self.files.items():
            target = self.root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for rel_path in self.executables:
            target = self.root / rel_path
            try:
                target.chmod(0o755)
            except OSError:
                pass
        return self.root

    def tree(self, max_depth: int = 4) -> list[dict[str, Any]]:
        nodes: dict[str, Any] = {}
        for rel_path in sorted(self.files):
            parts = rel_path.split("/")
            current = ""
            for depth, part in enumerate(parts):
                current = f"{current}/{part}" if current else part
                if current not in nodes:
                    nodes[current] = {
                        "name": part,
                        "path": current,
                        "type": "dir" if depth < len(parts) - 1 else "file",
                    }
                    if depth < len(parts) - 1:
                        nodes[current]["children"] = []
                if depth == len(parts) - 1:
                    meta = self.meta.get(rel_path)
                    nodes[current]["lines"] = meta.lines if meta else 0
                    nodes[current]["size"] = meta.bytes if meta else 0
        # ساخت درخت
        roots: list[dict[str, Any]] = []
        for path, node in nodes.items():
            if "/" not in path:
                roots.append(node)
            else:
                parent = nodes[path.rsplit("/", 1)[0]]
                parent.setdefault("children", []).append(node)

        def sort_nodes(items: list[dict[str, Any]], depth: int = 0) -> list[dict[str, Any]]:
            items.sort(key=lambda n: (n["type"] != "dir", n["name"].lower()))
            for item in items:
                if not item.get("children"):
                    continue
                if depth < max_depth:
                    item["children"] = sort_nodes(item["children"], depth + 1)
                else:
                    item["children"] = [
                        {"name": f"… ({len(item['children'])} مورد)", "type": "more"}
                    ]
            return items

        return sort_nodes(roots)


def slugify(text: str, fallback: str = "erp") -> str:
    """ساخت اسلاگ معتبر از متن (پشتیبانی از ورودی فارسی با حذف کاراکترها)."""
    ascii_text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return ascii_text or fallback


def pascal(text: str, fallback: str = "Erp") -> str:
    parts = re.split(r"[^A-Za-z0-9]+", text)
    result = "".join(p[:1].upper() + p[1:] for p in parts if p)
    return result or fallback


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
