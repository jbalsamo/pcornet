#!/bin/bash
################################################################################
# PCORnet Multi-Agent Chat System - Ubuntu 24 Installer
# 
# This script installs the PCORnet app as a systemd service with:
# - Automatic dependency installation
# - Service management (start/stop/restart)
# - Nginx reverse proxy
# - Proper environment configuration
#
# Usage: sudo ./install.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="pcornet"
APP_USER="pcornet"
APP_PORT=8888
APP_DIR="/opt/pcornet"
SERVICE_NAME="pcornet-chat"
NGINX_SITE_NAME="pcornet"
LOG_FILE="/var/log/${SERVICE_NAME}-install.log"

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
        error "Please run as root (use sudo ./install.sh)"
    fi
}

check_ubuntu_version() {
    if [ ! -f /etc/os-release ]; then
        error "Cannot determine OS version"
    fi
    
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        warn "This script is designed for Ubuntu. Your OS: $ID"
    fi
    
    log "Detected: $PRETTY_NAME"
}

################################################################################
# Check if already installed and stop service
################################################################################

check_and_stop_existing() {
    section "Checking for Existing Installation"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Service $SERVICE_NAME is running. Stopping..."
        systemctl stop "$SERVICE_NAME"
        log "Service stopped successfully"
    else
        log "Service $SERVICE_NAME is not running"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        log "Service $SERVICE_NAME is enabled. Disabling..."
        systemctl disable "$SERVICE_NAME"
        log "Service disabled successfully"
    fi
}

################################################################################
# Install System Dependencies
################################################################################

install_system_dependencies() {
    section "Installing System Dependencies"
    
    log "Updating package lists..."
    apt update >> "$LOG_FILE" 2>&1
    
    log "Installing required packages..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        ufw \
        git \
        curl >> "$LOG_FILE" 2>&1
    
    log "System dependencies installed successfully"
}

################################################################################
# Create Application User
################################################################################

create_app_user() {
    section "Creating Application User"
    
    if id "$APP_USER" &>/dev/null; then
        log "User $APP_USER already exists"
    else
        log "Creating user $APP_USER..."
        adduser --system --group --home "$APP_DIR" --shell /bin/bash "$APP_USER"
        log "User $APP_USER created successfully"
    fi
}

################################################################################
# Validate Required Files
################################################################################

validate_required_files() {
    section "Validating Required Files"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    log "Checking for required files in $SCRIPT_DIR..."
    
    # List of required files
    REQUIRED_FILES=(
        "main.py"
        "requirements.txt"
        "modules/config.py"
        "modules/master_agent.py"
    )
    
    MISSING_FILES=()
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$file" ]; then
            MISSING_FILES+=("$file")
            warn "Missing required file: $file"
        else
            log "Found: $file"
        fi
    done
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        error "Missing required files: ${MISSING_FILES[*]}\nPlease run this script from the PCORnet project directory."
    fi
    
    log "All required files present"
}

################################################################################
# Setup Application Directory
################################################################################

setup_app_directory() {
    section "Setting Up Application Directory"
    
    log "Creating application directory at $APP_DIR..."
    mkdir -p "$APP_DIR"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    log "Copying application files from $SCRIPT_DIR..."
    
    # Copy all necessary files
    rsync -av --exclude='.venv' \
              --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.git' \
              --exclude='data/' \
              --exclude='saved/' \
              --exclude='.env' \
              "$SCRIPT_DIR/" "$APP_DIR/" >> "$LOG_FILE" 2>&1
    
    # Create necessary directories
    mkdir -p "$APP_DIR/data"
    mkdir -p "$APP_DIR/saved"
    mkdir -p "$APP_DIR/logs"
    
    log "Application files copied successfully"
}

################################################################################
# Check Python Version
################################################################################

check_python_version() {
    section "Checking Python Version"
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        error "python3 is not installed. Please install Python 3 first."
    fi
    
    # Get Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log "Found Python version: $PYTHON_VERSION"
    
    # Extract major and minor version
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    # Check if Python 3.8 or higher
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    fi
    
    log "Python version check passed (3.8+ required)"
}

################################################################################
# Setup Python Virtual Environment
################################################################################

setup_python_environment() {
    section "Setting Up Python Virtual Environment"
    
    # Verify requirements.txt exists
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        error "requirements.txt not found in $APP_DIR"
    fi
    
    log "Creating virtual environment..."
    if sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"; then
        log "Virtual environment created successfully"
    else
        error "Failed to create virtual environment. Check if python3-venv is installed."
    fi
    
    log "Upgrading pip..."
    sudo -u "$APP_USER" bash -c "cd $APP_DIR && source .venv/bin/activate && pip install --upgrade pip" >> "$LOG_FILE" 2>&1
    
    log "Installing Python dependencies..."
    if sudo -u "$APP_USER" bash -c "cd $APP_DIR && source .venv/bin/activate && pip install -r requirements.txt" >> "$LOG_FILE" 2>&1; then
        log "Python dependencies installed successfully"
    else
        error "Failed to install Python dependencies. Check $LOG_FILE for details."
    fi
    
    log "Python environment configured successfully"
}

################################################################################
# Configure Environment Variables
################################################################################

configure_environment() {
    section "Configuring Environment Variables"
    
    ENV_FILE="$APP_DIR/.env"
    
    if [ -f "$ENV_FILE" ]; then
        log "Found existing .env file"
        warn "Please verify your Azure credentials in: $ENV_FILE"
    else
        log "Creating template .env file..."
        cat > "$ENV_FILE" << 'EOF'
# Azure OpenAI Credentials
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-openai-api-key"
AZURE_OPENAI_API_VERSION="2024-05-01-preview"
AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o"

# Azure AI Search Credentials
AZURE_AI_SEARCH_ENDPOINT="https://your-search-service-name.search.windows.net"
AZURE_AI_SEARCH_API_KEY="your-search-admin-or-query-key"
AZURE_AI_SEARCH_INDEX="pcornet-icd-index"
EOF
        warn "Created template .env file at: $ENV_FILE"
        warn "You MUST edit this file with your actual Azure credentials before starting the service!"
    fi
    
    # Set permissions
    chown "$APP_USER:$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
}

################################################################################
# Create Streamlit Config
################################################################################

create_streamlit_config() {
    section "Creating Streamlit Configuration"
    
    STREAMLIT_CONFIG_DIR="$APP_DIR/.streamlit"
    mkdir -p "$STREAMLIT_CONFIG_DIR"
    
    log "Creating Streamlit config.toml..."
    cat > "$STREAMLIT_CONFIG_DIR/config.toml" << EOF
[server]
headless = true
port = $APP_PORT
address = "127.0.0.1"
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
base = "dark"
primaryColor = "#1f77b4"
EOF
    
    chown -R "$APP_USER:$APP_USER" "$STREAMLIT_CONFIG_DIR"
    log "Streamlit configuration created"
}

################################################################################
# Create Systemd Service
################################################################################

create_systemd_service() {
    section "Creating Systemd Service"
    
    log "Creating systemd service file..."
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=PCORnet Multi-Agent Chat System
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/streamlit run main.py --server.port $APP_PORT --server.address 127.0.0.1
Restart=on-failure
RestartSec=5
StandardOutput=append:$APP_DIR/logs/streamlit.log
StandardError=append:$APP_DIR/logs/streamlit-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
EOF
    
    log "Reloading systemd daemon..."
    systemctl daemon-reload
    
    log "Enabling service to start on boot..."
    systemctl enable "$SERVICE_NAME"
    
    log "Systemd service created and enabled"
}

################################################################################
# Configure Nginx Reverse Proxy
################################################################################

configure_nginx() {
    section "Configuring Nginx Reverse Proxy"
    
    log "Creating Nginx site configuration..."
    cat > "/etc/nginx/sites-available/$NGINX_SITE_NAME" << EOF
# PCORnet Nginx Configuration
# Port 80 - HTTP (will be used by certbot for HTTPS setup)
server {
    listen 80;
    listen [::]:80;
    server_name _;  # Change to your domain (e.g., pcornet.example.com)

    # Proxy all requests to Streamlit app on internal port $APP_PORT
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Increase upload limit for file uploads
    client_max_body_size 100M;
}

# Port 443 - HTTPS (will be configured automatically by certbot)
# After running: sudo certbot --nginx -d your-domain.com
# Certbot will add the HTTPS server block here and redirect HTTP to HTTPS
EOF
    
    # Enable the site
    ln -sf "/etc/nginx/sites-available/$NGINX_SITE_NAME" "/etc/nginx/sites-enabled/$NGINX_SITE_NAME"
    
    # Remove default site if exists
    rm -f /etc/nginx/sites-enabled/default
    
    log "Testing Nginx configuration..."
    if nginx -t >> "$LOG_FILE" 2>&1; then
        log "Nginx configuration is valid"
        log "Reloading Nginx..."
        systemctl reload nginx
        log "Nginx configured successfully"
    else
        error "Nginx configuration test failed. Check $LOG_FILE for details"
    fi
}

################################################################################
# Configure Firewall
################################################################################

configure_firewall() {
    section "Configuring Firewall"
    
    log "Configuring UFW firewall..."
    
    # Check if UFW is installed
    if ! command -v ufw &> /dev/null; then
        warn "UFW not found, skipping firewall configuration"
        return
    fi
    
    # Allow SSH
    ufw allow OpenSSH >> "$LOG_FILE" 2>&1
    
    # Allow Nginx
    ufw allow 'Nginx Full' >> "$LOG_FILE" 2>&1
    
    # Enable UFW (will prompt if not already enabled)
    if ! ufw status | grep -q "Status: active"; then
        log "Enabling UFW firewall..."
        echo "y" | ufw enable >> "$LOG_FILE" 2>&1
    fi
    
    log "Firewall configured successfully"
    ufw status numbered
}

################################################################################
# Set Permissions
################################################################################

set_permissions() {
    section "Setting Permissions"
    
    log "Setting ownership and permissions..."
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    chmod 600 "$APP_DIR/.env"
    
    log "Permissions set successfully"
}

################################################################################
# Start Service and Display Logs
################################################################################

start_service_and_show_logs() {
    section "Starting Service"
    
    log "Starting $SERVICE_NAME service..."
    systemctl start "$SERVICE_NAME"
    
    # Wait a moment for service to start
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "Service started successfully!"
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Installation Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Service Status:${NC}"
        systemctl status "$SERVICE_NAME" --no-pager -l
        echo ""
        echo -e "${BLUE}Access your application at:${NC}"
        echo "  - http://localhost:$APP_PORT (if accessing locally)"
        echo "  - http://YOUR_SERVER_IP (from external network)"
        echo ""
        echo -e "${YELLOW}⚠️  REQUIRED CONFIGURATION:${NC}"
        echo ""
        echo "  ${YELLOW}1. Azure Credentials (REQUIRED)${NC}"
        echo "     Edit: $APP_DIR/.env"
        echo "     Fill in your actual Azure OpenAI and AI Search credentials"
        echo "     Then restart: sudo systemctl restart $SERVICE_NAME"
        echo ""
        echo "  ${YELLOW}2. Domain Name (Optional - for HTTPS)${NC}"
        echo "     Edit: /etc/nginx/sites-available/$NGINX_SITE_NAME"
        echo "     Change: server_name _; to server_name your-domain.com;"
        echo "     Then reload: sudo nginx -t && sudo systemctl reload nginx"
        echo ""
        echo "  ${YELLOW}3. HTTPS Setup (Recommended for production)${NC}"
        echo "     After setting domain name, run:"
        echo "     sudo apt install certbot python3-certbot-nginx"
        echo "     sudo certbot --nginx -d your-domain.com"
        echo ""
        echo -e "${BLUE}Service Management Commands:${NC}"
        echo "  - Start:   sudo systemctl start $SERVICE_NAME"
        echo "  - Stop:    sudo systemctl stop $SERVICE_NAME"
        echo "  - Restart: sudo systemctl restart $SERVICE_NAME"
        echo "  - Status:  sudo systemctl status $SERVICE_NAME"
        echo "  - Logs:    sudo journalctl -u $SERVICE_NAME -f"
        echo ""
        echo -e "${BLUE}Showing last 50 lines of logs:${NC}"
        echo "=========================================="
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager
        echo ""
        echo -e "${GREEN}Tailing logs (Ctrl+C to exit):${NC}"
        journalctl -u "$SERVICE_NAME" -f
    else
        error "Service failed to start. Check logs with: sudo journalctl -u $SERVICE_NAME -xe"
    fi
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    echo -e "${GREEN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║  PCORnet Multi-Agent Chat System - Ubuntu 24 Installer   ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    
    log "Installation started at $(date)"
    
    # Pre-flight checks
    check_root
    check_ubuntu_version
    check_python_version
    validate_required_files
    
    # Installation steps
    check_and_stop_existing
    install_system_dependencies
    create_app_user
    setup_app_directory
    setup_python_environment
    configure_environment
    create_streamlit_config
    set_permissions
    create_systemd_service
    configure_nginx
    configure_firewall
    start_service_and_show_logs
    
    log "Installation completed at $(date)"
}

# Run main installation
main
