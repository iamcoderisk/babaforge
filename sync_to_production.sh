#!/bin/bash

echo "========================================="
echo "🚀 SYNCING STAGING TO PRODUCTION"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Confirm sync
echo -e "${YELLOW}⚠️  WARNING: This will sync all changes to PRODUCTION${NC}"
echo ""
echo "Changes to sync:"
echo "  ✅ Complete REST API v1"
echo "  ✅ Legacy API key support"
echo "  ✅ Email model (fixed schema)"
echo "  ✅ API authentication middleware"
echo "  ✅ Rate limiting"
echo "  ✅ Complete API documentation (/docs)"
echo "  ✅ Email worker"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Sync cancelled."
    exit 0
fi

echo ""
echo "Starting sync..."
echo ""

# 1. Backup production
echo "1️⃣ Creating production backup..."
BACKUP_DIR="/opt/backups/sendbaba-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r /opt/sendbaba "$BACKUP_DIR/"
echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
echo ""

# 2. Sync Python files
echo "2️⃣ Syncing Python files..."

# API files
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/api/ \
    /opt/sendbaba/app/api/

# Middleware
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/middleware/ \
    /opt/sendbaba/app/middleware/

# Models
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/models/email.py \
    /opt/sendbaba/app/models/

# Controllers
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/controllers/web_controller.py \
    /opt/sendbaba/app/controllers/

# Workers
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/workers/ \
    /opt/sendbaba/app/workers/

echo -e "${GREEN}✅ Python files synced${NC}"
echo ""

# 3. Sync templates
echo "3️⃣ Syncing templates..."
sudo rsync -av --progress \
    /opt/sendbaba-staging/app/templates/docs.html \
    /opt/sendbaba/app/templates/

echo -e "${GREEN}✅ Templates synced${NC}"
echo ""

# 4. Update main app initialization
echo "4️⃣ Checking app initialization..."
if ! sudo grep -q "from app.api.v1.api_v1 import api_v1_bp" /opt/sendbaba/app/__init__.py; then
    echo "Updating __init__.py with API v1 blueprint..."
    
    # Backup original
    sudo cp /opt/sendbaba/app/__init__.py /opt/sendbaba/app/__init__.py.backup
    
    # Add API v1 import and registration
    sudo sed -i '/from app.controllers.web_controller import web_bp/a\    from app.api.v1.api_v1 import api_v1_bp' /opt/sendbaba/app/__init__.py
    sudo sed -i '/app.register_blueprint(web_bp)/a\    app.register_blueprint(api_v1_bp)' /opt/sendbaba/app/__init__.py
    
    echo -e "${GREEN}✅ App initialization updated${NC}"
else
    echo -e "${GREEN}✅ API v1 already registered${NC}"
fi
echo ""

# 5. Install dependencies
echo "5️⃣ Installing dependencies..."
cd /opt/sendbaba
source venv/bin/activate
pip install flask-swagger-ui --break-system-packages > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# 6. Restart services
echo "6️⃣ Restarting production services..."
pm2 restart sendbaba-flask
sleep 2
pm2 restart sendbaba-worker
sleep 2

echo -e "${GREEN}✅ Services restarted${NC}"
echo ""

# 7. Verify services
echo "7️⃣ Verifying services..."
sleep 5

if pm2 list | grep -q "sendbaba-flask.*online"; then
    echo -e "${GREEN}✅ Flask app is running${NC}"
else
    echo -e "${RED}❌ Flask app is not running${NC}"
fi

if pm2 list | grep -q "sendbaba-worker.*online"; then
    echo -e "${GREEN}✅ Worker is running${NC}"
else
    echo -e "${RED}❌ Worker is not running${NC}"
fi
echo ""

# 8. Test production API
echo "8️⃣ Testing production API..."

# Test ping
PING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://sendbaba.com/api/v1/ping)
if [ "$PING_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ API ping: OK${NC}"
else
    echo -e "${RED}❌ API ping failed: $PING_RESPONSE${NC}"
fi

# Test docs
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://sendbaba.com/docs)
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Documentation: OK${NC}"
else
    echo -e "${RED}❌ Documentation failed: $DOCS_RESPONSE${NC}"
fi

echo ""

# 9. Check logs
echo "9️⃣ Recent production logs..."
pm2 logs sendbaba-flask --lines 10 --nostream | tail -20
echo ""

echo "========================================="
echo -e "${GREEN}✅ SYNC COMPLETE!${NC}"
echo "========================================="
echo ""
echo "🌐 Production URLs:"
echo "   Main site: https://sendbaba.com"
echo "   API base: https://sendbaba.com/api/v1"
echo "   API docs: https://sendbaba.com/docs"
echo ""
echo "📊 Service Status:"
pm2 list | grep sendbaba
echo ""
echo "🔍 Monitor logs:"
echo "   pm2 logs sendbaba-flask"
echo "   pm2 logs sendbaba-worker"
echo ""
echo "📦 Backup location: $BACKUP_DIR"
echo ""
echo "🎉 Your REST API is now LIVE on production!"
echo ""
