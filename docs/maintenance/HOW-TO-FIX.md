# How to Fix — fuqing-scraper

> 接手项目时遇到 bug,先查这一份。讲清"症状 → 排查 → 修复"的标准流程。

---

## 0. 排查流程 (TL;DR)

```
跑批失败?
  ↓
[1] 看 del/run_logs/run_*.log 找异常
  ↓
[2] 看 del/*.png 截图判断是页面层/数据层/网络层
  ↓
[3] 看 .learnings/ERRORS.md ERR-* 历史
  ↓
[4] 如果没解决,看 docs/maintenance/LESSONS.md (v0.1.19-v0.1.23 4 个 fix 的排查路径)
  ↓
[5] 复现: PYTHONPATH=. pytest core/tests/ -v + 跑单个 scraper
  ↓
[6] fix → 测试 → review → commit
```

---

## 1. 跑批入口失败 (ImportError)

**症状**: `./START.sh` 起来直接 `ImportError: cannot import name 'X' from 'dmp_common'`

**根因**: dmp_common.py 的 re-export 缺失。v0.1.17 清理时误删过 `parse_number`,见 v0.1.19 fix。

**排查**:
```bash
cd /Users/hutou/Desktop/fuqin-date/fuqing-scraper
python3 -c "from dmp_common import parse_number"  # 应该 OK
```

**修复** (任意一种):
1. 在 `dmp_common.py` 顶部 `from core.utils.X import ...` 加缺失的 symbol
2. 检查 caller 文件 (`dmp_scraper.py` / `dmp_flow_scraper.py` / `dmp_item_insight_scraper.py`) 是否还有旧的 `from dmp_common import X`

---

## 2. 单品洞察 0/15 (Date Sanity Check 误杀)

**症状**: 跑批 0/15, 日志反复出现
```
⚠️ 严重：target_date=2026-06-13，但 SPA 显示'昨日'(2026/06/13)，URL 日期参数未生效
```

**根因**: Date Sanity Check 比较 `YYYY-MM-DD` (URL 格式) 和 `YYYY/MM/DD` (格式化的昨日), 字符串永远不等。v0.1.20 已修,见 `dmp_item_insight_scraper.py:_check_spa_date_match`。

**排查**:
```bash
cd core
python3 -c "
from datetime import date
from dmp_item_insight_scraper import _check_spa_date_match
print(_check_spa_date_match('2026-06-13', '昨日', date(2026,6,14)))
# 应该 (True, '2026/06/13', 'refreshed')
"
```

**修复**: 用 `_check_spa_date_match(date_str, spa_text, today_date)` 内部统一 `YYYY-MM-DD` 比较。

---

## 3. 流转数据 xinzeng 全 0

**症状**: data.csv 中 `xinzeng` 人群, initial > 0 但所有 transform 字段为 0 (6/7 起特别明显)。

**根因**:
- xinzeng (statusId=0) transfer API 响应延迟 30s+
- 旧代码放最后访问 → 切换 tab 时在途响应被丢弃
- `page.reload()` 不触发 SPA 重新请求 (DMP 前端缓存)

**修复** (v0.1.23):
1. `all_status_ids = [0, 2001, ...]` xinzeng 放第一个
2. 主页轮询 60s, retry 轮询 45s
3. 保留 `extract_xinzeng_flow_by_dom` 作为最后防线

**排查**:
```bash
# 1. 看 latest log 是否有 [API] xinzeng after retry
# 2. 验证 fallback: python3 -c "from dmp_flow_scraper import extract_xinzeng_flow_by_dom; print('OK')"
```

---

## 4. data3.csv / data.csv 写入 0 行 (陈旧数据)

**症状**: `is_X_data_stale` 触发, 跳过写入。日志: `[YYYY-MM-DD] X 数据未更新（陈旧），跳过写入`

**根因**: SPA 页面还没刷新, 数据是默认渲染。`xinzeng` initial=0 也判定为陈旧。

**修复**: 等 16:00 后 T+1 数据成熟再跑, 或者 `T_OFFSET=2` 跑 T-2。

---

## 5. chrome_profile 登录态失效

**症状**: `check_dmp_session` 3 次都返回 False, 进入 login_qianniu 分支。

**修复**:
1. **不要删 `core/chrome_profile/`** (登录态)
2. 手动打开 Chrome, 访问 dmp.taobao.com, 重新登录千牛
3. Cookie 自动存回 chrome_profile/
4. 重跑 scraper

---

## 6. pytest 失败

**跑测试**:
```bash
cd /Users/hutou/Desktop/fuqin-date/fuqing-scraper
PYTHONPATH=. pytest core/tests/ -v
```

**期望**: 128/128 passed (v0.1.17 后, 加 39 个 P1 + Gate 4 测试)。

**单跑 1 个**:
```bash
PYTHONPATH=. pytest core/tests/test_spa_date_match.py -v
```

**新加测试的约定**:
- 测试函数: `test_<场景>_<期望>`
- 场景: `happy` / `none` / `empty_dict` / `mismatch` / `t_minus_1`
- 文件名: `test_<被测模块>.py`

---

## 7. 数据状态查询 (不要 ad-hoc)

**❌ 错误**: 自己写 `python3 -c "sorted(...)"`, YYYY/M/D 字符串排序错乱。

**✅ 正确**: 用 `core.utils.csv_state` (v0.1.15, 见 CLAUDE.md §10):

```bash
# 总体
python3 -m core.utils.csv_state core/data3.csv

# 范围缺失
python3 -m core.utils.csv_state core/data3.csv 2026-05-01 2026-06-14
```

如果 csv_state.py 不能直接回答, 在 csv_state.py 加新函数 + 测试, **不要**在 ad-hoc 脚本里写。

---

## 8. 修改 scraper 的步骤

1. 改代码 (匹配现有风格, 不"改进"无关代码)
2. 更新 CHANGELOG.md (新版本 v0.1.x, 写"症状/根因/修复/验证")
3. 跑 pytest
4. git flow: branch → code → changelog → pytest → review → commit → push → qa → merge → push main → pull
5. **绝不**直接 commit 到 main

---

## 9. 关键文件清单

| 文件 | 改之前要查 |
|---|---|
| `core/dmp_common.py` | re-export 表面 (16 个 symbol) |
| `core/dmp_item_insight_scraper.py` | Date Sanity Check 在 `_check_spa_date_match` |
| `core/dmp_flow_scraper.py` | xinzeng 访问顺序 + 轮询 |
| `core/run.sh` / `START.sh` | 跑批入口, 别绕过 |
| `CHANGELOG.md` | 最近 v0.1.x 改了什么 |

---

## 10. 紧急回滚

```bash
# 找上次好的 commit
git log --oneline -- core/ | head -20

# 回滚
git checkout <good-commit>
cd core && python3 dmp_master.py --items  # 验证

# 不行再 git checkout main
```

如果 CHANGELOG 没写清楚, 就翻 git log:
```bash
git log --oneline --since="2 days ago" -- core/dmp_common.py
```
