"""
scraper/core/config/settings.py

Config single source of truth — Sprint 16 Wave 1 (v2 design, 2026-06-11).
Extracted from dmp_common.py. yaml items loaded on demand via Config.load_items().

v2 design: Config.ITEM_IDS DELETED 2026-06-11, use Config.load_items() instead.

零功能变更承诺: 所有属性跟原 dmp_common.py:46-81 行为完全一致。
- USER_DATA_DIR / ACCOUNT_FILE / *_DATA_FILE / DEBUG_DIR 都是绝对路径
  (用 os.path.join + Path(__file__).resolve().parent.parent 拿到 scraper/core/ 路径)
- DMP_SPM 完整 5 段: a2e3k.28338430.c0d46757f.de019e68a.1d1125eblwdosJ
- 保留 DMP_ROUTE_ASSETS / DMP_ROUTE_FLOW / DMP_ROUTE_ITEM 3 个常量
"""
from pathlib import Path
import os
import yaml

# scraper/core/ 绝对路径 (跟原 dmp_common.py:_SCRIPT_DIR 等价)
SCRAPER_CORE_DIR = Path(__file__).resolve().parent.parent
# items.yaml 在项目根 config/ (fuqing-crm-analytics/config/items.yaml)
# SCRAPER_CORE_DIR = .../scraper/core/, parent = .../scraper/, parent.parent = .../fuqing-crm-analytics/
CONFIG_ITEMS_YAML = SCRAPER_CORE_DIR.parent.parent / 'config' / 'items.yaml'


class Config:
    """集中管理所有路径和配置参数 (跟原 dmp_common.py:46-81 完全等价)"""

    # 脚本所在目录（供外部引用, 跟原 dmp_common.Config._SCRIPT_DIR 一致)
    _SCRIPT_DIR = str(SCRAPER_CORE_DIR)

    # === 数据文件路径 (绝对路径, 跟原 dmp_common.Config 一致) ===
    ASSETS_DATA_FILE = os.path.join(_SCRIPT_DIR, "data2.csv")
    FLOW_DATA_FILE = os.path.join(_SCRIPT_DIR, "data.csv")
    ITEM_DATA_FILE = os.path.join(_SCRIPT_DIR, "data3.csv")

    # === 调试目录 (绝对路径) ===
    DEBUG_DIR = os.path.join(_SCRIPT_DIR, "del")

    # === 浏览器用户数据目录（保持登录态, 绝对路径) ===
    USER_DATA_DIR = os.path.join(_SCRIPT_DIR, "chrome_profile")

    # === 账号文件 (绝对路径) ===
    ACCOUNT_FILE = os.path.join(_SCRIPT_DIR, "account.txt")

    # === 商品ID列表（与 config/items.yaml 保持一致, 跟原 dmp_common 完全一致) ===
    ITEM_IDS = [
        "587051744204", "597655781410", "587053192746", "683395365107", "654390297284",
        "803474428381", "870597889980", "621639424901", "601760206476", "612503357090",
        "803417397714", "994162104051", "933524395698", "900975734816",
        "1010458880710"  # 传明酸面膜（2026-04-21新增）
    ]

    # === 达摩盘 URL 配置 (跟原 dmp_common.Config 完全一致) ===
    DMP_BASE_URL = "https://dmp.taobao.com/index_new.html"
    # spm 参数（从浏览器地址栏复制，当前有效值，变动时需更新)
    DMP_SPM = "a2e3k.28338430.c0d46757f.de019e68a.1d1125eblwdosJ"
    # 各模块路由路径
    DMP_ROUTE_ASSETS = "#!/deeplink-new/assets-diagnose"
    DMP_ROUTE_FLOW = "#!/deeplink/flow"
    DMP_ROUTE_ITEM = "#!/items/item-insight"

    # === v2 新增: Config.load_items() 替代旧 Config.ITEM_IDS 直接引用 ===
    @classmethod
    def load_items(cls) -> list[str]:
        """从 config/items.yaml 加载 15 个商品 ID 列表 (替代旧 Config.ITEM_IDS 直接访问)。

        v2 设计: 删除 Config.ITEM_IDS 后, 新代码应该用 Config.load_items() 拿到 list[str]。
        旧 Config.ITEM_IDS 仍保留 (向后兼容 Wave 1 caller 文件), Wave 2 真改 import 路径后再删。
        """
        if not CONFIG_ITEMS_YAML.exists():
            raise FileNotFoundError(f'items.yaml not found at {CONFIG_ITEMS_YAML}')
        data = yaml.safe_load(CONFIG_ITEMS_YAML.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or 'items' not in data:
            raise ValueError(
                f'items.yaml schema invalid: expected dict with "items" key, got {type(data)}'
            )
        return data['items']
