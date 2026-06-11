"""Wave 1 of scraper Sprint 16 refactor (v2 design, dual-voice reviewed).

New in Sprint 16 Wave 1, replaces per-scraper T_OFFSET hardcoding.
"""

import os
from datetime import date, timedelta


def get_target_date(t_offset: int | None = None) -> date:
    """返回基于 T_OFFSET 环境变量的目标日期 (date 对象)。

    行为约定 (与 dmp_item_insight_scraper.py:257-275 现有硬编码 T+2 逻辑一致):
    - t_offset 为 None 时读取 os.environ.get('T_OFFSET', '1')
      默认 '1' 对应 dmp_item_insight_scraper 中"今天 - 1天"的历史基线;
      原 T+2 写法 (datetime.now() - timedelta(days=2)) 等价于 offset=2。
    - t_offset 为 int 时直接使用, 跳过环境变量读取 (便于测试和单点调用)。
    - 返回 date.today() - timedelta(days=offset), 即"今天往回数 offset 天"。

    Wave 2 计划:
      把 dmp_item_insight_scraper.py:257-275 的 hardcoded T+2 块替换为
      `target_date = get_target_date()`, 让 T_OFFSET 真正生效。
    """
    if t_offset is None:
        raw = os.environ.get('T_OFFSET', '1')
        try:
            t_offset = int(raw)
        except (TypeError, ValueError):
            t_offset = 1
    return date.today() - timedelta(days=t_offset)
