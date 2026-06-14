# CHANGELOG-GUIDE — 怎么读 + 怎么写

> CHANGELOG.md 是**事件流** ("某天发生了啥"), 不是**文档** ("项目长啥样")。这一份是"如何读 + 何时写 + 模板"。

---

## 1. 怎么读 CHANGELOG

### 1.1 想了解"现在项目长啥样"

**❌ 不要**从头读 CHANGELOG.md (50+ 版本条目, 770+ 行, 信息密度低)。

**✅ 应该**:
1. 读 `docs/maintenance/ARCHITECTURE.md` (10 分钟)
2. 跳到 `CHANGELOG.md` 最新 3-5 个版本, 看最近改了什么
3. 需要时按 `git log` 翻 commit

### 1.2 想了解"某天发生了什么"

`CHANGELOG.md` 按版本倒序, 最新在最上。每条 entry 含:
- 版本号 (v0.1.x)
- 日期
- 标题 (一行)
- 背景 / 改了什么 / 验证 / Lesson / Metadata

`grep "v0.1.20"` 直接跳到。

### 1.3 想了解"某个 bug 怎么修的"

**路径**:
1. `grep "ERR-" .learnings/ERRORS.md` 找历史 bug
2. `grep "v0.1.X" CHANGELOG.md` 找 fix 版本
3. 翻 `git log` 看具体 commit

### 1.4 想知道"为什么这样设计"

`CHANGELOG.md` 的 "Lesson" 段落 + `docs/maintenance/LESSONS.md` + `.learnings/ERRORS.md`。

---

## 2. 什么时候写

| 触发 | 必写 | 例 |
|---|---|---|
| 改了 `core/*.py` 业务逻辑 | ✅ | v0.1.20 Date Sanity fix |
| 加新模块 | ✅ | v0.1.0 22 模块拆分 |
| 加新测试 | ✅ | v0.1.17 19 个 P1 测试 |
| 改了 entry point | ✅ | v0.1.18 run.sh 升级 |
| 文档 / 注释微调 | ❌ | - |
| 重命名内部变量 | ❌ | - |
| 跑测试 / 清理 | ❌ | - |

**原则**: 用户能感知的改动必写。重构不算 (但 commit 必写)。

---

## 3. 版本号方案 (v0.1.x)

CLAUDE.md §6 已定义:

| 位 | 含义 | 例 |
|---|---|---|
| 0 | major (留作未来 scraper 重写) | 0.1.0 → 1.0.0 |
| 1 | minor (新功能) | 0.1.0 → 0.2.0 (新 scraper 模块) |
| x | patch (修 bug / 文档 / lint) | 0.1.0 → 0.1.1 |

**v0.1.x 范围**: 当前 scraper 内部迭代。

---

## 4. 模板 (复制粘贴)

```markdown
## [v0.1.XX] - YYYY-MM-DD - <type>(<scope>): <一行总结>

### 背景
(2-3 句: 什么问题/什么场景触发了这次改动)

### Fixed
(具体改了哪些文件, 各几行)

### Added
(新增了哪些文件/测试/功能)

### Changed
(行为变更, 但不改功能)

### Removed
(删了什么)

### 验证
- pytest X/X passed
- ./START.sh -X 行为正确
- (任何手动验证步骤)

### Lesson
(1-2 句, 这次学到了什么, 给未来人/未来 Claude 看的)

### Metadata
- Related Files: `core/X.py`, `core/tests/test_Y.py`
- Net diff: N files, +X/-Y 行
```

**type** 选一个: `feat` / `fix` / `chore` / `docs` / `test` / `refactor` / `perf`

**scope** 选一个: `cli` / `flow` / `items` / `assets` / `common` / `master` / `init` / `tests`

---

## 5. 实际例子

### 5.1 fix 的 entry (v0.1.19)

```markdown
## [v0.1.19] - 2026-06-14 - fix(cli): 修复 v0.1.17 误删 parse_number re-export 导致跑批入口崩溃

### 背景
v0.1.17 清理 `dmp_common.py` 死代码时, `from core.utils.dates import parse_number` 被当作 unused import 删除, 但 `dmp_scraper.py` 仍通过 `from dmp_common import parse_number` 引用。这导致 `./START.sh` / `./run.sh -a/-f/-A` 一运行就 `ImportError`, 跑批入口完全不可用。

### Fixed
- **core/dmp_common.py**: 恢复 `parse_number` 的 re-export (`from core.utils.dates import parse_date, format_date_for_csv, normalize_date_str, parse_number`)

### 验证
- `cd core && python3 -c "import dmp_master; print('import OK')"` → import OK
- `PYTHONPATH=. pytest core/tests/ -q` → **108/108 passed** (v0.1.23 累计)

### Metadata
- Related Files: `core/dmp_common.py`
- Root Cause: v0.1.17 误删 re-export
- Net diff: 1 文件, +1 行
```

### 5.2 feat 的 entry (v0.1.18)

```markdown
## [v0.1.18] - 2026-06-14 - feat(cli): run.sh/START.sh 支持实时监控、进度快照、环境变量透传

### 背景
用户排查 `core/run.sh` 与 `START.sh` 后发现两脚本仅支持基础分模块跑批, 缺少实时监控、进度可见、T_OFFSET/BACKFILL_DAYS 等 v0.1.9+ 环境变量的显式入口。本次升级为 shell 入口补全这些能力, 使其成为日常跑批首选入口。

### Added
- **core/run.sh**:
  - 运行日志自动写入 `core/del/run_logs/run_YYYYMMDD_HHMMSS_<module>.log` (tee 实时落盘)
  - `-m, --monitor` 在另一终端 `tail -f` 最新日志 (实时监控)
  - `-s, --status` 调用 `core.utils.csv_state` 查看 data3.csv 最新/缺失日期
  - `-t, --t-offset N` 设置 `T_OFFSET` (单品洞察日期偏移)
  - `-b, --backfill DAYS` 设置 `BACKFILL_DAYS` (历史回填天数)

### 验证
- `bash -n core/run.sh && bash -n START.sh` → syntax OK
- `./run.sh -h` / `./START.sh -h` → 帮助信息正确
- `./run.sh -s` → csv_state 输出 data3.csv 7223 行 / 最新 2026-06-12

### Metadata
- Related Files: `core/run.sh`, `START.sh`, `CLAUDE.md §3`
- Net diff: 3 files, ~+90/-30 行
```

---

## 6. 写完之后

1. 跑 `git add CHANGELOG.md` (不要 `git add -A`)
2. `git commit -m "fix(xxx): xxx"` 提交
3. push → qa → merge

**❌ 错误**: 写完 CHANGELOG 但没改代码, 或改了代码但没写 CHANGELOG。

---

## 7. 历史版本快速索引

| 版本 | 主题 | 关联 |
|---|---|---|
| v0.1.0 | 项目拆出独立 repo, 22 模块 | Sprint 16 Wave 1 |
| v0.1.16 | P0 + P1 技术债清理, P2 跳过 | CLAUDE.md §11 |
| v0.1.17 | WIP 收口, 19 个 P1 测试 | test_sanity_check 等 (103/103) → v0.1.20 补 5 个 (108/108) |
| v0.1.18 | run.sh 实时监控 + 进度快照 | HOW-TO-FIX §0 |
| v0.1.19 | 恢复 parse_number re-export | LESSONS §Fix 1 |
| v0.1.20 | T-1 Date Sanity 格式修复 | LESSONS §Fix 2 |
| v0.1.22 | xinzeng API 慢响应轮询 | LESSONS §Fix 3 |
| v0.1.23 | xinzeng tab 首位 + 60s 轮询 | LESSONS §Fix 4 |
