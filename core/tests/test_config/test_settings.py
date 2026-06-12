"""Tests for config/settings loading (Sprint 16 Wave 1, v2 design).

实际 schema: yaml 是 list[str] (不是 list[dict]), Config.ITEM_IDS 是 15 个商品 ID 字符串列表。
Config.load_items() 从 config/items.yaml 加载, 返回 list[str]。
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config.settings import Config, CONFIG_ITEMS_YAML


def test_config_load_items_reads_yaml(tmp_path: Path) -> None:
    """Config.load_items() reads items.yaml and returns list[str] of item IDs."""
    yaml_path = tmp_path / "items.yaml"
    yaml_path.write_text(
        "items:\n"
        "  - '587051744204'\n"
        "  - '597655781410'\n"
        "  - '587053192746'\n",
        encoding='utf-8',
    )
    # 用 monkeypatch 改 CONFIG_ITEMS_YAML 模块常量
    with patch('core.config.settings.CONFIG_ITEMS_YAML', yaml_path):
        items = Config.load_items()
    assert isinstance(items, list)
    assert len(items) == 3
    assert items == ['587051744204', '597655781410', '587053192746']
    # 全部是 str, 不是 dict
    assert all(isinstance(item, str) for item in items)


def test_config_load_items_missing_file_raises(tmp_path: Path) -> None:
    """Config.load_items() raises FileNotFoundError if yaml does not exist."""
    missing = tmp_path / "does_not_exist.yaml"
    with patch('core.config.settings.CONFIG_ITEMS_YAML', missing):
        with pytest.raises(FileNotFoundError, match="items.yaml not found"):
            Config.load_items()


def test_config_load_items_invalid_schema_raises(tmp_path: Path) -> None:
    """Config.load_items() raises ValueError if yaml schema is invalid (not dict / no 'items' key)."""
    # 测试 1: 顶层是 list, 不是 dict
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("- '587051744204'\n", encoding='utf-8')
    with patch('core.config.settings.CONFIG_ITEMS_YAML', bad_yaml):
        with pytest.raises(ValueError, match="schema invalid"):
            Config.load_items()

    # 测试 2: 是 dict 但没有 'items' key
    bad_yaml2 = tmp_path / "bad2.yaml"
    bad_yaml2.write_text("foo: bar\n", encoding='utf-8')
    with patch('core.config.settings.CONFIG_ITEMS_YAML', bad_yaml2):
        with pytest.raises(ValueError, match="schema invalid"):
            Config.load_items()


def test_config_class_attributes_unchanged() -> None:
    """Config class 静态属性 (跟原 dmp_common.Config 完全一致, 零行为变更)。"""
    # 路径常量 — 绝对路径, 跟原 dmp_common.Config 等价
    # Sprint 5 #21 删内层 scraper/ 后, 路径结尾从 `/scraper/core` 改为 `/core`
    assert Config._SCRIPT_DIR.endswith('/core')
    assert Config.ASSETS_DATA_FILE.endswith('data2.csv')
    assert Config.FLOW_DATA_FILE.endswith('data.csv')
    assert Config.ITEM_DATA_FILE.endswith('data3.csv')
    assert Config.DEBUG_DIR.endswith('del')
    assert Config.USER_DATA_DIR.endswith('chrome_profile')
    assert Config.ACCOUNT_FILE.endswith('account.txt')

    # URL / SPM 完整 5 段 (跟原 dmp_common.Config 一致)
    assert Config.DMP_BASE_URL == "https://dmp.taobao.com/index_new.html"
    assert Config.DMP_SPM == "a2e3k.28338430.c0d46757f.de019e68a.1d1125eblwdosJ"
    assert Config.DMP_ROUTE_ASSETS == "#!/deeplink-new/assets-diagnose"
    assert Config.DMP_ROUTE_FLOW == "#!/deeplink/flow"
    assert Config.DMP_ROUTE_ITEM == "#!/items/item-insight"

    # 15 个商品 (含传明酸面膜 2026-04-21 新增)
    assert len(Config.ITEM_IDS) == 15
    assert "1010458880710" in Config.ITEM_IDS  # 传明酸面膜
