# Nginx Configuration Templates

This directory contains reference nginx configurations for the PCORnet application.

## Files

### `pcornet-http-only.conf`
The default configuration installed by `install.sh`. Uses HTTP only on port 80.

**Use case:** Development and initial setup

### `pcornet-https-example.conf`
Example showing what the configuration looks like after HTTPS setup with certbot.

**Use case:** Reference for troubleshooting or manual HTTPS configuration

## Setup Methods

### Method 1: Automated HTTPS Setup (Recommended)

Use the provided setup script:

```bash
sudo ./setup_https.sh your-domain.com your-email@example.com
```

This script will:
- Update your nginx configuration with your domain
- Install certbot if needed
- Obtain SSL certificate
- Configure automatic HTTP to HTTPS redirect
- Set up certificate auto-renewal

### Method 2: Manual HTTPS Setup

1. **Update domain in nginx config:**
   ```bash
   sudo nano /etc/nginx/sites-available/pcornet
   # Change: server_name _; to server_name your-domain.com;
   ```

2. **Install certbot:**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   ```

3. **Obtain certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

4. **Verify configuration:**
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

## Configuration Locations

| Item | Location |
|------|----------|
| Active config | `/etc/nginx/sites-available/pcornet` |
| Symlink | `/etc/nginx/sites-enabled/pcornet` |
| SSL certificates | `/etc/letsencrypt/live/your-domain.com/` |
| Nginx main config | `/etc/nginx/nginx.conf` |

## Troubleshooting

### Test nginx configuration
```bash
sudo nginx -t
```

### Reload nginx
```bash
sudo systemctl reload nginx
```

### Check nginx status
```bash
sudo systemctl status nginx
```

### View nginx error logs
```bash
sudo tail -f /var/log/nginx/error.log
```

### Verify SSL certificate
```bash
sudo certbot certificates
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Keep certificates up to date** (certbot handles this automatically)
3. **Test renewal:** `sudo certbot renew --dry-run`
4. **Monitor certificate expiration:** Certificates expire in 90 days
5. **Enable firewall:** `sudo ufw allow 'Nginx Full'`

## Custom Configuration

If you need custom nginx settings:

1. **Edit the config:**
   ```bash
   sudo nano /etc/nginx/sites-available/pcornet
   ```

2. **Test changes:**
   ```bash
   sudo nginx -t
   ```

3. **Apply changes:**
   ```bash
   sudo systemctl reload nginx
   ```

## Common Customizations

### Increase upload size limit
```nginx
client_max_body_size 500M;  # Increase from 100M
```

### Add custom headers
```nginx
add_header X-Custom-Header "value" always;
```

### Enable gzip compression
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### Rate limiting
```nginx
limit_req_zone $binary_remote_addr zone=pcornet:10m rate=10r/s;
limit_req zone=pcornet burst=20;
```
