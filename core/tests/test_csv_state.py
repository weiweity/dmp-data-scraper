"""test_csv_state.py — csv_state 工具测试 (2026-06-14 创建, ERR-20260613-004 根治)

背景: 我反复犯"用 sorted(dates.keys()) 看 Latest"导致 YYYY/M/D 字典序 ≠ 时序错误.
csv_state.py 强制 parse_date → date 对象后 min/max, 杜绝此类错误.

测试:
  1. get_state 用 date 对象 (不是字符串)
  2. min/max 不受 lexical sort 误导 (5/9 < 5/10 在字符串是 False, 在 date 对象是 True)
  3. 范围缺失检测准确
  4. CLI 用法
"""
import csv
import tempfile
from datetime import date
from pathlib import Path

import pytest

from core.utils.csv_state import CSVState, get_missing_dates_in_range, get_state, print_state


def _write_csv(tmp_path: Path, rows: list) -> Path:
    """写测试用 CSV, 故意混合 YYYY/M/D 和 YYYY/MM/DD 格式 (测 parse_date 鲁棒性)"""
    p = tmp_path / "test_data3.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "时间", "资产总量"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return p


def test_get_state_min_max_uses_date_objects_not_strings(tmp_path: Path) -> None:
    """核心测试: 即使 CSV 含 YYYY/M/D 和 YYYY/MM/DD 混合, get_state 仍用 date 对象 min/max.

    5 个日期故意排序乱: 5/1, 5/9, 5/10, 5/30, 5/31
    字符串 min: '2026/5/1' < '2026/5/10' < ... (字典序 OK 因为都是 YYYY/M/D 同格式)
    字符串 max: '2026/5/9' (因为 '9' > '3' > '1' > '10'... 等等 '2026/5/9' 字符串是末尾)

    实际: YYYY/M/D 字符串 min='2026/5/1', max='2026/5/9' (字典序错乱)
    期望: date 对象 min=5/1, max=5/31 (时序正确)
    """
    p = _write_csv(tmp_path, [
        {"ID": "1", "时间": "2026/5/1", "资产总量": "100"},
        {"ID": "1", "时间": "2026/5/9", "资产总量": "100"},
        {"ID": "1", "时间": "2026/5/10", "资产总量": "100"},
        {"ID": "1", "时间": "2026/5/30", "资产总量": "100"},
        {"ID": "1", "时间": "2026/5/31", "资产总量": "100"},
    ])

    state = get_state(str(p))

    assert state.earliest_date == date(2026, 5, 1), f"earliest 应该是 5/1, 实际 {state.earliest_date}"
    assert state.latest_date == date(2026, 5, 31), f"latest 应该是 5/31, 实际 {state.latest_date} (不是 5/9 字符串错乱)"
    assert state.total_rows == 5
    assert state.unique_dates_count == 5


def test_get_state_handles_mixed_formats(tmp_path: Path) -> None:
    """测试 parse_date 同时支持 YYYY/M/D 和 YYYY/MM/DD (历史迁移数据混用场景)"""
    p = _write_csv(tmp_path, [
        {"ID": "1", "时间": "2026/5/1", "资产总量": "100"},   # 旧格式
        {"ID": "1", "时间": "2026/05/02", "资产总量": "100"}, # 新格式
        {"ID": "1", "时间": "2026/6/13", "资产总量": "100"},  # 旧格式 6 月
        {"ID": "1", "时间": "2026/06/14", "资产总量": "100"}, # 新格式 6 月
    ])

    state = get_state(str(p))

    assert state.earliest_date == date(2026, 5, 1)
    assert state.latest_date == date(2026, 6, 14)
    assert state.total_rows == 4


def test_get_state_mixed_format_lexical_sort_trap(tmp_path: Path) -> None:
    """核心防御测试: 5/1 到 5/31 全部有, 但如果用字符串 sorted 取 max 会得 '2026/5/9' (错).

    这正是 v0.1.14 之前我反复犯的错误心智模型.
    """
    p = _write_csv(tmp_path, [
        {"ID": str(i), "时间": f"2026/5/{d}", "资产总量": "100"}
        for i, d in enumerate([1, 9, 10, 19, 20, 30, 31])
    ])

    # 字符串 sorted 取 max 会得 '2026/5/9' (错)
    string_max = max([f"2026/5/{d}" for d in [1, 9, 10, 19, 20, 30, 31]])
    assert string_max == "2026/5/9", "验证字符串 max 错乱"
    assert string_max != "2026/5/31", "验证字符串 max 错乱 (这是 bug 来源)"

    # get_state 用 date 对象, 正确
    state = get_state(str(p))
    assert state.latest_date == date(2026, 5, 31), "get_state 用 date 对象, 正确识别 5/31 为最新"


def test_get_missing_dates_in_range(tmp_path: Path) -> None:
    """范围缺失检测: range 内完全没有数据的日期"""
    p = _write_csv(tmp_path, [
        {"ID": "1", "时间": "2026/05/01", "资产总量": "100"},
        {"ID": "1", "时间": "2026/05/03", "资产总量": "100"},
        {"ID": "1", "时间": "2026/05/05", "资产总量": "100"},
    ])

    missing = get_missing_dates_in_range(str(p), date(2026, 5, 1), date(2026, 5, 7))
    assert missing == [date(2026, 5, 2), date(2026, 5, 4), date(2026, 5, 6), date(2026, 5, 7)], \
        f"期望缺失 5/2, 5/4, 5/6, 5/7, 实际 {missing}"


def test_get_state_for_real_csv_data3() -> None:
    """集成测试: 跑 csv_state 在真实 data3.csv 上, 验证 latest 真的是 6/12 (不是 5/9 错乱)."""
    csv_path = Path(__file__).parent.parent / "data3.csv"
    if not csv_path.exists():
        pytest.skip("data3.csv not found (skip integration test)")

    state = get_state(str(csv_path))
    # 真实 data3.csv 在 6/14 跑完 Round 1-3 后, latest 应该是 6/12
    assert state.latest_date == date(2026, 6, 12), \
        f"data3.csv latest 应该是 2026/06/12, 实际 {state.latest_date}"
    # 5/1-6/12 共 43 天 × 15 商品 = 645 行 (允许一些历史数据偏差)
    assert state.total_rows >= 645, f"data3.csv 至少 645 行, 实际 {state.total_rows}"


def test_print_state_does_not_crash(tmp_path: Path, capsys) -> None:
    """print_state 打印可读状态 (烟雾测试)"""
    p = _write_csv(tmp_path, [
        {"ID": "1", "时间": "2026/05/01", "资产总量": "100"},
    ])

    print_state(str(p), date(2026, 5, 1), date(2026, 5, 7))

    captured = capsys.readouterr()
    assert "总行数: 1" in captured.out
    assert "最早日期" in captured.out
    assert "最新日期" in captured.out
    assert "2026/05/01" in captured.out
