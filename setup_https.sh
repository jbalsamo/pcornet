#!/bin/bash
################################################################################
# PCORnet HTTPS Setup Script
# 
# Automates HTTPS configuration with Let's Encrypt SSL certificates
#
# Prerequisites:
# - Domain name pointing to server IP
# - Ports 80 and 443 open in firewall
# - Nginx already installed and configured
#
# Usage: sudo ./setup_https.sh your-domain.com your-email@example.com
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NGINX_SITE_NAME="pcornet"
NGINX_CONFIG="/etc/nginx/sites-available/$NGINX_SITE_NAME"
SERVICE_NAME="pcornet-chat"
LOG_FILE="/var/log/pcornet-https-setup.log"

################################################################################
# Helper Functions
################################################################################

log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        error "Please run as root (use sudo ./setup_https.sh <domain> <email>)"
    fi
}

show_usage() {
    cat << EOF
${BLUE}PCORnet HTTPS Setup Script${NC}

${GREEN}Usage:${NC}
    sudo ./setup_https.sh <domain> <email>

${GREEN}Example:${NC}
    sudo ./setup_https.sh pcornet.example.com admin@example.com

${GREEN}Parameters:${NC}
    domain  - Your fully qualified domain name
    email   - Your email address for Let's Encrypt notifications

${GREEN}What this script does:${NC}
    1. Validates prerequisites
    2. Updates Nginx configuration with your domain
    3. Installs certbot if not present
    4. Obtains SSL certificate from Let's Encrypt
    5. Configures automatic HTTP to HTTPS redirect
    6. Sets up automatic certificate renewal
    7. Tests the configuration

EOF
}

check_prerequisites() {
    section "Checking Prerequisites"
    
    # Check Nginx
    if ! command -v nginx &gt; /dev/null; then
        error "Nginx is not installed. Run ./install.sh first"
    fi
    log "✓ Nginx is installed"
    
    # Check Nginx config exists
    if [ ! -f "$NGINX_CONFIG" ]; then
        error "Nginx config not found: $NGINX_CONFIG. Run ./install.sh first"
    fi
    log "✓ Nginx configuration exists"
    
    # Check if service is running
    if ! systemctl is-active --quiet nginx; then
        error "Nginx is not running. Start it with: sudo systemctl start nginx"
    fi
    log "✓ Nginx is running"
    
    # Check firewall
    if command -v ufw &gt; /dev/null; then
        if ufw status | grep -q "80.*ALLOW"; then
            log "✓ Port 80 is allowed in firewall"
        else
            warn "Port 80 may not be open in firewall"
        fi
        
        if ufw status | grep -q "443.*ALLOW"; then
            log "✓ Port 443 is allowed in firewall"
        else
            warn "Port 443 may not be open in firewall. Opening now..."
            ufw allow 443/tcp &gt;&gt; "$LOG_FILE" 2&gt;&amp;1
        fi
    fi
    
    log "Prerequisites check complete"
}

update_nginx_domain() {
    local domain=$1
    
    section "Updating Nginx Configuration"
    
    log "Backing up current config..."
    cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    
    log "Updating server_name to: $domain"
    sed -i "s/server_name _;/server_name $domain;/" "$NGINX_CONFIG"
    
    log "Testing Nginx configuration..."
    if nginx -t &gt;&gt; "$LOG_FILE" 2&gt;&amp;1; then
        log "✓ Nginx configuration is valid"
        log "Reloading Nginx..."
        systemctl reload nginx
        log "✓ Nginx reloaded successfully"
    else
        error "Nginx configuration test failed. Check $LOG_FILE"
    fi
}

install_certbot() {
    section "Installing Certbot"
    
    if command -v certbot &gt; /dev/null; then
        log "Certbot is already installed"
        certbot --version | tee -a "$LOG_FILE"
    else
        log "Installing certbot and nginx plugin..."
        apt update &gt;&gt; "$LOG_FILE" 2&gt;&amp;1
        apt install -y certbot python3-certbot-nginx &gt;&gt; "$LOG_FILE" 2&gt;&amp;1
        log "✓ Certbot installed successfully"
    fi
}

obtain_certificate() {
    local domain=$1
    local email=$2
    
    section "Obtaining SSL Certificate"
    
    log "Requesting certificate from Let's Encrypt..."
    log "Domain: $domain"
    log "Email: $email"
    
    if certbot --nginx \
        -d "$domain" \
        --email "$email" \
        --agree-tos \
        --no-eff-email \
        --redirect \
        --non-interactive &gt;&gt; "$LOG_FILE" 2&gt;&amp;1; then
        log "✓ SSL certificate obtained successfully"
    else
        error "Failed to obtain SSL certificate. Check $LOG_FILE for details"
    fi
}

test_renewal() {
    section "Testing Certificate Auto-Renewal"
    
    log "Running dry-run renewal test..."
    if certbot renew --dry-run &gt;&gt; "$LOG_FILE" 2&gt;&amp;1; then
        log "✓ Auto-renewal test passed"
    else
        warn "Auto-renewal test failed. Check $LOG_FILE"
    fi
}

show_summary() {
    local domain=$1
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}HTTPS Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Your application is now accessible at:${NC}"
    echo -e "  https://$domain"
    echo ""
    echo -e "${BLUE}Certificate Information:${NC}"
    certbot certificates 2&gt;/dev/null | grep -A 5 "$domain" || true
    echo ""
    echo -e "${BLUE}Certificate Auto-Renewal:${NC}"
    echo "  Certificates expire in 90 days"
    echo "  Auto-renewal runs twice daily via systemd timer"
    echo "  Check status: sudo systemctl status certbot.timer"
    echo ""
    echo -e "${BLUE}Manual Renewal:${NC}"
    echo "  sudo certbot renew"
    echo ""
    echo -e "${BLUE}Nginx Configuration:${NC}"
    echo "  Config file: $NGINX_CONFIG"
    echo "  Backup: ${NGINX_CONFIG}.backup.*"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View certificates: sudo certbot certificates"
    echo "  Renew manually: sudo certbot renew"
    echo "  Test renewal: sudo certbot renew --dry-run"
    echo "  View renewal timer: sudo systemctl list-timers certbot"
    echo ""
}

################################################################################
# Main
################################################################################

main() {
    echo -e "${GREEN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║         PCORnet HTTPS Setup - Let's Encrypt SSL          ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Parse arguments
    DOMAIN="${1:-}"
    EMAIL="${2:-}"
    
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        show_usage
        error "Missing required arguments"
    fi
    
    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    
    log "HTTPS setup started at $(date)"
    log "Domain: $DOMAIN"
    log "Email: $EMAIL"
    
    # Run setup
    check_root
    check_prerequisites
    update_nginx_domain "$DOMAIN"
    install_certbot
    obtain_certificate "$DOMAIN" "$EMAIL"
    test_renewal
    show_summary "$DOMAIN"
    
    log "HTTPS setup completed at $(date)"
}

main "$@"
