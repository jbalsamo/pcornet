#!/bin/bash
################################################################################
# PCORnet Service Management Script
# 
# Easy commands to manage the PCORnet systemd service
#
# Usage: sudo ./manage.sh [start|stop|restart|status|logs|tail]
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="pcornet-chat"
APP_DIR="/opt/pcornet"

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}[ERROR]${NC} Please run as root (use sudo ./manage.sh <command>)"
        exit 1
    fi
}

check_service_exists() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo -e "${RED}[ERROR]${NC} Service $SERVICE_NAME not found. Run ./install.sh first."
        exit 1
    fi
}

show_usage() {
    echo "PCORnet Service Management"
    echo ""
    echo "Usage: sudo ./manage.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the PCORnet service"
    echo "  stop     - Stop the PCORnet service"
    echo "  restart  - Restart the PCORnet service"
    echo "  status   - Show service status"
    echo "  logs     - Show recent logs (last 100 lines)"
    echo "  tail     - Tail logs in real-time (Ctrl+C to exit)"
    echo "  reload   - Reload systemd configuration"
    echo "  enable   - Enable service to start on boot"
    echo "  disable  - Disable service from starting on boot"
    echo ""
}

cmd_start() {
    echo -e "${BLUE}Starting $SERVICE_NAME...${NC}"
    systemctl start "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Check logs with: sudo ./manage.sh logs"
        exit 1
    fi
}

cmd_stop() {
    echo -e "${BLUE}Stopping $SERVICE_NAME...${NC}"
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service stopped${NC}"
}

cmd_restart() {
    echo -e "${BLUE}Restarting $SERVICE_NAME...${NC}"
    systemctl restart "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓ Service restarted successfully${NC}"
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        echo -e "${RED}✗ Service failed to restart${NC}"
        echo "Check logs with: sudo ./manage.sh logs"
        exit 1
    fi
}

cmd_status() {
    systemctl status "$SERVICE_NAME" --no-pager -l
}

cmd_logs() {
    echo -e "${BLUE}Showing last 100 lines of logs:${NC}"
    journalctl -u "$SERVICE_NAME" -n 100 --no-pager
}

cmd_tail() {
    echo -e "${BLUE}Tailing logs (Ctrl+C to exit):${NC}"
    journalctl -u "$SERVICE_NAME" -f
}

cmd_reload() {
    echo -e "${BLUE}Reloading systemd configuration...${NC}"
    systemctl daemon-reload
    echo -e "${GREEN}✓ Configuration reloaded${NC}"
}

cmd_enable() {
    echo -e "${BLUE}Enabling $SERVICE_NAME to start on boot...${NC}"
    systemctl enable "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service enabled${NC}"
}

cmd_disable() {
    echo -e "${BLUE}Disabling $SERVICE_NAME from starting on boot...${NC}"
    systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✓ Service disabled${NC}"
}

# Main
check_root
check_service_exists

COMMAND="${1:-}"

case "$COMMAND" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    tail)
        cmd_tail
        ;;
    reload)
        cmd_reload
        ;;
    enable)
        cmd_enable
        ;;
    disable)
        cmd_disable
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
