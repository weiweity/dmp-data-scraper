"""Tests for dmp_item_insight_scraper._check_spa_date_match.

覆盖 Date Sanity Check 中的日期格式比较逻辑 (v0.1.20 hotfix):
- T-1 + SPA "昨日" → 匹配
- T-2 + SPA "昨日" → 不匹配
- SPA 具体日期与 URL 目标一致 → 匹配
- SPA 具体日期与 URL 目标不一致 → 不匹配
"""
from datetime import date

from core.dmp_item_insight_scraper import _check_spa_date_match


def test_t_minus_1_yesterday_matches():
    """target_date = T-1, SPA 显示'昨日' → 匹配。"""
    today = date(2026, 6, 14)
    date_str = "2026-06-13"  # URL 格式 YYYY-MM-DD
    matches, actual, status = _check_spa_date_match(date_str, "昨日", today)
    assert matches is True
    assert actual == "2026/06/13"
    assert status == "refreshed"


def test_t_minus_2_yesterday_does_not_match():
    """target_date = T-2, SPA 显示'昨日'(T-1) → 不匹配。"""
    today = date(2026, 6, 14)
    date_str = "2026-06-12"
    matches, actual, status = _check_spa_date_match(date_str, "昨日", today)
    assert matches is False
    assert actual == "2026/06/13"
    assert status == "refreshed"


def test_specific_date_matches():
    """SPA 显示具体日期且与 target 一致 → 匹配。"""
    today = date(2026, 6, 14)
    date_str = "2026-06-11"
    matches, actual, status = _check_spa_date_match(date_str, "2026-06-11", today)
    assert matches is True
    assert actual == "2026/06/11"
    assert status == "matched"


def test_specific_date_mismatch():
    """SPA 显示具体日期但与 target 不一致 → 不匹配。"""
    today = date(2026, 6, 14)
    date_str = "2026-06-11"
    matches, actual, status = _check_spa_date_match(date_str, "2026-06-10", today)
    assert matches is False
    assert actual == "2026/06/10"
    assert status == "pending"


def test_unrecognized_text():
    """无法识别的 trigger 文本 → 不匹配。"""
    today = date(2026, 6, 14)
    matches, actual, status = _check_spa_date_match("2026-06-13", "近30天", today)
    assert matches is False
    assert actual is None
    assert status is None
