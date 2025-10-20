# PCORnet Ubuntu Deployment - Quick Start

## 🚀 One-Command Installation

```bash
# On your Ubuntu 24 server
cd /tmp
git clone <your-repo-url> pcornet  # or scp files
cd pcornet
sudo ./install.sh
```

## ⚙️ Post-Installation Setup

### 1. Configure Azure Credentials
```bash
sudo nano /opt/pcornet/.env
```

Update with your actual credentials, then:
```bash
sudo systemctl restart pcornet-chat
```

### 2. (Optional) Set Up HTTPS
```bash
# Update domain in Nginx
sudo nano /etc/nginx/sites-available/pcornet
# Change: server_name your-domain.com;

sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Service Management

```bash
# Quick commands
sudo ./manage.sh start      # Start service
sudo ./manage.sh stop       # Stop service
sudo ./manage.sh restart    # Restart service
sudo ./manage.sh status     # Check status
sudo ./manage.sh logs       # View logs
sudo ./manage.sh tail       # Follow logs
```

## 🌐 Access URLs

- **Local:** http://localhost:8888
- **Remote:** http://YOUR_SERVER_IP
- **Domain:** http://your-domain.com (after DNS setup)

## 🔄 Update Deployment

```bash
# Copy new files to server
scp -r modules/ ubuntu@server:/tmp/

# On server
sudo cp -r /tmp/modules/* /opt/pcornet/modules/
sudo chown -R pcornet:pcornet /opt/pcornet/modules/
sudo systemctl restart pcornet-chat
```

## 🧹 Uninstall

```bash
# Remove everything
sudo ./uninstall.sh

# Keep data for reinstall
sudo ./uninstall.sh --keep-data
```

## 📁 Important Locations

| Item | Path |
|------|------|
| App Files | `/opt/pcornet/` |
| Config | `/opt/pcornet/.env` |
| Logs | `/opt/pcornet/logs/` |
| Service | `/etc/systemd/system/pcornet-chat.service` |
| Nginx | `/etc/nginx/sites-available/pcornet` |

## 🔧 Troubleshooting

```bash
# Check service status
sudo systemctl status pcornet-chat

# View errors
sudo journalctl -u pcornet-chat -xe

# Check if running
sudo netstat -tlnp | grep 8888

# Verify environment
sudo cat /opt/pcornet/.env

# Test Nginx
sudo nginx -t
```

## 📚 Full Documentation

See [docs/UBUNTU_DEPLOYMENT.md](docs/UBUNTU_DEPLOYMENT.md) for complete guide.
