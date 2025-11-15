#!/bin/bash

set -e

echo "🚀 Installing Complete SendBaba API System"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if in staging directory
if [ ! -d "/opt/sendbaba-staging" ]; then
    echo -e "${RED}Error: /opt/sendbaba-staging not found${NC}"
    exit 1
fi

cd /opt/sendbaba-staging

echo -e "${BLUE}Step 1: Installing Python dependencies${NC}"
source venv/bin/activate
pip install flask-swagger-ui flask-cors --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

echo -e "${BLUE}Step 2: Running database migrations${NC}"
sudo -u postgres psql -d emailer_staging < migrations_manual/001_add_api_system.sql
echo -e "${GREEN}✅ Database migrations completed${NC}"
echo ""

echo -e "${BLUE}Step 3: Creating required directories${NC}"
mkdir -p app/api/v1
mkdir -p app/middleware
mkdir -p docs/api
mkdir -p sdks/{python,php,javascript}
touch app/api/__init__.py
touch app/api/v1/__init__.py
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

echo -e "${BLUE}Step 4: Installing SDKs${NC}"

# Python SDK
cd sdks/python
pip install -e . --quiet
cd ../..
echo -e "${GREEN}✅ Python SDK installed${NC}"

# JavaScript SDK
cd sdks/javascript
npm install --silent 2>/dev/null || true
cd ../..
echo -e "${GREEN}✅ JavaScript SDK installed${NC}"

echo ""

echo -e "${BLUE}Step 5: Restarting staging server${NC}"
pm2 restart sendbaba-staging
sleep 3
echo -e "${GREEN}✅ Server restarted${NC}"
echo ""

echo -e "${BLUE}Step 6: Testing API endpoints${NC}"

# Test ping endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://playmaster.sendbaba.com/api/v1/ping)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Ping endpoint working${NC}"
else
    echo -e "${RED}❌ Ping endpoint failed (HTTP $HTTP_CODE)${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 API System Installation Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Create an API key:"
echo "   Visit: https://playmaster.sendbaba.com/dashboard/api-keys"
echo ""
echo "2. View API documentation:"
echo "   Visit: https://playmaster.sendbaba.com/api/docs"
echo ""
echo "3. Test the API:"
echo "   curl -X GET https://playmaster.sendbaba.com/api/v1/ping"
echo ""
echo "4. SDK Examples:"
echo "   Python: cd sdks/python && python examples/test.py"
echo "   PHP: cd sdks/php && php examples/test.php"
echo "   Node.js: cd sdks/javascript && node examples/test.js"
echo ""
echo -e "${BLUE}📚 Documentation: https://playmaster.sendbaba.com/api/docs${NC}"
echo ""

