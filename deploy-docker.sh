#!/bin/bash
# SendBaba Docker Deployment Script
# Run this on your Contabo VPS: 156.67.29.186

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║    ███████╗███████╗███╗   ██╗██████╗ ██████╗  █████╗     ║
║    ██╔════╝██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔══██╗    ║
║    ███████╗█████╗  ██╔██╗ ██║██║  ██║██████╔╝███████║    ║
║    ╚════██║██╔══╝  ██║╚██╗██║██║  ██║██╔══██╗██╔══██║    ║
║    ███████║███████╗██║ ╚████║██████╔╝██████╔╝██║  ██║    ║
║    ╚══════╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝    ║
║                                                           ║
║         Docker Production Deployment v1.0                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Configuration
PROJECT_DIR="/opt/sendbaba-smtp"
DOMAIN="sendbaba.com"
VPS_IP="156.67.29.186"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}" 
   exit 1
fi

echo -e "${GREEN}Starting SendBaba Docker deployment...${NC}\n"

# Function to print section headers
print_section() {
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}► $1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# 1. Update System
print_section "Step 1/10: Updating System"
apt update && apt upgrade -y
echo -e "${GREEN}✓ System updated${NC}"

# 2. Install Docker
print_section "Step 2/10: Installing Docker"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker installed${NC}"
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi

# 3. Install Docker Compose
print_section "Step 3/10: Installing Docker Compose"
if ! docker compose version &> /dev/null; then
    apt install docker-compose-plugin -y
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi

# Verify installations
docker --version
docker compose version

# 4. Prepare Project Directory
print_section "Step 4/10: Preparing Project Directory"
cd $PROJECT_DIR

# Create necessary directories
mkdir -p logs keys ssl data/{postgres,redis} prometheus grafana/dashboards
chmod -R 755 logs keys ssl data

echo -e "${GREEN}✓ Directories created${NC}"

# 5. Update Environment Variables
print_section "Step 5/10: Updating Environment Variables"

# Update .env to use Docker service names
cat > .env << 'EOF'
# Production Environment
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=60b55ca25a3391f98774c37d68c65b88

# Database (Docker service names)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=emailer
POSTGRES_PASSWORD=SecurePassword123!
POSTGRES_DB=email_system
POSTGRES_MAX_CONNECTIONS=500

# Redis (Docker service name)
REDIS_HOST=redis
REDIS_PORT=6379

# Email Configuration
DOMAIN=sendbaba.com
SERVER_IP=156.67.29.186

# SMTP
SMTP_MAX_RETRIES=3
SMTP_TIMEOUT=60

# Workers
WORKER_CONCURRENCY=100
MIN_WORKERS=10
MAX_WORKERS=500

# Monitoring
GRAFANA_PASSWORD=sendbaba_grafana_pass_123

# For docker-compose.prod.yml
DB_PASSWORD=SecurePassword123!
RABBITMQ_PASSWORD=SecureRabbitMQPass123!
EOF

echo -e "${GREEN}✓ Environment variables configured${NC}"

# 6. Generate DKIM Keys
print_section "Step 6/10: Checking DKIM Keys"

if [ ! -f "data/dkim/sendbaba.com_private.key" ]; then
    echo "Generating DKIM keys..."
    
    # Install openssl if not present
    apt install openssl -y
    
    # Generate DKIM keys using openssl
    openssl genrsa -out data/dkim/sendbaba.com_private.key 2048
    openssl rsa -in data/dkim/sendbaba.com_private.key -pubout -out data/dkim/sendbaba.com_public.key
    
    chmod 600 data/dkim/*.key
    
    echo -e "${GREEN}✓ DKIM keys generated${NC}"
    
    # Show public key for DNS
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}IMPORTANT: Add this to your DNS records${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo "Type: TXT"
    echo "Name: default._domainkey"
    echo "Value: v=DKIM1; k=rsa; p=$(grep -v 'BEGIN\|END' data/dkim/sendbaba.com_public.key | tr -d '\n')"
    echo -e "${YELLOW}========================================${NC}\n"
else
    echo -e "${YELLOW}DKIM keys already exist${NC}"
fi

# 7. Create Dockerfile if not exists
print_section "Step 7/10: Preparing Docker Image"

if [ ! -f "Dockerfile" ]; then
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs keys data/dkim

# Expose ports
EXPOSE 5000 8000

# Default command
CMD ["python", "run.py"]
EOF
    echo -e "${GREEN}✓ Dockerfile created${NC}"
else
    echo -e "${YELLOW}Dockerfile already exists${NC}"
fi

# Create requirements.txt if not exists
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
Flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
asyncio==3.4.3
aiosmtplib==3.0.1
redis[hiredis]==5.0.1
dnspython==2.4.2
email-validator==2.1.0
cryptography==41.0.7
PyJWT==2.8.0
pydantic==2.5.0
prometheus-client==0.19.0
python-dotenv==1.0.0
requests==2.31.0
EOF
    echo -e "${GREEN}✓ requirements.txt created${NC}"
fi

# 8. Create/Update Nginx Configuration
print_section "Step 8/10: Configuring Nginx"

cat > nginx.conf << 'EOF'
events {
    worker_connections 4096;
}

http {
    upstream api_backend {
        least_conn;
        server api:8000;
    }

    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=send_limit:10m rate=5r/s;

    server {
        listen 80;
        server_name sendbaba.com www.sendbaba.com;

        client_max_body_size 10M;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        location /api/v1/send {
            limit_req zone=send_limit burst=10 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }

        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
EOF

echo -e "${GREEN}✓ Nginx configured${NC}"

# 9. Build Docker Image
print_section "Step 9/10: Building Docker Image"

docker build -t sendbaba-smtp:latest .

echo -e "${GREEN}✓ Docker image built${NC}"

# 10. Configure Firewall
print_section "Step 10/10: Configuring Firewall"

if ! command -v ufw &> /dev/null; then
    apt install ufw -y
fi

ufw --force reset
ufw default deny incoming
ufw default allow outgoing

ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 25/tcp    # SMTP
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus

ufw --force enable

echo -e "${GREEN}✓ Firewall configured${NC}"

# Start Services
print_section "Starting Docker Services"

# Stop any existing containers
docker compose -f deployment/docker/docker-compose.yml down 2>/dev/null || true

# Start services
echo "Starting production stack with monitoring..."
docker compose -f deployment/docker/docker-compose.yml up -d

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 10

# Check status
echo -e "\n${GREEN}Checking service status...${NC}"
docker compose -f deployment/docker/docker-compose.yml ps

# Final Status
print_section "Deployment Complete!"

echo -e "${GREEN}Service Status:${NC}"
docker compose -f deployment/docker/docker-compose.yml ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}          🎉 DEPLOYMENT SUCCESSFUL! 🎉${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Important Information:${NC}"
echo -e "  Domain: http://$DOMAIN"
echo -e "  VPS IP: $VPS_IP"
echo -e "  Project: $PROJECT_DIR"
echo ""
echo -e "${YELLOW}Access Points:${NC}"
echo -e "  API:        http://$DOMAIN/api/v1/"
echo -e "  Health:     http://$DOMAIN/health"
echo -e "  Grafana:    http://$VPS_IP:3000 (admin / sendbaba_grafana_pass_123)"
echo -e "  Prometheus: http://$VPS_IP:9090"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. ⚠️  Configure DNS records (see below)"
echo -e "  2. ⚠️  Request PTR record from Contabo"
echo -e "  3. Wait 30-120 min for DNS propagation"
echo -e "  4. Test: curl http://$DOMAIN/health"
echo -e "  5. Install SSL: see deployment guide"
echo ""
echo -e "${YELLOW}DNS Records to Add:${NC}"
echo -e "  A Record:    @ → $VPS_IP"
echo -e "  A Record:    www → $VPS_IP"
echo -e "  A Record:    mail → $VPS_IP"
echo -e "  MX Record:   @ → mail.$DOMAIN (Priority: 10)"
echo -e "  TXT (SPF):   @ → v=spf1 ip4:$VPS_IP ~all"
echo -e "  TXT (DKIM):  default._domainkey → (see above output)"
echo -e "  TXT (DMARC): _dmarc → v=DMARC1; p=none; rua=mailto:dmarc@$DOMAIN"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  View logs:     docker compose -f deployment/docker/docker-compose.yml logs -f"
echo -e "  Restart:       docker compose -f deployment/docker/docker-compose.yml restart"
echo -e "  Stop all:      docker compose -f deployment/docker/docker-compose.yml down"
echo -e "  Scale workers: docker compose -f deployment/docker/docker-compose.yml up -d --scale worker=100"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Create helper script
cat > /usr/local/bin/sendbaba << 'EOF'
#!/bin/bash
cd /opt/sendbaba-smtp

case "$1" in
    status)
        docker compose -f deployment/docker/docker-compose.yml ps
        ;;
    logs)
        docker compose -f deployment/docker/docker-compose.yml logs -f ${2:-}
        ;;
    restart)
        docker compose -f deployment/docker/docker-compose.yml restart ${2:-}
        ;;
    stop)
        docker compose -f deployment/docker/docker-compose.yml down
        ;;
    start)
        docker compose -f deployment/docker/docker-compose.yml up -d
        ;;
    scale)
        docker compose -f deployment/docker/docker-compose.yml up -d --scale worker=${2:-50}
        ;;
    update)
        docker compose -f deployment/docker/docker-compose.yml up -d --build
        ;;
    *)
        echo "SendBaba Management Tool"
        echo ""
        echo "Usage: sendbaba [command]"
        echo ""
        echo "Commands:"
        echo "  status          Show service status"
        echo "  logs [service]  View logs (optional: specific service)"
        echo "  restart [svc]   Restart services (optional: specific service)"
        echo "  stop            Stop all services"
        echo "  start           Start all services"
        echo "  scale <number>  Scale workers to <number>"
        echo "  update          Update and rebuild"
        ;;
esac
EOF

chmod +x /usr/local/bin/sendbaba

echo -e "${GREEN}✓ Helper script created: 'sendbaba' command${NC}"
echo ""
echo -e "${YELLOW}Quick commands:${NC}"
echo -e "  sendbaba status   - Check status"
echo -e "  sendbaba logs     - View logs"
echo -e "  sendbaba restart  - Restart all"
echo ""