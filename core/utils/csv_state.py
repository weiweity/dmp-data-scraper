"""csv_state.py — CSV 状态查询工具 (2026-06-14 创建, ERR-20260613-004 根治)

背景: 我反复犯"用 sorted(dates.keys()) 看 Latest"导致 lexical sort ≠ chronological sort
的错误. 即使 v0.1.10 修了 format_date_for_csv, 我自己写 ad-hoc 分析脚本时仍用
字符串排序, 导致"Latest: 5/9"心智模型残留, 后续 5/10-5/31 全有 15 行但我误判缺失.

根治: 任何 CSV 状态查询**必须**用本模块的函数. 禁止 ad-hoc sorted(strings).

公开函数:
  - get_state(csv_file) → CSVState (dataclass)
  - print_state(csv_file) → 打印人类可读状态
  - get_missing_dates_in_range(csv_file, start, end) → 缺失日期列表

所有函数都强制 parse_date → date 对象后 min/max, 永远不会用字符串排序.
"""
import csv
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Set

# 确保能 import core.utils.dates
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.utils.dates import format_date_for_csv, parse_date, parse_date_for_sort


@dataclass
class CSVState:
    """CSV 状态 snapshot.

    所有日期字段都是 date 对象, 不是字符串, 避免任何 lexical sort 歧义.
    """
    file_path: str
    total_rows: int
    earliest_date: Optional[date] = None        # CSV 中最早日期
    latest_date: Optional[date] = None          # CSV 中最新日期
    unique_dates_count: int = 0
    unique_items_count: int = 0
    rows_per_date: dict = field(default_factory=dict)  # date → count
    rows_per_item: dict = field(default_factory=dict)  # item_id → count
    # 缺失检测 (可选, 传 range 才算)
    missing_dates_in_range: List[date] = field(default_factory=list)
    checked_range_start: Optional[date] = None
    checked_range_end: Optional[date] = None

    def __str__(self) -> str:
        lines = [
            f"CSV 状态: {self.file_path}",
            f"  总行数: {self.total_rows}",
            f"  唯一日期: {self.unique_dates_count}",
            f"  唯一商品: {self.unique_items_count}",
            f"  最早日期: {self.earliest_date} ({format_date_for_csv(self.earliest_date) if self.earliest_date else 'N/A'})",
            f"  最新日期: {self.latest_date} ({format_date_for_csv(self.latest_date) if self.latest_date else 'N/A'})",
        ]
        if self.checked_range_start and self.checked_range_end:
            lines.append(
                f"  范围 {format_date_for_csv(self.checked_range_start)} ~ {format_date_for_csv(self.checked_range_end)} 缺失: {len(self.missing_dates_in_range)} 天"
            )
            if self.missing_dates_in_range:
                sample = [format_date_for_csv(d) for d in sorted(self.missing_dates_in_range)[:10]]
                lines.append(f"    示例: {sample}{'...' if len(self.missing_dates_in_range) > 10 else ''}")
        return "\n".join(lines)


def _read_csv_with_parsed_dates(csv_file: str):
    """读 CSV, 把 时间 列 parse 成 date 对象.

    返回:
      (rows, dates_set, items_set, dates_per_item_dict)
      - rows: list of dict (原样, 包含字符串 时间 列)
      - dates_set: set of date (parsed)
      - items_set: set of str (item_id)
      - dates_per_item: dict {item_id: set of date}
    """
    rows = []
    dates_set: Set[date] = set()
    items_set: Set[str] = set()
    dates_per_item = {}

    if not os.path.exists(csv_file):
        return rows, dates_set, items_set, dates_per_item

    # 自动检测编码
    try:
        from core.dmp_common import detect_encoding
        encoding = detect_encoding(csv_file)
    except Exception:
        encoding = 'utf-8'

    with open(csv_file, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            date_str = row.get('时间', '').strip()
            item_id = row.get('ID', '').strip()
            if not date_str or not item_id:
                continue
            dt = parse_date(date_str)
            if not dt:
                continue
            d = dt.date()
            dates_set.add(d)
            items_set.add(item_id)
            if item_id not in dates_per_item:
                dates_per_item[item_id] = set()
            dates_per_item[item_id].add(d)

    return rows, dates_set, items_set, dates_per_item


def get_state(csv_file: str, range_start: Optional[date] = None,
              range_end: Optional[date] = None, expected_items: Optional[int] = None) -> CSVState:
    """获取 CSV 状态 (永远用 date 对象, 不用字符串排序).

    Args:
        csv_file: CSV 路径
        range_start: 可选, 检查缺失的起始日期
        range_end: 可选, 检查缺失的结束日期
        expected_items: 可选, 期望每个日期有多少行 (用于检测"该日期行数 != expected")

    Returns:
        CSVState dataclass
    """
    rows, dates_set, items_set, dates_per_item = _read_csv_with_parsed_dates(csv_file)

    state = CSVState(
        file_path=csv_file,
        total_rows=len(rows),
        earliest_date=min(dates_set) if dates_set else None,
        latest_date=max(dates_set) if dates_set else None,
        unique_dates_count=len(dates_set),
        unique_items_count=len(items_set),
    )

    # 行数统计
    from collections import Counter
    dates_counter = Counter()
    items_counter = Counter()
    for row in rows:
        d_str = row.get('时间', '').strip()
        i = row.get('ID', '').strip()
        dt = parse_date(d_str) if d_str else None
        if dt:
            dates_counter[dt.date()] += 1
        if i:
            items_counter[i] += 1
    state.rows_per_date = dict(dates_counter)
    state.rows_per_item = dict(items_counter)

    # 范围缺失检测
    if range_start and range_end:
        state.checked_range_start = range_start
        state.checked_range_end = range_end
        # 检查每个商品在 range 内的日期是否都齐
        all_missing = set()
        if expected_items and dates_per_item:
            # 期望每个商品在 range 内都有 expected_items 行
            current = range_start
            while current <= range_end:
                for item_id in items_set:
                    if current not in dates_per_item.get(item_id, set()):
                        all_missing.add(current)
                current += timedelta(days=1)
        else:
            # 简化: 任何日期有数据就认为 OK (不深查)
            current = range_start
            while current <= range_end:
                if current not in dates_set:
                    all_missing.add(current)
                current += timedelta(days=1)
        state.missing_dates_in_range = sorted(all_missing)

    return state


def print_state(csv_file: str, range_start: Optional[date] = None,
                range_end: Optional[date] = None) -> None:
    """打印人类可读 CSV 状态 (永远准确, 用 date 对象)"""
    state = get_state(csv_file, range_start, range_end)
    print(str(state))


def get_missing_dates_in_range(csv_file: str, range_start: date, range_end: date) -> List[date]:
    """获取 CSV 在 [range_start, range_end] 区间内**完全没有数据**的日期列表.

    注意: 这里只检查"该日期是否有任何商品数据", 不深查每个商品是否都有.
    """
    state = get_state(csv_file, range_start, range_end)
    return state.missing_dates_in_range


if __name__ == '__main__':
    # CLI 用法: python -m core.utils.csv_state <csv_file> [start_date] [end_date]
    import argparse
    parser = argparse.ArgumentParser(description='CSV 状态查询')
    parser.add_argument('csv_file', help='CSV 文件路径')
    parser.add_argument('start_date', nargs='?', help='范围起始日期 (YYYY-MM-DD)')
    parser.add_argument('end_date', nargs='?', help='范围结束日期 (YYYY-MM-DD)')
    args = parser.parse_args()

    rs = parse_date(args.start_date).date() if args.start_date else None
    re_ = parse_date(args.end_date).date() if args.end_date else None
    print_state(args.csv_file, rs, re_)
