#!/bin/bash
# 一键启动脚本 - 芙清DMP数据抓取
# 用法: ./START.sh [选项]
#
# 本脚本为 run.sh 的薄包装，所有参数透传给 core/run.sh。

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/core"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${GREEN}芙清DMP数据抓取 - 一键启动${NC}"
    echo ""
    echo "用法: ./START.sh [选项]"
    echo ""
    echo "跑批选项:"
    echo "  -a, --assets        运行资产诊断抓取 (data2.csv)"
    echo "  -f, --flow          运行流转数据抓取 (data.csv)"
    echo "  -i, --items         运行单品洞察抓取 (data3.csv, 默认 T-1)"
    echo "  -A, --all           运行全部抓取（默认）"
    echo ""
    echo "监控/状态选项:"
    echo "  -m, --monitor       实时监控最新日志"
    echo "  -s, --status        查看 data3.csv 数据状态"
    echo ""
    echo "环境选项:"
    echo "  -t, --t-offset N    设置 T_OFFSET (单品洞察日期偏移, 默认 1)"
    echo "  -b, --backfill DAYS 设置 BACKFILL_DAYS (历史回填天数)"
    echo ""
    echo "示例:"
    echo "  ./START.sh              # 运行全部抓取"
    echo "  ./START.sh -i           # 单品洞察 T-1"
    echo "  ./START.sh -t 2 -i      # 单品洞察 T-2"
    echo "  ./START.sh -m           # 实时监控正在跑的日志"
    echo "  ./START.sh -s           # 查看 data3.csv 最新/缺失日期"
}

# 确保脚本可执行
chmod +x run.sh 2>/dev/null || true

# 无参数 → 默认全部
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    "")
        echo -e "${GREEN}运行全部抓取...${NC}"
        ./run.sh -A
        ;;
    *)
        ./run.sh "$@"
        ;;
esac
