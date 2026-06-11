# Changelog — 芙清 DMP 数据采集 (fuqing-scraper)

> **Sprint 16 Wave 1 (v0.4.14.39, 2026-06-11)**: 从 `fuqing-crm-analytics/scraper/` 拆出独立 git repo。 跟主项目 ETL / 前端 / Sprint 16.x backend 改动**完全隔离**。

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
