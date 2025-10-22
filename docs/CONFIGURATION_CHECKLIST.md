# Configuration Checklist

## Variables You Need to Configure

### ✅ **REQUIRED** - Azure Credentials

After installation, you **MUST** edit the `.env` file with your actual Azure credentials.

**File Location:** `/opt/pcornet/.env` (on the server after installation)

**Variables to Fill Out:**

```bash
# Azure OpenAI Credentials
AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE-NAME.openai.azure.com/"
AZURE_OPENAI_API_KEY="YOUR-ACTUAL-API-KEY"
AZURE_OPENAI_API_VERSION="2024-05-01-preview"
AZURE_OPENAI_CHAT_DEPLOYMENT="YOUR-DEPLOYMENT-NAME"  # e.g., gpt-4o

# Azure AI Search Credentials
AZURE_AI_SEARCH_ENDPOINT="https://YOUR-SEARCH-SERVICE.search.windows.net"
AZURE_AI_SEARCH_API_KEY="YOUR-SEARCH-API-KEY"
AZURE_AI_SEARCH_INDEX="pcornet-icd-index"  # Your index name
```

**How to Edit:**
```bash
sudo nano /opt/pcornet/.env
```

**After Editing:**
```bash
sudo systemctl restart pcornet-chat
```

---

### 🌐 **OPTIONAL** - Domain Name (for HTTPS)

If you want to use a custom domain with HTTPS, update the Nginx configuration.

**File Location:** `/etc/nginx/sites-available/pcornet`

**What to Change:**
```nginx
# Current (accepts all domains):
server_name _;

# Change to your domain:
server_name pcornet.example.com;
```

**How to Edit:**
```bash
sudo nano /etc/nginx/sites-available/pcornet
```

**After Editing:**
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Pre-Installation Requirements

The installer performs these validation checks **before** installation:

### ✅ **Python Version Check**
- **Minimum Required:** Python 3.8+
- **Checked Automatically:** Installer verifies python3 is installed and version is 3.8 or higher
- **If Check Fails:** Installation stops with error message

### ✅ **Required Files Check**
The installer validates these files exist:
- `main.py` - Application entry point
- `requirements.txt` - Python dependencies
- `modules/config.py` - Configuration module
- `modules/master_agent.py` - Master agent orchestrator

**If any files are missing:** Installation stops with list of missing files

### ✅ **Virtual Environment Creation**
- Creates `.venv` directory automatically
- Validates venv creation was successful
- Upgrades pip to latest version
- Installs all dependencies from requirements.txt
- **Error Handling:** Stops if venv creation or dependency installation fails

---

## Install Script Variables

The `install.sh` script has these **pre-configured** variables (you can customize before running):

```bash
# Application Configuration
APP_NAME="pcornet"              # Application name
APP_USER="pcornet"              # System user to run the app
APP_PORT=8888                   # Internal port for Streamlit
APP_DIR="/opt/pcornet"          # Installation directory
SERVICE_NAME="pcornet-chat"     # Systemd service name
NGINX_SITE_NAME="pcornet"       # Nginx site configuration name
```

**To Customize:** Edit these variables at the top of `install.sh` before running it.

---

## Port Configuration Summary

### How the Ports Work:

```
Internet → Port 80/443 (Nginx) → Port 8888 (Streamlit App)
```

**Port 80 (HTTP):**
- ✅ Configured by installer
- ✅ Listens for HTTP traffic
- ✅ Proxies to internal port 8888
- ✅ Accessible from external network

**Port 443 (HTTPS):**
- ⚙️ Configured by certbot (not the installer)
- ⚙️ Run certbot to enable HTTPS
- ⚙️ Will auto-redirect port 80 to 443

**Port 8888 (Internal):**
- ✅ Streamlit app listens here
- ✅ Only accessible from localhost (127.0.0.1)
- ✅ Not exposed to external network (secure)

### To Enable HTTPS:

**Option 1: Automated Setup (Recommended)**
```bash
# One-command HTTPS setup
sudo ./setup_https.sh your-domain.com your-email@example.com
```

**Option 2: Manual Setup**
```bash
# 1. Install certbot
sudo apt install certbot python3-certbot-nginx

# 2. Update your domain in nginx config first
sudo nano /etc/nginx/sites-available/pcornet
# Change: server_name your-domain.com;

# 3. Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# 4. Run certbot (will auto-configure port 443 and redirect)
sudo certbot --nginx -d your-domain.com
```

**Complete Guide:** See [docs/HTTPS_SETUP_GUIDE.md](docs/HTTPS_SETUP_GUIDE.md)

Certbot will:
- ✅ Obtain free SSL certificate from Let's Encrypt
- ✅ Add port 443 HTTPS configuration to nginx
- ✅ Configure automatic redirect from HTTP (80) to HTTPS (443)
- ✅ Set up auto-renewal (certs expire in 90 days)

---

## Quick Verification

After configuration, verify everything works:

```bash
# 1. Check .env file exists and has correct permissions
ls -la /opt/pcornet/.env
# Should show: -rw------- 1 pcornet pcornet (permissions 600)

# 2. Check service is running
sudo systemctl status pcornet-chat
# Should show: active (running)

# 3. Check nginx is listening on port 80
sudo netstat -tlnp | grep :80
# Should show nginx listening

# 4. Check app is listening on port 8888
sudo netstat -tlnp | grep :8888
# Should show streamlit on 127.0.0.1:8888

# 5. Test HTTP access
curl -I http://localhost
# Should return HTTP 200 OK

# 6. Check for errors in logs
sudo journalctl -u pcornet-chat -n 20
# Should show no Azure credential errors
```

---

## Updating Your Installation

### Quick Update

```bash
# Option 1: Automated patch mode (recommended)
sudo ./install.sh --patch

# Option 2: Let installer detect and prompt
sudo ./install.sh
```

The patch mode:
- ✅ Updates application code
- ✅ Updates Python dependencies
- ✅ Preserves .env configuration
- ✅ Preserves data and saved conversations
- ✅ Preserves HTTPS configuration

**Complete Guide:** See [docs/UPGRADE_AND_PATCHING.md](docs/UPGRADE_AND_PATCHING.md)

---

## Summary

### Must Fill Out:
1. ✅ **Azure OpenAI Endpoint** - Your Azure OpenAI resource URL
2. ✅ **Azure OpenAI API Key** - Your API key from Azure portal
3. ✅ **Azure OpenAI Deployment** - Your model deployment name
4. ✅ **Azure AI Search Endpoint** - Your Azure Search service URL
5. ✅ **Azure AI Search API Key** - Your Search API key
6. ✅ **Azure AI Search Index** - Your index name

### Optional Configuration:
7. 🌐 **Domain Name** - In nginx config (for HTTPS)

### Pre-Configured (No Action Needed):
- ✅ Port 80 → 8888 proxy (handled by installer)
- ✅ Port 8888 internal listening (handled by installer)
- ✅ Service auto-start (handled by installer)
- ✅ Firewall rules (handled by installer)

### Enhanced Features:
- 🔒 **HTTPS Setup** - Automated with `./setup_https.sh` script
- 🔄 **Easy Updates** - Patch mode with `./install.sh --patch`

---

**The installer handles all configuration automatically. You need to:**
1. Fill out Azure credentials in `.env`
2. (Optional) Set up HTTPS with `./setup_https.sh your-domain.com email@example.com`
3. (Future updates) Run `sudo ./install.sh --patch`
