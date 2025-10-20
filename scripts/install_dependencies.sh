#!/bin/bash
set -e

echo "📦 Installing dependencies for macOS..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies
echo "Installing system packages..."
brew install postgresql@15 redis rabbitmq python@3.11 libpq

# Start services
echo "Starting services..."
brew services start postgresql@15
brew services start redis
brew services start rabbitmq

# Wait for services
sleep 5

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip

cat > requirements.txt << 'EOF'
# Web Framework
Flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0

# Database
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# Async
asyncio==3.4.3
aiosmtplib==3.0.1
aio-pika==9.3.1

# Redis
redis[hiredis]==5.0.1

# Email
dkim==1.1.5
dnspython==2.4.2
email-validator==2.1.0

# Authentication
PyJWT==2.8.0
cryptography==41.0.7

# Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Monitoring
prometheus-client==0.19.0
sentry-sdk[flask]==1.38.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1

# Development
black==23.12.0
flake8==6.1.0
mypy==1.7.1
EOF

pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"