#!/bin/bash
set -e

echo "🚀 Deploying to production..."

# Build Docker image
echo "Building Docker image..."
docker build -t sendbaba-smtp:latest .

# Push to registry (configure your registry)
# docker push your-registry.com/sendbaba-smtp:latest

# Deploy with docker-compose
echo "Starting production stack..."
docker-compose -f deployment/docker/docker-compose.prod.yml up -d

echo "✅ Deployed successfully!"
