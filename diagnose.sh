#!/bin/bash
################################################################################
# PCORnet Diagnostics Script
# Run this on the server to diagnose Nginx and service issues
################################################################################

echo "=========================================="
echo "PCORnet Diagnostics"
echo "=========================================="
echo ""

echo "1. Checking Nginx sites-enabled:"
echo "------------------------------------------"
ls -la /etc/nginx/sites-enabled/
echo ""

echo "2. Checking which nginx config is active:"
echo "------------------------------------------"
sudo nginx -T 2>/dev/null | grep -A 5 "server_name"
echo ""

echo "3. Checking if pcornet service is running:"
echo "------------------------------------------"
sudo systemctl status pcornet-chat --no-pager -l
echo ""

echo "4. Checking if Streamlit is listening on port 8888:"
echo "------------------------------------------"
sudo netstat -tlnp | grep 8888
echo ""

echo "5. Testing connection to Streamlit:"
echo "------------------------------------------"
curl -I http://localhost:8888
echo ""

echo "6. Checking Nginx error logs:"
echo "------------------------------------------"
sudo tail -20 /var/log/nginx/error.log
echo ""

echo "7. Checking Nginx access logs:"
echo "------------------------------------------"
sudo tail -20 /var/log/nginx/access.log
echo ""

echo "8. Recent pcornet service logs:"
echo "------------------------------------------"
sudo journalctl -u pcornet-chat -n 30 --no-pager
echo ""

echo "=========================================="
echo "Quick Fix Commands (if needed):"
echo "=========================================="
echo ""
echo "# Remove default Nginx site:"
echo "sudo rm -f /etc/nginx/sites-enabled/default"
echo ""
echo "# Enable pcornet site:"
echo "sudo ln -sf /etc/nginx/sites-available/pcornet /etc/nginx/sites-enabled/pcornet"
echo ""
echo "# Test Nginx config:"
echo "sudo nginx -t"
echo ""
echo "# Reload Nginx:"
echo "sudo systemctl reload nginx"
echo ""
echo "# Restart pcornet service:"
echo "sudo systemctl restart pcornet-chat"
echo ""
