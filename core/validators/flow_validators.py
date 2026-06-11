"""Sprint 16 Wave 1 — validator split. flow_validators.py preserves 2026-06-01 hotfixes (_detect_copy_day, _check_api_health). LARK_ALERTS_ENABLED env var gates side effects for unit tests.

4 gates for DMP 流转数据 (dmp_flow_scraper.py, data.csv):
    a. validate_flow_data   — 8 fields (initial + 7 transform) 完整
    b. validate_xinzeng     — statusId=0 (新增人群) DOM fallback; all values ≥ 0
    c. check_date_sanity    — 格式 YYYY/MM/DD / YYYY-MM-DD
    d. check_business_smoothness — 环比 > 30% 告警

字段顺序（与 dmp_flow_scraper.py:597-600 一致）:
    date, crowd,
    initial, zhuanfaxian, zhuanzhongcao, zhuanhudong,
    zhuanxingdong, zhuanshougou, zhuanfugou, zhuanzhiai

statusId 映射（来自 dmp_flow_scraper.py:34-38）:
    2001=faxian, 2002=zhongcao, 2003=hudong, 2004=xingdong,
    2006=shougou, 2007=fugou, 2008=zhiai, 0=xinzeng
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta
from typing import Any


# ===========================================================================
# 字段定义（与 dmp_flow_scraper.py:597-600 一致）
# ===========================================================================

FLOW_FIELDS = (
    "date",
    "crowd",
    "initial",
    "zhuanfaxian",
    "zhuanzhongcao",
    "zhuanhudong",
    "zhuanxingdong",
    "zhuanshougou",
    "zhuanfugou",
    "zhuanzhiai",
)

# 7 个 transform 字段 (initial 之外的流转)
FLOW_TRANSFORM_FIELDS = (
    "initial",
    "zhuanfaxian",
    "zhuanzhongcao",
    "zhuanhudong",
    "zhuanxingdong",
    "zhuanshougou",
    "zhuanfugou",
    "zhuanzhiai",
)

# statusId=0 (xinzeng) 的特殊状态 — transfer API 不返回, 需 DOM 回退
XINZENG_STATUS_ID = 0
XINZENG_CROWD_KEY = "xinzeng"


def _strip_int(value: Any) -> int:
    if value is None:
        return 0
    s = str(value).replace('"', "").replace(",", "").strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


# ===========================================================================
# 门禁 a: validate_flow_data — 8 字段完整性
# ===========================================================================

def validate_flow_data(row: dict) -> tuple[bool, str]:
    """校验流转数据的 8 字段完整性。

    来源：dmp_flow_scraper.py:595-630 append_flow_to_csv。
    一条 flow 行 = (date, crowd, initial, 7 transform)。
    Args:
        row: dict 至少含 8 数值字段 + date + crowd
    Returns:
        (is_valid: bool, reason: str)
    """
    if not row:
        return False, "数据为空"
    missing = [f for f in FLOW_TRANSFORM_FIELDS if f not in row]
    if missing:
        return False, f"缺少字段: {missing}"
    if "date" not in row or not str(row.get("date", "")).strip():
        return False, "date 为空"
    if "crowd" not in row or not str(row.get("crowd", "")).strip():
        return False, "crowd 为空"
    return True, "OK"


# ===========================================================================
# 门禁 b: validate_xinzeng — statusId=0 (新增人群) DOM fallback
# ===========================================================================

def validate_xinzeng(row: dict) -> tuple[bool, str]:
    """校验 xinzeng (statusId=0) 新增人群流转数据。

    背景：dmp_flow_scraper.py:343-411 extract_xinzeng_flow_by_dom
    - transfer API 对 statusId=0 不返回流转数据
    - 必须 DOM fallback 提取
    - 提取后需校验所有值 ≥ 0 (人群数不能为负)

    Args:
        row: xinzeng 流转数据 dict（initial + 7 transform）
    Returns:
        (is_valid: bool, reason: str)
    """
    if not row:
        return False, "xinzeng 数据为空"

    # 全部 8 字段 ≥ 0
    negatives = []
    for f in FLOW_TRANSFORM_FIELDS:
        v = _strip_int(row.get(f, 0))
        if v < 0:
            negatives.append(f"{f}={v}")
    if negatives:
        return False, f"xinzeng 字段为负: {negatives}"

    # DOM fallback 标记（caller 写入时可识别数据源）
    source = row.get("_source", "")
    if source and source != "dom_fallback":
        # API 拦截一般不返回 xinzeng；如出现非 DOM 来源需 warn
        return True, f"OK (xinzeng source={source}，非 DOM fallback，建议 review)"

    return True, "OK"


# ===========================================================================
# 门禁 c: check_date_sanity — 日期格式
# ===========================================================================

def check_date_sanity(date_str: str) -> tuple[bool, str]:
    """日期格式校验（YYYY/MM/DD 或 YYYY-MM-DD）。

    复刻 scraper/core/sanity_check.py:161-188。
    """
    if not date_str:
        return False, "date_str 为空"
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            datetime.strptime(str(date_str).strip(), fmt)
            return True, "OK"
        except ValueError:
            continue
    return False, f"日期格式不识别: {date_str!r}（期望 YYYY/MM/DD 或 YYYY-MM-DD）"


# ===========================================================================
# 门禁 d: check_business_smoothness — 环比 > 30% 告警
# ===========================================================================

def check_business_smoothness(row: dict, prev_row: dict | None,
                              threshold: float = 0.30) -> str | None:
    """流转数据环比校验：initial 单日涨跌 > threshold 视为业务异常。

    复刻 dmp_item_insight_scraper._check_business_smoothness (line 2298-2331)，
    适配 flow initial 字段。
    """
    if not row or prev_row is None:
        return None

    current_initial = _strip_int(row.get("initial", 0))
    if current_initial == 0:
        return None

    prev_initial = _strip_int(prev_row.get("initial", 0))
    if prev_initial == 0:
        return None

    change_ratio = (current_initial - prev_initial) / prev_initial
    if abs(change_ratio) > threshold:
        direction = "上涨" if change_ratio > 0 else "下跌"
        return (
            f"人群 {row.get('crowd', '?')} 日期 {row.get('date', '?')} "
            f"initial 从 {prev_initial:,} {direction}到 {current_initial:,} "
            f"({change_ratio * 100:+.1f}%)，超过 {threshold * 100:.0f}% 阈值"
        )
    return None
