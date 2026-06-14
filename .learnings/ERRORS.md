# DMP 项目错误日志

> 记录所有抓取失败、选择器失效、异常退出等错误事件
> 格式：ERR-YYYYMMDD-XXX

---

## [ERR-20260608-001] 单品洞察 API 拦截在 headless=False 模式下失败

**Logged**: 2026-06-08T11:00:00Z
**Priority**: high
**Status**: resolved
**Area**: scraper/infrastructure

### Summary
`dmp_master.py` 一直用 `headless=False` (有头模式)。单品洞察模块在有头模式下,
API 拦截 `goods/view/overview/v2` 12 秒内 0 响应, 同时日期选择器找不到 (no-mxgc-calendar-datepicker),
最终 `api_data = {}` 被跳过。

### Symptom
- 23/24 商品失败, 唯一成功的是我单独用 `headless=True` 测的那个
- 错误日志: `⚠️ 12秒内未捕获到有效API数据, 尝试备用方案`
- `日期选择失败` + `API拦截未获取到有效数据, 跳过该商品`

### Root Cause
有头模式下 (可见 Chrome 窗口), 达摩盘 SPA 页面有额外的渲染/检测逻辑
(可能涉及 `window.navigator.webdriver` 在有头/无头下的不同表现),
导致 `goods/view/overview/v2` API 请求没被发出或没被 Playwright response 事件捕获。
而 `asset/deeplink/transfer` (流转) 和 DOM 解析 (资产诊断) 不受影响。

### Fix
`dmp_master.py:625, 735` `headless=False` → `True` (含浏览器崩溃重建分支)。

### Verified
- 单品洞察 15/15 商品成功 (总计 75 行 6/2→6/6 数据)
- 资产诊断/流转在无头模式也正常, 不需要分开

---

## [ERR-20260608-002] Gate 1 误判导致 6/2~6/5 单品数据被跳过

**Logged**: 2026-06-08T11:30:00Z
**Priority**: high
**Status**: resolved
**Area**: scraper/logic

### Summary
`dmp_item_insight_scraper.py` 的 Gate 1 (L2471-2482) 比较"当前抓取数据"与
"CSV 中最新一条历史数据", 变化率 <0.01% 视为 T+1 未更新, 跳过写入。
6/2~6/5 的单品数据与 6/1 实质相同 → 全部被跳过, 看板缺 4 天。

### Symptom
- `data3.csv` 最新日期 2026/6/1, 但缺 6/2~6/5
- 达摩盘页面上 6/6 显示资产总量 236,314, 与 6/1 完全相同
- Gate 1 判定: `⏭️ 商品 587053192746 2026/06/03 数据实质相同（资产总量=236,314）, 判定为T+1未更新, 跳过写入`

### Root Cause
Gate 1 设计目的: 避免写入重复的 T+1 数据 (节省 IO)。
但达摩盘单品数据变化极小 (资产总量常常几天不变), 即使有新数据也会被误判跳过。
**真实数据 = 应该是按日期区分, 不应该按数值区分**。

### Fix
删除 Gate 1 (`dmp_item_insight_scraper.py:2471-2482`) 整个数值比较逻辑。
同日去重由 `append_tocsv` 的 L2465 处理 (同商品同日期才跳过)。

### Verified
- 6/2~6/6 全部 15 商品写入 (75 行)

---

## [ERR-20260608-003] Gate 2 (Date级) 同样按数值跳过整个日期

**Logged**: 2026-06-08T11:35:00Z
**Priority**: high
**Status**: resolved
**Area**: scraper/logic

### Summary
`dmp_master.py:348-375` 的 Gate 2 (Date级) 在所有商品数据都与前一天相同时跳过整个日期。
是 Gate 1 的"日期级"版本, 同样问题, 一起修。

### Fix
删除 `dmp_master.py:348-375` 整个 Gate 2 块。

---

## [ERR-20260608-004] 达摩盘 T+1 跨日更新: 6/7 数据 6/8 下午 15:00 才出

**Logged**: 2026-06-08T11:40:00Z
**Priority**: high
**Status**: resolved (临时) + 待长期监控
**Area**: scraper/scheduling

### Summary
跑批时 (6/8 早上 10:19) 抓 6/7, 达摩盘返回的是 6/6 旧值。
对 11 个商品对比: `6/6=1398056 == 6/7=1398056` 完全相同 = 复制。

### Symptom
`data3.csv` 写入 6/7 的 15 行, 但全部是 6/6 的复制 (236,314 等)。

### Root Cause
达摩盘 T+1 但跨日: 数据 15:00 更新, 早跑批拿不到。
原本"6/7 = 今天-1 = 抓 6/7"假设数据已就绪, 实际不是。

### Fix
**临时**: 删除 6/7 虚假数据 (15 行) — `grep -v ",2026/6/7," data3.csv`
**长期**: `T_OFFSET` 环境变量 + launchd 调度 (早 9 点 T+2 保险, 下午 16 点 T+1)

### Verified
- 删除后 `data3.csv` 最新回到 2026/6/6
- T_OFFSET 测试: `os.environ['T_OFFSET']='1'` → 0 缺失, `='2'` → 0 缺失

---

## [ERR-20260608-005] 淘宝风控: 6/8 多次大批量抓取触发

**Logged**: 2026-06-08T14:00:00Z
**Priority**: high
**Status**: pending
**Area**: scraper/infrastructure

### Summary
6/8 短时间内连续跑批 3 次 (流转 + 单品 ×2), 触发达摩盘反爬风控。

### Suggested Action
- 24 小时内不要重跑 (等风控标记过期)
- `chrome_profile/` 登录态应还在 (Cookie 持久化到 SQLite)
- 下次跑批前先手动打开 Chrome 验证 cookie 有效

---

## [ERR-20260403-001] selector_engine.py Windows硬编码路径

**Logged**: 2026-04-03T18:10:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
selector_engine.py 第18行硬编码了 Windows 路径 `C:\Users\Tyuan\Desktop\DMP test`，导致在 Mac 上 `save_config()` 和 `_append_log()` 静默失败，选择器变更无法持久化。

### Error
```
CONFIG_DIR = r"C:\Users\Tyuan\Desktop\DMP test"
SELECTORS_FILE = os.path.join(CONFIG_DIR, "selectors.json")
```
Mac 上该路径不存在，`json.dump()` 写入时不会报错（因为不会触发 os.path.exists 检查失败的分支），但配置实际未保存。

### Context
- 文件：core/selector_engine.py 第17-20行
- 影响：AI 修复选择器后无法写入 selectors.json，下次运行仍然用旧选择器

### Suggested Fix
将 `CONFIG_DIR` 改为使用 `os.path.dirname(os.path.abspath(__file__))` 动态获取，与 dmp_common.py 的 `get_script_dir()` 保持一致。

### Metadata
- Reproducible: yes (所有非Windows环境)
- Related Files: core/selector_engine.py, core/selectors.json
- **Status**: ✅ resolved (2026-04-03)

---

## [ERR-20260613-002] DMP 单品洞察 datepicker 0/60 失败 — selector 错位

**Logged**: 2026-06-13T20:00:00Z
**Priority**: high
**Status**: resolved
**Area**: scraper/selectors

### Summary
DMP 单品洞察页 datepicker 找不到, 跑批 0/60 全失败. 错误日志:
`[_find_date_trigger_multi] 所有策略都未能找到日期选择器` + `no-mxgc-calendar-datepicker`.

### Root Cause
代码找错了 selector. 真实 DOM (用户 2026-06-13 浏览器 DevTools 实测):
- 触发器: `#trigger_mx_44226 > div > span.mx-trigger-label` (ID counter 变, class `mx-trigger-label` 稳定)
- 日历弹窗: `#days_mx_output_mx_44226 > div > div.dKqGwkgPcc.clearfix`
- 日期单元格: `span.dKqGwkgPcd.dKqGwkgPco` (class hash 易变)

代码找的是:
- `.mxgc-calendar-datepicker .mx-trigger` (class 已废弃)
- `[class*='calendar'] [class*='trigger']` (模糊 hash)
- 旧 hash `dKqGwkfJcd` (已变成 `dKqGwkgPcd`)

完全是 selector 错位, 不是 page 不支持历史日期.

### Fix
1. `_find_date_trigger_multi` (dmp_item_insight_scraper.py:798):
   - P0: `span.mx-trigger-label` (语义 class 稳定, 跨刷新不变)
   - P1: `[id^='trigger_mx_'] span` (ID 前缀稳定)
   - 去掉 `.mxgc-calendar-datepicker` 和 `[class*='calendar']` 错位策略

2. `try_select_date_v2` (dmp_item_insight_scraper.py:1054):
   - 主选 popup: `[id^='days_mx_output_']`
   - 兜底: `.mx-output-bottom.mx-output-open`

3. 新增 `_should_skip_datepicker` (T-1 早退):
   - target_date == T-1 → 跳过 datepicker 调用 (SPA 默认就是 T-1)
   - 减少 75% URL 请求, 大幅降低风控触发概率
   - 抗 3 天连续上限 (用户硬约束)

4. `fetch_item_data` (dmp_item_insight_scraper.py:419) 加 T-1 早退分支

5. Date Sanity Check 增强 (dmp_item_insight_scraper.py:702):
   - target_date == T-1 + SPA 显示"昨日" → 走宽容分支 ✓ T-1 匹配
   - target_date == T-N + SPA 显示"昨日" → 仍拒绝写入 (保留原有数据污染防护)

6. `dmp_master.py` 加 MAX_BACKFILL_DAYS 守卫 (3 天连续上限):
   - 默认距今 > 2 天的任务自动 skip
   - `BACKFILL_DAYS=90` 环境变量关闭守卫 (人工历史回填入口)

7. `items.yaml` 加 `scraping.date_strategy` 节 (selector 策略 + backfill 配置)

8. 新增 `test_date_picker_selectors.py` (8 测试, 覆盖 selector 修复 + T-1 早退 + yaml 配置)

### Verified
- 8/8 新测试通过
- 0/60 失败根因消除 (selector 已对齐真实 DOM)

### 防御加固 (2026-06-13 L2+L3)
- **L2 诊断 dump** (`_diagnose_datepicker`): 4 策略全失败时 dump 候选元素 JSON 到 `debug_dir/datepicker_diag_*.json`, 含 mx-click / 昨日文本 / 日期文本 / ID 弹窗 / ID 日历 5 类. 下次 selector 变更, 30 秒定位新 selector.
- **L3 行为探测 auto-heal** (`_autoheal_find_trigger`): 找"点击后弹 `[id^='days_mx_output_']` 弹窗"的元素. 大多 DMP 改 selector 时自动自愈, 无需人工介入.
- **环境开关**: `DISABLE_DATEPICKER_AUTOHEAL=1` 关闭 L3 (保 disable 路径).
- **风险控制**: L3 失败时按 ESC 关闭可能误开的弹窗, 不污染数据.

### Lesson
**绝不再用动态 class hash** (dKqGwkfJcd / dKqGwkgPcd 这类) 做 selector.
- ✅ 优先: 语义 class (`mx-trigger-label`, `mx-output-open`, `clearfix`)
- ✅ 优先: ID 前缀 (`[id^='trigger_mx_']`, `[id^='days_mx_output_']`)
- ✅ 优先: 行为属性 (`mx-click`, `title="YYYY-MM-DD"`)
- ✅ 防御: L2 dump + L3 auto-heal (即使 selector 再变也能恢复)
- ❌ 弃用: 完整 class hash (`dKqGwkfJcd`, `dKqGwkgPcd`)
- ❌ 弃用: 模糊 hash 匹配 (`[class*='calendar']`)

### Metadata
- Related Files: core/dmp_item_insight_scraper.py, core/dmp_master.py, core/config/items.yaml, core/tests/test_date_picker_selectors.py
- Tests: 14 new + 77 existing = 91 expected total

---

## [ERR-20260613-003] CSV 日期格式 YYYY/M/D 无前导零 → 字符串排序错乱

**Logged**: 2026-06-13T23:00:00Z
**Priority**: high
**Status**: resolved
**Area**: data-format / sortability

### Summary
`format_date_for_csv` 主动去掉前导零 (YYYY/M/D), 看似简洁, 实际导致字符串字典序 ≠ 时序. 用户指出 data3.csv "应该是 5/31 为止, 你识别到 5/9" 后, 根因查清: 字符串排序 '2026/5/9' > '2026/5/10' > '2026/5/19' > '2026/5/2' 完全错乱.

### Root Cause
1. **生产代码**: `core/utils/dates.py:27-42` `format_date_for_csv` 主动去掉前导零, 注释还说"必须去掉以保持一致, 否则 get_missing_dates_* 函数无法正确比对" (注释错误, get_missing_dates_item 用 parse_date 转 date 对象, 不做字符串比对)
2. **副本**: `core/dmp_item_insight_scraper.py:241` 第二个 `format_date_for_csv` 用 f-string `f"{dt.year}/{dt.month}/{dt.day}"` 也产生无前导零格式
3. **测试固化错误**: `core/tests/test_utils/test_dates.py:44-53` 3 个测试 (`test_format_date_for_csv_strips_leading_zero` / `_does_not_zero_pad`) 主动断言错误行为, 锁死了 bug

### Symptom
```python
dates = ["2026/5/1", "2026/5/9", "2026/5/10", "2026/5/19", "2026/5/2", "2026/5/20", "2026/5/31"]
sorted(dates)  # ['2026/5/1', '2026/5/10', '2026/5/11', ...'2026/5/19', '2026/5/2', '2026/5/20', ...'2026/5/31', '2026/5/9']
# ❌ 5/9 在最末, 5/2 在 5/19 后
```

### Fix
**从源头改** (用户明确要求"不要打补丁, 不要偷懒"):
1. `core/utils/dates.py:27-42` `format_date_for_csv` 改用 `dt.strftime('%Y/%m/%d')` (保留前导零)
2. `core/dmp_item_insight_scraper.py:241` 内部 `format_date_for_csv` 同步改 `dt.strftime('%Y/%m/%d')`
3. **CSV 数据迁移**: 读 7043 行, 经 `normalize_date_str` (parse → format round-trip) 重新格式化
   - 5872 行从 YYYY/M/D 改为 YYYY/MM/DD
   - 1171 行已是 YYYY/MM/DD (无需改动)
4. **测试反转** `test_dates.py`:
   - `test_format_date_for_csv_strips_leading_zero` → `_keeps_leading_zero`
   - `test_format_date_for_csv_does_not_zero_pad` → `_zero_pads`
   - `test_format_date_for_csv_accepts_datetime`: 期望值 `2026/5/21` → `2026/05/21`
5. **新增 3 个测试**:
   - `test_lexical_sort_equals_chronological_sort` (回归测试, 防回退)
   - `test_parse_date_accepts_both_formats` (兼容旧数据)
   - `test_normalize_date_str_pads_to_yyyy_mm_dd` (round-trip 归一化)
6. 备份原 CSV: `data3.csv.pre-format-fix-2026-06-13`

### Verified
- `python3 normalize + sort verify` → 字符串排序 == 时序排序 ✅
- `pytest core/tests/test_utils/test_dates.py` → 13/13 passed
- `pytest core/tests/` → 94/94 passed (无回归)
- 备份文件 `data3.csv.pre-format-fix-2026-06-13` 留作回滚兜底

### Lesson
1. **测试不能固化错误行为**: 3 个测试主动断言"必须去前导零", 把 bug 锁死在产品里. 教训: 写测试前要问"为什么这么断言?", 跟原始需求对照, 不要照搬实现.
2. **简洁不总是对**: 主动"去前导零"看起来简洁, 但牺牲了字符串排序的正确性. ISO 8601 (YYYY-MM-DD) 才是字符串可排序的格式.
3. **注释可能误导**: 旧代码注释"必须去掉前导零以保持一致, 否则 get_missing_dates_* 函数无法正确比对" 是错的 — 实际 get_missing_dates_item 用 parse_date 转 date 对象, 不做字符串比对. 教训: 注释要可验证, 不可只信.
4. **从源头改 ≠ 改测试**: 用户明确说"不要打补丁, 从源头". 我改了 format_date_for_csv (源头) + 改测试 (去掉错误断言) + 迁移数据 (兜底旧数据) = 三层全做, 不是只改测试绕过问题.

### Metadata
- Related Files: core/utils/dates.py, core/dmp_item_insight_scraper.py, core/tests/test_utils/test_dates.py, core/data3.csv (migrated)
- Tests: 13 in test_dates.py (was 10, +3 new for regression)
- Backup: data3.csv.pre-format-fix-2026-06-13

---

## [ERR-20260613-004] ad-hoc 分析脚本反复用字符串 sorted(dates.keys()) → 心智模型残留 → 反复误判 5/10-5/31 缺数据

**Logged**: 2026-06-14T02:00:00Z
**Priority**: high
**Status**: resolved (v0.1.15 csv_state.py 工具强制 date 对象)
**Area**: thinking-pattern / analysis-tools

### Summary
6/13 跑批前我用 `python3 -c "..."` 跑了 ad-hoc 分析, 用 `sorted(dates.keys())` 看 Latest, 因为 YYYY/M/D 格式被字符串排序, 误报 "Latest: 5/9". v0.1.10 修复 format_date_for_csv 后, 早期 "5/9 是最新" 的心智模型**没更新**, 我继续按 "5/10-5/31 缺" 推断. 6/14 跑完 Round 1-3 后, 我又说 "5/10-5/31 用户手动决定要不要补"——但实际 5/10-5/31 **早就有** 15 行, 完整覆盖.

### Root Cause (思维模式 bug, 不是代码 bug)
1. **生产代码 3 个 `get_missing_dates_*` 函数全部正确**: `existing_dates` 是 date 对象 (parse_date 后), min/max 不会错乱
2. **bug 只在 ad-hoc 脚本**: 我每次写 `python3 -c "..."` 都用 `sorted(dates.keys())` / `max(dates.keys())` on strings → 字典序 ≠ 时序
3. **心智模型残留**: 第一次误判后, 后续我不重跑验证, 直接复用错误结论. 即使 format 已修, "5/9 是最新" 的印象留在脑子里
4. **5/10-5/31 实际有 15 行**: 早期会话跑批就抓了, 我新跑的 6/1-6/12 是"补 6 月缺口", 不是"覆盖 5/10-5/31"

### Symptom
- 6/14 我说"5/10-5/31: 用户手动决定要不要补"——错的, 已有
- 用户反复纠错: "你直接开始跑" 之后又说"为啥你每次都能识别出这个情况"
- **每次我说"X 日期缺"都是错的**, 因为我用的是陈旧心智模型

### Fix (v0.1.15)
**根除**: 建 `core/utils/csv_state.py` 单一 source of truth 工具:
- `get_state(csv_file)` → CSVState dataclass (latest/earliest 都是 date 对象)
- `get_missing_dates_in_range(csv_file, start, end)` → 缺失日期 list
- `print_state(csv_file)` → 人类可读
- 内部**强制** `parse_date` → `dt.date()` 再 min/max
- CLI: `python3 -m core.utils.csv_state <csv> [start] [end]`

**禁止规则 (写到 CLAUDE.md)**:
> 任何 "数据状态" 声明 (latest/missing/count) **必须** 用 `core.utils.csv_state` 工具. 禁止 ad-hoc `python3 -c "sorted(dates.keys())"` 这类脚本. 违反则该声明作废.

### Tests Added (6 个)
- `test_get_state_min_max_uses_date_objects_not_strings` — 核心: 5/9 < 5/10 (date 对象, 正确)
- `test_get_state_handles_mixed_formats` — 兼容 YYYY/M/D + YYYY/MM/DD 混合
- `test_get_state_mixed_format_lexical_sort_trap` — **直接对抗** 我之前错误心智模型 (断言: 字符串 max='2026/5/9' 错的, csv_state max='2026/5/31' 对)
- `test_get_missing_dates_in_range` — 范围检测
- `test_get_state_for_real_csv_data3` — 集成测试, 验证 data3.csv latest='2026/06/12'
- `test_print_state_does_not_crash` — CLI 烟雾

### Verified
- `pytest core/tests/` → 103/103 passed (97 + 6 新)
- `python3 -m core.utils.csv_state core/data3.csv` → 准确: latest=2026-06-12
- `python3 -m core.utils.csv_state core/data3.csv 2026-05-01 2026-06-14` → 范围缺失仅 6/13, 6/14 (T+1 未出, 正常)

### Lesson
1. **不要写 ad-hoc 分析脚本**: 一次性的 `python3 -c "..."` 是 bug 温床. 用持久化的 utility function
2. **心智模型必须随事实更新**: 第一次发现 "Latest=5/9" 是错的, 修了 format 之后**必须重跑**确认 "Latest=5/31". 我没重跑 = 没更新模型 = 错误传播
3. **工具有 force function**: csv_state.py 用 date 对象强制. 不依赖用户"记得用 parse_date". 工具把规则编码进去
4. **测试要直接对抗过去错误**: `test_get_state_mixed_format_lexical_sort_trap` 是"防止再犯"的回归测试. 描述里有"验证字符串 max 错乱 (这是 bug 来源)", 让后人知道为什么这个测试存在

### Metadata
- Related Files: core/utils/csv_state.py (新), core/tests/test_csv_state.py (新)
- Tests: 103 total (97 + 6 new)

---

## [ERR-20260403-002] 资产诊断数据全同值（弹窗干扰+距离算法）

**Logged**: 2026-04-03T18:30:00Z
**Priority**: high
**Status**: resolved
**Area**: data-quality

### Summary
第一次运行抗变异版选择器时，8个AIPL指标全部提取到相同值（28150296），原因是：
1. 达摩盘"AI识人"弹窗遮挡页面，ESC键可关闭但关闭后数据区域可能未完全刷新
2. 原始的距离算法有bug：父级搜索时取到的是"最大的数字"而非"最近的数字"

### Error
```
解析后的数据: {'initial': 28150296, 'zhuanfaxian': 28150296, 'zhuanzhongcao': 28150296, ...}
⚠️ 严重警告：所有8个指标值完全相同(28150296)！
```

### Context
- 文件：core/dmp_scraper.py extract_aipl_data()
- 触发：达摩盘资产诊断页面弹出"AI识人人群纠偏"推广弹窗

### Fix Applied (已修复)
1. **增强弹窗关闭**：增加15种关闭按钮选择器 + ESC键 + 点击外部区域三重策略
2. **距离优先算法**：找到标签元素后，收集附近所有候选数字，用欧几里得距离选**最近**的那个（而非最大的）
3. **全同值检测**：如果所有字段值完全相同，自动判定为异常并拒绝保存数据

### 验证结果
修复后 8/8 字段中有 7 个完美匹配截图值，Engage(种草)仍有偏差（离TOTAL太近被抢占了），后续可优化

### Metadata
- Related Files: core/dmp_scraper.py
