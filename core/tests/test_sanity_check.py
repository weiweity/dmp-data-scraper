"""Tests for sanity_check.check_item_data_validity.

补测试覆盖 (P1 技术债):
  - check_item_data_validity(data: dict | None) -> (bool, str)

测试场景:
  1. 正常数据通过 (happy path)
  2. data=None / data={} → False
  3. zichan_zongliang=0 → False
  4. zichan_zongliang < shougou → False
  5. qian + shen > zichan * 1.5 → False
  6. shougou < 0 or shougou > zichan → False
"""

from core.sanity_check import check_item_data_validity


# ===== 门禁 2: check_item_data_validity =====
def test_check_item_data_validity_happy() -> None:
    """正常数据: zichan=1000, shougou=100, qian=500, shen=300 → valid."""
    data = {
        "zichan_zongliang": 1000,
        "shougou": 100,
        "qian_zhongcao": 500,
        "shen_zhongcao": 300,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is True, f"expected valid, got reason={reason!r}"
    assert reason == "OK"


def test_check_item_data_validity_none() -> None:
    """data=None → invalid."""
    is_valid, reason = check_item_data_validity(None)
    assert is_valid is False
    assert "空" in reason


def test_check_item_data_validity_empty_dict() -> None:
    """data={} → invalid (zichan 默认为 0)."""
    is_valid, reason = check_item_data_validity({})
    assert is_valid is False
    assert "0" in reason or "空" in reason


def test_check_item_data_validity_zero_total() -> None:
    """zichan_zongliang=0 → invalid (数据未刷新)."""
    data = {
        "zichan_zongliang": 0,
        "shougou": 100,
        "qian_zhongcao": 500,
        "shen_zhongcao": 300,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is False
    assert "0" in reason


def test_check_item_data_validity_total_less_than_shougou() -> None:
    """zichan=100, shougou=200 → invalid (资产总量 < 首购)."""
    data = {
        "zichan_zongliang": 100,
        "shougou": 200,
        "qian_zhongcao": 50,
        "shen_zhongcao": 30,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is False
    assert "首购" in reason or "资产总量" in reason


def test_check_item_data_validity_zhongcao_exceeds_total() -> None:
    """qian=500 + shen=400=900 > zichan=500*1.5=750 → invalid (种草异常)."""
    data = {
        "zichan_zongliang": 500,
        "shougou": 100,
        "qian_zhongcao": 500,
        "shen_zhongcao": 400,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is False
    assert "种草" in reason


def test_check_item_data_validity_shougou_negative() -> None:
    """shougou=-10 → invalid (首购超出合理范围)."""
    data = {
        "zichan_zongliang": 1000,
        "shougou": -10,
        "qian_zhongcao": 500,
        "shen_zhongcao": 300,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is False
    assert "首购" in reason


def test_check_item_data_validity_shougou_exceeds_total() -> None:
    """shougou=1100, zichan=1000 → invalid (首购超出合理范围)."""
    data = {
        "zichan_zongliang": 1000,
        "shougou": 1100,
        "qian_zhongcao": 500,
        "shen_zhongcao": 300,
    }
    is_valid, reason = check_item_data_validity(data)
    assert is_valid is False
    assert "首购" in reason
