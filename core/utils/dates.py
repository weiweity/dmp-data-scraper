"""Wave 1 of scraper Sprint 16 refactor (v2 design, dual-voice reviewed).

Extracted from dmp_common.py in Sprint 16 Wave 1 refactor. Zero functional change.
"""

from datetime import datetime

# Config is the canonical owner of paths/IDs; account file path lives there.


# ============ 日期工具 ============
def parse_date(date_str):
    """解析多种格式的日期字符串"""
    if not date_str:
        return None
    formats = ['%Y/%m/%d', '%Y-%m-%d', '%Y%m%d', '%m/%d/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None


def format_date_for_csv(dt):
    """将datetime或date格式化为CSV用的日期字符串 (2026/05/21)

    2026-06-13 改造（ERR-20260613-003）：保留前导零 (YYYY/MM/DD)
    - 旧版去前导零 (YYYY/M/D) 看似"更简洁"，但导致字符串字典序 ≠ 时序
      例: '2026/5/9' > '2026/5/10' > '2026/5/19' > '2026/5/2' 字符串排序
      实际时序应是 5/2 < 5/9 < 5/10 < 5/19
    - 修复后字符串排序 = 时序，可直接 sorted()，不再依赖 parse_date round-trip
    - parse_date 同时支持 YYYY/M/D 和 YYYY/MM/DD 两种输入（strptime 宽松）

    Args:
        dt: datetime 或 date 对象

    Returns:
        str: 'YYYY/MM/DD' 格式
    """
    if isinstance(dt, datetime):
        return dt.strftime('%Y/%m/%d')
    from datetime import date as _date
    if isinstance(dt, _date):
        return dt.strftime('%Y/%m/%d')
    return str(dt)


def parse_date_for_sort(date_str):
    """解析日期字符串为可比较的 (year, month, day) 元组,用于排序。

    注: 原 dmp_common.py 中没有此函数(根据 caller_map.json "not_in_dmp_common"),
    但 dmp_item_insight_scraper.py:2171 sortcsv_by_date 自带一个同名实现。
    本次 Wave 1 不移动该函数(避免跨文件行为变更), 仅占位留作 Wave 2 候选。
    """
    dt = parse_date(date_str)
    if not dt:
        return None
    return (dt.year, dt.month, dt.day)


# ============ 标准化 + 数字解析 (从 dmp_common.py 复制, 跟历史行为一致) ============
def normalize_date_str(date_str):
    """标准化日期字符串，处理各种格式不一致 (2026/1/16 -> 2026/01/16)

    注: dmp_item_insight_scraper.py:653 调用此函数把不一致格式归一化。
    """
    if not date_str:
        return date_str
    dt = parse_date(date_str.strip())
    if dt:
        return format_date_for_csv(dt)
    return date_str.strip()


def parse_number(value):
    """解析数字字符串（去除逗号）"""
    if not value:
        return 0
    try:
        return int(str(value).replace(',', '').strip())
    except Exception:
        return 0
