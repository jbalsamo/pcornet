# Ubuntu Server Deployment Guide

Complete guide for deploying PCORnet Multi-Agent Chat System on Ubuntu 24 as a production service.

## Quick Start

### 1. Transfer Files to Server

```bash
# From your local machine
scp -r pcornet/ ubuntu@your-server-ip:/tmp/
```

### 2. Run Installer

```bash
# SSH into your server
ssh ubuntu@your-server-ip

# Run the installer
cd /tmp/pcornet
sudo ./install.sh
```

The installer will:
- ✅ Check for existing installations and stop services
- ✅ Install system dependencies (Python, Nginx, UFW)
- ✅ Create dedicated `pcornet` user
- ✅ Set up application in `/opt/pcornet`
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Configure Streamlit settings
- ✅ Create systemd service
- ✅ Configure Nginx reverse proxy
- ✅ Set up firewall rules
- ✅ Start service and display logs

### 3. Configure Azure Credentials

**IMPORTANT:** Edit the `.env` file with your actual Azure credentials:

```bash
sudo nano /opt/pcornet/.env
```

Update these values:
```env
AZURE_OPENAI_ENDPOINT="https://your-actual-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-actual-api-key"
AZURE_AI_SEARCH_ENDPOINT="https://your-actual-search.search.windows.net"
AZURE_AI_SEARCH_API_KEY="your-actual-search-key"
```

Then restart the service:
```bash
sudo systemctl restart pcornet-chat
```

## Service Management

### Using the Management Script

```bash
# Start the service
sudo ./manage.sh start

# Stop the service
sudo ./manage.sh stop

# Restart the service
sudo ./manage.sh restart

# Check status
sudo ./manage.sh status

# View logs (last 100 lines)
sudo ./manage.sh logs

# Tail logs in real-time
sudo ./manage.sh tail

# Reload systemd configuration
sudo ./manage.sh reload

# Enable service on boot
sudo ./manage.sh enable

# Disable service on boot
sudo ./manage.sh disable
```

### Using systemctl Directly

```bash
# Start
sudo systemctl start pcornet-chat

# Stop
sudo systemctl stop pcornet-chat

# Restart
sudo systemctl restart pcornet-chat

# Status
sudo systemctl status pcornet-chat

# Logs
sudo journalctl -u pcornet-chat -f
```

## Access Your Application

### Local Access
```
http://localhost:8888
```

### Remote Access
```
http://YOUR_SERVER_IP
```

### Domain Access (after DNS configuration)
```
http://your-domain.com
```

## Setting Up HTTPS (Optional but Recommended)

### Prerequisites
1. Domain name pointing to your server IP
2. Ports 80 and 443 open in firewall (handled by installer)

### Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL Certificate

```bash
# Replace 'your-domain.com' with your actual domain
sudo certbot --nginx -d your-domain.com --redirect --agree-tos -m your@email.com -n
```

This will:
- Obtain a free SSL certificate from Let's Encrypt
- Automatically configure Nginx for HTTPS
- Set up auto-renewal (certificate expires in 90 days)

### Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

### Update Nginx Domain (Before SSL)

Edit the Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/pcornet
```

Change `server_name _;` to:
```nginx
server_name your-domain.com;
```

Reload Nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Deploying Updates

### Method 1: Using Git (Recommended)

```bash
# SSH into server
ssh ubuntu@your-server-ip

# Navigate to app directory
cd /opt/pcornet

# Pull latest changes
sudo -u pcornet git pull

# Update dependencies if requirements.txt changed
sudo -u pcornet bash -c 'source .venv/bin/activate && pip install -r requirements.txt'

# Restart service
sudo systemctl restart pcornet-chat

# Check logs
sudo journalctl -u pcornet-chat -f
```

### Method 2: Manual File Transfer

```bash
# From local machine, copy updated files
scp -r pcornet/modules/ ubuntu@your-server-ip:/tmp/

# On server
ssh ubuntu@your-server-ip
sudo cp -r /tmp/modules/* /opt/pcornet/modules/
sudo chown -R pcornet:pcornet /opt/pcornet/modules/
sudo systemctl restart pcornet-chat
```

## Monitoring and Troubleshooting

### View Service Status

```bash
sudo systemctl status pcornet-chat
```

### View Real-Time Logs

```bash
# All logs
sudo journalctl -u pcornet-chat -f

# Error logs only
sudo journalctl -u pcornet-chat -f -p err

# Last 100 lines
sudo journalctl -u pcornet-chat -n 100
```

### View Application Logs

```bash
# Streamlit output
sudo tail -f /opt/pcornet/logs/streamlit.log

# Error logs
sudo tail -f /opt/pcornet/logs/streamlit-error.log
```

### Check Nginx Status

```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

### Check Firewall Status

```bash
sudo ufw status verbose
```

### Common Issues

#### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u pcornet-chat -xe

# Verify .env file exists and has correct permissions
ls -la /opt/pcornet/.env

# Check Python environment
sudo -u pcornet /opt/pcornet/.venv/bin/python --version
```

#### Can't Access from External Network
```bash
# Check firewall
sudo ufw status

# Verify Nginx is running
sudo systemctl status nginx

# Check if app is listening
sudo netstat -tlnp | grep 8888
```

#### Azure Connection Errors
```bash
# Verify .env file has correct credentials
sudo cat /opt/pcornet/.env

# Check service logs for Azure errors
sudo journalctl -u pcornet-chat -n 50 | grep -i azure
```

#### Permission Denied Creating .venv
If you see: `[Errno 13] Permission denied: '/opt/pcornet/.venv'`

**Cause:** The pcornet user doesn't have write access to /opt/pcornet

**Fix:**
```bash
# Set correct ownership
sudo chown -R pcornet:pcornet /opt/pcornet

# Retry the installation or manually create venv
sudo -u pcornet python3 -m venv /opt/pcornet/.venv
```

**Note:** The latest installer version fixes this automatically by setting ownership before creating the venv.

## File Locations

| Item | Location |
|------|----------|
| Application Files | `/opt/pcornet/` |
| Virtual Environment | `/opt/pcornet/.venv/` |
| Environment Variables | `/opt/pcornet/.env` |
| Streamlit Config | `/opt/pcornet/.streamlit/config.toml` |
| Service File | `/etc/systemd/system/pcornet-chat.service` |
| Nginx Config | `/etc/nginx/sites-available/pcornet` |
| Application Logs | `/opt/pcornet/logs/` |
| Systemd Logs | `journalctl -u pcornet-chat` |

## Security Best Practices

### 1. Keep System Updated

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Secure the .env File

```bash
# Verify permissions (should be 600)
ls -la /opt/pcornet/.env

# Fix if needed
sudo chmod 600 /opt/pcornet/.env
sudo chown pcornet:pcornet /opt/pcornet/.env
```

### 3. Enable UFW Firewall

```bash
# Allow only necessary ports
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 4. Use HTTPS

Always use HTTPS in production (see HTTPS setup above).

### 5. Regular Backups

```bash
# Backup .env file
sudo cp /opt/pcornet/.env ~/pcornet-env-backup.txt

# Backup saved conversations
sudo tar -czf ~/pcornet-data-backup.tar.gz /opt/pcornet/saved/
```

## Uninstalling

### Remove Everything

```bash
cd /tmp/pcornet  # or wherever you have the scripts
sudo ./uninstall.sh
```

### Keep Data for Reinstall

```bash
sudo ./uninstall.sh --keep-data
```

This preserves files in `/opt/pcornet/` so you can reinstall later.

## Performance Tuning

### Increase File Upload Limits

Edit Nginx config:
```bash
sudo nano /etc/nginx/sites-available/pcornet
```

Add or modify:
```nginx
client_max_body_size 500M;  # Increase from 100M
```

Reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Adjust Service Limits

Edit service file:
```bash
sudo nano /etc/systemd/system/pcornet-chat.service
```

Add under `[Service]`:
```ini
LimitNOFILE=8192
LimitNPROC=512
```

Reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart pcornet-chat
```

## Multiple Environments

To run multiple instances (dev/staging/prod):

1. Modify `install.sh` to use different:
   - APP_DIR (e.g., `/opt/pcornet-dev`)
   - SERVICE_NAME (e.g., `pcornet-dev`)
   - APP_PORT (e.g., `8889`)
   - NGINX_SITE_NAME (e.g., `pcornet-dev`)

2. Run installer for each environment

3. Configure different domains/subdomains in Nginx

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u pcornet-chat -xe`
2. Review documentation: `docs/` directory
3. Verify Azure credentials in `.env` file
4. Check system resources: `htop` or `top`

---

**Installation complete!** Your PCORnet application is now running as a production service on Ubuntu 24.
