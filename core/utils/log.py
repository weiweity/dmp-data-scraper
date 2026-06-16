"""Wave 1 of scraper Sprint 16 refactor (v2 design, dual-voice reviewed).

Extracted from dmp_common.py in Sprint 16 Wave 1 refactor. Zero functional change.

log() 留在 dmp_common.py 顶部, 但 utils/account.py 等子模块需要 log() —
新建 utils/log.py 抽 log() 实现, 避免 utils → dmp_common → utils 循环 import。
"""
import os
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(_SCRIPT_DIR, 'del')
LOG_FILE = os.path.join(LOG_DIR, f'dmp_run_{datetime.now().strftime("%Y%m%d")}.log')

# 模块加载时一次性创建目录, 避免每次 log() 调用都执行 os.makedirs
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception as e:
    # best-effort: 目录创建失败不致命 (log() 仍可走 stdout), 但要可见
    print(f"WARNING: log dir init failed ({type(e).__name__}: {e}), 仅 stdout 日志", flush=True)


def log(msg):
    """统一日志函数（带时间戳）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)  # flush=True 确保 nohup 下立即输出
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{now}] {msg}\n")
    except Exception as e:
        # best-effort: 文件写失败不致命 (print 已输出), 但要可见
        # 仅每 ~50 次警告一次避免刷屏
        if not hasattr(log, "_file_err_count"):
            log._file_err_count = 0
        log._file_err_count += 1
        if log._file_err_count == 1 or log._file_err_count % 50 == 0:
            print(f"WARNING: log file write failed ({type(e).__name__}: {e}), 仅 stdout 日志 [累计 {log._file_err_count} 次]", flush=True)
