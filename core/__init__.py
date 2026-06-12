"""
core package — 芙清 DMP 数据采集核心模块

Sprint 5 #21 (v0.4.14.46) 删内层 scraper/ 后, 项目统一从根 core/ 加载:
- dmp_master.py 用 from dmp_common (top-level, 假设 core/ 在 sys.path)
- dmp_common.py 用 from core.utils.dates (绝对 import, 假设 core/ 是 package)

两种 import 模式并存, core/ 必须是 Python package, 否则 cd core && python3
dmp_master.py 启动时 dmp_common 内部 from core.X 失败 (ModuleNotFoundError)。

__init__.py 让 core/ 升级为 package, 两种 import 模式都能工作。
"""
