# Lessons — 4 fixes from 2026-06-14

> 4 个 fix 各自的症状/根因/修复/防退化。每个 fix 是一节课,讲清"为什么"。

---

## Fix 1: v0.1.19 — `parse_number` re-export 误删

**症状**: `./START.sh` 起来直接
```
ImportError: cannot import name 'parse_number' from 'dmp_common'
```
**0/1** 资产诊断、流转、单品, **全部模块崩溃**。

**根因**:
v0.1.17 清理 dmp_common.py 死代码时 (commit c172244), 我把 `from core.utils.dates import parse_number` 当作 unused import 删了。但 `dmp_scraper.py:25` 仍 `from dmp_common import parse_number` — 这条 import 链没断,只是 re-export 表面变了。

**修复**:
```python
# core/dmp_common.py:37
from core.utils.dates import (
    parse_date,
    format_date_for_csv,
    normalize_date_str,
    parse_number,  # ← 加回
)
```

**防退化**:
- 改 `dmp_common.py` 之前先 `grep -rn "from dmp_common import" core/`, 看哪些 symbol 真在用
- 用 `ruff --select F401` 自动检查 unused, 但**人工复核** — F401 报 unused 不等于真的没 caller
- 加 re-export 单元测试: `python3 -c "from dmp_common import parse_number, parse_date, ..."` 每个 symbol 一个用例

---

## Fix 2: v0.1.20 — T-1 Date Sanity Check 格式不匹配

**症状**: 跑批 0/15, 15 个商品全部被 Date Sanity Check 拒绝, 日志反复:
```
⚠️ 严重：target_date=2026-06-13，但 SPA 显示'昨日'(2026/06/13)，URL 日期参数未生效
```

**根因**:
`date_str` 是 URL 格式 `2026-06-13` (YYYY-MM-DD), 但 `yesterday_str` 用 `format_date_for_csv` 生成 `2026/06/13` (YYYY/MM/DD)。**字符串比较永远不等**, 误杀了所有 T-1 正确数据。

注释里写过"用 `format_date_for_csv` 统一", 但我 (Claude) 没意识到它生成的是 `/` 分隔, 不是 `-`。

**修复**:
抽取 `_check_spa_date_match(date_str, spa_text, today_date)` 纯函数, **内部用 `YYYY-MM-DD` 比较**, 输出显示才用 `format_date_for_csv`。

```python
def _check_spa_date_match(date_str, spa_date_text, today_date=None):
    yesterday_str = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')  # ← 一致
    if '昨日' in spa_date_text:
        if date_str == yesterday_str:
            return True, format_date_for_csv(...), 'refreshed'
        return False, ..., 'refreshed'
    ...
```

**防退化**:
- 日期格式不要混用 — URL 参数用 `-`, CSV 内部用 `/`, 比较时统一选一个
- 加 5 个测试: `test_t_minus_1_yesterday_matches` / `test_t_minus_2_yesterday_does_not_match` / `test_specific_date_matches` / `test_specific_date_mismatch` / `test_unrecognized_text`
- 涉及日期的 if/else, 提取为纯函数 + 加测试, 不要在 fetch_item_data 里写大段 if

---

## Fix 3: v0.1.22 — xinzeng transfer API 慢响应 + 错过

**症状**: 6/7 起 data.csv 中 xinzeng (新增) 人群, initial > 0 但所有 transform 为 0。

**根因** (3 层):
1. `statusId=0` transfer API 响应延迟约 **10~15 秒** (我加日志调试后发现)
2. 原代码 `time.sleep(8)` 后取数, 经常在响应到达前就判定为空
3. 写 0 是因为没有 fallback — `extract_xinzeng_flow_by_dom()` 函数从 v0.1.0 就存在, 但**从未被调用**

**修复** (1):
```python
# 把 time.sleep(8) 改成轮询
max_wait = 25
for attempt in range(max_wait):
    time.sleep(1)
    collected = collector.get_data()
    if collected.get('xinzeng', {}).get('faxian'):
        break
```

**修复** (2, v0.1.21): 把 DOM fallback 接到 xinzeng 空数据后:
```python
if not collected.get('xinzeng', {}).get('faxian'):
    dom_flows = extract_xinzeng_flow_by_dom(page)
    if dom_flows:
        for key, val in dom_flows.items():
            collected['xinzeng'][key] = val
```

**防退化**:
- "API 慢响应" 现象在 DMP 各种数据里都可能, **通用套路**: 轮询 + timeout, 固定 sleep 8s 是反模式
- DOM fallback 函数**写完必须接到主流程**, 用 `git grep "def extract_xxx" | xargs git log` 验证它有 caller
- 加 transfer API 响应时长监控: 如果 `len(collected['xinzeng']) == 0` 且 target != T+1, 告警

---

## Fix 4: v0.1.23 — xinzeng tab 移首位 + 60s 轮询

**症状**: v0.1.22 修了 25s 轮询, 重跑发现还是 xinzeng faxian > 0, 但 zhongcao/hudong/xingdong/shougou 全 0。

**根因** (2 层):
1. **page.reload() 不触发新请求** — DMP 前端缓存了 transfer API 响应, reload 后等再久也等不到
2. **tab 顺序问题** — 旧顺序 `2001→2002→...→0`, xinzeng 放最后, 前一个 tab 的 `page.goto` 把浏览器切换走时, xinzeng transfer 还在途的请求**被丢弃**

**修复** (1): reload → goto
```python
# 旧
page.reload(wait_until="domcontentloaded", timeout=60000)
time.sleep(8)

# 新
xinzeng_url = f"...?statusId=0&..."
page.goto(xinzeng_url, wait_until="domcontentloaded", timeout=60000)
# 然后轮询 45s
```

**修复** (2, 关键): tab 顺序调整
```python
# 旧
all_status_ids = [2001, 2002, 2003, 2004, 2006, 2007, 2008, 0]

# 新 — xinzeng 放第一位
all_status_ids = [0, 2001, 2002, 2003, 2004, 2006, 2007, 2008]
```

为什么首位有效: 先发起 xinzeng transfer 请求, 后续访问其他 tab 时, 响应会异步到达, collector 自然捕获。放最后则永远等不到。

**修复** (3): 主页轮询 60s
```python
log("【API方案】等待所有API响应完成（重点等 xinzeng）...")
max_wait = 60
for attempt in range(max_wait):
    time.sleep(1)
    collected = collector.get_data()
    if collected.get('xinzeng', {}).get('faxian'):
        break
```

**防退化**:
- **多 tab 访问** + **SPA 异步 API** 场景, "慢响应的 tab 必须放第一个"
- **page.reload() 在 SPA 场景失效**, 默认用 page.goto 强制新请求
- 加 [API-COLLECTOR] 日志: `transfer statusId={sid} list_len={n}`, 监控每个 tab 是否真返回数据

---

## Fix 5: v0.1.28 — xinzeng click 触发替代 page.goto (ERR-20260616-006, 待真实 DMP 验证)

**症状**: Fix 4 修了 reload + tab 顺序, 但 6/7~6/15 连续 9 天 xinzeng (新增) 数据全 0. ERR-005 (v0.1.27) 修了 stale check (all-zero 不写入), 但 xinzeng 仍持续 0, 说明 stale check 不是根因, transfer API 根本没拿到数据.

**根因** (1 层, SPA 路由上下文):
- DMP 是 SPA 应用. `page.goto + statusId=0` 是"裸 URL 访问", SPA 路由上下文未建立
- DMP 后端需要 SPA 激活状态下的 tab 切换请求才返回 transfer 数据
- page.goto 对其他 statusId 有效是因为 SPA 已被激活; statusId=0 是 SPA 初始状态, 后端不返回 transfer
- 用户实测: "先随机点一个 tab, 再点 xinzeng tab" 才触发 → 暗示需要前置 SPA 激活 + 真实 click (而非 navigate)

**修复** (1): 新增 `click_xinzeng_tab(page)` evaluate-click
```python
def click_xinzeng_tab(page):
    """click DMP '新增' tab 触发 SPA transfer API."""
    result = page.evaluate("""
        () => {
            const allEls = document.querySelectorAll('*');
            for (const el of allEls) {
                const text = (el.innerText || el.textContent || '').trim();
                if (text !== '新增') continue;  // 精确匹配, 避免 '新增流转'
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                if (rect.left < 200) continue;  // tab 通常在左侧
                el.click();
                return { ok: true, top: rect.top, left: rect.left, text };
            }
            return { ok: false };
        }
    """)
    return result
```

**修复** (2, 关键): tab 顺序反转 (Fix 4 的反向操作)
```python
# 旧 (Fix 4 改的, statusId=0 首位)
all_status_ids = [0, 2001, 2002, 2003, 2004, 2006, 2007, 2008]

# 新 (Fix 5, statusId=0 末尾, 让前置 7 个 page.goto 建立 SPA 路由上下文)
all_status_ids = [2001, 2002, 2003, 2004, 2006, 2007, 2008, 0]
```

**修复** (3): 主循环 xinzeng 用 click 替代 page.goto
```python
for status_id, crowd_name in zip(all_status_ids, all_crowd_names):
    if status_id == 0:
        click_result = click_xinzeng_tab(page)
        if not click_result.get('ok'):
            # 降级到 page.goto (旧方案)
            page.goto(xinzeng_url, wait_until="domcontentloaded", timeout=60000)
    else:
        page.goto(tab_url, wait_until="domcontentloaded", timeout=60000)
```

**修复** (4): 兜底 click 重试
- 60s 轮询失败时, click_xinzeng_tab 重试一次, 仍失败降级 page.goto + DOM fallback

**防退化**:
- **SPA 初始状态用 click, 不用 page.goto**: page.goto 仅在 SPA 已激活状态下有效; 初始状态 tab 必须用真实 click 触发
- **tab 顺序与 SPA 路由上下文**: 前置 tab 的 page.goto 帮助建立 SPA 路由上下文, 此时再 click 初始状态才触发. tab 顺序敏感, 反转 (Fix 4 → Fix 5) 触发完全不同的行为
- **降级路径要保留**: click_xinzeng_tab 找不到 '新增' tab 时降级到 page.goto + DOM fallback, 双重防御
- **JS 防退化测试**: 测试断言 JS 字符串含 '新增' + el.click() + rect.left 过滤 + getBoundingClientRect, 防止未来 PR 误删关键条件

**Lesson**: SPA 应用 (DMP / 任何 React/Vue SPA) 对状态 0 / 初始状态 的 page.goto 处理与用户实际操作有差异. 通用规则: 自动化场景用真实 click 触发初始状态 tab. 这条对所有 SPA 自动化 (不是 DMP 独有) 都适用.

---

## Fix 6: v0.1.29 — check_dmp_session 反安全 timeout 逻辑 (ERR-20260616-006 子 bug, 与 Fix 5 同事件)

**症状**: 6/16 跑批 (Fix 5 验证) 时, scraper 全部 0 行, click_xinzeng_tab 全部 `{ok: False}`. 截图 `/tmp/test_goto_dmp.png` 显示 DMP 8 秒后重定向 `login.html`. 但 check_dmp_session 日志说"3 次 API 调用均无明确结果，**默认相信 cookie 有效**", scraper 进 scraper 浪费 90s × 9 天.

**根因** (2 层):
1. **chrome_profile/Cookies 实际失效**: DMP 后端对老 session 拒绝服务, 8 秒后强制 redirect login.html. 这是用户层问题 (cookie 过期), 不是代码问题.
2. **check_dmp_session 反安全逻辑**: Sprint 19+ #141 设计"3 次 API timeout → 信任 cookie" (当时认为 timeout = 网络抖动). 现实踩坑: cookie 失效时 fetch API 必然异常, "信任 cookie" = scraper 浪费跑批. 错误假设.

**修复** (1): check_dmp_session 保守化
```python
# 旧 (Sprint 19+ #141)
if is_login is None:
    log(f"...默认相信 cookie 有效")
    return True  # 反安全: 浪费 90s × N 天

# 新 (Fix 6)
if is_login is None:
    log(f"...保守视为失效，需重新登录")
    return False  # 宁可重登一次, 不浪费一天跑批
```

**修复** (2): 测试同步翻转
- `test_check_dmp_session_api_timeout`: True → False
- `test_check_dmp_session_all_timeout_returns_true` → `..._returns_false` (重命名)
- `test_check_dmp_session_custom_max_retries`: True → False

**防退化**:
- **API timeout = cookie 失效 (主因) ≠ 网络抖动 (罕见)**: 反 Sprint 19+ #141 "信任 cookie" 设计
- **跑批失败先看截图**: 日志说"check_dmp_session 3 次 timeout 默认信任" 看起来正常, 但截图直接显示 redirect login.html. 看截图比看日志快.
- **scraper 入口必须有 fail-fast**: check_dmp_session 返回 False 立即中止, 不要进 scraper 后才发现 cookie 失效

**Lesson**: Sprint 19+ #141 的设计意图 ("避免误判重登") 与现实 ("cookie 失效时 scraper 浪费跑批") 矛盾. 设计"信任"假设时必须考虑"最坏情况是什么", 不能只看 "常见情况是什么".

---

## 跨 6 个 fix 的共同教训

| 教训 | 应用场景 |
|---|---|
| **改 dmp_common.py 之前先 grep caller** | 任何 re-export shim 改动 |
| **字符串比较日期前先想格式** | 任何 Date Sanity / 跨格式比较 |
| **固定 sleep 是反模式, 改轮询** | 任何慢响应 API (DMP 普遍 10s+) |
| **写完的函数必须接进主流程** | DOM fallback / sanity check / 任何"备用"逻辑 |
| **SPA 场景用 page.goto 不用 page.reload** | 任何 DMP 内部页面切换 |
| **多 tab 顺序: 慢的放第一个** | 任何"逐个访问 X tab 抓数据" |
| **抽纯函数 + 加测试** | 任何 if/else 复杂判断 (Date Sanity) |
| **SPA 初始状态 tab 用 click, 不用 page.goto** | 任何 SPA 应用 statusId=0 / 路由初始状态 (DMP / React / Vue) |
| **tab 顺序: 初始状态 tab 放最后** | 任何"逐个访问 X tab" + SPA 异步 API 场景 |
| **降级路径必须保留** | 任何 evaluate-click 找不到时降级到 page.goto + DOM fallback |
| **check_dmp_session: API timeout → 视为失效 (保守)** | 反 Sprint 19+ #141 设计. 旧 "timeout → 信任 cookie" 让 scraper 浪费 90s × N 天 |
| **跑批失败必须先看截图, 不要只看日志** | del/api_flow_*.png 截图能直接看出页面是否真到目标页 |

---

## 经验沉淀的"行动级别"清单

接手这个项目时:

- [ ] 看 `core/dmp_common.py` 顶部 16 个 re-export 表面, 心里有数
- [ ] 看 `core/dmp_item_insight_scraper.py:_check_spa_date_match`, 知道怎么验日期
- [ ] 看 `core/dmp_flow_scraper.py` 的 `all_status_ids` 顺序 + `click_xinzeng_tab`, 知道 xinzeng 在**末尾** (Fix 5 反转), 用 click 触发而非 page.goto (ERR-20260616-006)
- [ ] 看 `core/run.sh` / `START.sh`, 知道有 `-m/-s/-t/-b` 4 个新选项
- [ ] 跑 `./START.sh -s` 看 data3.csv 状态, 验证环境 OK
- [ ] 跑 `PYTHONPATH=. pytest core/tests/ -q` 看 128/128 passed
