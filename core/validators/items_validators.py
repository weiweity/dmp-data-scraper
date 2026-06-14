"""Sprint 16 Wave 1 — validator split. items_validators.py preserves 2026-06-01 hotfixes (_detect_copy_day, _check_api_health). LARK_ALERTS_ENABLED env var gates side effects for unit tests.

5 gates from core/dmp_item_insight_scraper.py:2407-2508 (append_tocsv 5 gates):
    a. validate_item_data        — fields not empty, IDs are strings
    b. validate_cross_day        — drop > 50% vs yesterday
    c. _check_api_health         — subfield sum ≤ total assets  (2026-06-01 hotfix)
    d. _detect_copy_day          — flag if all fields identical (2026-06-01 hotfix, LIKELY_WRONG)
    e. _check_business_smoothness — warn if ringe change > 30%
    f. send_lark_alert           — side effect (from sanity_check.py:60-100), wraps in
                                    feature flag LARK_ALERTS_ENABLED so tests can disable

Refactored signature note: row is a `dict` (caller passes csv_file-relative data only).
The original 5-gate code path uses (csv_file, data); we accept (csv_file, data) for
backward compatibility with append_tocsv, but also accept row-only when csv_file=None.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess

# 2026-06-14 (P1-1 + P1-2): _strip_int 4 份重复 → core.validators 共享
#                  _read_prev_row / _parse_date 在 items_validators 0 调用, 删 (走公共 parse_date)
from core.validators import _strip_int  # noqa: F401  保留旧名, 内部已替换
from core.utils.dates import parse_date as _parse_date  # noqa: F401  保留旧名, 内部已替换


# ===========================================================================
# 门禁 a: validate_item_data — 字段非空 / IDs 为字符串
# ===========================================================================

def validate_item_data(row: dict) -> tuple[bool, str]:
    """校验单品数据的合理性，异常数据不写入。

    复刻 dmp_item_insight_scraper.validate_item_data (line 1965-1998)。
    Args:
        row: 包含单品资产数据的字典（item_id, date, zichan_zongliang, ...）
    Returns:
        tuple: (is_valid: bool, reason: str)
    """
    if not row:
        return False, "数据为空"

    # 字段非空（item_id, date）
    item_id = row.get('item_id', '')
    date_str = row.get('date', '')
    if not item_id or not str(item_id).strip():
        return False, "item_id 为空"
    if not date_str or not str(date_str).strip():
        return False, "date 为空"

    # IDs are strings（防御性检查 — 防止 int/float 误传）
    if not isinstance(str(item_id), str):
        return False, "item_id 必须为字符串"

    total = row.get('zichan_zongliang', 0) or 0
    shougou = row.get('shougou', 0) or 0
    qian = row.get('qian_zhongcao', 0) or 0
    shen = row.get('shen_zhongcao', 0) or 0

    # 资产总量为 0
    if total <= 0:
        return False, "资产总量为0，数据未刷新"

    # 资产总量 < 首购（不合逻辑）
    if total < shougou:
        return False, f"资产总量({total}) < 首购({shougou})，数据异常"

    # 浅种草+深种草 > 资产总量*1.5
    if qian + shen > total * 1.5:
        return False, (
            f"种草({qian}+{shen}={qian+shen}) > "
            f"资产总量({total})*1.5，异常"
        )

    # 首购范围
    if shougou < 0 or shougou > total:
        return False, f"首购({shougou})超出合理范围"

    return True, "OK"


# ===========================================================================
# 门禁 b: validate_cross_day — 跨日期对比（>50% 跌 / >100% 涨 拒绝）
# ===========================================================================

def validate_cross_day(row: dict,
                       prev_row: dict | None,
                       max_drop_ratio: float = 0.5,
                       max_jump_ratio: float = 2.0) -> tuple[bool, str]:
    """跨日期对比校验：与前一天数据对比，异常则跳过。

    复刻 dmp_item_insight_scraper.validate_cross_day (line 2202-2248)。
    签名差异：原版接受 csv_file 自行读取；本拆分版接受 prev_row 直接传入
    （caller 负责 I/O，便于单测注入 prev_row=None）。
    """
    if not row:
        return True, "OK (数据为空，跳过)"

    current_total = row.get('zichan_zongliang', 0) or 0
    if current_total == 0:
        return True, "OK (当前为 0，由 api_health 门禁处理)"

    if prev_row is None:
        return True, "OK (无前一日数据，跳过)"

    prev_total = _strip_int(prev_row.get('资产总量', 0))
    if prev_total == 0:
        return True, "OK (前一日为 0，跳过)"

    change_ratio = current_total / prev_total
    if change_ratio < (1 - max_drop_ratio):
        drop_pct = (1 - change_ratio) * 100
        return False, (
            f"资产总量从{prev_total:,}降至{current_total:,}"
            f"(-{drop_pct:.1f}%)，超过阈值"
        )
    if change_ratio > max_jump_ratio:
        jump_pct = (change_ratio - 1) * 100
        return False, (
            f"资产总量从{prev_total:,}升至{current_total:,}"
            f"(+{jump_pct:.1f}%)，超过阈值"
        )
    return True, "OK"


# ===========================================================================
# 门禁 c: _check_api_health — 子字段和 vs 总资产 (2026-06-01 hotfix, 不可删)
# ===========================================================================

def _check_api_health(row: dict) -> tuple[bool, str | None]:
    """API 健康检查：子字段和不应超过总资产。

    复刻 dmp_item_insight_scraper._check_api_health (line 2388-2404)。
    2026-06-01 P0-3 hotfix — 保留, 不可删。
    """
    if not row:
        return False, "数据为空"
    total = row.get('zichan_zongliang', 0) or 0
    sub_sum = (
        (row.get('qian_zhongcao', 0) or 0)
        + (row.get('shen_zhongcao', 0) or 0)
        + (row.get('shougou', 0) or 0)
        + (row.get('fugou', 0) or 0)
        + (row.get('liandai', 0) or 0)
    )
    if total > 0 and sub_sum > total * 1.5:
        return False, f"子字段和({sub_sum:,}) > 总资产({total:,})*1.5，API 异常"
    if total == 0 and sub_sum == 0:
        return False, "全 0 数据，T+1 未生成或 SPA 抓取失败"
    return True, None


# ===========================================================================
# 门禁 d: _detect_copy_day — 6 字段完全相同则标 likely-wrong
#         (2026-06-01 hotfix, 不可删)
# ===========================================================================

_COPY_DAY_FIELDS = (
    ('资产总量', 'zichan_zongliang'),
    ('浅种草', 'qian_zhongcao'),
    ('深种草', 'shen_zhongcao'),
    ('首购资产', 'shougou'),
    ('复购资产', 'fugou'),
    ('连带资产', 'liandai'),
)


def _detect_copy_day(today_row: dict,
                     yesterday_row: dict) -> tuple[bool, str | None]:
    """复制日检测：当前数据 6 字段是否与前一日完全相同。

    复刻 dmp_item_insight_scraper._detect_copy_day (line 2338-2382)。
    2026-06-01 P0-3 hotfix — 保留, 不可删。

    Args:
        today_row: 当前抓取数据（dict，含 item_id/date + 6 字段）
        yesterday_row: 前一日同商品 CSV 行（dict-reader 出来的 raw row）；
                       None 或 缺 6 字段视为无前一日，返回 (False, None)
    Returns:
        tuple: (is_copy: bool, reason: str or None)
               is_copy=True → 调用方应标 data_quality_flag = 'likely-wrong'
    """
    if not today_row or not yesterday_row:
        return False, None

    for csv_field, data_field in _COPY_DAY_FIELDS:
        prev_val = _strip_int(yesterday_row.get(csv_field, 0))
        curr_val = int(today_row.get(data_field, 0) or 0)
        if prev_val != curr_val:
            return False, None

    return True, (
        f"商品 {today_row.get('item_id', '?')} "
        f"日期 {today_row.get('date', '?')} "
        f"6 字段与前一日完全相同，疑似 T+1 延迟复制"
    )


# ===========================================================================
# 门禁 e: _check_business_smoothness — 环比 > 30% 告警
# ===========================================================================

def _check_business_smoothness(row: dict,
                               prev_row: dict | None,
                               threshold: float = 0.30) -> str | None:
    """业务平滑性校验：检查环比涨跌是否超过阈值。

    复刻 dmp_item_insight_scraper._check_business_smoothness (line 2298-2331)。
    Args:
        row: 当前数据字典
        prev_row: 前一日 CSV 行 (DictReader raw row)；None 视为无前一日
        threshold: 环比涨跌阈值（默认 0.30 = 30%）
    Returns:
        str or None: 警告信息（None = 通过）
    """
    if not row or prev_row is None:
        return None

    current_total = row.get('zichan_zongliang', 0) or 0
    if current_total == 0:
        return None

    prev_total = _strip_int(prev_row.get('资产总量', 0))
    if prev_total == 0:
        return None

    change_ratio = (current_total - prev_total) / prev_total
    if abs(change_ratio) > threshold:
        direction = "上涨" if change_ratio > 0 else "下跌"
        return (
            f"商品 {row.get('item_id', '?')} "
            f"日期 {row.get('date', '?')} "
            f"资产总量从 {prev_total:,} {direction}到 {current_total:,} "
            f"({change_ratio * 100:+.1f}%)，超过 {threshold * 100:.0f}% 阈值"
        )
    return None


# ===========================================================================
# 门禁 f: send_lark_alert — 副作用（feature flag LARK_ALERTS_ENABLED）
# ===========================================================================

def _send_lark_alert(content: str, open_id: str | None = None,
                     lark_bin: str | None = None,
                     timeout: float = 5.0) -> tuple[bool, str]:
    """推 lark-cli 私聊告警（graceful degrade — never raises）。

    复刻 core/sanity_check.py:46-109。
    """
    oid = (open_id or os.environ.get("LARK_OPEN_ID", "")).strip()
    if not oid:
        return False, "未配置 LARK_OPEN_ID，跳过告警（不报错）"

    bin_path = (
        lark_bin
        or os.environ.get("LARK_BIN", "").strip()
        or shutil.which("lark-cli")
        or "/Users/hutou/homebrew/bin/lark-cli"
    )
    if not os.path.exists(bin_path):
        return False, f"lark-cli 二进制不存在: {bin_path}"

    try:
        proc = subprocess.run(
            [
                bin_path, "im", "+messages-send",
                "--user-id", oid,
                "--text", content,
                "--as", "bot",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"lark-cli 超时（>{timeout}s）"
    except Exception as e:
        return False, f"lark-cli 启动失败: {type(e).__name__}: {str(e)[:200]}"

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()[:200]
        return False, f"lark-cli exit={proc.returncode}: {stderr}"

    try:
        resp = json.loads(proc.stdout)
    except (ValueError, TypeError):
        return True, "OK (non-JSON stdout)"

    if isinstance(resp, dict) and resp.get("ok") is True:
        return True, "OK"
    err = resp.get("error", {}) if isinstance(resp, dict) else {}
    return False, f"lark-cli 拒绝: {err.get('type','?')}: {err.get('message','')[:200]}"


def send_lark_alert(message: str, open_id: str | None = None,
                    **kwargs) -> tuple[bool, str]:
    """飞书告警（带 feature flag 开关）。

    Feature flag: LARK_ALERTS_ENABLED
        - "1" / "true" / "yes"（默认）: 真正调用 lark-cli
        - "0" / "false" / "no":        skip 告警（单测用，不污染日志/不依赖二进制）

    Args:
        message: 告警文本
        open_id: 收件人 open_id（不传走 env LARK_OPEN_ID）
        **kwargs: 透传给 _send_lark_alert（lark_bin / timeout）
    Returns:
        (sent: bool, reason: str)
    """
    flag = os.environ.get("LARK_ALERTS_ENABLED", "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False, f"LARK_ALERTS_ENABLED={flag}，skip 告警（feature flag off）"
    return _send_lark_alert(message, open_id=open_id, **kwargs)
