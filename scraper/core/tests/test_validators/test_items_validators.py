"""Tests for items_validators (5 gates from dmp_item_insight_scraper.py, + send_lark_alert).

对齐实际实现 API (subagent 写, Sprint 16 Wave 1):
  - validate_item_data(row) -> (bool, str)
  - validate_cross_day(row, prev_row=None, max_drop_ratio=0.5, max_jump_ratio=2.0) -> (bool, str)
  - _check_api_health(row) -> (bool, str|None)
  - _detect_copy_day(today_row, yesterday_row) -> (bool, str|None)
  - _check_business_smoothness(row, prev_row, threshold=0.30) -> str | None
  - send_lark_alert(message, open_id=None) -> (bool, str)
"""
import pytest

from scraper.core.validators.items_validators import (
    _check_api_health,
    _check_business_smoothness,
    _detect_copy_day,
    send_lark_alert,
    validate_cross_day,
    validate_item_data,
)


# 测试 fixture: 中文 CSV header + 拼音 data dict (跟实现 _COPY_DAY_FIELDS 一致)
def _row(item_id: str = "item_0", date: str = "2026/6/10",
         zichan_zongliang: int = 1000, qian_zhongcao: int = 500,
         shen_zhongcao: int = 300, shougou: int = 100,
         fugou: int = 50, liandai: int = 50) -> dict:
    return {
        "item_id": item_id,
        "date": date,
        "zichan_zongliang": zichan_zongliang,
        "qian_zhongcao": qian_zhongcao,
        "shen_zhongcao": shen_zhongcao,
        "shougou": shougou,
        "fugou": fugou,
        "liandai": liandai,
    }


def _csv_row(item_id: str = "item_0", date: str = "2026/6/9",
             zichan_zongliang: int = 1000) -> dict:
    """CSV DictReader row, 用中文 header (跟 _COPY_DAY_FIELDS / _check_business_smoothness 一致)"""
    return {
        "ID": item_id,
        "时间": date,
        "资产总量": zichan_zongliang,
        "浅种草": 500,
        "深种草": 300,
        "首购资产": 100,
        "复购资产": 50,
        "连带资产": 50,
    }


# ===== 门禁 a: validate_item_data =====
def test_validate_item_data_happy() -> None:
    """validate_item_data: 完整 row 字段非空 + zichan > 0 + shougou <= zichan."""
    row = _row(zichan_zongliang=1000, shougou=100)
    is_valid, reason = validate_item_data(row)
    assert is_valid is True, f"expected valid, got reason={reason!r}"


def test_validate_item_data_empty_fields() -> None:
    """validate_item_data: item_id 空 → invalid."""
    row = _row(item_id="", zichan_zongliang=1000)
    is_valid, reason = validate_item_data(row)
    assert is_valid is False
    assert "item_id" in reason


def test_validate_item_data_zero_total() -> None:
    """validate_item_data: zichan_zongliang=0 → invalid (T+1 未刷新)."""
    row = _row(zichan_zongliang=0)
    is_valid, reason = validate_item_data(row)
    assert is_valid is False
    assert "资产总量" in reason or "0" in reason


# ===== 门禁 b: validate_cross_day =====
def test_validate_cross_day_happy() -> None:
    """validate_cross_day: prev_row 5% 涨 → 通过."""
    today = _row(zichan_zongliang=1050)
    prev = _csv_row(zichan_zongliang=1000)  # 5% 涨
    is_valid, reason = validate_cross_day(today, prev)
    assert is_valid is True, f"expected valid, got reason={reason!r}"


def test_validate_cross_day_drop_over_50_percent() -> None:
    """validate_cross_day: prev_row 90% drop → invalid."""
    today = _row(zichan_zongliang=100)  # 跌 90%
    prev = _csv_row(zichan_zongliang=1000)
    is_valid, reason = validate_cross_day(today, prev)
    assert is_valid is False
    assert "降至" in reason or "drop" in reason.lower() or "跌" in reason


def test_validate_cross_day_no_prev_row() -> None:
    """validate_cross_day: prev_row=None → OK (跳过, 由 caller 决定)."""
    today = _row(zichan_zongliang=1000)
    is_valid, reason = validate_cross_day(today, None)
    assert is_valid is True
    assert "前一日" in reason or "跳过" in reason or "OK" in reason


# ===== 门禁 c: _check_api_health (2026-06-01 hotfix, 不可删) =====
def test_check_api_health_happy() -> None:
    """_check_api_health: 子字段和 < 总资产*1.5 → OK."""
    row = _row(zichan_zongliang=1000, qian_zhongcao=200, shen_zhongcao=100,
               shougou=50, fugou=30, liandai=20)  # sum=400 < 1500
    is_valid, reason = _check_api_health(row)
    assert is_valid is True


def test_check_api_health_subfield_sum_exceeds_total() -> None:
    """_check_api_health: 子字段和 > 总资产*1.5 → invalid (API 异常)."""
    row = _row(zichan_zongliang=100, qian_zhongcao=200, shen_zhongcao=200,
               shougou=200, fugou=200, liandai=200)  # sum=1000 > 150
    is_valid, reason = _check_api_health(row)
    assert is_valid is False
    assert "子字段" in reason or "API" in reason


# ===== 门禁 d: _detect_copy_day (2026-06-01 hotfix, 不可删) =====
def test_detect_copy_day_identical_2_days_likely_wrong() -> None:
    """_detect_copy_day: 6 字段完全相同 → is_copy=True (LIKELY_WRONG, T+1 延迟)."""
    today = _row(zichan_zongliang=1000, qian_zhongcao=500, shen_zhongcao=300,
                 shougou=100, fugou=50, liandai=50)
    yesterday = _csv_row(zichan_zongliang=1000)  # 6 字段全相同 (默认 _csv_row 也是 1000/500/300/100/50/50)
    is_copy, reason = _detect_copy_day(today, yesterday)
    assert is_copy is True
    assert reason is not None
    assert "相同" in reason or "LIKELY_WRONG" in reason.upper() or "复制" in reason


def test_detect_copy_day_different_returns_false() -> None:
    """_detect_copy_day: 6 字段不同 → is_copy=False."""
    today = _row(zichan_zongliang=1000)
    yesterday = _csv_row(zichan_zongliang=1100)  # 略涨
    is_copy, reason = _detect_copy_day(today, yesterday)
    assert is_copy is False
    assert reason is None


# ===== 门禁 e: _check_business_smoothness =====
def test_check_business_smoothness_happy() -> None:
    """_check_business_smoothness: 5% 涨 → None (无报警)."""
    today = _row(zichan_zongliang=1050)
    prev = _csv_row(zichan_zongliang=1000)
    result = _check_business_smoothness(today, prev)
    assert result is None


def test_check_business_smoothness_huge_change() -> None:
    """_check_business_smoothness: 100% 涨 → 返回 warning 字符串 (标 review)."""
    today = _row(zichan_zongliang=2000)
    prev = _csv_row(zichan_zongliang=1000)
    result = _check_business_smoothness(today, prev)
    assert result is not None
    assert "超过" in result or "30%" in result or "上涨" in result


def test_check_business_smoothness_no_prev() -> None:
    """_check_business_smoothness: prev_row=None → None (跳过)."""
    today = _row(zichan_zongliang=2000)
    result = _check_business_smoothness(today, None)
    assert result is None


# ===== 门禁 f: send_lark_alert (副作用, LARK_ALERTS_ENABLED feature flag) =====
def test_send_lark_alert_disabled_by_env(disable_lark_alerts) -> None:
    """send_lark_alert 在 LARK_ALERTS_ENABLED=0 下不真发飞书."""
    import os
    assert os.environ.get("LARK_ALERTS_ENABLED") == "0"
    sent, reason = send_lark_alert("test message (should not actually send)")
    assert sent is False
    assert "LARK_ALERTS_ENABLED" in reason or "skip" in reason.lower()
