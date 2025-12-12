#!/bin/bash
# Start Application Script for CodeDeploy

set -e

echo "=== Starting Application ==="

cd /opt/peeragent

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Pull latest images and start services
docker-compose pull
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Health check
if curl -f http://localhost:8000/health; then
    echo "Application started successfully!"
else
    echo "Health check failed!"
    docker-compose logs
    exit 1
fi

echo "Application start complete"
