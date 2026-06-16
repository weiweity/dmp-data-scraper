# Architecture — fuqing-scraper

> 接手这个项目时,先读这一份。讲清"是什么、3 个数据怎么流、22 个模块怎么协作"。

---

## 1. 这是什么

**fuqing-scraper** 是芙清旗舰店在 **达摩盘 (DMP, dmp.taobao.com)** 抓数据的爬虫。3 个数据表,每日跑批。

| CSV | 表名 | 数据粒度 | 来源 |
|---|---|---|---|
| `core/data.csv` | 流转数据 | (日期, 人群) 8 行/天 | API 拦截 + DOM fallback |
| `core/data2.csv` | 资产诊断 | 每天 1 行 (TOTAL + 6 AIPL) | DOM 抓大数字 |
| `core/data3.csv` | 单品洞察 | (日期, 商品) 15 商品 × 1 行/天 | API 拦截 + Date Sanity Check |

> 7×24 累计 (2026-06-16 截至): data.csv 2409 行 + data2.csv 777 行 + data3.csv 7269 行 = 10455 行, append-only, 绝不覆盖。

---

## 2. 数据流 (单品洞察 data3.csv 举例)

```
千牛后台 https://dmp.taobao.com
    ↓ Playwright 浏览器 (headless=True, chrome_profile/ 持久化登录态)
core/dmp_master.py --items
    ↓ 主流程
dmp_item_insight_scraper.fetch_item_data(item_id, date)
    ├─ 访问 URL: ?itemId={id}&endDate={date}&analysisTab=compete
    ├─ _ItemAssetCollector 注册 Playwright response 拦截
    ├─ 拦截 goods/view/overview/v2 (SPA 异步 API)
    ├─ 12s Phase 1 轮询 (取"数据更好"的那一份)
    ├─ _check_spa_date_match 验日期 (T-1 走宽容分支)
    └─ append_tocsv → data3.csv (6 道门禁)
```

**关键**:
- `headless=True` 不可改 (Sprint 19 验证: 有头下 API 拦截失败,ERR-20260608-001)
- `analysisTab=compete` 是单品洞察参数,**不可去掉**
- Date Sanity Check: SPA trigger 显示的日期必须 == URL 目标日期,否则拒绝写入

---

## 3. 三层架构 (Master + Common + Scraper)

```
core/
├── dmp_master.py                 ← 统一入口 (--assets/--flow/--items, 775 行)
├── dmp_common.py                 ← 公共模块 (Config/BrowserManager/login/CSV 工具, 788 行 re-export shim)
├── dmp_scraper.py                ← 资产诊断 (Y轴锚点 DOM 抓取, data2.csv, 679 行)
├── dmp_flow_scraper.py           ← 流转数据 (API 拦截 + statusId=0 DOM fallback, data.csv, 806 行)
├── dmp_item_insight_scraper.py   ← 单品洞察 (API 拦截 + Date Sanity Check, 2454 行)
├── anti_detect.py                ← 反检测 (10 层防御)
├── sanity_check.py               ← 数据质量 (6 道门禁)
├── config/                       ← items.yaml + settings.py
├── utils/                        ← dates.py / account.py / log.py / t_offset.py / csv_state.py
├── validators/                   ← items/assets/flow 3 个 validator
└── tests/                        ← conftest.py + 128 tests
```

### 3.1 dmp_master.py (入口,775 行)

唯一入口,负责:
- 解析 CLI args (`--assets` / `--flow` / `--items`)
- 读取账号 (read_account)
- 调 `check_dmp_session` (3 次重试)
- 调 `_is_page_alive` 验页面健康 (模块间重建)
- 串接 3 个 scraper

**不要在 scraper 里加 if __name__ == '__main__'** — 旧版 dmp_common.py 早期有过独立入口,新代码统一走 master.py。

### 3.2 dmp_common.py (公共,788 行)

**re-export shim** — 内部定义:
- `log(msg)` — 统一日志函数,带时间戳,追加 `del/dmp_run_YYYYMMDD.log`
- `detect_encoding(file_path)` — 编码检测
- `get_missing_dates_assets/flow/item` — 缺失日期检测
- `BrowserManager` / `_update_spm_from_url` / `check_dmp_session` / `login_qianniu`

外部 re-export:
- `Config` (from `config/settings.py`)
- `parse_date` / `format_date_for_csv` / `normalize_date_str` / `parse_number` (from `utils/dates.py`)
- `read_account` (from `utils/account.py`)

**所有 scraper 都 `from dmp_common import X`** — 这是约定,别绕过。

### 3.3 3 个 scraper (679 / 806 / 2454 行)

| 模块 | 数据流 | 关键函数 |
|---|---|---|
| `dmp_scraper.py` | DOM 抓 Y 轴大数字 | `extract_assets_data` |
| `dmp_flow_scraper.py` | API 拦截 + DOM fallback | `extract_flow_data_by_dom_v3`, `extract_xinzeng_flow_by_dom` |
| `dmp_item_insight_scraper.py` | API 拦截 + Date Sanity | `fetch_item_data`, `_check_spa_date_match`, `_find_date_trigger_multi` |

---

## 4. 4 个不变量 (改了必坏)

| 不变量 | 改动的后果 |
|---|---|
| `headless=True` | 有头下 API 拦截失败, 整批空 (ERR-20260608-001) |
| `analysisTab=compete` | 单品洞察数据缺失 |
| `chrome_profile/` **不可删** | 登录态丢失, 需手动重登 |
| 写 CSV `mode='a'` | append-only 约定, **永远不覆盖** |

---

## 5. 状态机 (一次跑批)

```
START
  ↓
[master.py main] 解析 args
  ↓
[check_dmp_session] 3 次 API 重试 → 业务层 `/api_2/login/loginuserinfo` 检测
  ├─ True → 跳过 login
  └─ False → login_qianniu(username, password) 走千牛扫码
  ↓
[health check] GET DMP URL, 验 404
  ↓
[run_X_module] 按 args 跑对应模块
  ↓
[汇总] 打印 success/total
  ↓
END (with context manager 关浏览器)
```

**关键**: `_is_page_alive` 跨模块检查,page 失效时调 `_recreate_page_and_login` 重建。

---

## 6. 数据路径

```
项目根
├── core/
│   ├── data.csv          # 流转 (append)
│   ├── data2.csv         # 资产诊断 (append)
│   ├── data3.csv         # 单品洞察 (append)
│   ├── del/              # 调试 + 日志 + 截图
│   │   ├── dmp_run_YYYYMMDD.log       # 全局日志
│   │   ├── run_logs/run_*.log        # v0.1.18+ 每次跑批独立日志
│   │   ├── assets_YYYY-MM-DD.png     # 资产诊断截图
│   │   ├── api_flow_YYYY-MM-DD.png   # 流转截图
│   │   └── item_XXXX_initial/final.png  # 单品截图
│   └── chrome_profile/   # 登录态 (敏感, 不可删)
└── ...
```

---

## 7. 入口/启动 (项目根)

| 入口 | 用途 |
|---|---|
| `./START.sh` | 一键启动 (薄包装) |
| `./START.sh -i` | 单品洞察 (默认 T-1) |
| `./START.sh -t 2 -i` | 单品洞察 T-2 |
| `./START.sh -b 30 -i` | 回填 30 天 |
| `./START.sh -m` | 实时监控最新日志 |
| `./START.sh -s` | 查看 data3.csv 数据状态 |

**CLI vs Python**:
- 日常: `./START.sh` 一键
- 自动化: `cd core && python3 dmp_master.py --items` (设环境变量 `T_OFFSET=1`)

---

## 8. 关联文档

- `CLAUDE.md` — 全局 4 条准则 + 启动/验证/约束
- `CHANGELOG.md` — 版本事件流 (v0.1.0~v0.1.26)
- `KB-数据采集-SPA接口拦截.md` — SPA 拦截方法论
- `docs/maintenance/HOW-TO-FIX.md` — 怎么修 bug
- `docs/maintenance/LESSONS.md` — 今天 4 个 fix 的教训
- `docs/maintenance/CHANGELOG-GUIDE.md` — 怎么读 CHANGELOG
- `.learnings/ERRORS.md` — 历史 bug 编号
