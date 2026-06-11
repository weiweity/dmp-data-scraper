"""Tests for flow_validators (4 gates from dmp_flow_scraper.py + sanity_check.py).

对齐实际实现 API (subagent 写, Sprint 16 Wave 1):
  - validate_flow_data(row) -> (bool, str)
  - validate_xinzeng(row) -> (bool, str)
  - check_date_sanity(date_str) -> (bool, str)
  - check_business_smoothness(row, prev_row=None, threshold=0.30) -> str | None
"""
import pytest

from scraper.core.validators.flow_validators import (
    FLOW_FIELDS,
    check_business_smoothness,
    check_date_sanity,
    validate_flow_data,
    validate_xinzeng,
)


# 流转 row 字段 (跟 dmp_flow_scraper.py:597-600 + data.csv 一致)
def _row(date: str = "2026/6/10", crowd: str = "faxian",
         initial: int = 1000, zhuanfaxian: int = 100, zhuanzhongcao: int = 50,
         zhuanhudong: int = 20, zhuanxingdong: int = 10,
         zhuanshougou: int = 5, zhuanfugou: int = 2,
         zhuanzhiai: int = 1) -> dict:
    return {
        "date": date,
        "crowd": crowd,
        "initial": initial,
        "zhuanfaxian": zhuanfaxian,
        "zhuanzhongcao": zhuanzhongcao,
        "zhuanhudong": zhuanhudong,
        "zhuanxingdong": zhuanxingdong,
        "zhuanshougou": zhuanshougou,
        "zhuanfugou": zhuanfugou,
        "zhuanzhiai": zhuanzhiai,
    }


def test_validate_flow_data_happy() -> None:
    """validate_flow_data: 8 字段完整 + date + crowd → OK."""
    row = _row()
    is_valid, reason = validate_flow_data(row)
    assert is_valid is True, f"expected valid, got reason={reason!r}"


def test_validate_flow_data_missing_field() -> None:
    """validate_flow_data: 缺 zhuanfaxian → invalid."""
    row = _row()
    del row["zhuanfaxian"]
    is_valid, reason = validate_flow_data(row)
    assert is_valid is False
    assert "缺少字段" in reason or "zhuanfaxian" in reason


def test_validate_flow_data_empty_crowd() -> None:
    """validate_flow_data: crowd 空 → invalid."""
    row = _row(crowd="")
    is_valid, reason = validate_flow_data(row)
    assert is_valid is False
    assert "crowd" in reason


def test_validate_xinzeng_happy() -> None:
    """validate_xinzeng: statusId=0 DOM fallback 数据, 8 字段全 ≥ 0 → OK."""
    row = _row(crowd="xinzeng", initial=500, zhuanfaxian=100)
    is_valid, reason = validate_xinzeng(row)
    assert is_valid is True


def test_validate_xinzeng_negative_value() -> None:
    """validate_xinzeng: zhuanfaxian=-5 → invalid (人群数不能为负)."""
    row = _row(crowd="xinzeng", zhuanfaxian=-5)
    is_valid, reason = validate_xinzeng(row)
    assert is_valid is False
    assert "负" in reason or "-5" in reason


def test_validate_xinzeng_empty() -> None:
    """validate_xinzeng: row=None/空 → invalid."""
    is_valid, reason = validate_xinzeng(None)
    assert is_valid is False
    assert "为空" in reason


def test_check_date_sanity_happy() -> None:
    """check_date_sanity: '2026/6/10' → OK."""
    is_valid, reason = check_date_sanity("2026/6/10")
    assert is_valid is True


def test_check_date_sanity_bad_format() -> None:
    """check_date_sanity: '2026-13-99' (无效日期) → invalid."""
    is_valid, reason = check_date_sanity("2026-13-99")
    assert is_valid is False
    assert "不识别" in reason or "格式" in reason


def test_check_business_smoothness_happy() -> None:
    """check_business_smoothness: 5% 涨 → None (无报警)."""
    today = _row(date="2026/6/11", initial=1050, crowd="faxian")
    prev = _row(date="2026/6/10", initial=1000, crowd="faxian")
    result = check_business_smoothness(today, prev)
    assert result is None


def test_check_business_smoothness_huge_change() -> None:
    """check_business_smoothness: 4x 涨 → 返回 warning 字符串."""
    today = _row(date="2026/6/11", initial=400, crowd="faxian")
    prev = _row(date="2026/6/10", initial=100, crowd="faxian")
    result = check_business_smoothness(today, prev)
    assert result is not None
    assert "超过" in result or "30%" in result or "上涨" in result


def test_check_business_smoothness_no_prev() -> None:
    """check_business_smoothness: prev_row=None → None."""
    today = _row(initial=400)
    result = check_business_smoothness(today, None)
    assert result is None
