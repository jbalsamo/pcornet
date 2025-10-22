# Upgrade and Patching Guide

Complete guide for updating and patching your PCORnet installation.

## Table of Contents
- [Overview](#overview)
- [Installation Modes](#installation-modes)
- [Quick Update](#quick-update)
- [Update Methods](#update-methods)
- [What Gets Updated](#what-gets-updated)
- [Safety and Backups](#safety-and-backups)
- [Troubleshooting](#troubleshooting)

## Overview

The PCORnet installer now supports two modes:

1. **Full Install** - Fresh installation of the application
2. **Patch/Upgrade** - Update existing installation while preserving data and configuration

## Installation Modes

### Full Install Mode

Performs a complete fresh installation:
- Creates system user
- Installs all dependencies
- Configures nginx from scratch
- Sets up firewall rules
- Creates new .env template (if none exists)

**When to use:**
- First-time installation
- Complete reinstall needed
- Major version upgrades requiring fresh setup

**Command:**
```bash
sudo ./install.sh
```

### Patch/Upgrade Mode

Updates only the application code and dependencies:
- ✅ Updates application files (main.py, modules/, etc.)
- ✅ Updates Python dependencies
- ✅ Preserves .env configuration
- ✅ Preserves data/ and saved/ directories
- ✅ Preserves nginx configuration (including HTTPS)
- ✅ Skips system-level changes (user, firewall, etc.)
- ✅ Creates .env backup automatically

**When to use:**
- Code updates
- Bug fixes
- Feature updates
- Dependency updates
- Regular maintenance

**Commands:**
```bash
sudo ./install.sh --patch
# or
sudo ./install.sh --upgrade
```

## Quick Update

The simplest way to update your installation:

### Step 1: Transfer Updated Files

**Option A: Using Git (Recommended)**
```bash
# On the server
cd /opt/pcornet
sudo -u pcornet git pull origin main
```

**Option B: Using SCP**
```bash
# From your local machine
scp -r pcornet/ ubuntu@your-server-ip:/tmp/pcornet-update/
```

### Step 2: Run Patch Installer

```bash
# If using git (already in /opt/pcornet)
cd /opt/pcornet
sudo ./install.sh --patch

# If using SCP
cd /tmp/pcornet-update
sudo ./install.sh --patch
```

### Step 3: Verify Update

```bash
# Check service status
sudo systemctl status pcornet-chat

# View logs
sudo journalctl -u pcornet-chat -n 50

# Test access
curl -I http://localhost
```

**Done!** Your application is updated and running.

---

## Update Methods

### Method 1: Automatic Patch Detection

When you run the installer on an existing installation, it automatically detects this and prompts you:

```bash
sudo ./install.sh
```

**Output:**
```
Existing installation detected at /opt/pcornet
You have an existing installation.

Options:
  1. Update/Patch existing installation (recommended)
  2. Full reinstall (will preserve .env and data)
  3. Cancel

Choose option (1-3):
```

Select option **1** for a patch update.

### Method 2: Explicit Patch Mode

Skip the prompt by specifying patch mode directly:

```bash
sudo ./install.sh --patch
```

or

```bash
sudo ./install.sh --upgrade
```

### Method 3: Git-Based Updates

Best for ongoing development and updates:

#### Initial Setup (One-Time)

```bash
# On the server, clone the repo to /opt/pcornet
cd /opt
sudo git clone https://github.com/your-repo/pcornet.git
sudo chown -R pcornet:pcornet pcornet

# Run initial install
cd pcornet
sudo ./install.sh
```

#### Subsequent Updates

```bash
# Pull latest changes
cd /opt/pcornet
sudo -u pcornet git pull

# Apply updates
sudo ./install.sh --patch
```

### Method 4: Manual File Transfer

For environments without git access:

```bash
# 1. On local machine: Package updated files
tar -czf pcornet-update.tar.gz pcornet/

# 2. Transfer to server
scp pcornet-update.tar.gz ubuntu@server:/tmp/

# 3. On server: Extract
cd /tmp
tar -xzf pcornet-update.tar.gz

# 4. Run patch installer
cd pcornet
sudo ./install.sh --patch
```

---

## What Gets Updated

### Files Updated in Patch Mode

✅ **Application Code**
- `main.py` - Main application entry point
- `modules/` - All application modules
- `tests/` - Test suite
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `*.sh` - Shell scripts

✅ **Configuration Files**
- `requirements.txt` - Python dependencies
- `.cursorrules` - AI coding standards
- `.streamlit/config.toml` - Streamlit configuration
- `pytest.ini` - Test configuration

✅ **Python Dependencies**
- Upgrades packages in `requirements.txt`
- Updates virtual environment

### Files Preserved in Patch Mode

🔒 **Configuration**
- `.env` - Your Azure credentials (backed up automatically)
- `.env.backup.*` - Previous .env backups

🔒 **Data Directories**
- `data/` - Session data
- `saved/` - Saved conversations
- `logs/` - Application logs

🔒 **System Configuration**
- Nginx configuration (including HTTPS setup)
- Systemd service file
- Firewall rules
- System user and permissions

🔒 **Python Environment**
- `.venv/` - Virtual environment (packages updated, not recreated)

### Comparison Table

| Component | Full Install | Patch Mode |
|-----------|-------------|------------|
| Application code | ✅ Installed | ✅ Updated |
| Python dependencies | ✅ Installed | ✅ Upgraded |
| System packages | ✅ Installed | ⏭️ Skipped |
| .env file | ⚠️ Template created | ✅ Preserved |
| data/ directory | 📁 Created empty | ✅ Preserved |
| saved/ directory | 📁 Created empty | ✅ Preserved |
| Nginx config | ✅ Created | ✅ Preserved |
| HTTPS config | ⏭️ Manual setup | ✅ Preserved |
| System user | ✅ Created | ⏭️ Skipped |
| Firewall rules | ✅ Configured | ⏭️ Skipped |
| Systemd service | ✅ Created | ✅ Updated |

---

## Safety and Backups

### Automatic Backups

The patch installer automatically backs up critical files:

#### .env Backup
```bash
# Automatic backup created during patch
/opt/pcornet/.env.backup.YYYYMMDD_HHMMSS
```

**Example:**
```bash
/opt/pcornet/.env.backup.20250122_143025
```

#### Nginx Backup
```bash
# Manual backup when updating nginx
/etc/nginx/sites-available/pcornet.backup.YYYYMMDD_HHMMSS
```

### Manual Backups (Recommended)

Before any major update, create manual backups:

```bash
# Backup .env
sudo cp /opt/pcornet/.env ~/pcornet-env-backup.txt

# Backup data
sudo tar -czf ~/pcornet-data-$(date +%Y%m%d).tar.gz \
    /opt/pcornet/data/ \
    /opt/pcornet/saved/

# Backup entire installation
sudo tar -czf ~/pcornet-full-backup-$(date +%Y%m%d).tar.gz \
    /opt/pcornet/

# Backup nginx config
sudo cp /etc/nginx/sites-available/pcornet \
    ~/pcornet-nginx-backup.conf
```

### Restore from Backup

If something goes wrong:

#### Restore .env
```bash
sudo cp /opt/pcornet/.env.backup.* /opt/pcornet/.env
sudo systemctl restart pcornet-chat
```

#### Restore Data
```bash
sudo tar -xzf ~/pcornet-data-YYYYMMDD.tar.gz -C /
sudo chown -R pcornet:pcornet /opt/pcornet/data /opt/pcornet/saved
sudo systemctl restart pcornet-chat
```

#### Restore Full Installation
```bash
# Stop service
sudo systemctl stop pcornet-chat

# Restore
sudo rm -rf /opt/pcornet
sudo tar -xzf ~/pcornet-full-backup-YYYYMMDD.tar.gz -C /
sudo chown -R pcornet:pcornet /opt/pcornet

# Restart
sudo systemctl start pcornet-chat
```

---

## Update Workflow

### Recommended Update Process

```
1. Backup Data
   ↓
2. Pull/Transfer Code
   ↓
3. Review Changes (git diff, changelog)
   ↓
4. Run Patch Installer
   ↓
5. Test Service
   ↓
6. Monitor Logs
   ↓
7. Verify Functionality
```

### Detailed Steps

#### 1. Pre-Update Checks

```bash
# Check current version/commit
cd /opt/pcornet
git log -1 --oneline  # If using git

# Check service status
sudo systemctl status pcornet-chat

# Backup data
sudo tar -czf ~/pcornet-backup-$(date +%Y%m%d).tar.gz \
    /opt/pcornet/.env \
    /opt/pcornet/data/ \
    /opt/pcornet/saved/
```

#### 2. Get Updates

```bash
# Using git
cd /opt/pcornet
sudo -u pcornet git pull

# Or transfer files via SCP
# (see Method 4 above)
```

#### 3. Review Changes

```bash
# View changes (git)
git log --oneline -10
git diff HEAD~1 requirements.txt  # Check dependency changes

# Review changelog
cat CHANGELOG.md  # If available
```

#### 4. Apply Update

```bash
sudo ./install.sh --patch
```

**Watch for:**
- ✅ Green "SUCCESS" messages
- ⚠️ Yellow "WARNING" messages (usually safe)
- ❌ Red "ERROR" messages (needs attention)

#### 5. Verify Service

```bash
# Check service started
sudo systemctl status pcornet-chat

# Should show: "active (running)"
```

#### 6. Monitor Logs

```bash
# Watch logs in real-time
sudo journalctl -u pcornet-chat -f

# Look for:
# - ✅ "Streamlit server started"
# - ✅ No Azure credential errors
# - ✅ No import errors
```

#### 7. Test Functionality

```bash
# Test HTTP access
curl -I http://localhost

# Should return: HTTP/1.1 200 OK

# Test HTTPS (if configured)
curl -I https://your-domain.com

# Should return: HTTP/2 200
```

**Manual Testing:**
- Open application in browser
- Test chat functionality
- Test ICD search
- Verify data persistence

---

## Troubleshooting

### Issue: Service Won't Start After Update

**Check logs:**
```bash
sudo journalctl -u pcornet-chat -n 50
```

**Common causes:**

1. **Missing Python dependencies**
   ```bash
   # Reinstall dependencies
   cd /opt/pcornet
   sudo -u pcornet bash -c 'source .venv/bin/activate && pip install -r requirements.txt'
   sudo systemctl restart pcornet-chat
   ```

2. **Python syntax errors**
   ```bash
   # Test Python imports
   cd /opt/pcornet
   sudo -u pcornet bash -c 'source .venv/bin/activate && python -c "import main"'
   ```

3. **Missing .env file**
   ```bash
   # Restore from backup
   sudo cp /opt/pcornet/.env.backup.* /opt/pcornet/.env
   ```

### Issue: Update Fails Midway

**Safe to retry:**
```bash
# Patch mode is idempotent - safe to run multiple times
sudo ./install.sh --patch
```

**Or rollback:**
```bash
# Restore from backup
sudo tar -xzf ~/pcornet-backup-YYYYMMDD.tar.gz -C /
sudo systemctl restart pcornet-chat
```

### Issue: Dependencies Not Updating

**Force dependency upgrade:**
```bash
cd /opt/pcornet
sudo -u pcornet bash -c 'source .venv/bin/activate && pip install -r requirements.txt --upgrade --force-reinstall'
sudo systemctl restart pcornet-chat
```

### Issue: Permission Denied Errors

**Fix ownership:**
```bash
sudo chown -R pcornet:pcornet /opt/pcornet
sudo chmod 755 /opt/pcornet
sudo chmod 600 /opt/pcornet/.env
```

### Issue: Old Code Still Running

**Clear Python cache:**
```bash
cd /opt/pcornet
sudo find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
sudo find . -type f -name "*.pyc" -delete
sudo systemctl restart pcornet-chat
```

### Issue: Azure Credentials Error After Update

**Verify .env:**
```bash
sudo cat /opt/pcornet/.env
```

**If corrupted, restore:**
```bash
sudo cp /opt/pcornet/.env.backup.* /opt/pcornet/.env
sudo systemctl restart pcornet-chat
```

---

## Best Practices

### 1. Always Backup Before Updates
Even though patch mode preserves data, backups provide additional safety.

### 2. Test in Development First
If possible, test updates in a dev/staging environment before production.

### 3. Update During Low-Traffic Periods
Schedule updates when fewer users are active.

### 4. Monitor After Updates
Watch logs for 5-10 minutes after updating to catch issues early.

### 5. Keep Update Schedule
Regular updates ensure security patches and improvements are applied.

### 6. Document Changes
Keep notes on what was updated and when.

### 7. Use Git Tags/Releases
Tag stable versions for easy rollback:
```bash
git tag -a v1.2.0 -m "Stable release 1.2.0"
git push origin v1.2.0
```

---

## Quick Reference

### Update Commands

```bash
# Automated patch (with auto-detection)
sudo ./install.sh

# Explicit patch mode
sudo ./install.sh --patch
sudo ./install.sh --upgrade

# Git-based update
cd /opt/pcornet
sudo -u pcornet git pull
sudo ./install.sh --patch

# Check service status
sudo systemctl status pcornet-chat

# View logs
sudo journalctl -u pcornet-chat -f

# Restart service
sudo systemctl restart pcornet-chat
```

### Backup Commands

```bash
# Backup .env
sudo cp /opt/pcornet/.env ~/env-backup.txt

# Backup data
sudo tar -czf ~/data-backup.tar.gz /opt/pcornet/data/ /opt/pcornet/saved/

# Backup full install
sudo tar -czf ~/full-backup.tar.gz /opt/pcornet/

# List backups
ls -lh ~/*.tar.gz
```

### Verification Commands

```bash
# Test HTTP
curl -I http://localhost

# Test service
sudo systemctl status pcornet-chat

# Check Python environment
sudo -u pcornet /opt/pcornet/.venv/bin/python --version

# List installed packages
sudo -u pcornet /opt/pcornet/.venv/bin/pip list
```

---

## Update Checklist

Use this checklist for updates:

- [ ] Backup .env file
- [ ] Backup data directories
- [ ] Check current service status
- [ ] Note current version/commit
- [ ] Pull/transfer updated code
- [ ] Review changes (git log, changelog)
- [ ] Run patch installer: `sudo ./install.sh --patch`
- [ ] Verify service started
- [ ] Check logs for errors
- [ ] Test HTTP/HTTPS access
- [ ] Test application functionality
- [ ] Monitor for 5-10 minutes
- [ ] Document update (date, version, issues)

---

**Need help?** Check logs with `sudo journalctl -u pcornet-chat -xe` or refer to the troubleshooting section above.
