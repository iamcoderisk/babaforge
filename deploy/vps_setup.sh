#!/bin/bash
# VPS Setup Script for 156.67.29.186
# Run as: sudo bash vps_setup.sh

set -e

echo "=========================================="
echo "Custom SMTP Relay Setup for sendbaba.com"
echo "VPS IP: 156.67.29.186"
echo "=========================================="

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    redis-server \
    postgresql \
    nginx \
    supervisor \
    ufw \
    fail2ban \
    dnsutils

# Configure firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 25/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 587/tcp
ufw --force enable

# Start services
systemctl enable redis-server postgresql nginx
systemctl start redis-server postgresql nginx

echo "✅ VPS setup complete!"
echo ""
echo "Next steps:"
echo "1. Upload application: rsync -avz . root@156.67.29.186:/opt/sendbaba-smtp/"
echo "2. Install Python packages: pip install -r requirements.txt"
echo "3. Configure DNS records"
echo "4. Start services"
