"""Sprint 16 Wave 1 — validator split. assets_validators.py preserves 2026-06-01 hotfixes (_detect_copy_day, _check_api_health). LARK_ALERTS_ENABLED env var gates side effects for unit tests.

4 gates for DMP 资产诊断 (dmp_scraper.py, data2.csv):
    a. validate_assets_data     — 7 fields (TOTAL + 6 AIPL) 完整
    b. validate_assets_total    — TOTAL ≥ 0
    c. check_date_sanity        — 格式 YYYY/MM/DD / YYYY-MM-DD
    d. check_business_smoothness — 环比 > 30% 告警

字段顺序（与 dmp_scraper.py:489 + front-end data.js 对齐）:
    TOTAL资产总量, Discover发现, Engage种草, Enthuse互动,
    Perform行动, Initial首购, Numerous复购, Keen至爱
"""
from __future__ import annotations

from datetime import datetime

# 2026-06-14 (P1-1): _strip_int 4 份重复 → core.validators 共享
from core.validators import _strip_int  # noqa: F401  保留旧名, 内部已替换


# ===========================================================================
# 字段定义（与 dmp_scraper.py:503-504 一致）
# ===========================================================================

ASSETS_FIELDS = (
    "TOTAL资产总量",
    "Discover发现",
    "Engage种草",
    "Enthuse互动",
    "Perform行动",
    "Initial首购",
    "Numerous复购",
    "Keen至爱",
)


# ===========================================================================
# 门禁 a: validate_assets_data — 7 字段完整性
# ===========================================================================

def validate_assets_data(row: dict) -> tuple[bool, str]:
    """校验资产诊断数据的 7 字段完整性。

    来源：dmp_scraper.py:484 append_to_csv + front-end data.js 期望格式。
    Args:
        row: dict 至少含 7 字段（TOTAL + 6 AIPL）
    Returns:
        (is_valid: bool, reason: str)
    """
    if not row:
        return False, "数据为空"
    missing = [f for f in ASSETS_FIELDS if f not in row]
    if missing:
        return False, f"缺少字段: {missing}"

    total = _strip_int(row.get("TOTAL资产总量", 0))
    if total <= 0:
        return False, f"TOTAL资产总量={total}，数据未刷新或异常"

    return True, "OK"


# ===========================================================================
# 门禁 b: validate_assets_total — TOTAL ≥ 0
# ===========================================================================

def validate_assets_total(row: dict) -> tuple[bool, str]:
    """TOTAL 资产总量 ≥ 0（防御性检查 — 防负数 / None）。"""
    if not row:
        return False, "数据为空"
    total = _strip_int(row.get("TOTAL资产总量", 0))
    if total < 0:
        return False, f"TOTAL 资产总量={total} 为负数，异常"
    return True, "OK"


# ===========================================================================
# 门禁 c: check_date_sanity — 日期格式
# ===========================================================================

def check_date_sanity(date_str: str) -> tuple[bool, str]:
    """日期格式校验（YYYY/MM/DD 或 YYYY-MM-DD）。

    复刻 core/sanity_check.py:161-188 check_date_sanity。
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
    """资产诊断环比校验：单日 TOTAL 涨跌 > threshold 视为业务异常。

    复刻 dmp_item_insight_scraper._check_business_smoothness (line 2298-2331)，
    适配 assets TOTAL 字段。
    """
    if not row or prev_row is None:
        return None

    current_total = _strip_int(row.get("TOTAL资产总量", 0))
    if current_total == 0:
        return None

    prev_total = _strip_int(prev_row.get("TOTAL资产总量", 0))
    if prev_total == 0:
        return None

    change_ratio = (current_total - prev_total) / prev_total
    if abs(change_ratio) > threshold:
        direction = "上涨" if change_ratio > 0 else "下跌"
        return (
            f"日期 {row.get('time', '?')} "
            f"TOTAL 从 {prev_total:,} {direction}到 {current_total:,} "
            f"({change_ratio * 100:+.1f}%)，超过 {threshold * 100:.0f}% 阈值"
        )
    return None
