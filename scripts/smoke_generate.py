# -*- coding: utf-8 -*-
"""دود-تست خط لوله تولید بسته (کوچک‌ترین انتخاب ممکن)."""
import json, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "builder" / "backend"))

from app.config import OUTPUT_DIR
from app.generator import generate_package
from app.schemas import ProjectConfig, Selection

modules = sys.argv[1:] or ["A1", "B1", "F9"]
project = ProjectConfig(
    id="smoke",
    name="ERP کارخانه نمونه",
    name_en="Sample Factory ERP",
    description="دود-تست موتور تولید",
    preset_key="general_discrete",
    selection=Selection(modules=modules),
    settings={"company_name": "کارخانه نمونه", "industry": "general_discrete", "db_driver": "mysql"},
)
t0 = time.time()
result = generate_package(project)
dt = time.time() - t0
print(f"package  : {result.package_id}")
print(f"duration : {dt:.1f}s")
print(f"files    : {result.file_count}")
print(f"lines    : {result.line_count}")
print(f"zip      : {Path(result.zip_path).name} ({result.zip_size_bytes/1024/1024:.1f} MB)")
print("areas    :", json.dumps({k: v["files"] for k, v in result.stats["areas"].items()}, ensure_ascii=False))
print("notes    :")
for n in result.notes:
    print("  -", n)
print("counters :", json.dumps(result.manifest["counters"], ensure_ascii=False))
