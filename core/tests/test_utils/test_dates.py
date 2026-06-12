"""Tests for date parsing/formatting utilities (Sprint 16 Wave 1).

注意: parse_date 用 datetime.strptime 实现, 返回 datetime (不是 date)。
原 dmp_common.py:99-110 行为完全保留 (零功能变更)。
"""
from datetime import date, datetime

import pytest

from core.utils.dates import format_date_for_csv, parse_date


def test_parse_date_slash_format_returns_datetime() -> None:
    """parse_date accepts '2026/4/3' and returns datetime(2026, 4, 3, 0, 0)."""
    result = parse_date("2026/4/3")
    assert result == datetime(2026, 4, 3, 0, 0)
    assert result.date() == date(2026, 4, 3)  # 也可转 date


def test_parse_date_dash_format_returns_datetime() -> None:
    """parse_date accepts '2026-04-03' and returns datetime(2026, 4, 3, 0, 0)."""
    result = parse_date("2026-04-03")
    assert result == datetime(2026, 4, 3, 0, 0)


def test_parse_date_compact_format_returns_datetime() -> None:
    """parse_date accepts '20260403' and returns datetime(2026, 4, 3, 0, 0)."""
    result = parse_date("20260403")
    assert result == datetime(2026, 4, 3, 0, 0)


def test_parse_date_empty_returns_none() -> None:
    """parse_date of empty/None returns None (跟原 dmp_common.py:99-110 行为一致)."""
    assert parse_date("") is None
    assert parse_date(None) is None


def test_parse_date_invalid_returns_none() -> None:
    """parse_date of unrecognized format returns None (回退到 None, 不抛错)."""
    assert parse_date("not a date") is None
    assert parse_date("2026/13/99") is None


def test_format_date_for_csv_strips_leading_zero() -> None:
    """format_date_for_csv strips leading zero: date(2026, 5, 21) -> '2026/5/21'."""
    assert format_date_for_csv(date(2026, 5, 21)) == "2026/5/21"


def test_format_date_for_csv_does_not_zero_pad() -> None:
    """format_date_for_csv must not produce '2026/05/21' for May 21."""
    formatted = format_date_for_csv(date(2026, 5, 21))
    assert formatted != "2026/05/21"
    assert "/05/" not in formatted


def test_format_date_for_csv_accepts_datetime() -> None:
    """format_date_for_csv also accepts datetime (跟原 dmp_common.py 行为一致)."""
    dt = datetime(2026, 5, 21, 14, 30, 0)
    assert format_date_for_csv(dt) == "2026/5/21"


def test_round_trip_parse_format_preserves_date() -> None:
    """parse(format(d)).date() == d for a sample date."""
    d = date(2026, 5, 21)
    assert parse_date(format_date_for_csv(d)).date() == d


def test_round_trip_multiple_dates() -> None:
    """Round-trip works for several dates including Jan and Dec."""
    for d in [date(2026, 1, 1), date(2026, 6, 11), date(2026, 12, 31)]:
        assert parse_date(format_date_for_csv(d)).date() == d
