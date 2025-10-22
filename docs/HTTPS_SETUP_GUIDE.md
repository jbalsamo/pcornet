# HTTPS Setup Guide for PCORnet

Complete guide for securing your PCORnet installation with HTTPS/SSL certificates.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Setup (Automated)](#quick-setup-automated)
- [Manual Setup](#manual-setup)
- [Nginx Configuration](#nginx-configuration)
- [Certificate Management](#certificate-management)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before setting up HTTPS, ensure you have:

### 1. Domain Name
- A registered domain name (e.g., `pcornet.yourdomain.com`)
- DNS A record pointing to your server's public IP address

### 2. Server Requirements
- PCORnet already installed (run `./install.sh` first)
- Ports 80 and 443 open in firewall
- Nginx installed and running

### 3. Verify DNS Resolution
```bash
# Check if your domain resolves to your server
dig your-domain.com +short
# Should show your server's IP address

# Or use host command
host your-domain.com
```

## Quick Setup (Automated)

The easiest way to enable HTTPS is using the provided setup script:

### Step 1: Run the HTTPS Setup Script

```bash
sudo ./setup_https.sh your-domain.com your-email@example.com
```

**Example:**
```bash
sudo ./setup_https.sh pcornet.mydomain.com admin@mydomain.com
```

### What the Script Does

1. ✅ Validates prerequisites (nginx, DNS, firewall)
2. ✅ Updates nginx configuration with your domain
3. ✅ Installs certbot if not present
4. ✅ Obtains SSL certificate from Let's Encrypt
5. ✅ Configures automatic HTTP to HTTPS redirect
6. ✅ Sets up automatic certificate renewal (runs twice daily)
7. ✅ Tests the configuration

### Step 2: Verify HTTPS is Working

```bash
# Test HTTPS access
curl -I https://your-domain.com

# Should return: HTTP/2 200 OK
```

Access your application:
```
https://your-domain.com
```

**That's it!** Your application is now secured with HTTPS.

---

## Manual Setup

If you prefer manual configuration or need more control:

### Step 1: Update Nginx Domain

Edit the nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/pcornet
```

Change the `server_name` directive:
```nginx
# Before:
server_name _;

# After:
server_name your-domain.com;  # Replace with your actual domain
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

### Step 2: Test and Reload Nginx

```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 3: Install Certbot

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

### Step 4: Obtain SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will:
- Verify domain ownership
- Obtain SSL certificate
- Automatically modify nginx config
- Set up HTTP to HTTPS redirect
- Configure auto-renewal

**Follow the prompts:**
1. Enter your email address
2. Agree to terms of service
3. Choose whether to redirect HTTP to HTTPS (select Yes/2)

### Step 5: Verify Certificate

```bash
# Check certificate status
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Nginx Configuration

### HTTP-Only Configuration (Default)

After initial install, nginx is configured for HTTP only:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name _;  # Accepts all domains
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        # ... proxy headers ...
    }
}
```

**Reference:** See `nginx-templates/pcornet-http-only.conf`

### HTTPS Configuration (After Certbot)

After running certbot, nginx is automatically updated:

```nginx
# HTTP Server - Redirects to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server - Main application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;
    
    # SSL Certificate (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://127.0.0.1:8888;
        # ... proxy headers ...
    }
}
```

**Reference:** See `nginx-templates/pcornet-https-example.conf`

### Custom Configuration

#### Add Additional Security Headers

Edit `/etc/nginx/sites-available/pcornet`:

```nginx
# Inside the HTTPS server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

#### Increase Upload Size

```nginx
client_max_body_size 500M;  # Increase from 100M default
```

After making changes:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Certificate Management

### Auto-Renewal

Certificates expire in 90 days but renew automatically via systemd timer.

#### Check Renewal Timer Status
```bash
sudo systemctl status certbot.timer
sudo systemctl list-timers certbot
```

#### Manual Renewal (if needed)
```bash
sudo certbot renew
```

#### Test Renewal Process
```bash
sudo certbot renew --dry-run
```

### Certificate Information

#### View All Certificates
```bash
sudo certbot certificates
```

**Output includes:**
- Certificate name
- Domains covered
- Expiry date
- Certificate path
- Key path

#### View Certificate Details
```bash
sudo openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout
```

### Renewal Notifications

Let's Encrypt sends email notifications:
- 30 days before expiration
- 7 days before expiration
- When renewal fails

Make sure you provided a valid email during setup.

---

## Troubleshooting

### Issue: DNS Not Resolving

**Symptom:** Certbot fails with "DNS resolution failed"

**Solution:**
```bash
# Check DNS
host your-domain.com

# If not resolving:
# 1. Verify A record in DNS provider
# 2. Wait for DNS propagation (can take up to 48 hours)
# 3. Use DNS checker: https://dnschecker.org
```

### Issue: Port 80 or 443 Blocked

**Symptom:** Certbot can't verify domain ownership

**Solution:**
```bash
# Check firewall
sudo ufw status

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 'Nginx Full'

# Check if ports are listening
sudo netstat -tlnp | grep -E ':80|:443'
```

### Issue: Certificate Already Exists

**Symptom:** "Certificate already exists" error

**Solution:**
```bash
# Renew existing certificate
sudo certbot renew --force-renewal

# Or delete and recreate
sudo certbot delete --cert-name your-domain.com
sudo certbot --nginx -d your-domain.com
```

### Issue: Nginx Configuration Error

**Symptom:** `nginx -t` fails after certbot

**Solution:**
```bash
# Restore backup
sudo cp /etc/nginx/sites-available/pcornet.backup.* /etc/nginx/sites-available/pcornet

# Test configuration
sudo nginx -t

# If it works, reload
sudo systemctl reload nginx

# Try HTTPS setup again
```

### Issue: Mixed Content Warnings

**Symptom:** Browser shows "Not Secure" or mixed content warnings

**Solution:**
1. Ensure all resources load via HTTPS
2. Update `proxy_set_header X-Forwarded-Proto $scheme;` in nginx
3. Add HSTS header (already in HTTPS config)

### Issue: Certificate Expired

**Symptom:** Browser shows "Certificate Expired"

**Solution:**
```bash
# Check certificate expiry
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Reload nginx
sudo systemctl reload nginx

# Check auto-renewal is working
sudo systemctl status certbot.timer
```

### Check Service Logs

```bash
# Nginx error log
sudo tail -f /var/log/nginx/error.log

# Nginx access log
sudo tail -f /var/log/nginx/access.log

# Certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# PCORnet service
sudo journalctl -u pcornet-chat -f
```

---

## Security Best Practices

### 1. Always Use HTTPS in Production
Never deploy production applications without HTTPS.

### 2. Keep Certificates Updated
While automatic, monitor renewal:
```bash
sudo certbot certificates
```

### 3. Use Strong SSL Configuration
Certbot configures strong SSL by default. Verify:
```bash
# Test SSL strength
https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### 4. Enable HSTS
Already configured in HTTPS setup:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### 5. Regular Security Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update certbot
sudo apt install --only-upgrade certbot python3-certbot-nginx
```

### 6. Monitor Certificate Expiration
Set up monitoring or use email notifications from Let's Encrypt.

---

## Quick Reference

### Files and Locations

| Item | Location |
|------|----------|
| HTTPS setup script | `./setup_https.sh` |
| Nginx config | `/etc/nginx/sites-available/pcornet` |
| SSL certificate | `/etc/letsencrypt/live/your-domain.com/fullchain.pem` |
| SSL private key | `/etc/letsencrypt/live/your-domain.com/privkey.pem` |
| Certbot config | `/etc/letsencrypt/renewal/your-domain.com.conf` |
| Nginx templates | `nginx-templates/` directory |

### Common Commands

```bash
# Setup HTTPS (automated)
sudo ./setup_https.sh your-domain.com your-email@example.com

# Manual certificate request
sudo certbot --nginx -d your-domain.com

# View certificates
sudo certbot certificates

# Renew manually
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check renewal timer
sudo systemctl status certbot.timer
```

---

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [SSL Labs Testing](https://www.ssllabs.com/ssltest/)

---

**Need help?** Check the troubleshooting section or review nginx logs for errors.
