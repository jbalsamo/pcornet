#!/bin/bash
################################################################################
# PCORnet Uninstaller
# 
# Removes the PCORnet service and optionally removes all files
#
# Usage: sudo ./uninstall.sh [--keep-data]
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="pcornet-chat"
APP_USER="pcornet"
APP_DIR="/opt/pcornet"
NGINX_SITE_NAME="pcornet"

KEEP_DATA=false

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}[ERROR]${NC} Please run as root (use sudo ./uninstall.sh)"
        exit 1
    fi
}

confirm_uninstall() {
    echo -e "${YELLOW}WARNING: This will remove the PCORnet service${NC}"
    if [ "$KEEP_DATA" = false ]; then
        echo -e "${YELLOW}         All application data will be deleted!${NC}"
    else
        echo -e "${GREEN}         Application data will be preserved in $APP_DIR${NC}"
    fi
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Uninstall cancelled"
        exit 0
    fi
}

stop_and_disable_service() {
    echo -e "${BLUE}Stopping and disabling service...${NC}"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}✓ Service stopped${NC}"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME"
        echo -e "${GREEN}✓ Service disabled${NC}"
    fi
}

remove_service_file() {
    echo -e "${BLUE}Removing systemd service file...${NC}"
    
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        echo -e "${GREEN}✓ Service file removed${NC}"
    fi
}

remove_nginx_config() {
    echo -e "${BLUE}Removing Nginx configuration...${NC}"
    
    if [ -L "/etc/nginx/sites-enabled/$NGINX_SITE_NAME" ]; then
        rm -f "/etc/nginx/sites-enabled/$NGINX_SITE_NAME"
        echo -e "${GREEN}✓ Nginx site disabled${NC}"
    fi
    
    if [ -f "/etc/nginx/sites-available/$NGINX_SITE_NAME" ]; then
        rm -f "/etc/nginx/sites-available/$NGINX_SITE_NAME"
        echo -e "${GREEN}✓ Nginx configuration removed${NC}"
    fi
    
    if systemctl is-active --quiet nginx; then
        nginx -t && systemctl reload nginx
        echo -e "${GREEN}✓ Nginx reloaded${NC}"
    fi
}

remove_app_files() {
    if [ "$KEEP_DATA" = true ]; then
        echo -e "${YELLOW}Keeping application data at $APP_DIR${NC}"
        return
    fi
    
    echo -e "${BLUE}Removing application files...${NC}"
    
    if [ -d "$APP_DIR" ]; then
        rm -rf "$APP_DIR"
        echo -e "${GREEN}✓ Application files removed${NC}"
    fi
}

remove_app_user() {
    if [ "$KEEP_DATA" = true ]; then
        echo -e "${YELLOW}Keeping user $APP_USER${NC}"
        return
    fi
    
    echo -e "${BLUE}Removing application user...${NC}"
    
    if id "$APP_USER" &>/dev/null; then
        deluser --remove-home "$APP_USER" 2>/dev/null || userdel -r "$APP_USER" 2>/dev/null || true
        echo -e "${GREEN}✓ User removed${NC}"
    fi
}

main() {
    echo -e "${RED}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║        PCORnet Multi-Agent Chat System - Uninstaller      ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Parse arguments
    if [[ "$1" == "--keep-data" ]]; then
        KEEP_DATA=true
    fi
    
    check_root
    confirm_uninstall
    
    stop_and_disable_service
    remove_service_file
    remove_nginx_config
    remove_app_files
    remove_app_user
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Uninstall Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [ "$KEEP_DATA" = true ]; then
        echo -e "${YELLOW}Application data preserved at: $APP_DIR${NC}"
        echo -e "${YELLOW}To reinstall, run: sudo ./install.sh${NC}"
    else
        echo -e "${GREEN}All PCORnet components removed${NC}"
    fi
    echo ""
}

main "$@"
