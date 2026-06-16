"""test_dmp_common.py — Sprint 19+ #141 治根 check_dmp_session 业务层 session 验证 (3 tests)

背景: 6/11 跑批 0/15 根因 — chrome_profile cookie HTTP 200 但业务码失效
      check_dmp_session 旧实现只检测 DOM 假阳性 (立即登录按钮 + page_title)
      新加 /api_2/login/loginuserinfo API 调用, 业务层 isLogin=false → 返 False
"""
from datetime import date, datetime

from unittest.mock import MagicMock

from core.dmp_common import check_dmp_session


def _mock_page(is_login=None, api_exc=None):
    """构造 MagicMock page 对象, 跳过真实浏览器。

    is_login: True/False/None (None=不设 evaluate, 旧路径)
    api_exc: Exception 实例 (触发 api 异常分支)
    """
    page = MagicMock()
    page.goto = MagicMock(return_value=None)
    page.wait_for_timeout = MagicMock()
    page.query_selector_all = MagicMock(return_value=[])
    page.title = MagicMock(return_value="达摩盘")
    if api_exc is not None:
        page.evaluate = MagicMock(side_effect=api_exc)
    elif is_login is True:
        page.evaluate = MagicMock(return_value={
            'status': 200,
            'body': {'data': {'isLogin': True}}
        })
    elif is_login is False:
        page.evaluate = MagicMock(return_value={
            'status': 200,
            'body': {'data': {'isLogin': False}}
        })
    return page


def test_check_dmp_session_valid_business_layer():
    """业务层 session 有效 (isLogin=true) → 返 True"""
    page = _mock_page(is_login=True)
    assert check_dmp_session(page) is True


def test_check_dmp_session_business_layer_invalid():
    """业务层 session 失效 (isLogin=false) → 返 False (强制 login_qianniu)"""
    page = _mock_page(is_login=False)
    assert check_dmp_session(page) is False


def test_check_dmp_session_api_timeout():
    """API 调用异常 (timeout) → 3 次重试后返 False (保守视为失效, 需重登)

    Sprint 19+ #141 旧设计: timeout → True (信任 cookie, 避免误判触发不必要的重登)
    2026-06-16 ERR-20260616-006 修复: timeout → False (保守, 宁可重登一次不浪费一天跑批).
    现实踩坑: 6/16 跑批 cookie 实际失效 (DMP 重定向 login.html), 3 次 fetch API 都失败,
    旧逻辑信任 cookie 让 scraper 浪费 90s × 9 天.
    """
    page = _mock_page(api_exc=Exception("API timeout"))
    assert check_dmp_session(page) is False
    # 验证重试 3 次（不再是 1 次）
    assert page.evaluate.call_count == 3


# ===== 2026-06-14: data['date'] 格式修复 (v0.1.14) =====
def test_dmp_item_insight_data_date_uses_format_date_for_csv() -> None:
    """dmp_item_insight_scraper.fetch_item_data 写入 data['date'] 必须用 format_date_for_csv (YYYY/MM/DD).

    背景: 6/14 跑批 6/1-6/12 共 180 行写入后, 发现 data['date'] 用 strftime('%-m/%-d')
    (YYYY/M/D), 绕过 v0.1.10 改的 format_date_for_csv. 造成字符串排序错乱 + 与迁移后 CSV 不一致.
    """
    from core.dmp_item_insight_scraper import fetch_item_data
    import inspect

    source = inspect.getsource(fetch_item_data)
    # 关键: 不应再出现 strftime('%-m/%-d')
    assert "strftime('%Y/%-m/%-d')" not in source, (
        "fetch_item_data 仍用 strftime('%-m/%-d') 产生 YYYY/M/D, 应改用 format_date_for_csv (YYYY/MM/DD)"
    )
    # 关键: 必须用 format_date_for_csv
    assert "format_date_for_csv(target_date)" in source, (
        "fetch_item_data 必须用 format_date_for_csv(target_date) 设置 data['date']"
    )


def test_format_date_for_csv_yyyymmdd() -> None:
    """format_date_for_csv 统一产生 YYYY/MM/DD (回归测试)"""
    from core.utils.dates import format_date_for_csv
    # 各种日期类型都应产生带前导零
    assert format_date_for_csv(date(2026, 6, 1)) == "2026/06/01"
    assert format_date_for_csv(date(2026, 12, 31)) == "2026/12/31"
    assert format_date_for_csv(date(2026, 1, 1)) == "2026/01/01"
    dt = datetime(2026, 6, 13, 14, 30, 0)
    assert format_date_for_csv(dt) == "2026/06/13"
