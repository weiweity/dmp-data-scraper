"""Tests for dmp_common.check_dmp_session (Sprint 19+ 重试改造).

补测试覆盖 (P1 技术债修复):
  - check_dmp_session(page, max_retries=3) -> bool

测试场景:
  1. isLogin=true 单次成功 → True
  2. isLogin=false → False
  3. API timeout 重试后 isLogin=true → True
  4. API 全部 timeout → 默认 True（信任 cookie）
  5. API 返回无 isLogin 字段 → 重试
  6. 页面有'立即登录'按钮 → False
  7. 页面 title 含'登录' → False
"""
from unittest.mock import MagicMock, patch


from core.dmp_common import check_dmp_session


# ===== 重试机制测试 =====
@patch("core.dmp_common.log")
def test_check_dmp_session_isLogin_true(mock_log) -> None:
    """isLogin=true 一次成功 → True."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        "status": 200,
        "body": {"data": {"isLogin": True}}
    }
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "达摩盘"

    result = check_dmp_session(mock_page)

    assert result is True
    assert mock_page.evaluate.call_count == 1


@patch("core.dmp_common.log")
def test_check_dmp_session_isLogin_false(mock_log) -> None:
    """isLogin=false → 立即 False（不重试）."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        "status": 200,
        "body": {"data": {"isLogin": False}}
    }

    result = check_dmp_session(mock_page)

    assert result is False
    assert mock_page.evaluate.call_count == 1  # 不重试


@patch("core.dmp_common.log")
def test_check_dmp_session_timeout_then_success(mock_log) -> None:
    """API timeout 2 次后第 3 次成功 → True（重试机制）."""
    mock_page = MagicMock()
    # 前 2 次抛异常，第 3 次成功
    mock_page.evaluate.side_effect = [
        Exception("API timeout"),
        Exception("API timeout"),
        {"status": 200, "body": {"data": {"isLogin": True}}},
    ]
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "达摩盘"

    result = check_dmp_session(mock_page)

    assert result is True
    assert mock_page.evaluate.call_count == 3


@patch("core.dmp_common.log")
def test_check_dmp_session_all_timeout_returns_true(mock_log) -> None:
    """3 次 API 都 timeout → 默认 True（信任 cookie 在）."""
    mock_page = MagicMock()
    mock_page.evaluate.side_effect = Exception("API timeout")
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "达摩盘"

    result = check_dmp_session(mock_page, max_retries=3)

    assert result is True  # 不再误判为失效
    assert mock_page.evaluate.call_count == 3


@patch("core.dmp_common.log")
def test_check_dmp_session_no_isLogin_field_retries(mock_log) -> None:
    """API 返回无 isLogin 字段 → 重试."""
    mock_page = MagicMock()
    mock_page.evaluate.side_effect = [
        {"status": 200, "body": {}},  # 无 data 字段
        {"status": 200, "body": {}},  # 无 data 字段
        {"status": 200, "body": {"data": {"isLogin": True}}},  # 成功
    ]
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "达摩盘"

    result = check_dmp_session(mock_page, max_retries=3)

    assert result is True
    assert mock_page.evaluate.call_count == 3


@patch("core.dmp_common.log")
def test_check_dmp_session_login_button_detected(mock_log) -> None:
    """页面有'立即登录'按钮 → False."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        "status": 200,
        "body": {"data": {"isLogin": True}}
    }
    # 模拟有"立即登录"按钮
    mock_page.query_selector_all.return_value = [MagicMock()]

    result = check_dmp_session(mock_page)

    assert result is False


@patch("core.dmp_common.log")
def test_check_dmp_session_login_in_title(mock_log) -> None:
    """页面 title 含'登录' → False."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        "status": 200,
        "body": {"data": {"isLogin": True}}
    }
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "请登录 - 达摩盘"

    result = check_dmp_session(mock_page)

    assert result is False


@patch("core.dmp_common.log")
def test_check_dmp_session_custom_max_retries(mock_log) -> None:
    """自定义 max_retries=5，5 次都 timeout → True."""
    mock_page = MagicMock()
    mock_page.evaluate.side_effect = Exception("timeout")
    mock_page.query_selector_all.return_value = []
    mock_page.title.return_value = "达摩盘"

    result = check_dmp_session(mock_page, max_retries=5)

    assert result is True
    assert mock_page.evaluate.call_count == 5
