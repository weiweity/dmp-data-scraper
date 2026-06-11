"""Wave 1 of scraper Sprint 16 refactor (v2 design, dual-voice reviewed).

Extracted from dmp_common.py in Sprint 16 Wave 1 refactor. Zero functional change.
"""

# Config 提供 ACCOUNT_FILE 路径, log() 提供日志能力。
# 与原实现保持一致,这两个依赖都通过 dmp_common 的兼容 shim 提供。
from ..config.settings import Config
from .log import log


# ============ 账号读取 ============
def read_account():
    """从 account.txt 读取账号密码

    支持多种格式：
        账号：xxx
        账号:xxx
        账号=xxx
        password:xxx
        password=xxx
    """
    try:
        with open(Config.ACCOUNT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) < 2:
                log("账号文件格式错误：至少需要两行（账号和密码）")
                return None, None

            # 解析第一行（账号）
            line1 = lines[0].strip()
            username = None
            for prefix in ['账号：', '账号:', '账号=', 'username:', 'username=', 'user:', 'user=']:
                if line1.startswith(prefix):
                    username = line1[len(prefix):].strip()
                    break
            if not username:
                # 尝试用冒号或等号分割
                if ':' in line1:
                    username = line1.split(':', 1)[1].strip()
                elif '=' in line1:
                    username = line1.split('=', 1)[1].strip()
                else:
                    username = line1

            # 解析第二行（密码）
            line2 = lines[1].strip()
            password = None
            for prefix in ['密码：', '密码:', '密码=', 'password:', 'password=', 'pass:', 'pass=']:
                if line2.startswith(prefix):
                    password = line2[len(prefix):].strip()
                    break
            if not password:
                # 尝试用冒号或等号分割
                if ':' in line2:
                    password = line2.split(':', 1)[1].strip()
                elif '=' in line2:
                    password = line2.split('=', 1)[1].strip()
                else:
                    password = line2

            if username and password:
                log(f"读取到用户名: {username}")
                return username, password
            else:
                log("账号文件格式错误：无法解析用户名或密码")
                return None, None
    except Exception as e:
        log(f"读取账号文件失败: {e}")
        return None, None
