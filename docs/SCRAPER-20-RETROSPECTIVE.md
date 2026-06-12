# Sprint 16.5+1 + 19+ Retrospective — fuqing-scraper 收口

> 独立 repo fuqing-scraper Sprint 16.5+1 (v0.4.14.40) + Sprint 19+ #141 (v0.4.14.41) 完整收口
> 创建: 2026-06-12, 跟主项目 Sprint 19 retrospective 9bd4274 同步

## Sprint 16.5+1 收口 (v0.4.14.40 + 跨子项目 B1 治根 v0.4.14.53)

### 4 阶段执行

1. **阶段 1 独立 repo 补 5 文档**: 隐式同步 (5 文档已在 Sprint 16 Wave 1 commit 10ff8da)
2. **阶段 2 独立 repo pytest 验证**: 55/55 passed 0.04s (dmp_common.py Wave 1 shim 完整)
3. **阶段 3 CHANGELOG 双向同步**: 独立 v0.4.14.40 (5 文档记录) + 主项目 v0.4.14.52 (Sprint 16.5+1 scraper hotfix)
4. **阶段 4 跨子项目 B1 治根** (user 拍板 B1 治根跨子项目依赖):
   - **新建 scripts/etl/common/__init__.py**
   - **新建 scripts/etl/common/lark.py** (94 行, 1:1 复刻 _send_lark_alert)
   - **scripts/etl/notify.py:13-17** 改 import
   - **scripts/etl/assertions.py:37** 改 import
   - **scripts/etl/dq_monitor.py:73** 改 import
   - **pytest backend/tests/**: 507 passed

### 教训

- 跨子项目依赖是隐性债 (Sprint 16.5+1 阶段 4 才暴露)
- 5 文档隐式同步 (Sprint 16 Wave 1) 需正式记录 (v0.4.14.40 entry)
- 跨子项目依赖用 lint 检测 (留 Sprint 20+ 治理)

## Sprint 19+ #141 治根 (v0.4.14.41)

### Root Cause (Playwright 监听器确诊)

- chrome_profile cookie 业务层失效 (HTTP 200 但 /api_2/login/loginuserinfo 业务码失效)
- SPA 检测后不跳顶级 page, 嵌 4 iframe (含千牛登录页)
- 顶级 page 仍 dmp.taobao.com 主页布局, 永不触发 goods/view/overview/v2

### check_dmp_session 假阳性 (dmp_common.py:444)

- 只检测 "立即登录" 按钮 + page_title 含 "登录"
- 不调 /api_2/login/loginuserinfo API 验证业务 session

### 治根 (dmp_common.py:444-471)

- 加 /api_2/login/loginuserinfo API 调用 (page.evaluate fetch)
- 业务码失效 (body.data.isLogin=false) → 返 False (强制 login_qianniu 重登)
- API 异常 → 返 False (graceful fallback)

### 测试 (3 新增, 55+3=58)

- test_check_dmp_session_valid_business_layer
- test_check_dmp_session_business_layer_invalid
- test_check_dmp_session_api_timeout

### 教训

- HTTP 200 不代表业务有效 (千牛 DMP SPA 业务码独立)
- check_dmp_session 必须有业务层 API 验证 (单 HTTP 200 检测不够)
- Playwright 监听器 (request/response/console/frame) 是确诊运行时证据的必备工具

## 跑批业务不阻塞

- data3.csv 7164 → 7209 (+45 行 = 3 天 × 15 商品, 0 行污染)
- 6/9 + 6/10 + 6/11 全部补完
- 业务码失效 scraper 永远会走 login_qianniu 重登 (Sprint 19+ #141 治根)
- 跨子项目依赖: B1 治根 (v0.4.14.53, lark 通道 ETL 自治)
- GitHub 推送: weiweity/dmp-data-scraper main = 06cc0f3

## 留 Sprint 20+ 治理 (5 工单)

- #15 主项目 scraper/ 软删 + symlink (P0)
- #16 独立 repo 双层 scraper/ 清理 (P1)
- #17 5 行修 dmp_master.py:678 重建 + commit (P2)
- #18 简历文档 dmp-data-scraper.md 跟新 (P1)
- #19 SCRAPER-20-PLAN.md 创建 (P0, 本 PR)
