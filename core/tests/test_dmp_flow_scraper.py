"""Tests for dmp_flow_scraper.py helpers (Gate 4 残缺检测 + int parser).

Gate 4 设计: 检测 initial > 0 但非零流转列 ≤ 1 (只有 self 或全 0) 的残缺数据,
用于兜底 DMP transfer API 在 6/13+ 只返回 self 1 item 的情况.
"""

from core.dmp_flow_scraper import (
    _FLOW_TRANSFER_FIELDS,
    _check_partial_flow_rows,
    _to_int,
    is_flow_data_stale,
)

# ========== _to_int ==========

def test_to_int_basic() -> None:
    """_to_int: 普通数字字符串."""
    assert _to_int("123") == 123


def test_to_int_with_comma() -> None:
    """_to_int: 千分位逗号 (CSV 字符串常见格式)."""
    assert _to_int("1,234") == 1234
    assert _to_int("11,084,794") == 11084794


def test_to_int_empty_returns_zero() -> None:
    """_to_int: 空字符串 / None / 空白 → 0."""
    assert _to_int("") == 0
    assert _to_int("  ") == 0
    assert _to_int(None) == 0


def test_to_int_int_passthrough() -> None:
    """_to_int: int 直接返回."""
    assert _to_int(42) == 42
    assert _to_int(0) == 0


def test_to_int_negative() -> None:
    """_to_int: 负数."""
    assert _to_int("-5") == -5


# ========== _check_partial_flow_rows (Gate 4) ==========

def _row(crowd: str = "faxian", initial: int = 0, **transfers) -> dict:
    """构造流转 row. 默认所有 zhuan* = 0, 用 **transfers 覆盖指定列.

    设计: 不设默认 zhuanfaxian 等, 避免在多 crowd 测试里"上一个 crowd 的 self
    残留成下一个 crowd 的 zhuanfaxian=非 0"这种假阳性.
    """
    base = {
        "date": "2026/6/14",
        "crowd": crowd,
        "initial": initial,
        "zhuanfaxian": 0,
        "zhuanzhongcao": 0,
        "zhuanhudong": 0,
        "zhuanxingdong": 0,
        "zhuanshougou": 0,
        "zhuanfugou": 0,
        "zhuanzhiai": 0,
    }
    base.update(transfers)
    return base


def test_gate4_pass_5_nonzero_cols() -> None:
    """Gate 4: 6/12 完整数据 (5 非零列) → pass (空列表)."""
    rows = [_row(
        initial=10332714,
        zhuanfaxian=9769587, zhuanzhongcao=562155, zhuanhudong=81,
        zhuanxingdong=616, zhuanshougou=275,
    )]
    assert _check_partial_flow_rows(rows) == []


def test_gate4_pass_3_nonzero_cols() -> None:
    """Gate 4: 3 非零列 (zhongcao→hudong/xingdong/shougou 合法 pattern) → pass."""
    rows = [_row(
        crowd="zhongcao",
        initial=43922093,
        zhuanzhongcao=43917495,  # self
        zhuanhudong=278, zhuanxingdong=2612, zhuanshougou=1708,
    )]
    assert _check_partial_flow_rows(rows) == []


def test_gate4_fail_only_self() -> None:
    """Gate 4: 6/14 模式 (只有 self 1 个非零列) → fail."""
    rows = [_row(initial=11000601, zhuanfaxian=11000601)]
    partial = _check_partial_flow_rows(rows)
    assert len(partial) == 1
    assert "faxian" in partial[0]
    assert "非零列=1" in partial[0]


def test_gate4_fail_all_zero_transfers() -> None:
    """Gate 4: initial > 0 但所有流转列都 0 (包括 self) → fail."""
    rows = [_row(initial=243399)]  # zhiai 模式: initial 有, self 都缺
    partial = _check_partial_flow_rows(rows)
    assert len(partial) == 1
    assert "faxian" in partial[0]
    assert "非零列=0" in partial[0]


def test_gate4_skip_xinzeng_initial_zero() -> None:
    """Gate 4: xinzeng 经常 initial=0, 不参与判断."""
    rows = [_row(crowd="xinzeng", initial=0)]
    assert _check_partial_flow_rows(rows) == []


def test_gate4_skip_xinzeng_even_with_initial() -> None:
    """Gate 4: xinzeng 即便 initial > 0 也不参与 (其 transfer 列特殊, 不在 zhuan* 列)."""
    rows = [_row(crowd="xinzeng", initial=4888470, zhuanfaxian=0)]
    assert _check_partial_flow_rows(rows) == []


def test_gate4_skip_initial_zero() -> None:
    """Gate 4: initial=0 的非 xinzeng 行不参与判断."""
    rows = [_row(initial=0, zhuanfaxian=0)]
    assert _check_partial_flow_rows(rows) == []


def test_gate4_report_multiple_crowds() -> None:
    """Gate 4: 多人群都残缺 → 报告所有 (而不是 first-match-return)."""
    rows = [
        _row(crowd="faxian", initial=11000601, zhuanfaxian=11000601),  # 只 self
        _row(crowd="zhongcao", initial=44682728, zhuanzhongcao=44682728),
        _row(crowd="hudong", initial=4007132, zhuanhudong=4007132),
        _row(crowd="xingdong", initial=2491715, zhuanxingdong=2491715),
        _row(crowd="shougou", initial=948690, zhuanshougou=948690),
        _row(crowd="fugou", initial=255944, zhuanfugou=255944),
        _row(crowd="zhiai", initial=243399),  # self 都缺, 非零列=0
        _row(crowd="xinzeng", initial=0),  # skip
    ]
    partial = _check_partial_flow_rows(rows)
    # 7 个非 xinzeng 人群, 都 ≤ 1 非零列 → 全部报告
    assert len(partial) == 7
    for crowd in ("faxian", "zhongcao", "hudong", "xingdong", "shougou", "fugou", "zhiai"):
        assert any(crowd in p for p in partial), f"missing {crowd} in {partial}"


def test_gate4_mixed_pass_and_fail() -> None:
    """Gate 4: 同一天有完整人群也有残缺人群 → 全部报告 (因为跳整日)."""
    rows = [
        _row(crowd="faxian", initial=11000601,
             zhuanfaxian=9769587, zhuanzhongcao=562155, zhuanhudong=81,
             zhuanxingdong=616, zhuanshougou=275),  # 5 非零 → pass
        _row(crowd="zhongcao", initial=44682728, zhuanzhongcao=44682728),  # 只 self → fail
        _row(crowd="hudong", initial=4007132, zhuanhudong=4007132),  # 只 self → fail
    ]
    partial = _check_partial_flow_rows(rows)
    # zhongcao + hudong fail
    assert len(partial) == 2
    assert any("zhongcao" in p for p in partial)
    assert any("hudong" in p for p in partial)
    assert not any(p.startswith("faxian") for p in partial)


def test_flow_transfer_fields_count() -> None:
    """_FLOW_TRANSFER_FIELDS: 应恰好 7 个 (faxian/zhongcao/hudong/xingdong/shougou/fugou/zhiai)."""
    assert len(_FLOW_TRANSFER_FIELDS) == 7
    assert "initial" not in _FLOW_TRANSFER_FIELDS
    assert "xinzeng" not in _FLOW_TRANSFER_FIELDS  # xinzeng 不在 zhuan* 列


# ========== is_flow_data_stale 全 0 边界 (防 6/7 全 0 误写入) ==========

def _all_zero_flow_data() -> dict:
    """构造一个所有 crowd initial=0 + 所有 transfer=0 的 flow_data (模拟 API 没加载)."""
    keys = ("initial", "faxian", "zhongcao", "hudong", "xingdong", "shougou", "fugou", "zhiai", "xinzeng")
    return {c: dict.fromkeys(keys, 0) for c in ("faxian", "zhongcao", "hudong", "xingdong", "shougou", "fugou", "zhiai", "xinzeng")}


def test_is_flow_data_stale_all_zero_returns_true() -> None:
    """is_flow_data_stale: 全部 initial=0 (API 没加载) → 必须 True (跳过写入).

    背景: 2026-06-16 22:10 run 抓 6/7, API 返回全 0, is_flow_data_stale 返回 False (旧逻辑),
    导致 6/7 8 行全 0 写入 data.csv. 这是 P0 bug.
    """
    assert is_flow_data_stale(_all_zero_flow_data()) is True


def test_is_flow_data_stale_xinzeng_only_returns_false() -> None:
    """is_flow_data_stale: 只有 xinzeng initial > 0 → False (有新增数据).

    反向 case: xinzeng initial > 0 视为有新增, 不算陈旧.
    """
    data = _all_zero_flow_data()
    data["xinzeng"]["initial"] = 100
    assert is_flow_data_stale(data) is False


def test_is_flow_data_stale_real_data_with_movement_returns_false() -> None:
    """is_flow_data_stale: 有初始值 + 有真实流转 → False (新鲜数据).

    反向 case: 模拟 6/15 抓到 faxian initial=11.9M + self=23.9M (有变化).
    """
    data = _all_zero_flow_data()
    data["faxian"]["initial"] = 11969651
    data["faxian"]["faxian"] = 23939302  # self != 0, 算真实流转
    assert is_flow_data_stale(data) is False


def test_is_flow_data_stale_self_only_stale_returns_true() -> None:
    """is_flow_data_stale: 有 initial 但 self=initial + 跨阶段全 0 (陈旧复制) → True.

    反向 case: 验证 Gate 3 之前的核心 case (DMP 复制日).
    """
    data = _all_zero_flow_data()
    data["faxian"]["initial"] = 11000601
    data["faxian"]["faxian"] = 11000601  # self == initial, 没跨阶段流转
    assert is_flow_data_stale(data) is True


# ========== click_xinzeng_tab (ERR-20260616-006) ==========

from unittest.mock import MagicMock

from core.dmp_flow_scraper import click_xinzeng_tab


def test_click_xinzeng_tab_returns_evaluate_result_verbatim() -> None:
    """click_xinzeng_tab: 返回值 = page.evaluate() 的结果 (透传)."""
    page = MagicMock()
    page.evaluate.return_value = {"ok": True, "top": 120, "left": 50, "text": "新增"}

    result = click_xinzeng_tab(page)

    assert result == {"ok": True, "top": 120, "left": 50, "text": "新增"}
    assert page.evaluate.call_count == 1


def test_click_xinzeng_tab_passes_js_to_evaluate() -> None:
    """click_xinzeng_tab: 调用 page.evaluate 时传入 JS 字符串 (非 callable)."""
    page = MagicMock()
    page.evaluate.return_value = {"ok": False}

    click_xinzeng_tab(page)

    # 验证传入 page.evaluate 的是 str (Playwright 接受 str 或 callable)
    js_arg = page.evaluate.call_args[0][0]
    assert isinstance(js_arg, str)
    assert len(js_arg) > 50  # 防止 JS 被误删成空


def test_click_xinzeng_tab_js_contains_required_matchers() -> None:
    """click_xinzeng_tab: JS 必须含 '新增' 文字匹配 + click() 调用 + 位置过滤.

    防退化: 未来 PR 简化 JS 时可能误删过滤条件, 导致点击错误元素或点击 '新增流转' 等.
    """
    page = MagicMock()
    page.evaluate.return_value = {"ok": False}

    click_xinzeng_tab(page)
    js = page.evaluate.call_args[0][0]

    # 必须含核心选择逻辑
    assert "'新增'" in js or '"新增"' in js, "JS 必须精确匹配 '新增' 文字"
    assert "el.click()" in js, "JS 必须调用 el.click()"
    assert "rect.left" in js, "JS 必须用 rect.left 做位置过滤"
    assert "getBoundingClientRect" in js, "JS 必须用 getBoundingClientRect 取位置"
    # 防退化: 位置过滤语义必须是"右侧跳过, 左侧执行 click"
    # 之前误写 `rect.left < 200 continue` (左侧跳过, 反逻辑), 已修
    assert ">= 200" in js, "JS 必须用 '>= 200' 跳过右侧元素 (左侧 tab 才 click)"


def test_click_xinzeng_tab_handles_ok_false() -> None:
    """click_xinzeng_tab: 找不到 '新增' tab 时返回 {ok: False}, 不抛异常."""
    page = MagicMock()
    page.evaluate.return_value = {"ok": False}

    result = click_xinzeng_tab(page)

    assert result == {"ok": False}
    # 不重试 / 不抛异常 (调用方负责降级到 page.goto)
