"""Tests for assets_validators (4 gates from dmp_scraper.py + sanity_check.py).

对齐实际实现 API (subagent 写, Sprint 16 Wave 1):
  - validate_assets_data(row) -> (bool, str)
  - validate_assets_total(row) -> (bool, str)
  - check_date_sanity(date_str) -> (bool, str)
  - check_business_smoothness(row, prev_row=None, threshold=0.30) -> str | None
"""
import pytest

from core.validators.assets_validators import (
    ASSETS_FIELDS,
    check_business_smoothness,
    check_date_sanity,
    validate_assets_data,
    validate_assets_total,
)


# 资产诊断 row 用中文 header (跟 dmp_scraper.py:503-504 + data2.csv 一致)
def _row(time: str = "2026/6/10", total: int = 100000,
         discover: int = 10000, engage: int = 50000,
         enthuse: int = 30000, perform: int = 5000,
         initial: int = 3000, numerous: int = 1000,
         keen: int = 1000) -> dict:
    return {
        "time": time,
        "TOTAL资产总量": total,
        "Discover发现": discover,
        "Engage种草": engage,
        "Enthuse互动": enthuse,
        "Perform行动": perform,
        "Initial首购": initial,
        "Numerous复购": numerous,
        "Keen至爱": keen,
    }


def test_validate_assets_data_happy() -> None:
    """validate_assets_data: 7 字段完整 + TOTAL>0 → OK."""
    row = _row(total=100000)
    is_valid, reason = validate_assets_data(row)
    assert is_valid is True, f"expected valid, got reason={reason!r}"


def test_validate_assets_data_missing_field() -> None:
    """validate_assets_data: 缺字段 → invalid."""
    row = _row()
    del row["Discover发现"]
    is_valid, reason = validate_assets_data(row)
    assert is_valid is False
    assert "缺少字段" in reason or "Discover" in reason


def test_validate_assets_data_zero_total() -> None:
    """validate_assets_data: TOTAL=0 → invalid (T+1 未刷新)."""
    row = _row(total=0)
    is_valid, reason = validate_assets_data(row)
    assert is_valid is False
    assert "TOTAL" in reason or "未刷新" in reason


def test_validate_assets_total_happy() -> None:
    """validate_assets_total: TOTAL>=0 → OK."""
    row = _row(total=100000)
    is_valid, reason = validate_assets_total(row)
    assert is_valid is True


def test_validate_assets_total_negative() -> None:
    """validate_assets_total: TOTAL=-100 → invalid (防御性检查)."""
    row = _row(total=-100)
    is_valid, reason = validate_assets_total(row)
    assert is_valid is False
    assert "负数" in reason or "-100" in reason


def test_check_date_sanity_happy() -> None:
    """check_date_sanity: 标准 '2026/6/10' 格式 → OK."""
    is_valid, reason = check_date_sanity("2026/6/10")
    assert is_valid is True


def test_check_date_sanity_dash_format() -> None:
    """check_date_sanity: '2026-06-10' 格式也接受."""
    is_valid, reason = check_date_sanity("2026-06-10")
    assert is_valid is True


def test_check_date_sanity_bad_format() -> None:
    """check_date_sanity: 'not-a-date' → invalid."""
    is_valid, reason = check_date_sanity("not-a-date")
    assert is_valid is False
    assert "不识别" in reason or "格式" in reason


def test_check_date_sanity_empty() -> None:
    """check_date_sanity: 空字符串 → invalid."""
    is_valid, reason = check_date_sanity("")
    assert is_valid is False
    assert "为空" in reason


def test_check_business_smoothness_happy() -> None:
    """check_business_smoothness: 4% 涨 → None (无报警)."""
    today = _row(time="2026/6/11", total=520)
    prev = _row(time="2026/6/10", total=500)
    result = check_business_smoothness(today, prev)
    assert result is None


def test_check_business_smoothness_huge_change() -> None:
    """check_business_smoothness: 200% 涨 → 返回 warning 字符串."""
    today = _row(time="2026/6/11", total=1500)
    prev = _row(time="2026/6/10", total=500)
    result = check_business_smoothness(today, prev)
    assert result is not None
    assert "超过" in result or "30%" in result or "上涨" in result


def test_check_business_smoothness_no_prev() -> None:
    """check_business_smoothness: prev_row=None → None (跳过)."""
    today = _row(total=1500)
    result = check_business_smoothness(today, None)
    assert result is None
