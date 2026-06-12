# Sprint 5 Plan — fuqing-scraper 治理 backlog (5+1 工单 #20-#25)

> 独立 repo fuqing-scraper Sprint 5 治理计划
> 创建: 2026-06-12, 跟 Sprint 4 收口 (v0.4.14.44) 同步

## 背景

Sprint 4 改名收口 (v0.4.14.43 5 件文档改名 + 5 工单 Task #15-#19 → Task #20-#24 编号) 完成后, 留 5 工单 backlog + 1 新发现 (紧急) 进入 Sprint 5。 Sprint 5 同时也是"双层 scraper/ 治理"+"主项目软删"+"简历跟新"+"5 行修"+"Sprint 19+ #141 修复实际未生效治根"集中收口 sprint。

**Sprint 5 启动前关键发现** (从 Sprint 4 收口 analysis 中识别):
- Sprint 19+ #141 修复实际**未生效** — 修复在内层 `scraper/core/dmp_common.py:451-472`, 但生产 `core/dmp_master.py:30` 走的是外层 `core/dmp_common.py` (30413 字节, 无修复)。 业务码失效时 scraper **仍不**会走 login_qianniu 重登。

## 6 工单 (按执行顺序)

### P0 #25 Sprint 19+ #141 修复同步到外层 (新发现, 紧急)
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-scraper
- **根因**: 
  - commit da6240b (v0.4.14.41) 改的是 `scraper/core/dmp_common.py` (内层)
  - 生产 `core/dmp_master.py:30` 解析到 `core/dmp_common.py` (外层, 30413 字节, 无修复)
  - `core/tests/test_dmp_common.py:10` 走 `from scraper.core.dmp_common import` (测内层)
  - 58/58 pytest 通过假象, 业务码失效时 scraper **仍不**会走重登
- **步骤**:
  1. 切 fix/sprint20-141-fix-outer-layer 分支 from main 9e8a6ba
  2. Edit `core/dmp_common.py:444-465` 复制内层 22 行修复 (line 451-472 from `scraper/core/dmp_common.py`)
  3. 跑 `PYTHONPATH=. pytest core/tests/ -v` 验证 58/58 (外层有修复)
  4. 跑 `python3 -c "from core.dmp_common import check_dmp_session; ..."` 验证运行时拿到修复
  5. 走 12 步流程 + CHANGELOG v0.4.14.45
  6. push to GitHub
- **风险**: 内层 `scraper/core/dmp_common.py` 修复保留, 跟外层同步
- **执行**: Sprint 5 第 1 工单 (本 PR)

### P0 #20 主项目 scraper/ 软删 + symlink
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-crm-analytics
- **修正**: 之前错报"已软删", 实际还有 (13 子目录, 6/8 15:13)
- **步骤**:
  1. 切 fix/sprint20-143-scraper-soft-delete 分支 from main 9bd4274
  2. mv scraper scraper.legacy
  3. ln -s /Users/hutou/Desktop/fuqin-date/fuqing-scraper scraper
  4. 验证 (python3 -c "from scraper.core import dmp_common; print('OK')")
  5. 跑 pytest backend/tests/ 验证 507 passed
  6. 走 12 步流程 + CHANGELOG v0.4.14.55
- **风险**: 主项目跑批影响 (scraper/ 软删后跑批走 symlink → 独立 repo)
- **依赖**: 独立 (跟 #25 / #21 / #22 / #23 无依赖)
- **执行**: Sprint 5 第 2 工单 (可跟 #22 / #23 并行)

### P1 #21 独立 repo 双层 scraper/ 清理
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-scraper
- **问题**: `/scraper/core/` 跟 `/core/` 内容部分重叠 (Sprint 16 Wave 1 拆出时外层 scraper/ 没清理)
- **决策翻转**: 
  - 计划说"大概率外层 scraper/ 全删" (v0.4.14.42 plan 阶段误判)
  - 实际: 内层 `scraper/core/dmp_common.py` 有 Sprint 19+ #141 修复, 外层没有
  - **修订决策**: #25 完成后, 外层有完整能力, **删内层** (`/scraper/` 全删)
- **步骤**:
  1. 等 #25 完成 (外层 `core/dmp_common.py` 有修复) ✅ (v0.4.14.45)
  2. 切 fix/sprint5-146-double-layer-cleanup 分支 from main ca85a7f ✅
  3. 改 8 个 .py 文件的 `from scraper.core.X` → `from core.X` ✅
  4. `git rm -rf scraper/` (内层) ✅
  5. 验证: `python3 -c "from core.dmp_common import check_dmp_session; ..."` 仍拿到修复 ✅
  6. 跑 pytest core/tests/ 验证 58/58 ✅
  7. 跑 `python3 core/dmp_master.py --help` 验证入口正常 ✅
  8. 走 12 步流程 + CHANGELOG v0.4.14.46 ✅
  9. push to GitHub (待用户 merge)
- **风险**: 删除错误的层 (#25 完成后外层有修复, 风险低) → 0 风险, 两层 diff 验证空
- **依赖**: #25 必须先完成 ✅
- **执行**: Sprint 5 第 3 工单 ✅ completed (v0.4.14.46)

### P2 #22 5 行修 dmp_master.py:678 重建 + commit
- **路径**: /Users/hutou/Desktop/fuqin-date/fuqing-scraper
- **状态**: 5 行修未真正 commit, 7 个 dangling 都没 marker
- **步骤**:
  1. 用户回忆 5 行内容
  2. 切 fix/sprint20-142-5-line-rebuild 分支 from main (含 #25 fix)
  3. 重新 Edit core/dmp_master.py:678 加 5 行 (在 if args.items: 内, for 循环之前)
  4. 验证 git diff 5 行净增
  5. 跑 pytest core/tests/ 验证 58 passed
  6. 走 12 步流程 + CHANGELOG v0.4.14.47
- **风险**: 跑批不受影响 (之前跑批已经靠重登 cookie 成功)
- **依赖**: 用户提供 5 行内容
- **执行**: Sprint 5 第 4 工单 (留 Sprint 6+)

### P1 #23 简历文档 dmp-data-scraper.md 跟新
- **路径**: /Users/hutou/Desktop/简历/项目技术文档/dmp-data-scraper.md
- **问题**: 1.1 写"项目路径 fuqing-crm-analytics/scraper/core/data3.csv" 跟实际状态 100% 不一致
- **步骤**:
  1. 读简历文档 (2026-06-07 状态)
  2. 跟新 1.1 路径 (主项目部分) → /Users/hutou/Desktop/fuqin-date/fuqing-scraper/core/
  3. 跟新 1.2 状态 (主项目 9bd4274 软删 scraper/ + Sprint 19+ P2 batch)
  4. 跟新 1.4 核心约束 (Sprint 19+ #141 治根 check_dmp_session 业务层 session 验证, **含 #25 修复同步到外层**)
  5. 跟新 8.2 项目事实 (独立 repo v0.4.14.45+, 58/58 pytest, 22 模块)
  6. 保留 1.3 技术栈跟 3 三层架构跟 4 核心模块详解跟 6 数据策略跟 7 自动化机制跟 8 约束速查跟 8.6 历史事故跟 8.7 待办跟 8.8 反检测跟 8.9 错误排查 跟 Sprint 5 状态
- **风险**: 简历文档不在 git 里, 写完不 commit
- **依赖**: 独立 (跟 #25 / #20 / #21 / #22 无依赖)
- **执行**: Sprint 5 第 5 工单 (留 Sprint 6+)

## 执行顺序 (按依赖)

```
#25 (P0 紧急, 内层修复 → 外层) → #21 (P1, 删内层)
  #20 (P0, 主项目软删, 跟 #25 / #21 / #22 / #23 无依赖, 可并行)
  #22 (P2, 等用户提供 5 行内容)
  #23 (P1, 跟 #25 / #20 / #21 / #22 无依赖, 可并行)
```

## Sprint 5 启动验证 (执行前)

- [x] Sprint 4 收口 (v0.4.14.44) 推送 9e8a6ba ✅
- [x] 跑批业务不阻塞 (data3.csv 7164 → 7209, 0 行污染)
- [x] 6 工单 #20-#25 backlog 记录

## 风险

1. **#25 (最关键)**: 修复同步到外层后, 跑批业务 (data3.csv) 必须保持 0 行污染, 业务码失效时真走重登
2. **#20 (主项目跨子)**: 主项目 scraper/ 软删后, 跑批走 symlink → 独立 repo, 主项目 507 pytest 必须保持
3. **#21 (依赖 #25)**: #25 失败 #21 不能做, 删错层会丢失修复
4. **#22 (用户依赖)**: 5 行内容没回忆出来就留 Sprint 6+
5. **#23 (独立)**: 简历文档不在 git 里, 写完不 commit 风险

## 验证 (Sprint 5 收口时)

- pytest core/tests/: 58/58 passed
- 跑批 (data3.csv): 0 行污染, 业务码失效 scraper 走重登
- 主项目 scraper/ → symlink → 独立 repo, pytest backend/tests/ 507 passed
- 双层清理: `scraper/` 目录不存在, 生产 `core/dmp_common.py` 有完整修复
- 简历文档跟新: 1.1/1.2/1.4/8.2 跟 Sprint 5 状态 100% 同步
- 5 行修: dmp_master.py:678 +5 行净增, 7 个 dangling 全消
- GitHub: weiweity/dmp-data-scraper main 同步到最新 v0.4.14.4x
- 跟主项目解耦: 主项目 9bd4274 scraper/ 软删 + 跨子项目 B1 治根 v0.4.14.53
