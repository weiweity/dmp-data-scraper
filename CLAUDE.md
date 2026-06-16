# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 0. 文档路由 (新接手先读这里)

**项目是什么、3 个数据怎么流、22 个模块怎么协作** → [`docs/maintenance/ARCHITECTURE.md`](docs/maintenance/ARCHITECTURE.md)

**跑批失败 / ImportError / Date Sanity 误杀 / xinzeng 全 0** → [`docs/maintenance/HOW-TO-FIX.md`](docs/maintenance/HOW-TO-FIX.md)

**为什么这 4 个 fix 这么改 (parse_number / Date Sanity / xinzeng tab 顺序)** → [`docs/maintenance/LESSONS.md`](docs/maintenance/LESSONS.md)

**怎么读 + 怎么写 CHANGELOG** → [`docs/maintenance/CHANGELOG-GUIDE.md`](docs/maintenance/CHANGELOG-GUIDE.md)

> 本文件以下章节是 CLAUDE 项目的**长期约束** (4 准则 + 关键红线 + Git 工作流), 不是项目结构说明。

---

## 工作准则 (来自全局 CLAUDE.md, 已自动应用)

> 全局 4 条准则已自动从 `~/.claude/CLAUDE.md` 应用到所有项目。此处副本便于本项目独立查阅。

### 1. 编码前先思考
不假设、不隐藏困惑、呈现权衡。多种解释就呈现出来——不默默选；不清楚就停下来问。

### 2. 简洁优先
不做推测性工作；不为一次性代码创建抽象；不为不可能发生的场景做错误处理。200 行能用 50 行就重写。

### 3. 精准修改
只碰必须碰的地方。匹配现有风格，不要"改进"相邻代码。预先存在的死代码**提及即可，不要删**。

### 4. 目标驱动执行
把任务转为可验证目标（"添加验证"→"写测试并让它们通过"），循环直到验证通过。弱标准（"让它工作"）需要不断澄清。

---

## CodeGraph 索引 (MCP + CLI)

项目已建索引 — **32 文件 / 486 节点 / 1367 边 / 1.45 MB, 索引耗时 155ms**。

**MCP 工具** (Claude Code 内置, 写代码**前**查, **中**不查):
- `codegraph_explore "<问题或符号>"` — 一次调用返回相关符号源码（首选, Read 等价）
- `codegraph_callers <symbol>` / `codegraph_callees <symbol>` — 反向/正向调用
- `codegraph_impact <symbol>` — 重构前 blast radius
- `codegraph_files` / `codegraph_search` / `codegraph_status` / `codegraph_node`

**CLI** (在项目根):
```bash
codegraph status .                                # 索引健康
codegraph explore . "check_dmp_session 业务层"     # 重点函数源码
codegraph callers . read_account                  # 反向追踪
```

**节点类型分布**: function 211 / import 111 / variable 71 / constant 30 / method 25 / class 7

---

## 0. 项目是什么

**fuqing-scraper** — 芙清旗舰店 **达摩盘（DMP）** 数据自动采集工具（独立 git repo, 仅负责爬虫 + 生成数据）。

| 维度 | 值 |
|---|---|
| 项目路径 | `/Users/hutou/Desktop/fuqin-date/fuqing-scraper` |
| GitHub | `git@github.com:weiweity/dmp-data-scraper.git` |
| 版本 | **v0.1.24** (2026-06-14) |
| pytest | **113/113 passed** (v0.1.17 后 +24) |
| 跑批业务 | data3.csv ~7200 行 (单品洞察, 每日) |
| 索引统计 | 40 files / 566 nodes / 1573 edges (1.70 MB) |

> ⚠️ **本项目自包含**: 跟其他项目无 import / 调度 / 配置依赖。

---

## 1. 三层架构 (Master + Common + Scraper)

22 模块分层详见 [`docs/maintenance/ARCHITECTURE.md` §3](docs/maintenance/ARCHITECTURE.md#3-三层架构-master--common--scraper)。

```
core/
├── dmp_master.py                 ← 统一入口 (--assets/--flow/--items)
├── dmp_common.py                 ← 公共模块 (re-export shim, ~810 行)
├── dmp_scraper.py                ← 资产诊断 (Y轴锚点 DOM 抓取)
├── dmp_flow_scraper.py           ← 流转数据 (Network API 拦截 + statusId=0 DOM 回退)
├── dmp_item_insight_scraper.py   ← 单品洞察 (API 拦截 + Date Sanity Check, ~3250 行)
├── anti_detect.py                ← 反检测模块 (10 层防御)
├── sanity_check.py               ← 数据质量检查 (6 道门禁)
├── config/                       ← items.yaml + settings.py
├── utils/                        ← dates.py / account.py / log.py / t_offset.py / csv_state.py
├── validators/                   ← items/assets/flow 3 validators
└── tests/                        ← conftest.py + 113 tests
```

> 💡 **架构探查**: 不确定某函数在哪个文件？用 `codegraph_explore "dmp_master 入口分发"` 一次拿到。

**数据流**:
```
千牛后台 (dmp.taobao.com)
  → Playwright 浏览器 (headless=True, chrome_profile/ 持久化登录态)
  → dmp_master.py --items (单品洞察)
  → fetch_item_data() 注册 _ItemAssetCollector API 拦截
  → goods/view/overview/v2 拦截 + 12s Phase 1 轮询
  → api_data != {} → append_tocsv() 6 道门禁
  → data3.csv 追加 (append-only, ⚠️ 不覆盖)
```

---

## 2. 关键约束 (红线)

| 维度 | 约束 | 违规后果 |
|---|---|---|
| 写 CSV | **只追加不覆盖** | 数据丢失不可恢复 |
| 删除 `chrome_profile/` | **绝对禁止** | 登录态丢失, 需手动重登 |
| `headless=True` | 固定 | 有头下 API 拦截失败 |
| 改 SPM | 不可回滚 | 旧 SPM 404 |
| 改 URL 模板 | 不可去掉 `&analysisTab=compete` | 单品洞察数据缺失 |
| check_dmp_session | 必须有业务层 API 调用 (`/api_2/login/loginuserinfo`) | 业务码失效 scraper 不重登 |
| launchctl load | user 手动 (auto mode 禁) | agent 违反 |

---

## 3. 启动方式

```bash
# 进入项目根
cd /Users/hutou/Desktop/fuqin\-date/fuqing-scraper

# 安装依赖
pip install playwright pyyaml
playwright install chromium

# 跑测试 (113/113 passed)
PYTHONPATH=. pytest core/tests/ -v

# 一键启动 (项目根)
./START.sh                       # 运行全部模块
./START.sh -i                    # 单品洞察 (默认 T-1)
./START.sh -t 2 -i               # 单品洞察 T-2
./START.sh -b 30 -i              # 单品洞察回填 30 天
./START.sh -m                    # 实时监控最新日志
./START.sh -s                    # 查看 data3.csv 数据状态

# core/run.sh (等价入口, 支持交互菜单)
cd core
./run.sh -a                      # 资产诊断 (data2.csv)
./run.sh -f                      # 流转数据 (data.csv)
./run.sh -i                      # 单品洞察 (data3.csv, 默认 T-1)
./run.sh -A                      # 全部模块
./run.sh -m                      # 实时监控最新日志 (另一个终端)
./run.sh -s                      # 查看 data3.csv 最新/缺失日期

# 跑批环境变量 (T+1 跨日保护)
T_OFFSET=2 ./run.sh -i           # 早 9:00 跑, 补 T-2
T_OFFSET=1 ./run.sh -i           # 下午 16:00 跑, 补 T-1
BACKFILL_DAYS=30 ./run.sh -i     # 历史回填 30 天
```

> 日志位置: `core/del/run_logs/run_YYYYMMDD_HHMMSS_<module>.log`, 实时写入, 可用 `./run.sh -m` 在另一终端 tail。

---

## 4. 验证项目

```bash
# 1. 验证 pytest
PYTHONPATH=. pytest core/tests/ -v
# 期望: 113 passed

# 2. 验证 ruff lint
ruff check core/

# 3. 验证 chrome_profile 登录态
ls -la chrome_profile/Default/Cookies  # 应 < 30 天 modified

# 4. 验证数据完整性
wc -l core/data3.csv                       # 应 ≥ 7000 行
```

---

## 5. 修改决策树

```
需要修改什么？
│
├── 抓取失败 / 选择器失效？
│   └── 修改对应 scraper 的提取逻辑
│       └── 用中文标签 + .font-tahoma 定位 (不要用随机 class 名)
│
├── 业务码失效 scraper 不重登？
│   └── 检查 check_dmp_session 是否调 /api_2/login/loginuserinfo
│
├── 新增商品 ID？
│   └── 修改 core/config/items.yaml (单一来源)
│
├── CSV 数据异常？
│   └── 检查 .learnings/ERRORS.md 中是否有已知问题
│
├── 登录失效？
│   └── 手动打开 Chrome 重新登录千牛 → cookie 自动存 chrome_profile/
│       └── 不要删除 chrome_profile/ !
```

---

## 6. Git 工作流

### 禁止事项

| # | 禁止行为 |
|---|---|
| 1 | 跳过 `review` 直接 commit |
| 2 | 跳过 `qa` 直接 merge |
| 3 | merge 后不 pull 就重启 |
| 4 | 直接在 main commit |
| 5 | `commit -m "fix"` / `"update"` |
| 6 | commit 混多个不相关功能 |
| 7 | commit 后不 push |
| 8 | 跳过更新 CHANGELOG |

### 12 步流程

> ℹ️ 本项目版本采用 **v0.1.x 方案** (独立于任何外部项目, 便于识别爬虫版本)。

```
① git checkout -b feature/xxx
② 写代码
③ 更新 CHANGELOG  ← 写入 v0.1.x 标记 (本次: v0.1.0 = "Git 工作流新增")
④ pytest core/tests/ -x -q
⑤ review skill    ← 跑前必看 §4 验证项目
⑥ 修复 review 问题
⑦ git commit -m "feat: xxx"
⑧ git push origin feature/xxx
⑨ qa skill
⑩ git checkout main && git merge feature/xxx --no-ff
⑪ git push origin main
⑫ git pull origin main --ff-only
```

**v0.1.x 方案**:
- 首个版本 = v0.1.0
- 第三位 = 小变更 (例: v0.1.0 → v0.1.1, 修 typo / 文档 / lint)
- 第二位 = 新功能 (例: v0.1.1 → v0.2.0, 加新 scraper 模块)
- 第一位 = 大重构 (留作未来 v1.0.0 scraper 重写)

---

## 7. 文档索引

| 文档 | 路径 | 用途 |
|---|---|---|
| 项目说明 | `README.md` | 项目概述 + 快速开始 |
| 变更日志 | `CHANGELOG.md` | v0.1.x 版本历史 |
| SPA 拦截方法论 | `KB-数据采集-SPA接口拦截.md` | Network 拦截核心知识 |
| 经验日志 | `.learnings/LEARNINGS.md` | 技术发现 + 最佳实践 |
| 错误日志 | `.learnings/ERRORS.md` | 已知错误 + 修复 |
| 工作流指南 | `workflows/README.md` | 6 个 JS workflow 使用 |

---

## 8. 工作流 (6 个 JS)

```bash
# 在 Claude Code 中运行 (路径已对齐本项目)
Workflow({scriptPath: "workflows/dmp-daily-run.js"})      # 每日数据采集
Workflow({scriptPath: "workflows/dmp-data-sync.js"})      # 数据同步
Workflow({scriptPath: "workflows/dmp-data-fix.js"})       # 数据修复
Workflow({scriptPath: "workflows/dmp-data-verify.js"})    # 数据验证
Workflow({scriptPath: "workflows/dmp-monitor.js"})        # 监控告警
Workflow({scriptPath: "workflows/dmp-optimization.js"})   # 优化执行
```

> ℹ️ 6 个 JS workflow 路径已统一对齐本项目 `/Users/hutou/Desktop/fuqin-date/fuqing-scraper/core/`。

---

## 9. CodeGraph 暴露的技术债 (2026-06-13 识别)

### 🟡 P1: dmp_common.py 死代码 (~65 行)
`core/dmp_common.py` 中 `read_account` 函数体在迁移到 `utils/account.py` 后未清理。按 §3 准则"提及即可, 不要删"。

### 🟡 P1: 关键函数 0 测试覆盖
codegraph 标 "⚠️ no covering tests found":
- ~~`check_item_data_validity` (sanity_check.py:195) — 1 caller, **0 tests**~~ ✅ v0.1.17 关闭 (test_sanity_check.py 8 tests)
- ~~`apply_anti_detect` (anti_detect.py:537) — 1 caller, **0 tests**~~ ✅ v0.1.17 关闭 (test_anti_detect.py 3 tests)
- ~~`check_dmp_session` (dmp_common.py:374)~~ ✅ v0.1.17 关闭 (test_check_dmp_session.py 8 tests)

---

## 10. 严禁 ad-hoc 数据分析脚本 (2026-06-14, ERR-20260613-004)

> 任何"数据状态"声明 (latest/missing/count/range) **必须**用 `core.utils.csv_state` 工具. 禁止 ad-hoc `python3 -c "sorted(dates.keys())"` 之类.

### 工具用法

```bash
# 总体状态
python3 -m core.utils.csv_state core/data3.csv

# 范围缺失检测
python3 -m core.utils.csv_state core/data3.csv 2026-05-01 2026-06-14
```

### Python API

```python
from core.utils.csv_state import get_state, get_missing_dates_in_range, print_state
from datetime import date

state = get_state('core/data3.csv')
print(f"Earliest: {state.earliest_date}, Latest: {state.latest_date}")

missing = get_missing_dates_in_range('core/data3.csv', date(2026, 5, 1), date(2026, 6, 14))
print(f"Missing: {[d.isoformat() for d in missing]}")
```

### 为何禁止 ad-hoc
- `sorted(dates.keys())` 对 YYYY/M/D 字符串会字典序错乱 (e.g., '2026/5/9' > '2026/5/10')
- 我 (Claude) 反复犯此错, 6/13 误报 "Latest=5/9" → 心智模型残留 → 6/14 又说"5/10-5/31 缺" (实际早就有)
- csv_state.py 内部**强制** `parse_date` → `dt.date()` 再 min/max, 工具级杜绝

### 何时需要新分析
如果 csv_state.py 不能直接回答你的问题 (e.g., "每个商品 X 维度的均值"), 在 csv_state.py 加新函数 + 加测试, 不要在 ad-hoc 脚本里写.

详见 `.learnings/ERRORS.md` ERR-20260613-004.

---

## 11. P2 跳过的技术债 (2026-06-14 不动, 因为不懂)

| 问题 | 为何跳过 | 重启时机 |
|------|---------|---------|
| `dmp_item_insight_scraper.py` 2565 行单文件拆 (CLAUDE.md 写 3246 已过期) | 业务逻辑+DOM+日期+存储全纠缠, 拆错一个函数可能让 0/60 重现. 不知道每个函数的实际调用链. | ✅ **部分完成** (2026-06-16): `core/validators/items_validators.py` 已拆出 5 Gate 函数 (validate_item_data / validate_cross_day / _check_api_health / _detect_copy_day / _check_business_smoothness + send_lark_alert) + `core/tests/test_validators/test_items_validators.py` 8+ 测试. **但 dmp_item_insight_scraper.py 还有重复定义 (lines 1639-2128), 未启用 items_validators**. 完整启用需把 append_tocsv 签名从 (csv_file, data) 改成 (row, prev_row), 调用方先读 CSV 再传 dict — 风险高 (改 append_tocsv 是 P0 写路径). **重启时机**: append_tocsv 单元测试覆盖率 ≥ 80% 后, 单 PR 启用 |
| 异常处理 4 种风格统一 (log-only / log+return / log+raise / bare pass) | `except: pass` 在某处可能是 best-effort cleanup (e.g., 关闭浏览器 IO 失败). 改 log 反而引入新失败. 猜不出哪些是故意的. | ✅ **已建标准 (§12)** (2026-06-16): 不批量改, 但建立 4 风格决策表 + 观察期触发条件. 单点 fix 仍走 §0 流程 |
| 三模块 retry 策略统一 (items 60s / assets 10-14-18s / flow 无) | 不懂哪种对业务最合理. 改错会让抓批更不稳定. | ✅ **已建标准 (§12)** (2026-06-16): 文档化现状 + 各模块"何时该 retry"决策表. 跑批观察期触发条件. |
| `chrome_profile` basename vs 全路径混用 (`os.path.basename(self.config_obj.USER_DATA_DIR)`) | 可能是为了拿字符串当 folder name (Playwright 接受相对路径), 改成全路径可能错. 猜不到原意. | ✅ **已清** (2026-06-16 commit 7aec1e6): USING_COMMON=False 分支删除后, ConfigAdapter 的 get('paths')/get('browser') 也成为死代码, 顺手删 os.path.basename 死调用 |
| `_parse_date` / `_read_prev_row` 0 调用 (在 items_validators.py) | v0.1.16 已删. sanity_check.py 还在用 (3 调用), 不动. | ✅ **已清** (2026-06-16 commit 7b54989): 删 `_parse_date` 死 re-export, sanity_check.py 用自己的定义 (3 调用保留) |
| 4 处 bare `except: pass` (dmp_common:56, 71 / log.py:18, 29) | 同上, 可能是 best-effort cleanup. 不知道. | ✅ **已清** (2026-06-16 commit 6867dfa): 加 print 警告 (throttle 50 次一次避免刷屏). best-effort 语义保留, 但 silent fail → visible |
| `dmp_flow_scraper.py` 的 `format_date_for_csv` 有条件分支 (USING_COMMON 三元) | 不懂 USING_COMMON 是什么, 不敢简化. | ✅ **已清** (2026-06-16 commit 7aec1e6): USING_COMTERN 永远 True (dmp_master.py sys.path.insert + 测试用绝对 import). 删 21+ ternary + 52 行 fallback 定义 + 1 个死 buggy login_qianniu 包装 |
| SPM 硬编码在 settings.py | 不懂 SPM 是什么, 不敢改. | 不知道. |

---

## 12. 异常处理 + Retry 策略 标准 (2026-06-16 新增, §11 P2 第 2/3 件已建标准)

### 12.1 异常处理 4 风格决策表

| 风格 | 适用场景 | 示例 |
|------|---------|------|
| `log-only` (log + pass) | 真正 best-effort cleanup: 失败不影响主流程, 仅影响日志可观察性 | `os.makedirs(LOG_DIR, exist_ok=True)` 模块 init (dmp_common:55), `log()` 文件写 (dmp_common:70, utils/log.py:29), `BrowserManager.__exit__` 双重 close (dmp_common:336-342) |
| `log + return None/False` | 抓取失败但上层有 retry/兜底: 函数返回 falsy 让 caller 决定下一步 | `detect_encoding` (dmp_common:80), `read_account` 失败 (dmp_common:229), `_load_completed_items` 缓存读失败 (dmp_item_insight_scraper.py), `login_qianniu` 子步骤失败 (dmp_common:518-527, 679-680) |
| `log + raise` (or re-raise) | 数据完整性 / 业务不变量被破坏, 必须让 caller 知道 | `validate_item_data` 返回 (False, reason) 但 caller 仍 raise (append_tocsv), 配置文件 YAML 解析失败 (items_validators.py:96-109) |
| `bare pass` (no log) | **禁止**: 任何 silent fail 都难追. 2026-06-16 commit 6867dfa 已把 4 处典型 (`os.makedirs` / `log()`) 改成 log + throttle warning | — |

**何时打破规则**:
- 跑批发现某异常被吞掉导致后续崩溃 → 单点 fix (走 §0 Git 流程), 不要批量统一
- 新代码默认 `log + raise`, 除非确认是 best-effort cleanup 才用 `log + return`

### 12.2 Retry 策略 (各模块现状)

| 模块 | 当前策略 | 触发条件 | max wait |
|------|---------|---------|----------|
| **assets** (`dmp_scraper.py:332-338`) | 固定次数重试 + 递增等待 | `non_zero_count < 3` (有效数据 < 3) | 10s + 14s + 18s = **42s 总** |
| **items** (`dmp_item_insight_scraper.py:518-627`) | 3 阶段轮询 (无固定 retry count) | Phase 1: 12s 内 API 不响应; Fallback: 10s; Phase 2: ~24s (max_attempts=12, delay=1.5-2.5s) | **~46s 总** (但不重试, 一次性轮询) |
| **flow** (`dmp_flow_scraper.py`) | **无 retry**, 一次性抓取 | N/A | N/A |

**何时打破规则**:
- 跑批发现某模块频繁超时 → 单点调对应模块的 max_wait / retry count
- 切忌: 把 assets 的 42s 改成 items 的 46s, 或反向. 每模块业务不同 (资产诊断 / 单品洞察 / 流转数据)

### 12.3 观察期触发条件 (未来 fix 触发)

如果以下任一条件命中, 单独 fix 对应模块:

1. **异常被吞掉导致数据错乱**: `log-only` 实例中某个实际导致数据写入异常 → 单点改 `log + raise`
2. **某模块跑批成功率 < 90%**: 检查对应模块 retry 策略是否够 (assets 90% < → 考虑加 retry 4 次)
3. **某模块超时太频繁 (> 5% run 失败)**: 考虑放宽 max_wait

---

*此文件由 AI 维护, 最后更新 2026-06-16 (Tech debt §11 P2 第 1/2/3/4 件清完: bare except + _parse_date + USING_COMTERN + chrome_profile basename. 第 2/3 件建标准 (§12). 剩 3 件: 大文件拆 / SPM 硬编码)*
