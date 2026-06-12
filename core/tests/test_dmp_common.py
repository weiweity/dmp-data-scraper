"""test_dmp_common.py — Sprint 19+ #141 治根 check_dmp_session 业务层 session 验证 (3 tests)

背景: 6/11 跑批 0/15 根因 — chrome_profile cookie HTTP 200 但业务码失效
      check_dmp_session 旧实现只检测 DOM 假阳性 (立即登录按钮 + page_title)
      新加 /api_2/login/loginuserinfo API 调用, 业务层 isLogin=false → 返 False
"""
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
    """API 调用异常 (timeout) → 返 False (graceful fallback)"""
    page = _mock_page(api_exc=Exception("API timeout"))
    assert check_dmp_session(page) is False
