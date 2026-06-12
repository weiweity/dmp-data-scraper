# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 0. 项目是什么

**fuqing-scraper** — 芙清旗舰店 **达摩盘（DMP）** 数据自动采集工具（独立 git repo）。

| 维度 | 值 |
|---|---|
| 项目路径 | `/Users/hutou/Desktop/fuqin date/fuqing-scraper` |
| GitHub | `git@github.com:weiweity/dmp-data-scraper.git` (main = `06cc0f3`) |
| 版本 | **v0.4.14.41** (2026-06-12, Sprint 19+ #141 治根) |
| 父项目 | `fuqing-crm-analytics` (主项目 9bd4274, scraper/ 已软删) |
| 跨子项目依赖 | **B1 治根 v0.4.14.53** (lark 通道 ETL 自治) |
| pytest | **58/58 passed** (55 原有 + 3 Sprint 19+ #141 新增) |
| 跑批业务 | data3.csv 7164 → 7209 (+45 行, 0 行污染, 6/9-6/11 全部补完) |

> ⚠️ **不参与其他工单** (跟主项目 ETL/前端/backend 解耦, 留 Sprint 4 治理 backlog)

---

## 1. Sprint 16-19+ 5 件变更摘要 (必读)

**避免重复踩坑** — 后续 AI 必须知道:

1. **Sprint 16 Wave 1 (v0.4.14.39)**: 5 个 580+ 行单文件 → 22 模块 (core/ 拆分 utils/validators/config/tests/)
2. **Sprint 16.5+1 (v0.4.14.40)**: 5 文档同步 (BUGFIX_2026-04-06 + 3 MEMO + launchd README)
3. **Sprint 19+ #141 (v0.4.14.41)**: `check_dmp_session` 业务层 session 验证 — 加 `/api_2/login/loginuserinfo` API 调用
4. **跨子项目 B1 治根 (v0.4.14.53)**: 主项目抽 `_send_lark_alert` 到 `scripts/etl/common/lark.py`, 3 ETL 脚本 import 改完
5. **GitHub 推送 (2026-06-12)**: 远程 `weiweity/dmp-data-scraper` main = `06cc0f3`, 跟本地 100% 同步

**达摩盘数据特性**: T+1 跨日更新 (6/7 数据 6/8 下午 15:00 才出), 多次跑批会触发风控。

**调度**: `~/Library/LaunchAgents/com.fuqing.dmp-scraper.{morning,afternoon}.plist`
(需用户手动 `launchctl load`, auto mode 不允许 agent 加载)

详细见 `CHANGELOG.md` + `.learnings/ERRORS.md` + `core/README-dmp-scraper-launchd.md`。

---

## 2. 三层架构 (Master + Common + Scraper)

```
core/
├── dmp_master.py                 ← 统一入口 (--assets/--flow/--items)
├── dmp_common.py                 ← 公共模块 (Config/BrowserManager/login/CSV 工具, 444 行 re-export shim)
├── dmp_scraper.py                ← 资产诊断 (Y轴锚点 DOM 抓取)
├── dmp_flow_scraper.py           ← 流转数据 (Network API 拦截 + statusId=0 DOM 回退)
├── dmp_item_insight_scraper.py   ← 单品洞察 (API 拦截 + Date Sanity Check, 2826 行)
├── anti_detect.py                ← 反检测模块 (10 层防御)
├── sanity_check.py               ← 数据质量检查 (6 道门禁)
├── config/                       ← items.yaml + settings.py (Config 迁入此)
├── utils/                        ← dates.py / account.py / log.py / t_offset.py (4 文件)
├── validators/                   ← items/assets/flow 3 validators
└── tests/                        ← conftest.py + 55 + 3 = 58 tests
```

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

## 3. 关键约束 (跟主项目差异)

| 维度 | 约束 | 违规后果 |
|---|---|---|
| 写 CSV | **只追加不覆盖** | 数据丢失不可恢复 |
| 删除 `chrome_profile/` | **绝对禁止** | 登录态丢失, 需手动重登 |
| `headless=True` | 固定 | 有头下 API 拦截失败 (CLAUDE.md 0.3 6/8 修复) |
| 改 SPM | 不可回滚 (6/8 已修 `...OCRO8L` → `...lwdosJ`) | 旧 SPM 404 |
| 改 URL 模板 | 不可去掉 `&analysisTab=compete` | 单品洞察 6/8 修复 |
| check_dmp_session | 必须有业务层 API 调用 (Sprint 19+ #141 治根) | 业务码失效 scraper 不重登 |
| 跑批 dmp_master.py | 不在主项目跑 (主项目 scraper/ 已软删) | 跨子项目依赖违规 |
| launchctl load | user 手动 (auto mode 禁) | agent 违反 |

---

## 4. 启动方式 (独立 repo 路径)

```bash
# 进入项目根
cd /Users/hutou/Desktop/fuqin\ date/fuqing-scraper

# 安装依赖
pip install playwright pyyaml
playwright install chromium

# 跑测试 (58/58 passed)
PYTHONPATH=. pytest core/tests/ -v

# 跑批 (单 module, 5-10 min)
cd core
python3 dmp_master.py --items   # 单品洞察 (data3.csv, 每日)
python3 dmp_master.py --flow    # 流转数据 (data.csv, T-2)
python3 dmp_master.py --assets  # 资产诊断 (data2.csv, T-1)
python3 dmp_master.py           # 全部模块

# 跑批环境变量 (T+1 跨日保护)
T_OFFSET=2 python3 dmp_master.py --items  # 早 9:00 跑, 补 T-2
T_OFFSET=1 python3 dmp_master.py --items  # 下午 16:00 跑, 补 T-1
```

---

## 5. 验证项目

```bash
# 1. 验证 pytest
PYTHONPATH=. pytest core/tests/ -v
# 期望: 58 passed (55 原有 + 3 Sprint 19+ #141 新增)

# 2. 验证 ruff lint
ruff check core/

# 3. 验证 chrome_profile 登录态
ls -la chrome_profile/Default/Cookies  # 应 < 30 天 modified

# 4. 验证数据完整性
wc -l core/data3.csv                       # 应 ≥ 7000 行
grep "2026/6/9\|2026/6/10\|2026/6/11" core/data3.csv | wc -l  # 应 45 行 (3 天 × 15 商品)
```

---

## 6. 修改决策树

```
需要修改什么？
│
├── 抓取失败 / 选择器失效？
│   └── 修改对应 scraper 的提取逻辑
│       └── 用中文标签 + .font-tahoma 定位 (不要用随机 class 名)
│
├── 业务码失效 scraper 不重登？
│   └── 检查 check_dmp_session 是否调 /api_2/login/loginuserinfo (Sprint 19+ #141 治根)
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
│
├── Sprint 4 工单？
│   └── 5 个专有工单 (Task #20-#24) 留 Sprint 4 治理
│       └── 不参与主项目 ETL/前端/backend 治理
```

---

## 7. 5 个专有工单 (Sprint 4 backlog)

| # | 工单 | 优先级 | 状态 |
|---|---|---|---|
| **#15** | 主项目 scraper/ 软**删** + symlink (修正错报) | P0 | pending |
| **#16** | 独立 repo 双层 scraper/ 清**理** (`/scraper/core/` 跟 `/core/` 选一) | P1 | pending |
| **#17** | 5 行修 dmp_master.py:678 重建 + commit | P2 | pending |
| **#18** | 简历文档 `dmp-data-scraper.md` 跟新 (路径 → 独立 repo) | P1 | pending |
| **#19** | SCRAPER-4-PLAN.md 创**建** (Sprint 4 scraper 治理 backlog) | P0 | ✅ completed (v0.4.14.42) |

---

## 8. 文档索引

| 文档 | 路径 | 用途 |
|---|---|---|
| 项目说明 | `README.md` | 项目概述 + 快速开始 |
| 变更日志 | `CHANGELOG.md` | v0.4.14.39/40/41 完整记录 |
| SPA 拦截方法论 | `KB-数据采集-SPA接口拦截.md` | Network 拦截核心知识 |
| Bug 修复报告 | `core/BUGFIX_2026-04-06.md` | 新增人群数据为 0 修复 |
| 内部备忘 | `core/MEMO_2026-05-26.md` / `MEMO_2026-06-01.md` / `MEMO_2026-06-02.md` | Sprint 1 改动记录 |
| launchd 调度 | `core/README-dmp-scraper-launchd.md` | 调度文档 |
| 经验日志 | `.learnings/LEARNINGS.md` | 技术发现 + 最佳实践 |
| 错误日志 | `.learnings/ERRORS.md` | 已知错误 + 修复 |
| 功能需求 | `.learnings/FEATURE_REQUESTS.md` | 待实现功能 |
| 工作流指南 | `workflows/README.md` | 6 个 JS workflow 使用 |
| 清理报告 | `CLEANUP_FINAL.md` | 清理历史 |

---

## 9. 工作流 (6 个 JS)

```bash
# 在 Claude Code 中运行
Workflow({scriptPath: "workflows/dmp-daily-run.js"})      # 每日数据采集
Workflow({scriptPath: "workflows/dmp-data-sync.js"})      # 数据同步
Workflow({scriptPath: "workflows/dmp-data-fix.js"})       # 数据修复
Workflow({scriptPath: "workflows/dmp-data-verify.js"})    # 数据验证
Workflow({scriptPath: "workflows/dmp-monitor.js"})        # 监控告警
Workflow({scriptPath: "workflows/dmp-optimization.js"})   # 优化执行
```

⚠️ **路径不一致**: workflow JS 硬编码路径 `/Users/hutou/Desktop/work plat/DMP_test_package/core/`, 跟当前项目 `/Users/hutou/Desktop/fuqin date/fuqing-scraper/core/` **不**一致, 需更新后才能直接执行。

---

*此文件由 AI 维护, 最后更新 2026-06-12 (Sprint 19+ #141 治根收口)*
