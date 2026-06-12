# Sprint 4 Plan — fuqing-scraper 治理 backlog

> 独立 repo fuqing-scraper 后续治理计划
> 创建: 2026-06-12, 跟 Sprint 19 retrospective 9bd4274 同步

## 背景

Sprint 16 Wave 1 (v0.4.14.39) 拆出独立 repo, Sprint 16.5+1 (v0.4.14.40) 5 文档同步, Sprint 19+ #141 (v0.4.14.41) 治根 check_dmp_session 业务层 session 验证, B1 治根 (v0.4.14.53) 跨子项目依赖解耦, GitHub 推送 weiweity/dmp-data-scraper main = 06cc0f3。 Sprint 4 5 工单留 backlog, 跟主项目 fuqing-crm-analytics 9bd4274 同步, 跑批业务不阻塞 (data3.csv 7164 → 7209, 0 行污染)。

## 5 工单 (按执行顺序)

### P0 #19 SCRAPER-20-PLAN.md 创建 (本工单)
- **状态**: ✅ completed (本 PR)
- **内容**: docs/SCRAPER-20-PLAN.md
- **执行**: 本 subagent

### P0 #15 主项目 scraper/ 软删 + symlink
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-crm-analytics
- **修正**: 之前错报"已软删", 实际还有 (15 子目录, 6/8 15:13)
- **步骤**:
  1. 切 fix/sprint20-143-scraper-soft-delete 分支 from main 9bd4274
  2. mv scraper scraper.legacy
  3. ln -s /Users/hutou/Desktop/fuqin-date/fuqing-scraper scraper
  4. 验证 (python3 -c "from scraper.core import dmp_common; print('OK')")
  5. 跑 pytest backend/tests/ 验证 507 passed
  6. 走 12 步流程 + CHANGELOG v0.4.14.55
- **风险**: 主项目跑批影响 (scraper/ 软删后跑批走 symlink → 独立 repo)
- **执行**: Sprint 4 第 2 工单

### P1 #16 独立 repo 双层 scraper/ 清理
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-scraper
- **问题**: `/scraper/core/` 跟 `/core/` 内容部分重叠 (Sprint 16 Wave 1 拆出时外层 scraper/ 没清理)
- **步骤**:
  1. 切 fix/sprint20-145-double-layer-cleanup 分支 from main 06cc0f3
  2. 验证哪一层是真正活跃的 (外层 6/8 vs 内层 6/11)
  3. 删除冗余的一层 (大概率外层 scraper/ 全删)
  4. 验证 pytest 55+3=58 passed
  5. 跑 dmp_master.py --items 验证 (data3.csv +0 行, 跑通即可)
  6. 走 12 步流程 + CHANGELOG v0.4.14.42 (本 PR 同步)
- **风险**: 删除错误的层 (先备份)
- **执行**: Sprint 4 第 3 工单

### P2 #17 5 行修 dmp_master.py:678 重建 + commit
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-scraper
- **状态**: 5 行修未真正 commit, 7 个 dangling 都没 marker
- **步骤**:
  1. 切 fix/sprint20-142-5-line-rebuild 分支 from main 06cc0f3
  2. 重新 Edit core/dmp_master.py:678 加 5 行 (在 if args.items: 内, for 循环之前)
  3. 验证 git diff 5 行净增
  4. 跑 pytest core/tests/ 验证 58 passed
  5. 走 12 步流程 + CHANGELOG v0.4.14.43
- **风险**: 跑批不受影响 (之前跑批已经靠重登 cookie 成功)
- **执行**: Sprint 4 第 4 工单

### P1 #18 简历文档 dmp-data-scraper.md 跟新
- **路径**: /Users/hutou/Desktop/简历/项目技术文档/dmp-data-scraper.md
- **问题**: 1.1 写"项目路径 fuqing-crm-analytics/scraper/core/data3.csv" 跟实际状态 100% 不一致
- **步骤**:
  1. 读简历文档 (2026-06-07 状态)
  2. 跟新 1.1 路径 (主项目部分) → /Users/hutou/Desktop/fuqin-date/fuqing-scraper/core/
  3. 跟新 1.2 状态 (主项目 9bd4274 软删 scraper/ + Sprint 19+ P2 batch)
  4. 跟新 1.4 核心约束 (Sprint 19+ #141 治根 check_dmp_session 业务层 session 验证)
  5. 跟新 8.2 项目事实 (独立 repo v0.4.14.41, 58/58 pytest, 22 模块)
  6. 保留 1.3 技术栈跟 3 三层架构跟 4 核心模块详解跟 6 数据策略跟 7 自动化机制跟 8 约束速查跟 8.6 历史事故跟 8.7 待办跟 8.8 反检测跟 8.9 错误排查 跟 Sprint 4 状态
- **风险**: 简历文档不在 git 里, 写完不 commit
- **执行**: Sprint 4 第 5 工单 (留 Sprint 21+)

## 执行顺序 (按依赖)

#19 (Sprint 4 计划) → #15 (主项目软删) → #16 (双层清理) → #17 (5 行修) → #18 (简历更新)

## 验证

- 跑批业务: data3.csv 7164 → 7209 (+45 行, 0 行污染)
- pytest: 58/58 passed (55 原有 + 3 Sprint 19+ #141 新增)
- GitHub: weiweity/dmp-data-scraper main = 06cc0f3
- 跟主项目解耦: 主项目 9bd4274 scraper/ 软删 + 跨子项目 B1 治根 v0.4.14.53
