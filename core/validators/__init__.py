"""Sprint 16 Wave 1 — validators package. Exports all gate functions for easy import.

items_validators.py  preserves 2026-06-01 hotfixes (_detect_copy_day, _check_api_health).
LARK_ALERTS_ENABLED env var gates side effects for unit tests.

Re-exports:
    # items (5 gates + lark alert)
    items_validators.validate_item_data
    items_validators.validate_cross_day
    items_validators._check_api_health         # 2026-06-01 hotfix, 不可删
    items_validators._detect_copy_day          # 2026-06-01 hotfix, 不可删
    items_validators._check_business_smoothness
    items_validators.send_lark_alert

    # assets (4 gates)
    assets_validators.validate_assets_data
    assets_validators.validate_assets_total
    assets_validators.check_date_sanity
    assets_validators.check_business_smoothness

    # flow (4 gates)
    flow_validators.validate_flow_data
    flow_validators.validate_xinzeng
    flow_validators.check_date_sanity
    flow_validators.check_business_smoothness
"""
from typing import Any

# ============ 共享 helper (2026-06-14 合并: 4 份 _strip_int 重复实现) ============
# 必须在 `from . import items_validators` 之前定义, 避免子模块反向 import __init__ 循环
def _strip_int(value: Any) -> int:
    """CSV 单元格 → int（去除逗号 / 引号 / 空白）。"""
    if value is None:
        return 0
    s = str(value).replace('"', "").replace(",", "").strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


from . import items_validators
from . import assets_validators
from . import flow_validators

__all__ = [
    # items
    "items_validators",
    "validate_item_data",
    "validate_cross_day",
    "_check_api_health",
    "_detect_copy_day",
    "_check_business_smoothness",
    "send_lark_alert",
    # assets
    "assets_validators",
    "validate_assets_data",
    "validate_assets_total",
    "check_date_sanity_assets",
    "check_business_smoothness_assets",
    # flow
    "flow_validators",
    "validate_flow_data",
    "validate_xinzeng",
    "check_date_sanity_flow",
    "check_business_smoothness_flow",
    # 共享 helper
    "_strip_int",
]

# module-level short names (re-exported from submodules)
validate_item_data = items_validators.validate_item_data
validate_cross_day = items_validators.validate_cross_day
_check_api_health = items_validators._check_api_health
_detect_copy_day = items_validators._detect_copy_day
_check_business_smoothness = items_validators._check_business_smoothness
send_lark_alert = items_validators.send_lark_alert

validate_assets_data = assets_validators.validate_assets_data
validate_assets_total = assets_validators.validate_assets_total
# assets: 4 gates 同名 (check_date_sanity / check_business_smoothness)
#  走 sub-module attribute access 避免与 flow 冲突
# 顶层只导出 assets_validators.check_date_sanity / flow_validators.check_date_sanity
check_date_sanity_assets = assets_validators.check_date_sanity
check_business_smoothness_assets = assets_validators.check_business_smoothness

validate_flow_data = flow_validators.validate_flow_data
validate_xinzeng = flow_validators.validate_xinzeng
check_date_sanity_flow = flow_validators.check_date_sanity
check_business_smoothness_flow = flow_validators.check_business_smoothness
