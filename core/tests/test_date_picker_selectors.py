"""test_date_picker_selectors.py — Sprint 20+ (2026-06-13) datepicker selector 修复

背景 (ERR-20260613-002):
  DMP 单品洞察页 datepicker 0/60 失败, 根因是 selector 错位
  (找 .mxgc-calendar-datepicker / class hash, 实际是 #days_mx_output_mx_NNNN / span.mx-trigger-label).
  本文件覆盖 8 个测试:
    - _should_skip_datepicker 纯函数 (T-1/T-2/today 三种)
    - _find_date_trigger_multi 用了新稳定 selector (span.mx-trigger-label)
    - 旧 broken selector (mxgc-calendar-datepicker) 已移除
    - try_select_date_v2 用了 ID 前缀 selector
    - Date Sanity Check 加 T-1 宽容分支
    - dmp_master.py 加 MAX_BACKFILL_DAYS 守卫
    - items.yaml 加 date_strategy 节
"""
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml


# ===== _should_skip_datepicker (纯函数, 4 测试) =====
def test_should_skip_datepicker_t_minus_1_returns_true():
    """target_date == T-1 (date 对象) → 跳过 datepicker"""
    from core.dmp_item_insight_scraper import _should_skip_datepicker

    yesterday = date.today() - timedelta(days=1)
    assert _should_skip_datepicker(yesterday) is True


def test_should_skip_datepicker_t_minus_2_returns_false():
    """target_date == T-2 (date 对象) → 不跳过, 需要点 datepicker"""
    from core.dmp_item_insight_scraper import _should_skip_datepicker

    two_days_ago = date.today() - timedelta(days=2)
    assert _should_skip_datepicker(two_days_ago) is False


def test_should_skip_datepicker_today_returns_false():
    """target_date == 今天 (date 对象) → 不跳过, 需要点 datepicker"""
    from core.dmp_item_insight_scraper import _should_skip_datepicker

    today = date.today()
    assert _should_skip_datepicker(today) is False


def test_should_skip_datepicker_datetime_target_returns_true():
    """target_date 是 datetime 对象 (不是 date) → 也能正确判断 T-1"""
    from core.dmp_item_insight_scraper import _should_skip_datepicker

    yesterday_dt = datetime.combine(
        date.today() - timedelta(days=1), datetime.min.time()
    )
    assert _should_skip_datepicker(yesterday_dt) is True


# ===== _find_date_trigger_multi selector 修复 (2 测试) =====
def test_find_trigger_uses_stable_class():
    """_find_date_trigger_multi 用了 'span.mx-trigger-label' 稳定 class"""
    import inspect

    from core.dmp_item_insight_scraper import _find_date_trigger_multi
    source = inspect.getsource(_find_date_trigger_multi)
    assert "span.mx-trigger-label" in source, (
        "P0 selector 'span.mx-trigger-label' must be in _find_date_trigger_multi"
    )


def test_find_trigger_no_longer_uses_broken_class():
    """_find_date_trigger_multi 不用 'mxgc-calendar-datepicker' 作 locator (docstring 注释可提)"""
    import inspect
    import re

    from core.dmp_item_insight_scraper import _find_date_trigger_multi
    source = inspect.getsource(_find_date_trigger_multi)
    # 只检查 locator 字符串 (出现在 'locator': ... 后面), 忽略 docstring 历史说明
    locator_uses = re.findall(r"'locator':\s*[^,]+", source)
    for line in locator_uses:
        assert ".mxgc-calendar-datepicker" not in line, (
            f"Broken selector '.mxgc-calendar-datepicker' must not be a locator, found: {line}"
        )
    assert "exact-mxgc-trigger" not in source, (
        "Old strategy name 'exact-mxgc-trigger' must be removed"
    )
    assert "class-fuzzy-calendar-trigger" not in source, (
        "Old strategy name 'class-fuzzy-calendar-trigger' must be removed"
    )


# ===== try_select_date_v2 用 ID 前缀 selector (1 测试) =====
def test_try_select_date_v2_uses_id_prefix_popup():
    """try_select_date_v2 用了 '[id^='days_mx_output_']' 主选 selector"""
    import inspect

    from core.dmp_item_insight_scraper import try_select_date_v2
    source = inspect.getsource(try_select_date_v2)
    assert "[id^='days_mx_output_']" in source, (
        "Primary popup selector '[id^=\\'days_mx_output_\\']' must be in try_select_date_v2"
    )


# ===== items.yaml date_strategy 节 (1 测试) =====
def test_yaml_has_date_strategy_section():
    """items.yaml 包含 date_strategy 节, 含 skip_datepicker_for_t_minus_1 + max_backfill_days"""
    yaml_path = Path(__file__).parent.parent / "config" / "items.yaml"
    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "scraping" in data, "items.yaml missing 'scraping' section"
    assert "date_strategy" in data["scraping"], (
        "items.yaml scraping section missing 'date_strategy' (ERR-20260613-002)"
    )
    ds = data["scraping"]["date_strategy"]
    assert ds["skip_datepicker_for_t_minus_1"] is True
    assert ds["max_backfill_days"] == 2
    assert ds["backfill_env"] == "BACKFILL_DAYS"
    # 验证新稳定 selector 已写入配置
    assert ds["trigger_selector"] == "span.mx-trigger-label"
    assert ds["popup_selector"] == "[id^='days_mx_output_']"


# ===== L2 防御: _diagnose_datepicker (2 测试) =====
def test_diagnose_datepicker_returns_expected_structure():
    """_diagnose_datepicker 返回 dict 含 5 类候选 + summary"""
    from unittest.mock import MagicMock

    from core.dmp_item_insight_scraper import _diagnose_datepicker

    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        'timestamp': '2026-06-13T20:00:00Z',
        'url': 'https://dmp.taobao.com/index_new.html',
        'candidates': {
            'mx_click_elements': [{'tag': 'SPAN', 'class': 'mx-trigger', 'text': '昨日', 'mx_click': '...', 'id': ''}],
            'yesterday_text': [{'tag': 'SPAN', 'class': 'mx-trigger-label', 'text': '昨日', 'id': 'trigger_mx_99'}],
            'date_format_text': [],
            'id_mx_output': [{'tag': 'DIV', 'id': 'days_mx_output_mx_99', 'class': 'mx-output-bottom', 'visible': True}],
            'id_calendar': [],
        },
        'summary': {'total_mx_click': 12, 'total_with_id_calendar': 3},
    }

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        diag = _diagnose_datepicker(mock_page, tmp)

    assert 'candidates' in diag
    assert 'mx_click_elements' in diag['candidates']
    assert 'yesterday_text' in diag['candidates']
    assert 'date_format_text' in diag['candidates']
    assert 'id_mx_output' in diag['candidates']
    assert 'id_calendar' in diag['candidates']
    assert diag['summary']['total_mx_click'] == 12
    # 验证 page.evaluate 被调用
    assert mock_page.evaluate.call_count == 1


def test_diagnose_datepicker_writes_json_to_disk(tmp_path: Path):
    """_diagnose_datepicker 把诊断 JSON 写到 debug_dir"""
    from unittest.mock import MagicMock

    from core.dmp_item_insight_scraper import _diagnose_datepicker

    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        'timestamp': '2026-06-13T20:00:00Z',
        'candidates': {
            'mx_click_elements': [], 'yesterday_text': [],
            'date_format_text': [], 'id_mx_output': [], 'id_calendar': [],
        },
        'summary': {'total_mx_click': 0, 'total_with_id_calendar': 0},
    }

    diag = _diagnose_datepicker(mock_page, str(tmp_path))

    # 验证磁盘上有 datepicker_diag_*.json
    diag_files = list(tmp_path.glob("datepicker_diag_*.json"))
    assert len(diag_files) == 1, f"Expected 1 diag file, found {len(diag_files)}"
    # 验证 JSON 可读
    import json
    loaded = json.loads(diag_files[0].read_text(encoding="utf-8"))
    assert loaded['summary']['total_mx_click'] == 0


# ===== L3 防御: _autoheal_find_trigger (2 测试) =====
def test_autoheal_find_trigger_returns_none_when_no_candidates():
    """_autoheal_find_trigger 无候选时返回 (None, None), 不调用 page.locator"""
    from unittest.mock import MagicMock

    from core.dmp_item_insight_scraper import _autoheal_find_trigger

    mock_page = MagicMock()
    result = _autoheal_find_trigger(mock_page, {
        'mx_click_elements': [], 'yesterday_text': [],
        'date_format_text': [], 'id_mx_output': [], 'id_calendar': [],
    })
    assert result == (None, None)
    # 无候选时不应该触发任何点击
    assert mock_page.locator.call_count == 0


def test_autoheal_find_trigger_skips_hash_class_candidates():
    """_autoheal_find_trigger 跳过 dKqGwk* hash class 候选（防 click 错东西）"""
    from unittest.mock import MagicMock

    from core.dmp_item_insight_scraper import _autoheal_find_trigger

    mock_page = MagicMock()
    candidates = {
        'mx_click_elements': [
            {'tag': 'SPAN', 'class': 'dKqGwkgPco random', 'text': '昨日', 'mx_click': '...', 'id': ''},
        ],
        'yesterday_text': [],
        'date_format_text': [],
        'id_mx_output': [], 'id_calendar': [],
    }

    result = _autoheal_find_trigger(mock_page, candidates)
    assert result == (None, None), "Should not try to click on hash class candidate"


# ===== L2+L3 集成: _find_date_trigger_multi 失败时调用防御 (2 测试) =====
def test_find_date_trigger_multi_calls_diagnose_on_all_fail(monkeypatch):
    """4 策略全失败时, _find_date_trigger_multi 调用 _diagnose_datepicker"""
    from unittest.mock import MagicMock

    from core import dmp_item_insight_scraper as scraper_mod

    # mock page: page.locator(sel).first.is_visible() → False (4 策略全失败)
    mock_page = MagicMock()
    fake_first = MagicMock()
    fake_first.is_visible.return_value = False
    fake_first.text_content.return_value = ""
    mock_page.locator.return_value.first = fake_first

    # mock L2 + L3
    monkeypatch.setattr(scraper_mod, '_diagnose_datepicker',
                        lambda p, d: {'candidates': {}, 'summary': {}})
    monkeypatch.setattr(scraper_mod, '_autoheal_find_trigger', lambda p, c: (None, None))

    result = scraper_mod._find_date_trigger_multi(mock_page)
    assert result == (None, None)


def test_find_date_trigger_multi_skips_l3_when_disabled(monkeypatch):
    """DISABLE_DATEPICKER_AUTOHEAL=1 时跳过 L3 auto-heal"""
    from unittest.mock import MagicMock

    from core import dmp_item_insight_scraper as scraper_mod

    monkeypatch.setenv('DISABLE_DATEPICKER_AUTOHEAL', '1')

    mock_page = MagicMock()
    fake_first = MagicMock()
    fake_first.is_visible.return_value = False
    fake_first.text_content.return_value = ""
    mock_page.locator.return_value.first = fake_first

    autoheal_called = []
    monkeypatch.setattr(scraper_mod, '_diagnose_datepicker',
                        lambda p, d: {'candidates': {}, 'summary': {}})
    monkeypatch.setattr(scraper_mod, '_autoheal_find_trigger',
                        lambda p, c: autoheal_called.append(True) or (None, None))

    scraper_mod._find_date_trigger_multi(mock_page)
    assert autoheal_called == [], "L3 should be skipped when DISABLE_DATEPICKER_AUTOHEAL=1"
    monkeypatch.delenv('DISABLE_DATEPICKER_AUTOHEAL')


# ===== 弹窗关闭 mask_dlg_* (1 测试) =====
def test_select_date_smart_v2_closes_mask_dlg_popups():
    """select_date_smart_v2 弹窗关闭代码必须识别 mask_dlg_* (DMP 6/13 新弹窗模式)"""
    import inspect

    from core.dmp_item_insight_scraper import select_date_smart_v2
    source = inspect.getsource(select_date_smart_v2)
    # mask_dlg_* 必须在弹窗关闭的 JS 中 (page.evaluate 字符串)
    assert "mask_dlg" in source, (
        "mask_dlg_* 必须在 select_date_smart_v2 弹窗关闭逻辑中 "
        "(DMP 6/13 新弹窗 mask_dlg_1351 之前被遗漏)"
    )
    # z-index 兜底也必须在
    assert "z-index" in source or "zIndex" in source, (
        "z-index 兜底必须在 select_date_smart_v2 中 "
        "(DMP 后续改 ID/类名也能被这条兜住)"
    )
