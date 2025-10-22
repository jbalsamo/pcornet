# Ubuntu Server Installer - Summary

## 📦 What Was Created

### Installation Scripts

#### 1. **install.sh** - Main Installer
**Features:**
- ✅ Checks for existing installation and stops service gracefully
- ✅ Installs system dependencies (Python3, pip, venv, Nginx, UFW)
- ✅ Creates dedicated `pcornet` system user
- ✅ Sets up application in `/opt/pcornet/` with proper permissions
- ✅ Creates Python virtual environment and installs dependencies
- ✅ Configures Streamlit for headless operation (port 8888)
- ✅ Creates systemd service with auto-restart capability
- ✅ Configures Nginx reverse proxy
- ✅ Sets up UFW firewall rules
- ✅ Starts service and displays live logs
- ✅ Colorized output with detailed logging

**Usage:**
```bash
sudo ./install.sh
```

#### 2. **manage.sh** - Service Management
**Commands:**
- `start` - Start the PCORnet service
- `stop` - Stop the PCORnet service
- `restart` - Restart the PCORnet service
- `status` - Show detailed service status
- `logs` - Show last 100 lines of logs
- `tail` - Follow logs in real-time (Ctrl+C to exit)
- `reload` - Reload systemd configuration
- `enable` - Enable service to start on boot
- `disable` - Disable service from starting on boot

**Usage:**
```bash
sudo ./manage.sh [command]
```

#### 3. **uninstall.sh** - Complete Removal
**Features:**
- Stops and disables service
- Removes systemd service file
- Removes Nginx configuration
- Removes application files (optional)
- Removes application user (optional)
- Prompts for confirmation before removal

**Usage:**
```bash
# Remove everything
sudo ./uninstall.sh

# Keep data for reinstall
sudo ./uninstall.sh --keep-data
```

### Documentation Files

#### 4. **docs/UBUNTU_DEPLOYMENT.md** - Complete Deployment Guide
Comprehensive documentation covering:
- Quick start instructions
- Detailed service management
- HTTPS setup with Let's Encrypt
- Deployment update procedures
- Monitoring and troubleshooting
- Security best practices
- Performance tuning
- Multiple environment setup
- Common issues and solutions

#### 5. **docs/DEPLOYMENT_QUICK_START.md** - Quick Reference
One-page quick reference with:
- Installation command
- Post-installation steps
- Service management commands
- Access URLs
- Update procedures
- Troubleshooting commands
- Important file locations

#### 6. **README.md** - Updated
Added new "Deployment Options" section:
- Local development instructions (existing)
- Ubuntu Server production deployment (new)
- Links to complete deployment guide

## 🎯 Key Features

### Installation Behavior

**Smart Installation:**
- Detects existing installations automatically
- Stops running services before reinstall
- Preserves data during reinstall
- Creates template .env file if missing
- Validates Nginx configuration before applying
- Sets proper file permissions and ownership

**Security:**
- Creates dedicated system user (not root)
- Restricts .env file permissions (600)
- Configures UFW firewall
- Binds Streamlit to localhost (127.0.0.1)
- Nginx handles external connections
- No root privileges for application

**Production Ready:**
- Systemd service with auto-restart
- Starts on boot by default
- Logs to systemd journal and files
- Graceful service management
- Zero-downtime updates possible

### File Structure After Installation

```
/opt/pcornet/                      # Application directory
├── modules/                       # Python modules
│   ├── agents/                    # AI agents
│   ├── config.py                  # Configuration
│   ├── master_agent.py           # Master orchestrator
│   └── ...                        # Other modules
├── tests/                         # Test suite
├── docs/                          # Documentation
├── data/                          # Session data
├── saved/                         # Saved conversations
├── logs/                          # Application logs
│   ├── streamlit.log             # stdout
│   └── streamlit-error.log       # stderr
├── .venv/                         # Python virtual environment
├── .env                           # Azure credentials (YOU MUST EDIT)
├── .streamlit/                    # Streamlit config
│   └── config.toml               # Headless mode, port 8888
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
└── ...                            # Other files

/etc/systemd/system/
└── pcornet-chat.service          # Systemd service definition

/etc/nginx/sites-available/
└── pcornet                        # Nginx reverse proxy config

/var/log/
└── pcornet-chat-install.log      # Installation log
```

## 🚀 Quick Start Workflow

### 1. Transfer Files
```bash
# Option A: Git
git clone <repo-url> /tmp/pcornet

# Option B: SCP
scp -r pcornet/ ubuntu@server:/tmp/
```

### 2. Install
```bash
ssh ubuntu@server
cd /tmp/pcornet
sudo ./install.sh
```

### 3. Configure
```bash
sudo nano /opt/pcornet/.env
# Edit Azure credentials
```

### 4. Restart
```bash
sudo systemctl restart pcornet-chat
```

### 5. Verify
```bash
# Check status
sudo systemctl status pcornet-chat

# Follow logs
sudo journalctl -u pcornet-chat -f

# Access app
http://YOUR_SERVER_IP
```

## 🔄 Update Workflow

### For Code Changes:
```bash
# On server
cd /opt/pcornet
sudo -u pcornet git pull
sudo systemctl restart pcornet-chat
```

### For Dependency Changes:
```bash
cd /opt/pcornet
sudo -u pcornet bash -c 'source .venv/bin/activate && pip install -r requirements.txt'
sudo systemctl restart pcornet-chat
```

### For Configuration Changes:
```bash
sudo nano /opt/pcornet/.env
# or
sudo nano /opt/pcornet/.streamlit/config.toml
sudo systemctl restart pcornet-chat
```

## 🔒 Security Considerations

### What's Secure:
- ✅ Application runs as non-root user
- ✅ .env file has restricted permissions (600)
- ✅ UFW firewall configured (SSH + HTTP/HTTPS only)
- ✅ Streamlit binds to localhost only
- ✅ Nginx handles external connections
- ✅ Service isolation with systemd

### What You Should Do:
- 🔐 Set up HTTPS with Let's Encrypt (free)
- 🔐 Use strong Azure API keys
- 🔐 Keep system updated: `sudo apt update && sudo apt upgrade`
- 🔐 Monitor logs regularly
- 🔐 Back up .env and saved/ directory

## 📊 Monitoring

### Check Service Health:
```bash
sudo ./manage.sh status
# or
sudo systemctl status pcornet-chat
```

### View Logs:
```bash
# Real-time
sudo ./manage.sh tail

# Last 100 lines
sudo ./manage.sh logs

# Search for errors
sudo journalctl -u pcornet-chat | grep -i error

# Today's logs
sudo journalctl -u pcornet-chat --since today
```

### Check Resource Usage:
```bash
# CPU and memory
top -p $(systemctl show -p MainPID --value pcornet-chat)

# Disk space
df -h /opt/pcornet
```

## 🧪 Testing the Installation

### 1. Service Status
```bash
sudo systemctl is-active pcornet-chat
# Should output: active
```

### 2. Port Listening
```bash
sudo netstat -tlnp | grep 8888
# Should show Streamlit listening on 127.0.0.1:8888
```

### 3. HTTP Access
```bash
curl -I http://localhost
# Should return HTTP 200 OK
```

### 4. Check Logs
```bash
sudo journalctl -u pcornet-chat -n 10
# Should show recent activity, no errors
```

## ❓ Troubleshooting

### Service Won't Start
```bash
# Check detailed error
sudo journalctl -u pcornet-chat -xe

# Verify virtual environment
sudo -u pcornet /opt/pcornet/.venv/bin/python --version

# Check .env exists
ls -la /opt/pcornet/.env
```

### Can't Access from Browser
```bash
# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check firewall
sudo ufw status

# Check if port is open
sudo netstat -tlnp | grep 8888
```

### Azure Connection Errors
```bash
# Verify credentials
sudo cat /opt/pcornet/.env

# Check logs for Azure errors
sudo journalctl -u pcornet-chat | grep -i azure
```

## 📝 Notes

- **Port:** Application runs on port 8888 (configurable in install.sh)
- **User:** Application runs as `pcornet` system user
- **Auto-start:** Service starts automatically on boot
- **Auto-restart:** Service restarts on failure (5 second delay)
- **Logs:** Both systemd journal and file logs are kept
- **Updates:** Can be updated without reinstalling

## 🎓 Advanced Topics

See [docs/UBUNTU_DEPLOYMENT.md](docs/UBUNTU_DEPLOYMENT.md) for:
- HTTPS setup with Let's Encrypt
- Multiple environment deployment
- Performance tuning
- Custom Nginx configuration
- Database integration
- Monitoring setup
- Backup strategies
- CI/CD integration

---

**All scripts are executable and ready to use on Ubuntu 24 Server!**
