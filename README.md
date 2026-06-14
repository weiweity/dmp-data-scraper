# fuqing-scraper (芙清 DMP 数据采集)

> 达摩盘 SPA 自动抓数, 独立 git repo
> **v0.1.24** (2026-06-14)

独立 git repo, 22 模块拆分, **只负责爬虫 + 生成数据**, 跟其他项目无依赖。

- **项目路径**: `/Users/hutou/Desktop/fuqin-date/fuqing-scraper`
- **GitHub**: `git@github.com:weiweity/dmp-data-scraper.git`
- **pytest**: **113/113 passed** (v0.1.17 后加 24 个 P1 测试)
- **跑批业务**: data3.csv ~7200 行 (单品洞察, 每日)

## 三大数据产品

| 类型 | 脚本 | 数据文件 | 频率 |
|---|---|---|---|
| 资产诊断 | dmp_scraper.py | data2.csv | T-1 |
| 流转数据 | dmp_flow_scraper.py | data.csv | T-2 |
| 单品洞察 | dmp_item_insight_scraper.py | data3.csv | 每日 |

## 快速开始

```bash
cd /Users/hutou/Desktop/fuqin\-date/fuqing-scraper
pip install playwright pyyaml
playwright install chromium
PYTHONPATH=. pytest core/tests/ -v   # 113/113 passed
cd core
python3 dmp_master.py --items  # 单品洞察
T_OFFSET=2 python3 dmp_master.py --items  # 早 9:00 (T-2)
T_OFFSET=1 python3 dmp_master.py --items  # 下午 16:00 (T-1)
```

## 验证

```bash
PYTHONPATH=. pytest core/tests/ -v   # 113/113 passed
ruff check core/
wc -l core/data3.csv               # ≥ 7000 行
```

## 目录结构 (22 模块)

```
core/ - dmp_master.py + dmp_common.py + dmp_scraper.py + dmp_flow_scraper.py
     + dmp_item_insight_scraper.py + anti_detect.py + sanity_check.py
     + run.sh + config/ (3) + utils/ (4) + validators/ (3) + tests/ (8)
```

## 关键约束

- CSV **只追加不覆盖**（数据丢失不可恢复）
- `chrome_profile/` **绝对禁止删除**（千牛登录态丢失）
- `headless=True` 固定

详见 `CLAUDE.md` §2。

## 维护文档

- 项目结构 / 数据流 / 不变量 → `docs/maintenance/ARCHITECTURE.md`
- 跑批失败排查 → `docs/maintenance/HOW-TO-FIX.md`
- 今天 4 个 fix 的根因 → `docs/maintenance/LESSONS.md`
- CHANGELOG 怎么读 + 怎么写 → `docs/maintenance/CHANGELOG-GUIDE.md`

## GitHub

https://github.com/weiweity/dmp-data-scraper
