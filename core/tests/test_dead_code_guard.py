"""Dead code 守卫 — 防止 v0.1.16 风格的"未集成"误删复发 (ERR 历史背景: claude 自报"0 引用" 实际有 caller).

参照 v0.1.17 教训: 死代码清理必须先 `grep -rn` 实证 0 调用,再用 Python re 强删,而不是用 Edit 字节匹配 (Edit 报"成功"也可能没改, 见 LRN-20260608-001).

本测试做 2 件事:
1. 验 _ItemAssetCollector + _ITEM_STATUS_MAP 还能 import + 6 个 statusId 映射完整
2. 验死函数 0 调用方 (防止下次再把它们"复活")
"""

import re
import subprocess
from pathlib import Path

from core.dmp_item_insight_scraper import (
    _ITEM_STATUS_MAP,
    _ItemAssetCollector,
    validate_item_data,
)


# statusId → (字段名, 中文名) 6 个, 一个不能少
EXPECTED_STATUS_IDS = {0, 8001, 8002, 8003, 8004, 8005}


def test_item_status_map_has_all_six_entries() -> None:
    """6 个 statusId 都在映射表里 (资产/浅种草/深种草/首购/复购/连带)."""
    assert set(_ITEM_STATUS_MAP.keys()) == EXPECTED_STATUS_IDS, (
        f"statusId 映射缺失, 实际 {set(_ITEM_STATUS_MAP.keys())} "
        f"期望 {EXPECTED_STATUS_IDS}"
    )


def test_item_asset_collector_default_threshold() -> None:
    """collector 默认 min_valid_total=20000 (防 benchmark 数据污染)."""
    c = _ItemAssetCollector()
    assert c.min_valid_total == 20000
    assert c.assets == {}
    assert c.captured_count == 0


def test_item_asset_collector_explicit_threshold() -> None:
    """显式传 min_valid_total 优先 (Sprint 17 引入)."""
    c = _ItemAssetCollector(target_item_id="587051744204", min_valid_total=50000)
    assert c.min_valid_total == 50000
    assert c.target_item_id == "587051744204"


def test_validate_item_data_still_importable() -> None:
    """validate_item_data 必须在 L1701 还能 import (删除时不能误伤)."""
    # 留作"存在性"测试, 实际行为见 test_sanity_check.py
    assert callable(validate_item_data)


def test_no_external_callers_of_dead_functions() -> None:
    """死函数守卫: 防止 extract_item_data* 复活.

    fetch_item_data 主流程只调 _ItemAssetCollector 类 (L425),
    extract_item_data_by_dom / extract_item_data_by_api / extract_item_data 0 调用.
    """
    project_root = Path(__file__).parent.parent.parent  # core/tests/ → 项目根
    result = subprocess.run(
        [
            "grep", "-rn",
            r"extract_item_data(_by_api|_by_dom)?\b",
            str(project_root / "core"),
            "--include=*.py",
        ],
        capture_output=True,
        text=True,
    )
    # grep 输出含:
    # 1. 死函数自己的 def 行 (在 dmp_item_insight_scraper.py)
    # 2. 本测试文件的 import 行 (test_dead_code_guard.py)
    # 3. dmp_item_insight_scraper.py docstring / 注释里的提及
    # 排除 1 + 3: 真正的"调用方"应该出现在 def 之外
    lines = [
        ln for ln in result.stdout.splitlines()
        if "def extract_item_data" not in ln
        and "test_dead_code_guard.py" not in ln
    ]

    # 剩余行只允许是注释/docstring 提及, 不允许是调用
    # 真调用形如 `extract_item_data_by_dom(page)` 或 `from ... import extract_item_data`
    call_pattern = re.compile(r"extract_item_data(_by_api|_by_dom)?\s*\(")
    real_callers = [ln for ln in lines if call_pattern.search(ln)]

    assert not real_callers, (
        f"死函数被调用, 清理假设失效:\n"
        + "\n".join(real_callers)
        + "\n如果确实要复活, 请先更新 CLAUDE.md 路由 + CHANGELOG"
    )
