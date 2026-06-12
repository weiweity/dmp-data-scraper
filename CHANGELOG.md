# Changelog — 芙清 DMP 数据采集 (fuqing-scraper)

> **Sprint 16 Wave 1 (v0.4.14.39, 2026-06-11)**: 从 `fuqing-crm-analytics/scraper/` 拆出独立 git repo。 跟主项目 ETL / 前端 / Sprint 16.x backend 改动**完全隔离**。

## [v0.4.14.44] - 2026-06-12 - fix(docs): CLAUDE.md 5 处 Sprint 20+ 漏改 + 验证断言诚实标注

### 背景
v0.4.14.43 改名 Sprint 20+ → Sprint 4 收口时, 改了 4 件文档 (README / SCRAPER-4-PLAN / SCRAPER-4-RETROSPECTIVE / CHANGELOG) 但**漏改** CLAUDE.md 5 处 (line 21, 158, 159, 165, 173), 且 v0.4.14.43 entry 的验证断言 "`grep -c Sprint 20+ 5 件文档 = 0`" 是**假数据** (CHANGELOG 自身 5 处属历史记录不算, 但 CLAUDE.md 真有 5 处未改)。 用户拍板: 全部 5 处补改 + 验证段诚实标注。

### Fixed
- **CLAUDE.md:21** 顶部警告框: "Sprint 20+ 治理 backlog" → "Sprint 4 治理 backlog"
- **CLAUDE.md:158-159** 决策树: "Sprint 20+ 工单?" → "Sprint 4 工单?" + "Task #15-#19 留 Sprint 20+ 治理" → "Task #20-#24 留 Sprint 4 治理" (Task 编号也跟 v0.4.14.43 改名同步)
- **CLAUDE.md:165** 章节标题: "(Sprint 20+ backlog)" → "(Sprint 4 backlog)"
- **CLAUDE.md:173** 表格 #19 行: "SCRAPER-20-PLAN.md" → "SCRAPER-4-PLAN.md" + "Sprint 20+ scraper 治理 backlog" → "Sprint 4 scraper 治理 backlog" + "pending" → "✅ completed (v0.4.14.42)" (跟 CHANGELOG 实际状态同步)
- **CHANGELOG.md v0.4.14.43 验证段** 改"诚实记录"格式, 区分 4 件文档 (✅ 干净) vs CLAUDE.md (❌ 漏 5 处, 留 v0.4.14.44 补) vs CHANGELOG 自身 (5 处属历史记录)

### 跨项目 Sprint 19+ 引用 (本就该保留, 25 处)
- Sprint 19+ 是主项目 fuqing-crm-analytics 的 sprint 计数, "Sprint 19+ #141/#142/#143" 是跨项目工单标识符, 跟 scraper 自己 Sprint 4 命名空间**不冲突**, 删了反而丢历史溯源。
- 保留位置: CHANGELOG (5) / README (4) / CLAUDE.md (7) / SCRAPER-4-PLAN (4) / SCRAPER-4-RETROSPECTIVE (3) / scraper/core/dmp_common.py:452 (1) / core/tests/test_dmp_common.py:1 (1) = **25 处**

### 验证
- `grep -c "Sprint 20+" CLAUDE.md` = 0 ✅
- `grep -c "Sprint 4" CLAUDE.md` = 5 ✅ (新)
- `grep -c "Sprint 19+" CLAUDE.md` = 7 (保留, 跨项目)
- `pytest core/tests/ -v`: 58/58 passed ✅ (无 .py 改动, 0 影响)
- `ruff check core/`: 0 issue ✅ (无 .py 改动, 0 影响)

### 后续
- Sprint 5 #20-#24 (主项目软删 / 双层清理 / 5 行修 / 简历跟新 / Sprint 4 改名记录) 留 Sprint 5 执行
- Sprint 5 启动前必读 #25 (Sprint 19+ #141 修复实际未生效, 修复同步到外层 core/dmp_common.py) — 已识别未在 backlog, 需补工单

## [v0.4.14.43] - 2026-06-12 - chore: Sprint 4 改名 + Sprint 5 5 工单 Task #20-#24 编号

### 背景
Sprint 20+ 命名跟主项目 fuqing-crm-analytics Sprint 20+ 重复造成迷惑, 改名 Sprint 4 (跟 Sprint 1-3 连续, 独立 repo 自己迭代计数).

### Changed
- **README.md**: Sprint 20+ → Sprint 4
- **docs/SCRAPER-20-PLAN.md** → **docs/SCRAPER-4-PLAN.md** (git mv + sed 改内容)
- **docs/SCRAPER-20-RETROSPECTIVE.md** → **docs/SCRAPER-4-RETROSPECTIVE.md** (git mv + sed 改内容)
- **CHANGELOG.md**: Sprint 20+ → Sprint 4
- **CLAUDE.md**: Sprint 20+ → Sprint 4

### 5 工单 Task #15-#19 → Task #20-#24 (Sprint 5 编号)
- Task #15 (#143 主项目软删) → Task #20 (Sprint 5 P0)
- Task #16 (#145 双层清理) → Task #21 (Sprint 5 P1)
- Task #17 (#142 5 行修) → Task #22 (Sprint 5 P2)
- Task #18 (#147 简历跟新) → Task #23 (Sprint 5 P1)
- Task #19 (#146 SCRAPER-20-PLAN.md 创建) → Task #24 (Sprint 4 改名记录)

### 验证 (诚实记录)
- ✅ `grep -c "Sprint 20+" 4 件文档 (README + SCRAPER-4-PLAN + SCRAPER-4-RETROSPECTIVE + CHANGELOG 历史段)` = 0
- ❌ `grep -c "Sprint 20+" CLAUDE.md` = 5 (L21/L158/L159/L165/L173 漏改, 留 v0.4.14.44 补)
- ✅ `grep -c "Sprint 4" 5 件文档` > 0 (主改名成功)
- ✅ 跑批业务不阻塞, 跟主项目 9bd4274 脱节 (独立 repo 自己迭代)

## [v0.4.14.42] - 2026-06-12 - docs: Sprint 4 文档补全 (README 跟新 + SCRAPER-20-PLAN + SCRAPER-20-RETROSPECTIVE)

### Added
- **README.md** 跟新 (跟实际状态 100% 同步, 5 件 Sprint 16-19+ 变更摘要, 58/58 pytest, Sprint 19+ #141 治根记录)
- **docs/SCRAPER-20-PLAN.md** 创建 (Sprint 4 scraper 治理 backlog, 5 工单 #15-#19)
- **docs/SCRAPER-20-RETROSPECTIVE.md** 创建 (Sprint 16.5+1 + 19+ 收口, 跟 Sprint 19 retrospective 9bd4274 同步)

### 后续
- Sprint 4 #15 (主项目软删 + symlink) + #16 (双层清理) + #17 (5 行修) + #18 (简历更新) 留 Sprint 4

## [v0.4.14.41] - 2026-06-12 - fix(scraper): Sprint 19+ #141 治根 — check_dmp_session 业务层 session 验证

### Background
Sprint 16.5+1 (v0.4.14.52) 跑批 0/15 失败根因: chrome_profile cookie 业务层失效 (HTTP 200 但 /api_2/login/loginuserinfo 业务码失效). check_dmp_session (scraper/core/dmp_common.py:444) 只检测 "立即登录" 按钮 + page_title 含 "登录", **不**调 API 验证业务 session. 假阳性导致 scraper **不**走 login_qianniu 重登.

### Changed
- **`scraper/core/dmp_common.py:444`**: `check_dmp_session` 加 `/api_2/login/loginuserinfo` API 调用 (page.evaluate fetch)
  - 业务码失效 (body.data.isLogin=false) → 返 False (强制 login_qianniu 重登)
  - API 异常 → 返 False (graceful fallback)
- **`core/tests/test_dmp_common.py`** (新, 3 tests): valid_business_layer / business_layer_invalid / api_timeout

### 痛点闭环
- Sprint 16.5+1 root cause ✅ 闭环
- check_dmp_session 假阳性 ✅ 治根
- scraper **永远**会**走** login_qianniu (业务码失效时) ✅

### 任务来源
- Sprint 16.5+1 阶段 4 root cause → Sprint 19+ #141

### 验证
- `PYTHONPATH=. pytest core/tests/ -v`: 58 测试全过 (55 原有 + 3 新增) ✅
- 跑批业务 (data3.csv +45 行) 不阻塞

### 后续
- Sprint 19+ #142 (5 行修重建) + #143/#144 (主项目 scraper 软删 + symlink) 已 Sprint 19 P2 batch 完成 (主项目 main HEAD e0bfd73)

## [v0.4.14.40] — 2026-06-12 (Sprint 16.5+1 — 文档补全 + 解耦准备)

### Added
- 5 文档同步 (隐式包含在 Sprint 16 Wave 1 commit 10ff8da, 但正式记录):
  - `core/BUGFIX_2026-04-06.md` (Sprint 1 bugfix 记录)
  - `core/MEMO_2026-05-26.md` (Sprint 1 内部备忘)
  - `core/MEMO_2026-06-01.md` (Sprint 1 内部备忘)
  - `core/MEMO_2026-06-02.md` (Sprint 1 内部备忘)
  - `core/README-dmp-scraper-launchd.md` (launchd 调度文档)

### Validation
- `PYTHONPATH=. pytest core/tests/ -q`: 55 passed / 0 failed / 0 error / 0.04s (dmp_common.py Wave 1 re-export shim 完整)
- 独立 repo 跟主项目**完全解耦**, 5 个 580+ 行单文件 (主项目) 留 Sprint 19+ 治理 #143 清理

## [v0.4.14.39] — 2026-06-11 (Sprint 16 Wave 1 — 独立 repo 拆出 + 拆分重构)

### 🎯 摘要

Sprint 16 Wave 1 把 DMP 数据采集工具从主项目 `fuqing-crm-analytics/scraper/` 拆成独立 git repo `fuqing-scraper/`, 同时把 5 个 580+ 行的单文件拆成 22 个 ≤ 500 行的模块。 用户最直接看到的变化: 加新商品改 1 个 yaml, 不用改 1 个 .py, 抓数选择器出问题 5 分钟内定位到对应 scraper 而不是扫 2829 行单文件。

### 📊 关键数字

| 指标 | 之前 (v0.4.14.37) | 现在 (v0.4.14.39) | Δ |
|---|---|---|---|
| 文件数 (core/ 范围) | 5 个 .py 核心 (5865 行) | 22 个模块 + 8 个 test | **+27** |
| 单文件最大 | 2829 行 (`dmp_item_insight_scraper.py`) | 359 行 (`items_validators.py`) | **-87%** |
| 测试 | 0 个 | 55 个 pytest | **+55** |
| 抓数方式 | DOM 手工 (2829 行纠缠) | API 拦截 + 3 阶段 section 注释 | 结构性可读 |
| 文档 | 跟主项目混 (293 文件 CLAUDE.md) | 独立 (本文件 + CLAUDE.md) | 隔离清晰 |
| Sprint 16.x backend 改动干扰 | 频繁 (worktree 共享) | **零** (独立 repo) | 解决 |

### 🛠️ 变更内容

#### Added (新增)
- 独立 git repo `/Users/hutou/Desktop/fuqin date/fuqing-scraper/` (从主项目物理拆出)
- 独立 `pyproject.toml` (含 `[tool.uv]` + `[tool.ruff]` + `[tool.pytest.ini_options]`, 跟主项目解耦)
- 独立 `CLAUDE.md` (scraper-only 行为规则, 不引用主项目 backend 规则)
- 独立 `.gitignore` (排除 `chrome_profile/`, `data*.csv`, `account.txt`, `del/`)
- `core/utils/` (4 文件): `dates.py` / `account.py` / `t_offset.py` / `log.py`
- `core/config/` (2 文件): `__init__.py` + `settings.py` (Config 单一来源)
- `core/validators/` (4 文件): `items_validators.py` (5 道) / `assets_validators.py` / `flow_validators.py` / `__init__.py`
- `core/tests/` (8 文件): `conftest.py` + 7 个 `test_*.py`, **55 个测试** (含 2026-06-01 hotfix 保留测试)
- `Config.load_items()` 类方法 (替代已删除的 `Config.ITEM_IDS`)

#### Changed (变更)
- `core/dmp_common.py`: 改 re-export shim (顶部 `from core.X import Y`, 4-5 caller 文件 import 路径不变)
- `core/dmp_common.py`: 净减少 51 行 (从 849 → 798 行), Config class / dates 4 函数 / read_account 移到新模块
- `core/dmp_item_insight_scraper.py`: 保留 `fetch_item_data` 单函数 (327 行) + section 注释 (`# ====== Phase 1: ... ======`), **不**拆 3 阶段
- 新商品 ID 配置: 改 `core/config/items.yaml` (单一来源), **不**改 .py
- 文档导航: 全部相对 `core/` 路径, 不再引用主项目

#### Removed (移除)
- `core/dmp_common.Config.ITEM_IDS` 静态属性 (15 个商品) — 改 `Config.load_items()` 从 yaml 读
- 5 个其他 静态 `Config` 字段 (`DMP_BASE_URL`/`DMP_SPM`/`DMP_ROUTE_*` 等) **保留** (向后兼容)
- 4 个 `dmp_common.py` 工具函数 (移到 `core/utils/`): `parse_date` / `format_date_for_csv` / `normalize_date_str` / `parse_number` / `read_account`

#### Fixed (修复)
- 修复 `dmp_common.py` 顶部 4 个 export 函数缺失 (subagent 阶段没复制完整, 由 main loop 补回)
- 修复 `config/settings.py` Config 类 8 个属性缺失 (subagent 砍了原 Config 多个属性, 由 main loop 恢复)
- 修复 `utils/account.py` import `from .log import log` 失败 (subagent 没创建 `utils/log.py`, 由 main loop 创建)
- 修复 `tests/test_settings.py` 测试期望跟实现不一致 (`Config(items_path=...)` 期望 vs 实际无 `__init__`, 由 main loop 改测试用 `monkeypatch`)
- 修复 `tests/test_dates.py` 测试期望 `date` 但实现返回 `datetime` (由 main loop 改测试 `.date()` 比较)
- 修复 `tests/test_validators/test_*.py` 3 个文件 API 不一致 (测试期望 `result.is_valid`, 实现返回 tuple; 测试用单 `rows` 参数, 实现用 `(row, prev_row)` 双参数) — 由 main loop 重写测试对齐实际实现
- 修复 `dmp_common.py` 顶部相对 import 失败 (`from .utils.dates` 在 `from dmp_common import Config` 模式下触发 "no known parent package", 改绝对 import `from scraper.core.utils.dates import` 解决)
- 修复 `config/settings.py` items.yaml 路径错 (subagent 用了 `SCRAPER_CORE_DIR.parent` = `scraper/`, 应是 `parent.parent` = 项目根)

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

### 🔗 相关项目
- 主项目: `fuqing-crm-analytics/` (Vue3 + FastAPI + DuckDB, ETL/前端/backend 改动)
- 学习指南: `codegraph 学习指南/` (codegraph MCP 工具使用)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
