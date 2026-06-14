#!/bin/bash
# DMP数据抓取 - 单一入口脚本 (Mac版)
# 用法:
#   ./run.sh          # 显示交互式菜单
#   ./run.sh -a      # 运行资产诊断 (data2.csv)
#   ./run.sh -f      # 运行流转数据 (data.csv)
#   ./run.sh -i      # 运行单品洞察 (data3.csv, 默认 T-1)
#   ./run.sh -A      # 运行全部模块
#   ./run.sh -m      # 实时监控最新日志
#   ./run.sh -s      # 查看 data3.csv 数据状态
#   ./run.sh -t N    # 设置 T_OFFSET (默认 1)
#   ./run.sh -b DAYS # 设置 BACKFILL_DAYS (历史回填)

set -e

cd "$(dirname "$0")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志目录
LOG_DIR="del/run_logs"
mkdir -p "$LOG_DIR"

# 环境变量透传 (v0.1.18 新增)
export T_OFFSET BACKFILL_DAYS MAX_BACKFILL_DAYS SKIP_RETRY LARK_ALERTS_ENABLED

log_file() {
    local module="$1"
    echo "${LOG_DIR}/run_$(date +%Y%m%d_%H%M%S)_${module}.log"
}

show_help() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  芙清DMP数据抓取 - 单一入口${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "用法: ./run.sh [选项]"
    echo ""
    echo "跑批选项:"
    echo -e "  ${GREEN}-a, --assets${NC}    运行资产诊断 (data2.csv)"
    echo -e "  ${GREEN}-f, --flow${NC}      运行流转数据 (data.csv)"
    echo -e "  ${GREEN}-i, --items${NC}     运行单品洞察 (data3.csv, 默认 T-1)"
    echo -e "  ${GREEN}-A, --all${NC}       运行全部模块"
    echo ""
    echo "监控/状态选项:"
    echo -e "  ${GREEN}-m, --monitor${NC}   实时监控最新日志 (Ctrl+C 退出)"
    echo -e "  ${GREEN}-s, --status${NC}    查看 data3.csv 数据状态"
    echo ""
    echo "环境选项:"
    echo -e "  ${GREEN}-t, --t-offset N${NC}  设置 T_OFFSET (单品洞察日期偏移, 默认 1)"
    echo -e "  ${GREEN}-b, --backfill DAYS${NC} 设置 BACKFILL_DAYS (历史回填天数)"
    echo ""
    echo "示例:"
    echo "  ./run.sh              # 交互式菜单"
    echo "  ./run.sh -i           # 单品洞察 T-1"
    echo "  ./run.sh -t 2 -i      # 单品洞察 T-2"
    echo "  ./run.sh -b 30 -i     # 单品洞察回填 30 天"
    echo "  ./run.sh -m           # 实时监控正在跑的日志"
    echo "  ./run.sh -s           # 查看 data3.csv 最新/缺失日期"
}

show_menu() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  芙清DMP数据抓取 - 交互式菜单${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "请选择操作:"
    echo ""
    echo "  ${GREEN}[1]${NC} 运行全部模块 (资产 + 流转 + 单品)"
    echo "  ${GREEN}[2]${NC} 资产诊断 (data2.csv)"
    echo "  ${GREEN}[3]${NC} 流转数据 (data.csv)"
    echo "  ${GREEN}[4]${NC} 单品洞察 (data3.csv, T-1)"
    echo "  ${GREEN}[5]${NC} 资产 + 流转"
    echo "  ${GREEN}[6]${NC} 实时监控最新日志"
    echo "  ${GREEN}[7]${NC} 查看 data3.csv 数据状态"
    echo ""
    echo -e "  ${YELLOW}[0]${NC} 退出"
    echo ""
}

show_progress() {
    local log="${1:-$(ls -t ${LOG_DIR}/run_*.log 2>/dev/null | head -1)}"
    if [[ ! -f "$log" ]]; then
        return
    fi
    local completed
    completed=$(grep -c "数据提取成功" "$log" 2>/dev/null || echo 0)
    echo ""
    echo -e "${CYAN}进度快照${NC} (${log}):"
    echo "  成功抓取: ${completed} 条"
    tail -n 3 "$log" 2>/dev/null | sed 's/^/  /' || true
}

monitor_latest() {
    local log
    log=$(ls -t ${LOG_DIR}/run_*.log 2>/dev/null | head -1)
    if [[ -z "$log" ]]; then
        echo -e "${RED}暂无运行日志${NC}"
        exit 1
    fi
    echo -e "${CYAN}实时监控: ${log}${NC} (Ctrl+C 退出)"
    tail -f "${log}"
}

show_status() {
    echo -e "${CYAN}data3.csv 数据状态:${NC}"
    PYTHONPATH=.. python3 -m core.utils.csv_state data3.csv
}

run_module() {
    local module="$1"
    local label="$2"
    local log
    log=$(log_file "$module")
    echo -e "${GREEN}▶ ${label}...${NC} 日志: ${log}"
    python3 dmp_master.py --"${module}" 2>&1 | tee -a "${log}"
    echo -e "${GREEN}✓ ${label} 完成${NC}"
    show_progress "${log}"
}

run_assets() {
    run_module assets "资产诊断"
}

run_flow() {
    run_module flow "流转数据"
}

run_items() {
    if [[ -z "${T_OFFSET:-}" ]]; then
        export T_OFFSET=1
    fi
    run_module items "单品洞察"
}

run_all() {
    echo -e "${GREEN}▶ 运行全部模块...${NC}"
    echo ""
    run_assets
    echo ""
    run_flow
    echo ""
    run_items
}

# 处理 -t / -b 前缀参数
if [[ "${1:-}" == "-t" || "${1:-}" == "--t-offset" ]]; then
    T_OFFSET="${2:-1}"
    shift 2
    exec "$0" "$@"
fi

if [[ "${1:-}" == "-b" || "${1:-}" == "--backfill" ]]; then
    BACKFILL_DAYS="${2:-}"
    if [[ -z "$BACKFILL_DAYS" ]]; then
        echo -e "${RED}错误: -b 需要天数参数${NC}"
        exit 1
    fi
    shift 2
    exec "$0" "$@"
fi

# 主逻辑
case "${1:-}" in
    -a|--assets)
        run_assets
        ;;
    -f|--flow)
        run_flow
        ;;
    -i|--items)
        run_items
        ;;
    -A|--all)
        run_all
        ;;
    -m|--monitor)
        monitor_latest
        ;;
    -s|--status)
        show_status
        ;;
    -h|--help)
        show_help
        ;;
    "")
        show_menu
        read -p "请输入选项 (0-7): " choice
        echo ""
        case $choice in
            1) run_all ;;
            2) run_assets ;;
            3) run_flow ;;
            4) run_items ;;
            5)
                run_assets
                echo ""
                run_flow
                ;;
            6) monitor_latest ;;
            7) show_status ;;
            0)
                echo "退出"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选项${NC}"
                exit 1
                ;;
        esac
        ;;
    *)
        show_help
        exit 1
        ;;
esac

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✓ 执行完成${NC}"
echo -e "${CYAN}========================================${NC}"
