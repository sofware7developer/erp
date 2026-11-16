# -*- coding: utf-8 -*-
"""رجیستری کاتالوگ: تجمیع ۲۲ بخش و تولید آمار و خروجی JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .dsl import CatalogIndex
from .sections.a_manufacturing import SECTION_A
from .sections.b_quality import SECTION_B
from .sections.c_maintenance import SECTION_C
from .sections.d_supply_chain import SECTION_D
from .sections.e_sales import SECTION_E
from .sections.f_finance import SECTION_F
from .sections.g_hrm import SECTION_G
from .sections.h_engineering import SECTION_H
from .sections.i_project import SECTION_I
from .sections.j_iot import SECTION_J
from .sections.k_ai_core import SECTION_K
from .sections.l_bi import SECTION_L
from .sections.m_hse import SECTION_M
from .sections.n_energy import SECTION_N
from .sections.o_grc import SECTION_O
from .sections.p_dms_bpm import SECTION_P
from .sections.q_fleet import SECTION_Q
from .sections.r_strategic import SECTION_R
from .sections.s_infrastructure import SECTION_S
from .sections.t_industries import SECTION_T
from .sections.u_contractors import SECTION_U
from .sections.v_performance import SECTION_V

ALL_SECTIONS: list[dict[str, Any]] = [
    SECTION_A, SECTION_B, SECTION_C, SECTION_D, SECTION_E, SECTION_F,
    SECTION_G, SECTION_H, SECTION_I, SECTION_J, SECTION_K, SECTION_L,
    SECTION_M, SECTION_N, SECTION_O, SECTION_P, SECTION_Q, SECTION_R,
    SECTION_S, SECTION_T, SECTION_U, SECTION_V,
]


@lru_cache(maxsize=1)
def catalog() -> list[dict[str, Any]]:
    """کاتالوگ کامل (کش‌شده)."""
    return ALL_SECTIONS


@lru_cache(maxsize=1)
def index() -> CatalogIndex:
    """ایندکس سریع کاتالوگ."""
    return CatalogIndex.build(catalog())


def stats() -> dict[str, Any]:
    """آمار کلان کاتالوگ."""
    idx = index()
    counts = idx.counts()
    per_section = [
        {
            "code": sec["code"],
            "name": sec["name"],
            "name_en": sec["name_en"],
            "color": sec["color"],
            "icon": sec["icon"],
            "modules": sec["module_count"],
            "groups": sum(m["group_count"] for m in sec["modules"]),
            "items": sec["item_count"],
            "ai_points": sec["ai_count"],
        }
        for sec in catalog()
    ]
    return {
        "totals": counts,
        "per_section": per_section,
        "version": "1.0.0",
    }


def ai_points() -> list[dict[str, Any]]:
    """فهرست همه نقاط هوش مصنوعی کاتالوگ."""
    idx = index()
    result = []
    for code, item in idx.ai_items.items():
        module_code = idx.module_of_item[code]
        mod = idx.modules[module_code]
        section_code = idx.section_of_module[module_code]
        sec = idx.sections[section_code]
        result.append(
            {
                "code": code,
                "name": item["name"],
                "module_code": module_code,
                "module_name": mod["name"],
                "section_code": section_code,
                "section_name": sec["name"],
                "deps": item["deps"],
            }
        )
    return result


def to_json(indent: int = 2) -> str:
    """خروجی JSON کاتالوگ کامل (برای مصرف فرانت‌اند و ژنراتور)."""
    return json.dumps(catalog(), ensure_ascii=False, indent=indent)


def search(query: str, limit: int = 60) -> list[dict[str, Any]]:
    """جست‌وجوی ساده و سریع در همه سطوح کاتالوگ."""
    idx = index()
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for code, blob in idx.search_blob.items():
        if q in blob:
            item = idx.items[code]
            module_code = idx.module_of_item[code]
            mod = idx.modules[module_code]
            group_code = code.rsplit(".", 1)[0]
            grp = idx.groups[group_code]
            hits.append(
                {
                    "code": code,
                    "name": item["name"],
                    "ai": item["ai"],
                    "group_code": group_code,
                    "group_name": grp["name"],
                    "module_code": module_code,
                    "module_name": mod["name"],
                    "section_code": idx.section_of_module[module_code],
                    "section_name": idx.sections[idx.section_of_module[module_code]]["name"],
                }
            )
        if len(hits) >= limit:
            break
    return hits
