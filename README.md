# fuqing-scraper (芙清 DMP 数据采集)

> 达摩盘 SPA 自动抓数, Sprint 16 Wave 1 拆出独立 git repo
> v0.4.14.41 (2026-06-12, Sprint 19+ #141 治根)

## 跟主项目 fuqing-crm-analytics 解耦

独立 git repo, 22 模块拆分, 跟主项目 ETL/前端/Sprint 16.x backend 改动完全隔离。

- **项目路径**: `/Users/hutou/Desktop/fuqin-date/fuqing-scraper`
- **GitHub**: `git@github.com:weiweity/dmp-data-scraper.git` (main = `06cc0f3`)
- **父项目**: `fuqing-crm-analytics` (主项目 `scraper/` 目录仍保留, 尚未完成软删 + symlink; 仅被 `scripts/etl/notify.py` 引用)
- **跨子项目依赖**: **B1 治根 v0.4.14.53** (lark 通道 ETL 自治)
- **pytest**: **58/58 passed** (55 原有 + 3 Sprint 19+ #141 新增)
- **跑批业务**: data3.csv 7164 → 7209 (+45 行, 0 行污染, 6/9-6/11 全部补完)

## 5 件 Sprint 16-19+ 变更摘要

1. **Sprint 16 Wave 1 (v0.4.14.39)**: 5 个 580+ 行单文件 → 22 模块 (core/ 拆分 utils/validators/config/tests/)
2. **Sprint 16.5+1 (v0.4.14.40)**: 5 文档同步 (BUGFIX_2026-04-06 + 3 MEMO + launchd README)
3. **Sprint 19+ #141 (v0.4.14.41)**: `check_dmp_session` 业务层 session 验证 — 加 `/api_2/login/loginuserinfo` API 调用
4. **跨子项目 B1 治根 (v0.4.14.53)**: 主项目抽 `_send_lark_alert` 到 `scripts/etl/common/lark.py`, 3 ETL 脚本 import 改完
5. **GitHub 推送 (2026-06-12)**: 远程 `weiweity/dmp-data-scraper` main = `06cc0f3`, 跟本地 100% 同步

## Sprint 19+ #141 治根记录

**Root Cause (Playwright 监听器确诊)**:
- chrome_profile cookie 业务层失效 (HTTP 200 但 `/api_2/login/loginuserinfo` 业务码失效)
- SPA 检测后不跳顶级 page, 嵌 4 iframe (含千牛登录页)
- 顶级 page 仍 dmp.taobao.com 主页布局, 永不触发 goods/view/overview/v2

**check_dmp_session 假阳性 (dmp_common.py:444)**:
- 只检测 "立即登录" 按钮 + page_title 含 "登录"
- 不调 `/api_2/login/loginuserinfo` API 验证业务 session

**治根 (dmp_common.py:444-471)**:
- 加 `/api_2/login/loginuserinfo` API 调用 (page.evaluate fetch)
- 业务码失效 (body.data.isLogin=false) → 返 False (强制 login_qianniu 重登)
- API 异常 → 返 False (graceful fallback)

**测试 (3 新增, 55+3=58)**:
- test_check_dmp_session_valid_business_layer
- test_check_dmp_session_business_layer_invalid
- test_check_dmp_session_api_timeout

## 三大数据产品

| 类型 | 脚本 | 数据文件 | 频率 |
|---|---|---|---|
| 资产诊断 | dmp_scraper.py | data2.csv | T-1 |
| 流转数据 | dmp_flow_scraper.py | data.csv | T-2 |
| 单品洞察 | dmp_item_insight_scraper.py | data3.csv | 每日 |

## 快速开始

```bash
cd /Users/hutou/Desktop/fuqin\ date/fuqing-scraper
pip install playwright pyyaml
playwright install chromium
PYTHONPATH=. pytest core/tests/ -v   # 58/58 passed
cd core
python3 dmp_master.py --items  # 单品洞察
T_OFFSET=2 python3 dmp_master.py --items  # 早 9:00 (T-2)
T_OFFSET=1 python3 dmp_master.py --items  # 下午 16:00 (T-1)
```

## 验证

```bash
PYTHONPATH=. pytest core/tests/ -v   # 58/58 passed
ruff check core/
wc -l core/data3.csv               # ≥ 7000 行
```

## 目录结构 (22 模块)

```
core/ - dmp_master.py + dmp_common.py + dmp_scraper.py + dmp_flow_scraper.py
     + dmp_item_insight_scraper.py + anti_detect.py + sanity_check.py
     + run.sh + config/ (3) + utils/ (4) + validators/ (3) + tests/ (8)
```

## Sprint 4 5 工单 (留 backlog)

- #15 主项目 scraper/ 软删 + symlink (P0)
- #16 独立 repo 双层 scraper/ 清理 (P1)
- #17 5 行修 dmp_master.py:678 重建 + commit (P2)
- #18 简历文档 dmp-data-scraper.md 跟新 (P1)
- #19 SCRAPER-20-PLAN.md 创建 (P0, 本次)

详见 `docs/SCRAPER-20-PLAN.md` + `docs/SCRAPER-20-RETROSPECTIVE.md`。

## GitHub

https://github.com/weiweity/dmp-data-scraper
