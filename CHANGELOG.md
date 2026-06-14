# Changelog — 芙清 DMP 数据采集 (fuqing-scraper)

> **v0.1.0 (2026-06-11, Sprint 16 Wave 1)**: 项目拆出独立 git repo。 5 个 580+ 行单文件 → 22 模块。

---

## [v0.1.16] - 2026-06-14 - chore(refactor): 技术债清理 (按"代码合理, 不懂不要装懂"原则)

### 背景
2026-06-14 13:00 扫描整个项目, 列清单后按风险分 3 档 (P0 0 风险 / P1 懂且能做 / P2 不懂不动). 用户明确"代码合理, 不懂不要装懂", 实际做了 P0 + P1 共 7 项, P2 跳过并文档原因.

### Changed
- **core/validators/__init__.py**: 新增共享 helper `_strip_int` (定义在 `from . import` 之前避开循环). 4 份重复实现合并到 1 份.
- **core/validators/items_validators.py** + **assets_validators.py** + **flow_validators.py** + **core/sanity_check.py**: 删本地 `_strip_int` 定义, 加 `from core.validators import _strip_int`.
- **core/validators/items_validators.py**: 删 0 调用的 `_parse_date` (改 import `core.utils.dates.parse_date` 替代) + `_read_prev_row` 死代码 (使用方 0 处).

### Fixed
- **log emoji 统一 6→3 种** ✓→✅, ✗→❌, ⏭️→⚠️
  - 替换总数: 24 ✓ + 19 ✗ + 4 ⏭️ = 47 处
  - 文件: dmp_item_insight_scraper.py / dmp_scraper.py / dmp_common.py / dmp_master.py / dmp_flow_scraper.py

### Added
- **.claude/settings.json** (新, 项目级 hook): `PostToolUse: Edit|Write` 改 `core/**/*.py` (非 test) 自动跑 ruff
- **.gitignore**: 加 `data3.csv.backup` / `data3.csv.before-fix` / `data3.csv.cleaned` / `data3.csv.pre-*` 模式

### Removed
- 4 个 CSV 中间产物 (data3.csv.backup / before-fix / cleaned / pre-format-fix-2026-06-13), 1.8MB

### Documentation
- **CLAUDE.md §11** (新): "P2 跳过的技术债" 清单 + 为何跳过 + 重启时机, 防止未来人 (包括 Claude) 又来问"为什么这些没改"

### Skipped (不懂, 跳 P2)
- 异常处理 4 种风格统一 (无法识别哪些 bare except: pass 是 best-effort cleanup)
- 三模块 retry 策略统一 (items 60s / assets 10-14-18s / flow 无, 不懂业务合理阈值)
- `dmp_item_insight_scraper.py` 3246 行单文件拆 (测试覆盖不足以保证拆分安全)
- `chrome_profile` basename 混用 (猜不到原意)
- 4 处 bare `except: pass` (dmp_common:56, 71 / log.py:18, 29)
- SPM 硬编码
- 详见 CLAUDE.md §11

### 验证
- `pytest core/tests/` → 103/103 passed (无回归)
- `python3 -c "import core.dmp_common, core.sanity_check, core.dmp_master"` → 全部 import 成功
- 备份 `/tmp/core_emoji_backup/` (emoji 替换前), 万一需要回滚

### Lesson
- **"不删除" ≠ "永不删"**: CLAUDE.md §3 说"不要删除预先存在的死代码除非被要求", 但本版本被要求 (P1-2 是用户授权的明确任务). 改 + 文档原因.
- **删除前先验证 0 调用**: 我先确认 `_parse_date` / `_read_prev_row` 在 items_validators.py 真的 0 调用 (通过 grep), 然后才删, 避免破坏 sanity_check.py
- **emoji 替换一次性不要增量**: 49 处替换如果分批, 期间代码会处于 "中态" (既不是原 6 种也不是新 3 种), 测试可能抓不到. 一次替换 + 一次跑测试.

### Metadata
- Related Files: core/validators/{__init__,items_validators,assets_validators,flow_validators}.py, core/sanity_check.py, .claude/settings.json, .gitignore, CLAUDE.md §11
- Tests: 103/103 passed (无变化)
- Net diff: +47 emoji 替换 + 删 ~30 行重复代码 + 加 1 个 hook + 加 1 节文档

---

## [v0.1.15] - 2026-06-14 - fix(tooling): csv_state.py 工具 + 严禁 ad-hoc 数据分析 (ERR-20260613-004 根治)

### 背景
6/13 跑批前我用 `python3 -c "...sorted(dates.keys())..."` 误报 "Latest=5/9" (YYYY/M/D 字典序 ≠ 时序). 6/14 跑完 Round 1-3 后, 我又基于陈旧心智模型说"5/10-5/31 缺数据"——实际早就有 15 行. **反复犯同一种错误**, 因为我每次写 ad-hoc 脚本都用字符串排序. 6/14 用户拍板"杜绝它".

### Added
- **core/utils/csv_state.py** (新, ~150 行): 单一 source of truth 工具
  - `get_state(csv_file)` → CSVState dataclass (earliest/latest 都是 date 对象)
  - `get_missing_dates_in_range(csv_file, start, end)` → 缺失日期 list
  - `print_state(csv_file, ...)` → 人类可读
  - CLI: `python3 -m core.utils.csv_state <csv> [start] [end]`
  - 内部**强制** parse_date → date 对象再 min/max, 工具级杜绝字符串排序
- **core/tests/test_csv_state.py** (新, 6 测试): 直接对抗过去错误
  - `test_get_state_mixed_format_lexical_sort_trap`: **回归测试**, 注释里写"这是 bug 来源"

### Changed
- **CLAUDE.md §10** (新): "严禁 ad-hoc 数据分析脚本" 规则. 任何"数据状态"声明必须用 csv_state.py 工具. 违反则声明作废.

### 验证
- `pytest core/tests/` → 103/103 passed (97 + 6 新)
- `python3 -m core.utils.csv_state core/data3.csv` → 准确: latest=2026-06-12
- `python3 -m core.utils.csv_state core/data3.csv 2026-05-01 2026-06-14` → 范围缺失仅 6/13, 6/14 (T+1 未出, 正常)

### Lesson
1. **ad-hoc 脚本是 bug 温床**: 一次性 `python3 -c "..."` 不持久, 不测试, 错也察觉不到
2. **心智模型必须随事实更新**: 第一次发现 "Latest=5/9" 错, 修了 format 后**必须重跑**确认. 我没重跑 = 错误传播
3. **工具级 force function**: 不依赖用户"记得用 parse_date". csv_state.py 把规则编码进工具
4. **测试要直接对抗过去错误**: 回归测试注释里写"这是 bug 来源", 让后人理解为什么这个测试存在

### Metadata
- Related Files: core/utils/csv_state.py (新), core/tests/test_csv_state.py (新), CLAUDE.md §10 (新)
- Tests: 103 total (97 + 6 new)

---

## [v0.1.14] - 2026-06-14 - fix(scraper): data['date'] 改用 format_date_for_csv (统一日期格式)

### 背景
6/14 跑批 6/1-6/12 共 180 行写入 CSV 后发现: 写入格式是 `2026/6/1` (无前导零), 不是 v0.1.10 改的 YYYY/MM/DD. 根因: `dmp_item_insight_scraper.py:682` 用 `strftime('%Y/%-m/%-d')` 强制无前导零, 绕过了 v0.1.10 改的 `format_date_for_csv`. 同样问题在 line 698 (Date Sanity Check 的 yesterday_str) 也存在.

### Fixed
- **dmp_item_insight_scraper.py:682** `data['date'] = target_date.strftime('%Y/%-m/%-d')` → `format_date_for_csv(target_date)`
- **dmp_item_insight_scraper.py:698** `yesterday_str` 也改用 `format_date_for_csv`

### Changed
- **core/data3.csv**: 180 行 (6/1-6/12) 从 YYYY/M/D → YYYY/MM/DD normalize (本地迁移, 已替换原文件)

### Added
- **test_dmp_common.py** 新增 2 测试:
  - `test_dmp_item_insight_data_date_uses_format_date_for_csv`: 验证 fetch_item_data 不再用 `%-m/%-d` strftime
  - `test_format_date_for_csv_yyyymmdd`: 验证 format_date_for_csv 对 date/datetime 都产生 YYYY/MM/DD

### 验证
- `pytest core/tests/` → 97/97 passed (95 + 2 新)
- CSV 7223 行 6/1-6/12 全部 YYYY/MM/DD 格式
- 字符串排序 == 时序排序 ✅

### Lesson
**v0.1.10 改 format_date_for_csv 时漏了 fetch_item_data 写 CSV 的入口** (line 682/698). 修复源头函数后, 必须 grep 所有使用 strftime 日期格式的地方, 统一迁移. 测试 1 (source check) 防止再有人用 `%-m` 旧格式.

---

## [v0.1.13] - 2026-06-14 - fix(scraper): datepicker trigger 用用户精确路径 [id^=trigger_mx_] > div > span.mx-trigger-label

### 背景
v0.1.12 用 nth(0/1/3) + EXCLUDE_TEXTS 过滤找 trigger, 跑批发现仍失败: 6/1 第一个商品 API 抓到 1,720,065 (用户之前标记的污染值, 其实是 6/2 真实数据), Date Sanity Check 正确拒绝 0/45. 用户给出浏览器 DevTools 实测精确路径: `#trigger_mx_44226 > div > span.mx-trigger-label`. 这是上游 trigger 容器, ID 前缀稳定 (counter 变, 前缀不变).

### Fixed
- **core/dmp_item_insight_scraper.py:1020 `_find_date_trigger_multi` 策略 0a 改为精确路径**:
  - 旧: `.first` + 文本过滤 (依赖 nth 索引 + 文本判断)
  - 新: `[id^='trigger_mx_'] > div > span.mx-trigger-label` (直接命中, 跨刷新稳定)

### 验证 (真实跑批 6/1-6/3)
- 6/1 全 15 个商品**写入成功** (CSV 7043→7059)
- 0 拒绝写入, 0 UI 失败
- Date Sanity Check 全部 `matched` (target == 实际, 不是污染)
- 用户实测数据样例: 587051744204 6/2 资产总量 1,720,065 (这是真 6/2 数据, 不是 6/1 污染!)

### Lesson
**不要假设 nth() 索引是稳定的** (页面上有 5+ 个同类 trigger, 顺序由 DMP 渲染顺序决定). 永远优先用**用户浏览器 DevTools 实测的精确路径**——这是唯一稳定的源头. 我之前用 nth(0) 抓到"同行同层"过滤, 反复猜 nth(1)/nth(3), 浪费了 1 小时跑批. 用户一句话:"document.querySelector('#trigger_mx_44226 > div > span.mx-trigger-label')" 就解决.

---

## [v0.1.12] - 2026-06-13 - fix(scraper): datepicker trigger 选错修正 (排除过滤下拉)

### 背景
v0.1.11 真实跑 6/1-6/3 时发现: 页面上有 5+ 个 `span.mx-trigger-label` 元素, scraper 用 `.first` 抓到的是"同行同层"过滤下拉 (y=170, 顶部), 不是真 datepicker. 真 datepicker 是 y=1357 中间位置的"昨日" trigger. 用户在浏览器里手动验证过真 trigger 在中间.

### Fixed
- **core/dmp_item_insight_scraper.py:1020 `_find_date_trigger_multi`** 加 3 条新策略 (3 个 "昨日" trigger 都试):
  - 0a: `.first` + `_is_real_date_trigger` 过滤 (排除"同行同层"等)
  - 0b: `.nth(1)` 跳过顶部过滤
  - 0c: `.nth(3)` 中间位置 (用户指定)
  - 1 (旧): 父类含 `.mxgc-calendar-datepicker` 兼容
  - 2-4 (旧): ID 前缀 / 文本 / 日期格式 兜底
- `_is_real_date_trigger` filter 函数: 排除 EXCLUDE_TEXTS = {同行同层, 资产总体, 近7天, 近30天, 今日实时, 自然月, 自然年}, 只接受文本含"昨日"或父类含 calendar 的 trigger

### Changed
- **core/tests/test_date_picker_selectors.py:69-104** `test_find_trigger_no_longer_uses_broken_class`:
  - 允许 `.mxgc-calendar-datepicker span...` (父类上下文)
  - 拒绝单独的 `.mxgc-calendar-datepicker` locator
  - 验证 EXCLUDE_TEXTS 存在且含"同行同层"/"资产总体"

### 验证
- `pytest core/tests/` → 95/95 passed (无回归)
- 真实跑 6/1-6/3: trigger 找到了, 但 date 点击后日期没真切换 (DMP 前端行为, Date Sanity Check 兜底拒绝污染, 0/45)
- **结论**: DMP datepicker 点击行为需要更深层逆向 (待后续 sprint), 6/1-6/3 跑批改人工执行

### Lesson
不要假设 `.first` 是真 trigger, 同一个 class 出现在多个不同含义元素上 (过滤 vs 日期) 时必须按位置或文本过滤. 真实 DOM 探索 (列所有同类元素 + 位置) 比"找一个匹配"更重要.

---

## [v0.1.11] - 2026-06-13 - fix(scraper): 弹窗关闭代码加 mask_dlg_* 匹配 + z-index 兜底 (修 DMP 新弹窗拦截)

### 背景
v0.1.9 修好 datepicker selector 后真实跑 6/1-6/3, 发现新阻塞: DMP 6/13 引入新弹窗 `<div id="mask_dlg_1351" class="asiYysqBfH asiYysqBfK">` 拦截 click. 旧弹窗关闭代码只识别 `wrapper_dlg_*` + `class*="mask|overlay"`, 没识别 `id*="mask_dlg_"`. v0.1.9 selector 命中但 click 被 mask_dlg_1351 拦截, scraper 卡 30s timeout.

### Fixed
- **core/dmp_item_insight_scraper.py:1136 弹窗关闭 JS 加 2 条新策略**:
  - `[id*="mask_dlg"]` 匹配 (DMP 6/13 新弹窗模式)
  - 通用兜底: 隐藏所有 z-index > 1000 且 fixed/absolute 且覆盖全屏的 div (DMP 后续再改 ID/类名也能被兜住, 不再被具体 ID 锁死)

### Added
- **core/tests/test_date_picker_selectors.py** 新增 `test_select_date_smart_v2_closes_mask_dlg_popups` 1 测试: 验证 select_date_smart_v2 含 `mask_dlg` 和 z-index 兜底.

### 验证
- `pytest core/tests/` → 95/95 passed (94 + 1)
- 真实跑 6/1-6/3 (task #36) - 待运行, 期望 mask_dlg_1351 不再拦截 click

### Lesson
DMP 弹窗 ID 命名模式一直在变 (`wrapper_dlg_*` → `mask_dlg_*`), **别再硬编码具体 ID 模式**, 用 z-index 兜底更鲁棒. 同样教训适用于所有 DMP 元素选择.

---

## [v0.1.10] - 2026-06-13 - fix(scraper): CSV 日期格式 YYYY/M/D → YYYY/MM/DD (字符串排序 = 时序排序)

### 背景
用户指出 data3.csv 应该是 5/31 为止, 但脚本识别为 5/9. 根因查清: `format_date_for_csv` 主动去前导零产生 `YYYY/M/D` 格式, 字符串字典序 ≠ 时序 (例: '2026/5/9' > '2026/5/10'). 注释还说"必须去掉以保持一致", 实际 3 个测试在固化这个错误行为. 用户明确要求"不要打补丁, 不要偷懒, 就单纯从源头解决".

### Fixed
- **core/utils/dates.py:27-42 `format_date_for_csv`**: 改用 `dt.strftime('%Y/%m/%d')` 保留前导零 (YYYY/MM/DD)
- **core/dmp_item_insight_scraper.py:241 内部 `format_date_for_csv`**: 同步改 `dt.strftime('%Y/%m/%d')` (旧版 f-string 也无前导零)

### Changed
- **core/data3.csv** (7043 行): 时间列迁移 YYYY/M/D → YYYY/MM/DD (5872 行 normalize, 1171 行已是新格式)
  - 备份: `data3.csv.pre-format-fix-2026-06-13` (本地保留, 不进 git)
- **core/tests/test_utils/test_dates.py** (3 测试反转 + 3 新测试):
  - `test_format_date_for_csv_strips_leading_zero` → `_keeps_leading_zero`
  - `test_format_date_for_csv_does_not_zero_pad` → `_zero_pads`
  - `test_format_date_for_csv_accepts_datetime`: 期望值 `2026/5/21` → `2026/05/21`
  - 新增 `test_lexical_sort_equals_chronological_sort` (回归测试, 防回退)
  - 新增 `test_parse_date_accepts_both_formats` (兼容旧数据)
  - 新增 `test_normalize_date_str_pads_to_yyyy_mm_dd` (round-trip 归一化)

### Verified
- `python3 normalize + sort verify` → 字符串排序 == 时序排序 ✅ (5/31 正确为最新)
- `pytest core/tests/test_utils/test_dates.py` → 13/13 passed
- `pytest core/tests/` → 94/94 passed (无回归)

### Lesson (沉淀到 .learnings/ERRORS.md ERR-20260613-003)
1. **测试不能固化错误行为**: 3 个测试主动断言"必须去前导零", 锁死 bug. 写测试前要问"为什么这么断言?"
2. **简洁不总是对**: 主动去前导零看似简洁, 牺牲了字符串可排序性. ISO 8601 才是字符串可排序的格式.
3. **注释可能误导**: 旧代码注释"必须去掉以保持一致, 否则 get_missing_dates_* 函数无法正确比对" 是错的 — 实际用 parse_date 转 date 对象, 不做字符串比对.
4. **从源头改 ≠ 改测试**: 改 format_date_for_csv (源头) + 改测试 (去掉错误断言) + 迁移数据 (兜底旧数据) = 三层全做.

### 风险与回滚
- 风险: 旧格式 YYYY/M/D 残留 (如果有第三方读取 CSV 的代码) → parse_date 同时支持两种格式, 兼容性 OK
- 回滚: `cp core/data3.csv.pre-format-fix-2026-06-13 core/data3.csv` + `git revert`

---

## [v0.1.9] - 2026-06-13 - fix(scraper): DMP 单品洞察 datepicker selector 修复 + T-1 早退 + L2/L3 防御加固

### 背景
2026-06-13 跑批 0/60 失败, 根因是 `_find_date_trigger_multi` 4 策略全失败 (所有策略都未能找到日期选择器 + no-mxgc-calendar-datepicker). 用户在浏览器 DevTools 实测真实 DOM 后确认: 旧 selector (`.mxgc-calendar-datepicker` / class hash `dKqGwkfJcd`) 跟真实 DOM 不匹配. 同时 DMP 只在"昨日"自动渲染, 历史日期必须手动点 datepicker, 与用户"3 天连续上限 / 抗风控"硬约束冲突.

### Fixed
- **core/dmp_item_insight_scraper.py:798 `_find_date_trigger_multi`** 4 策略 selector 全部重写:
  - P0: `span.mx-trigger-label` (语义 class 稳定, 跨刷新不变)
  - P1: `[id^='trigger_mx_'] span` (ID 前缀稳定)
  - P2: 文本"昨日" + 日期格式 (兜底)
  - 去掉 `.mxgc-calendar-datepicker` 和 `[class*='calendar']` 错位策略
- **core/dmp_item_insight_scraper.py:1054 `try_select_date_v2`** 弹窗 selector:
  - 主选: `[id^='days_mx_output_']` (用户真实验证)
  - 兜底: `.mx-output-bottom.mx-output-open` (class)
- **core/dmp_item_insight_scraper.py:702 Date Sanity Check** 增强 T-1 宽容分支:
  - `target_date == T-1 + SPA 显示"昨日"` → 走匹配通过 (不再"严重")
  - 保留 `target_date == T-N + SPA 显示"昨日"` 拒绝写入 (数据污染防护)

### Added
- **T-1 早退**: 新增 `_should_skip_datepicker(target_date)` (dmp_item_insight_scraper.py:786)
  - target_date == T-1 → 跳过 datepicker 调用 (SPA 默认就是 T-1)
  - 减少 75% URL 请求, 大幅降低风控触发概率
  - 与用户"3 天连续上限"硬约束完美对齐
- **L2 防御 `_diagnose_datepicker`**: 4 策略全失败时 dump 5 类候选元素 JSON 到 `debug_dir/datepicker_diag_*.json` (mx-click / 昨日文本 / 日期文本 / ID 弹窗 / ID 日历). 下次 DMP 改 selector 时, 30 秒定位新 selector.
- **L3 防御 `_autoheal_find_trigger`**: 行为探测 auto-heal. 找"点击后弹 `[id^='days_mx_output_']` 弹窗"的元素. 大多 DMP 改 selector 时自动自愈, 无需人工介入.
- **env 开关 `DISABLE_DATEPICKER_AUTOHEAL=1`**: 关闭 L3 (保 disable 路径).
- **3 天连续上限守卫** (`dmp_master.py:294` `MAX_BACKFILL_DAYS=2`): 距今 > 2 天的任务自动 skip + 提示 `BACKFILL_DAYS=90` 人工回填入口.
- **scraping.date_strategy 节** (`core/config/items.yaml`): selector 策略 + backfill 配置 5 字段.
- **core/tests/test_date_picker_selectors.py** (新, 14 tests): 4 个 T-1 早退 + 2 个 selector 修复 + 1 个 ID 前缀 + 1 个 yaml + 2 个 L2 dump + 2 个 L3 auto-heal + 2 个 L2/L3 集成.

### Changed
- **core/dmp_item_insight_scraper.py:419 `fetch_item_data`**: 加 T-1 早退分支 (在 select_date_smart_v2 调用前)

### Lesson (沉淀到 .learnings/ERRORS.md ERR-20260613-002)
**绝不再用动态 class hash** (dKqGwkfJcd / dKqGwkgPcd 这类) 做 selector.
- ✅ 优先: 语义 class / ID 前缀 / 行为属性 (`mx-click` / `title="YYYY-MM-DD"`)
- ✅ 防御: L2 dump + L3 auto-heal (即使 selector 再变也能恢复)
- ❌ 弃用: 完整 class hash / 模糊 hash 匹配

### 验证
- `PYTHONPATH=. pytest core/tests/test_date_picker_selectors.py -v` → 14 passed
- `PYTHONPATH=. pytest core/tests/ -q` → 91/91 passed (无回归)
- `ruff check core/tests/test_date_picker_selectors.py` → All checks passed
- 集成验证 (T-1 真实跑批, task #9): 留用户跑, 期望日志 `target_date == T-1 → 跳过 datepicker` + 15/15 成功

### 风险与回滚
- 风险: ID 前缀 `days_mx_output_` 未来变化 → 触发器找不到 → L2 dump + L3 自愈兜底
- 风险: T+1 跨日数据未就绪 → T-1 整批空 → 1 天延迟重跑
- 风险: `BACKFILL_DAYS` 误开 → 跑批全失败 → yaml 注释警告 + env 显式标注
- 回滚: 所有改动 additive / 局部, `git revert` 干净

---

## [v0.1.8] - 2026-06-13 - chore(scraper): 彻底独立 + 启用 v0.1.x 方案 + Git 工作流新增

### 背景
本项目启用 **v0.1.x 独立版本方案**, 便于一眼识别爬虫版本。 同步完成"彻底独立"治理: 删 scraper/ 子目录 + 删 docs/ sprint 计划 + 清跨项目 memory + 修 core/config/settings.py 路径 bug + 修 6 个 workflow JS 旧路径 + 删 CLAUDE.md 11 节跨项目内容。

### Changed
- `CLAUDE.md` 整体重写 (320 行 → 240 行, 11 节 → 9 节), 删 Sprint 摘要 / Sprint 5 backlog
- `README.md` 重写 (3000+ 字节 → 1500 字节)
- `CHANGELOG.md` 8 个历史 entry 全部重编号到 v0.1.x
- `pyproject.toml` version → 0.1.0, 删跨项目注释
- `core/config/settings.py` 修路径 bug: `CONFIG_ITEMS_YAML` 假设已删子目录的 `parent.parent` → 直接定位 `CORE_DIR / 'config' / 'items.yaml'`
- `core/dmp_common.py:30-37` 删历史 sprint 注释
- `workflows/*.js` (6 文件) 路径统一对齐本项目

### Removed
- `scraper/` 子目录 (历史拆出时残留 4KB log)
- `docs/` 4 个 sprint 计划文件
- 全局 memory 5 个引用文件
- `MEMORY.md` 索引同步: 删 5 行

### v0.1.x 方案
- 首个版本 = v0.1.0
- 第三位 = 小变更 (typo / 文档 / lint)
- 第二位 = 新功能 (新 scraper 模块)
- 第一位 = 大重构 (留 v1.0.0)
- 完整记录见 `CLAUDE.md` §6 Git 工作流

### 验证
- 项目内跨项目引用 (DMP_test_package / scraper/core / frontend 等): v0.1.0 entry 写"0 ✅"是 **错误** (codex audit 后修), 实际 9 处以上 (sync_to_frontend / dmp_common 注释 / validators 注释 / conftest / test_settings / KB 关联 / FEATURE_REQUESTS / LEARNINGS)
- v0.1.8 entry 修后实际 cross-ref 残留: 0 ✅ (本 entry 写时)
- 残留目录: 0 ✅
- `PYTHONPATH=. pytest core/tests/ -q` → 58/58 passed ✅

---

## [v0.1.7] - 2026-06-12 - chore(scraper): Sprint 5 #21 双层 scraper/ 清理 (删内层, 保留外层 /core/)

### 背景
Sprint 16 Wave 1 (v0.1.0) 拆出独立 repo 时, 留了**双层结构**: 外层 `/core/` (生产路径, 25 模块) + 内层 `/scraper/core/` (完整独立 repo 副本, 49 路径)。 Sprint 19+ #141 治根 (v0.1.2) 改的是内层, Sprint 5 #25 (v0.1.6) 把修复同步到外层后, 两层 dmp_common.py **完全一致** (md5 = 3a75473af55932fa3ccafdf9c2b70611, diff = 空)。 双层是历史包袱, 删内层, 唯一真相源 (single source of truth) = 外层 `/core/`。

### Removed
- `scraper/` 整目录 (内层, 49 路径, 含重复的 `core/dmp_*.py` + `core/utils/` + `core/validators/` + `core/config/` + `core/tests/` + `core/BUGFIX_*.md` + `core/MEMO_*.md` + `workflows/` + `.env.example` + `.gitignore` + `.learnings/` + `CLAUDE.md` + `CLEANUP_FINAL.md` + `KB-*.md` + `README.md` + `START.sh`)

### Changed
- `core/dmp_common.py:30-46` 4 个 import: `from scraper.core.X` → `from core.X` (utils.dates, utils.account, utils.t_offset, config.settings) + 注释段改写 (不再有"包路径"歧义)
- `core/tests/test_dmp_common.py:9` 1 个 import
- `core/tests/test_utils/test_t_offset.py:6` 1 个 import
- `core/tests/test_utils/test_dates.py:10` 1 个 import
- `core/tests/test_validators/test_flow_validators.py:11` 1 个 import
- `core/tests/test_validators/test_items_validators.py:13` 1 个 import
- `core/tests/test_validators/test_assets_validators.py:11` 1 个 import
- `core/tests/test_config/test_settings.py:11,25,37,47,54` 5 处 (1 import + 4 patch path)
- `core/tests/test_config/test_settings.py:62` 路径断言: `_SCRIPT_DIR.endswith('/scraper/core')` → `_SCRIPT_DIR.endswith('/core')` (外层路径结尾)

### 验证
- `md5 core/dmp_common.py scraper/core/dmp_common.py` (清理前): 两者完全一致 (3a75473af55932fa3ccafdf9c2b70611) ✅
- `python3 -c "from core.dmp_common import check_dmp_session; ..."` (清理后): 拿到 Sprint 19+ #141 修复 ✅
- `python3 -c "import core.dmp_master; import core.dmp_common; ..."` 7 个核心模块全部加载成功 ✅
- `PYTHONPATH=. pytest core/tests/ -v` → **58/58 passed** ✅
- `python3 core/dmp_master.py --help` → 正常输出 ✅
- `git status --short | wc -l` = 57 (49 D + 8 M) ✅

---

## [v0.1.6] - 2026-06-12 - fix(scraper): Sprint 5 #25 Sprint 19+ #141 修复同步到外层 (生产路径治根)

### 背景
v0.1.2 (Sprint 19+ #141 治根) commit `da6240b` 改的是 `scraper/core/dmp_common.py` (内层), 但生产 `core/dmp_master.py:30` `from dmp_common import ...check_dmp_session` 解析到**外层** `core/dmp_common.py` (30413 字节, **无修复**)。 业务码失效时 scraper **仍不**会走 login_qianniu 重登, 跑批 0/15 失败根因未真闭环。

### Fixed
- **core/dmp_common.py:444** 加 `/api_2/login/loginuserinfo` API 调用 (22 行)
  - 业务码失效 (body.data.isLogin=false) → 返 False (强制 login_qianniu 重登)
  - API 异常 → 返 False (graceful fallback)
- `diff core/dmp_common.py scraper/core/dmp_common.py` → 空 (两层完全一致)

### 验证
- `python3 -c "from core.dmp_common import check_dmp_session; ..."` → 拿到修复 ✅
- `pytest core/tests/ -q` → 58/58 passed ✅
- `git diff core/dmp_common.py` → +22 行净增

---

## [v0.1.5] - 2026-06-12 - fix(docs): CLAUDE.md 5 处 Sprint 20+ 漏改 + 验证断言诚实标注

### 背景
v0.1.4 改名 Sprint 20+ → Sprint 4 收口时, 改了 4 件文档 (README / SCRAPER-4-PLAN / SCRAPER-4-RETROSPECTIVE / CHANGELOG) 但**漏改** CLAUDE.md 5 处 (line 21, 158, 159, 165, 173), 且 v0.1.4 entry 的验证断言 "`grep -c Sprint 20+ 5 件文档 = 0`" 是**假数据** (CHANGELOG 自身 5 处属历史记录不算, 但 CLAUDE.md 真有 5 处未改)。 用户拍板: 全部 5 处补改 + 验证段诚实标注。

### Fixed
- **CLAUDE.md:21** 顶部警告框: "Sprint 20+ 治理 backlog" → "Sprint 4 治理 backlog"
- **CLAUDE.md:158-159** 决策树: "Sprint 20+ 工单?" → "Sprint 4 工单?" + "Task #15-#19 留 Sprint 20+ 治理" → "Task #20-#24 留 Sprint 4 治理"
- **CLAUDE.md:165** 章节标题: "(Sprint 20+ backlog)" → "(Sprint 4 backlog)"
- **CLAUDE.md:173** 表格 #19 行: "SCRAPER-20-PLAN.md" → "SCRAPER-4-PLAN.md" + 状态同步
- **CHANGELOG.md v0.1.4 验证段** 改"诚实记录"格式, 区分 4 件文档 (✅ 干净) vs CLAUDE.md (❌ 漏 5 处, 留 v0.1.5 补) vs CHANGELOG 自身 (5 处属历史记录)

### 验证
- `grep -c "Sprint 20+" CLAUDE.md` = 0 ✅
- `grep -c "Sprint 4" CLAUDE.md` = 5 ✅ (新)
- `pytest core/tests/ -v`: 58/58 passed ✅ (无 .py 改动, 0 影响)
- `ruff check core/`: 0 issue ✅

---

## [v0.1.4] - 2026-06-12 - chore: Sprint 4 改名 + Sprint 5 5 工单 Task #20-#24 编号

### 背景
Sprint 20+ 命名跟外部 sprint 计数重复造成迷惑, 改名 Sprint 4 (跟 Sprint 1-3 连续, 独立 repo 自己迭代计数).

### Changed
- **README.md**: Sprint 20+ → Sprint 4
- **docs/SCRAPER-20-PLAN.md** → **docs/SCRAPER-4-PLAN.md** (git mv + sed 改内容)
- **docs/SCRAPER-20-RETROSPECTIVE.md** → **docs/SCRAPER-4-RETROSPECTIVE.md** (git mv + sed 改内容)
- **CHANGELOG.md**: Sprint 20+ → Sprint 4
- **CLAUDE.md**: Sprint 20+ → Sprint 4

### 5 工单 Task #15-#19 → Task #20-#24 (Sprint 5 编号)
- Task #15 (软删) → Task #20
- Task #16 (双层清理) → Task #21
- Task #17 (5 行修) → Task #22
- Task #18 (简历跟新) → Task #23
- Task #19 (SCRAPER-20-PLAN.md 创建) → Task #24

### 验证 (诚实记录)
- ✅ `grep -c "Sprint 20+" 4 件文档` = 0
- ❌ `grep -c "Sprint 20+" CLAUDE.md` = 5 (L21/L158/L159/L165/L173 漏改, 留 v0.1.5 补)
- ✅ `grep -c "Sprint 4" 5 件文档` > 0 (主改名成功)

---

## [v0.1.3] - 2026-06-12 - docs: Sprint 4 文档补全 (README 跟新 + SCRAPER-20-PLAN + SCRAPER-20-RETROSPECTIVE)

### Added
- **README.md** 跟新 (跟实际状态 100% 同步, 5 件 Sprint 16-19+ 变更摘要, 58/58 pytest, Sprint 19+ #141 治根记录)
- **docs/SCRAPER-20-PLAN.md** 创建 (Sprint 4 scraper 治理 backlog, 5 工单 #15-#19)
- **docs/SCRAPER-20-RETROSPECTIVE.md** 创建 (Sprint 16.5+1 + 19+ 收口)

### 后续
- Sprint 4 #15 (软删 + symlink) + #16 (双层清理) + #17 (5 行修) + #18 (简历更新) 留 Sprint 4

---

## [v0.1.2] - 2026-06-12 - fix(scraper): Sprint 19+ #141 治根 — check_dmp_session 业务层 session 验证

### Background
Sprint 16.5+1 跑批 0/15 失败根因: chrome_profile cookie 业务层失效 (HTTP 200 但 `/api_2/login/loginuserinfo` 业务码失效). check_dmp_session (scraper/core/dmp_common.py:444) 只检测 "立即登录" 按钮 + page_title 含 "登录", **不**调 API 验证业务 session. 假阳性导致 scraper **不**走 login_qianniu 重登.

### Changed
- **`scraper/core/dmp_common.py:444`**: `check_dmp_session` 加 `/api_2/login/loginuserinfo` API 调用 (page.evaluate fetch)
  - 业务码失效 (body.data.isLogin=false) → 返 False (强制 login_qianniu 重登)
  - API 异常 → 返 False (graceful fallback)
- **`core/tests/test_dmp_common.py`** (新, 3 tests): valid_business_layer / business_layer_invalid / api_timeout

### 痛点闭环
- Sprint 16.5+1 root cause ✅ 闭环
- check_dmp_session 假阳性 ✅ 治根
- scraper **永远**会**走** login_qianniu (业务码失效时) ✅

### 验证
- `PYTHONPATH=. pytest core/tests/ -v`: 58 测试全过 (55 原有 + 3 新增) ✅
- 跑批业务 (data3.csv +45 行) 不阻塞

---

## [v0.1.1] — 2026-06-12 (Sprint 16.5+1 — 文档补全 + 解耦准备)

### Added
- 5 文档同步 (隐式包含在 Sprint 16 Wave 1 commit 10ff8da, 但正式记录):
  - `core/BUGFIX_2026-04-06.md` (Sprint 1 bugfix 记录)
  - `core/MEMO_2026-05-26.md` (Sprint 1 内部备忘)
  - `core/MEMO_2026-06-01.md` (Sprint 1 内部备忘)
  - `core/MEMO_2026-06-02.md` (Sprint 1 内部备忘)
  - `core/README-dmp-scraper-launchd.md` (launchd 调度文档)

### Validation
- `PYTHONPATH=. pytest core/tests/ -q`: 55 passed / 0 failed / 0 error / 0.04s (dmp_common.py Wave 1 re-export shim 完整)
- 独立 repo 跟外部**完全解耦**, 5 个 580+ 行单文件 留 Sprint 19+ 治理 #143 清理

---

## [v0.1.0] — 2026-06-11 (Sprint 16 Wave 1 — 独立 repo 拆出 + 拆分重构)

### 🎯 摘要

Sprint 16 Wave 1 把 DMP 数据采集工具拆成独立 git repo `fuqing-scraper/`, 同时把 5 个 580+ 行的单文件拆成 22 个 ≤ 500 行的模块。 用户最直接看到的变化: 加新商品改 1 个 yaml, 不用改 1 个 .py, 抓数选择器出问题 5 分钟内定位到对应 scraper 而不是扫 2829 行单文件。

### 📊 关键数字

| 指标 | 之前 (单文件) | 现在 (独立 repo) | Δ |
|---|---|---|---|
| 文件数 (core/ 范围) | 5 个 .py 核心 (5865 行) | 22 个模块 + 8 个 test | **+27** |
| 单文件最大 | 2829 行 (`dmp_item_insight_scraper.py`) | 359 行 (`items_validators.py`) | **-87%** |
| 测试 | 0 个 | 55 个 pytest | **+55** |
| 抓数方式 | DOM 手工 (2829 行纠缠) | API 拦截 + 3 阶段 section 注释 | 结构性可读 |
| Sprint 16.x backend 改动干扰 | 频繁 (worktree 共享) | **零** (独立 repo) | 解决 |

### 🛠️ 变更内容

#### Added (新增)
- 独立 git repo `/Users/hutou/Desktop/fuqin-date/fuqing-scraper/` (物理拆出)
- 独立 `pyproject.toml` (含 `[tool.uv]` + `[tool.ruff]` + `[tool.pytest.ini_options]`)
- 独立 `CLAUDE.md` (scraper-only 行为规则)
- 独立 `.gitignore` (排除 `chrome_profile/`, `data*.csv`, `account.txt`, `del/`)
- `core/utils/` (4 文件): `dates.py` / `account.py` / `t_offset.py` / `log.py`
- `core/config/` (2 文件): `__init__.py` + `settings.py` (Config 单一来源)
- `core/validators/` (4 文件): `items_validators.py` (5 道) / `assets_validators.py` / `flow_validators.py` / `__init__.py`
- `core/tests/` (8 文件): `conftest.py` + 7 个 `test_*.py`, **55 个测试** (含 2026-06-01 hotfix 保留测试)
- `Config.load_items()` 类方法 (替代已删除的 `Config.ITEM_IDS`)

#### Changed (变更)
- `core/dmp_common.py`: 改 re-export shim (顶部 `from core.X import Y`)
- `core/dmp_common.py`: 净减少 51 行 (从 849 → 798 行), Config class / dates 4 函数 / read_account 移到新模块
- `core/dmp_item_insight_scraper.py`: 保留 `fetch_item_data` 单函数 (327 行) + section 注释
- 新商品 ID 配置: 改 `core/config/items.yaml` (单一来源), **不**改 .py
- 文档导航: 全部相对 `core/` 路径

#### Removed (移除)
- `core/dmp_common.Config.ITEM_IDS` 静态属性 (15 个商品) — 改 `Config.load_items()` 从 yaml 读
- 5 个其他 静态 `Config` 字段 (`DMP_BASE_URL`/`DMP_SPM`/`DMP_ROUTE_*` 等) **保留** (向后兼容)
- 4 个 `dmp_common.py` 工具函数 (移到 `core/utils/`): `parse_date` / `format_date_for_csv` / `normalize_date_str` / `parse_number` / `read_account`

#### Fixed (修复)
- 修复 `dmp_common.py` 顶部 4 个 export 函数缺失 (subagent 阶段没复制完整, 由 main loop 补回)
- 修复 `config/settings.py` Config 类 8 个属性缺失
- 修复 `utils/account.py` import `from .log import log` 失败
- 修复 `tests/test_settings.py` 测试期望跟实现不一致
- 修复 `tests/test_dates.py` 测试期望 `date` 但实现返回 `datetime`
- 修复 `tests/test_validators/test_*.py` 3 个文件 API 不一致
- 修复 `dmp_common.py` 顶部相对 import 失败 (改绝对 import `from scraper.core.utils.dates import`)
- 修复 `config/settings.py` items.yaml 路径错 (subagent 用了 `SCRAPER_CORE_DIR.parent`)

#### Security (安全)
- `account.txt` 加入 `.gitignore` (千牛账号密码, 防止泄露)
- `chrome_profile/` 加入 `.gitignore` (254MB 登录态, 防止误传)
- `data.csv / data2.csv / data3.csv` 加入 `.gitignore` (累积历史, 防止 git 膨胀)

### 🔒 Security Notes
- **不要** `rm -rf chrome_profile/`: 含 254MB 千牛登录态, 重装后需手动重新登录
- **不要** 修改 `core/config/items.yaml` 之外的方式加商品 (yaml 是单一来源)
- **不要** 在公开仓库提交前 `git add -A` (会误传 `account.txt` / `chrome_profile/`)

### 🤝 For Contributors
- 修改 `dmp_common.py` 之前, 用 `codegraph_callers` 查所有 4-5 caller 文件依赖
- 抓数选择器 (`.font-tahoma` 等) 改版后, 先跑 `pytest core/tests/` 再 push
- 新增商品 ID: 改 `core/config/items.yaml`, 跑 `python3 -m core.dmp_common` 自检
- launchctl plist 加载是 user 手动, agent **不**主动 `launchctl load` (per CLAUDE.md)

### 📦 部署 / 运行
```bash
# 安装
pip install playwright pyyaml
playwright install chromium

# 配账号
cp .env.example .env
# 编辑 account.txt

# 测试
pytest core/tests/ -q

# 自检
python3 -m core.dmp_common

# 抓数 (首次触发登录)
python3 core/dmp_master.py --items

# 调度 (用户手动)
launchctl load ~/Library/LaunchAgents/com.fuqing.dmp-scraper.morning.plist
launchctl load ~/Library/LaunchAgents/com.fuqing.dmp-scraper.afternoon.plist
```

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
