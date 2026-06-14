"""Tests for anti_detect.apply_anti_detect.

补测试覆盖 (P1 技术债):
  - apply_anti_detect(page, extra_headers=None) -> dict

测试场景:
  1. 正常调用返回 headers dict
  2. extra_headers 合并到默认 headers
  3. CDP 调用失败不影响返回 headers

Mock 对象:
  - core.anti_detect.inject_stealth_scripts (无返回值)
  - core.anti_detect.get_random_headers (返回 dict)
  - page.context.new_cdp_session (mock CDP session)
"""
from unittest.mock import MagicMock, patch

from core.anti_detect import apply_anti_detect


# ===== 便捷函数: apply_anti_detect =====
@patch("core.anti_detect.get_random_headers")
@patch("core.anti_detect.inject_stealth_scripts")
def test_apply_anti_detect_happy(mock_inject: MagicMock, mock_get_headers: MagicMock) -> None:
    """正常调用: 返回 headers dict, 调用 inject_stealth_scripts."""
    mock_get_headers.return_value = {"User-Agent": "test", "Accept": "text/html"}
    mock_page = MagicMock()
    mock_cdp = MagicMock()
    mock_page.context.new_cdp_session.return_value = mock_cdp

    result = apply_anti_detect(mock_page)

    # 验证返回 headers
    assert isinstance(result, dict)
    assert "User-Agent" in result
    assert "Accept" in result

    # 验证调用了 inject_stealth_scripts
    mock_inject.assert_called_once_with(mock_page)

    # 验证调用了 get_random_headers
    mock_get_headers.assert_called_once()

    # 验证 CDP session 创建和调用
    mock_page.context.new_cdp_session.assert_called_once_with(mock_page)
    mock_cdp.send.assert_called_once_with("Network.setExtraHTTPHeaders", {"headers": result})


@patch("core.anti_detect.get_random_headers")
@patch("core.anti_detect.inject_stealth_scripts")
def test_apply_anti_detect_with_extra_headers(mock_inject: MagicMock, mock_get_headers: MagicMock) -> None:
    """extra_headers 合并到默认 headers."""
    mock_get_headers.return_value = {"User-Agent": "test", "Accept": "text/html"}
    mock_page = MagicMock()
    mock_cdp = MagicMock()
    mock_page.context.new_cdp_session.return_value = mock_cdp

    extra_headers = {"X-Custom": "value123", "Accept": "application/json"}
    result = apply_anti_detect(mock_page, extra_headers=extra_headers)

    # 验证 extra_headers 被合并
    assert result["X-Custom"] == "value123"
    # extra_headers 中的 Accept 应该覆盖默认的
    assert result["Accept"] == "application/json"
    # 默认 headers 保留
    assert result["User-Agent"] == "test"


@patch("core.anti_detect.get_random_headers")
@patch("core.anti_detect.inject_stealth_scripts")
def test_apply_anti_detect_cdp_failure(mock_inject: MagicMock, mock_get_headers: MagicMock) -> None:
    """CDP 调用失败不影响返回 headers."""
    mock_get_headers.return_value = {"User-Agent": "test", "Accept": "text/html"}
    mock_page = MagicMock()
    # 模拟 CDP 创建失败
    mock_page.context.new_cdp_session.side_effect = Exception("CDP not available")

    # 不应该抛出异常
    result = apply_anti_detect(mock_page)

    # 验证仍然返回 headers
    assert isinstance(result, dict)
    assert "User-Agent" in result
    assert "Accept" in result

    # 验证 inject_stealth_scripts 仍然被调用
    mock_inject.assert_called_once_with(mock_page)
