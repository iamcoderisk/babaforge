#!/bin/bash
set -e

echo "🗄️  Initializing database..."

# Database configuration
DB_NAME="smtp_enterprise"
DB_USER="smtp_admin"
DB_PASSWORD="change_me_in_production"

# Check if PostgreSQL is running
if ! pg_isready &> /dev/null; then
    echo "❌ PostgreSQL is not running. Start it with: brew services start postgresql@15"
    exit 1
fi

# Create database user
echo "Creating database user..."
psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || true

# Create database
echo "Creating database..."
psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Create extensions
psql $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
psql $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

echo "✅ Database initialized successfully!"

# Initialize tables (will be created by Flask app)
echo "Tables will be created on first run of the application"


# ============= scripts/start_local.sh =============
#!/bin/bash
set -e

echo "🚀 Starting Enterprise SMTP Server locally..."

# Activate virtual environment
source venv/bin/activate

# Export environment variables
export FLASK_APP=app.main:create_app
export FLASK_ENV=development
export PYTHONPATH=$(pwd)

# Create necessary directories
mkdir -p logs keys ssl data/{postgres,redis}

# Generate DKIM keys if not exist
if [ ! -f "keys/dkim_private.pem" ]; then
    echo "Generating DKIM keys..."
    python -c "from app.services.dkim_service import DKIMService; DKIMService().generate_keys()"
fi

# Generate self-signed SSL cert if not exist
if [ ! -f "ssl/cert.pem" ]; then
    echo "Generating SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout ssl/key.pem -out ssl/cert.pem -days 365 \
        -subj "/CN=localhost"
fi

# Create .env file if not exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Environment
ENVIRONMENT=development
DEBUG=True

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smtp_enterprise
DB_USER=smtp_admin
DB_PASSWORD=change_me_in_production

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Domain
PRIMARY_DOMAIN=localhost
HOSTNAME=localhost

# Security
SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

# Start email worker in background
echo "Starting email worker..."
python app/workers/email_worker.py &
WORKER_PID=$!

# Start Flask API
echo "Starting Flask API..."
gunicorn -w 4 -b 0.0.0.0:5000 \
    --timeout 300 \
    --worker-class sync \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    "app.main:create_app()" &
API_PID=$!

echo ""
echo "✅ Server started successfully!"
echo ""
echo "📊 Services:"
echo "   API:        http://localhost:5000"
echo "   PostgreSQL: localhost:5432"
echo "   Redis:      localhost:6379"
echo "   RabbitMQ:   localhost:5672"
echo ""
echo "📝 Logs:"
echo "   Application: tail -f logs/smtp_server.log"
echo "   Access:      tail -f logs/access.log"
echo "   Error:       tail -f logs/error.log"
echo ""
echo "🔑 API Test:"
echo "   First create an organization to get API key:"
echo "   curl -X POST http://localhost:5000/api/v1/organizations/ \\"
echo "        -H 'X-Admin-Key: YOUR_SECRET_KEY' \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"name\": \"My Org\", \"max_emails_per_hour\": 1000000}'"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for interrupt
trap "kill $WORKER_PID $API_PID 2>/dev/null; echo 'Stopped.'; exit" SIGINT SIGTERM
wait
