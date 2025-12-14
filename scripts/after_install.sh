#!/bin/bash
# After Install Hook for AWS CodeDeploy
# Sets up permissions and configurations

set -e

echo "==============================================="
echo "PeerAgent - After Install"
echo "==============================================="

APP_DIR="/opt/peeragent"
LOG_DIR="/var/log/peeragent"

cd ${APP_DIR}

# Set proper ownership
echo "Setting file ownership..."
chown -R peeragent:peeragent ${APP_DIR}
chown -R peeragent:peeragent ${LOG_DIR} 2>/dev/null || mkdir -p ${LOG_DIR} && chown peeragent:peeragent ${LOG_DIR}

# Make scripts executable
echo "Making scripts executable..."
chmod +x ${APP_DIR}/scripts/*.sh

# Create .env from example if not exists
if [ ! -f "${APP_DIR}/.env" ] && [ -f "${APP_DIR}/.env.example" ]; then
    echo "Creating .env from .env.example..."
    cp ${APP_DIR}/.env.example ${APP_DIR}/.env
    echo "⚠️ WARNING: Please configure ${APP_DIR}/.env with your API keys!"
fi

# Verify Docker is accessible
echo "Verifying Docker access..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not accessible. Please check Docker installation."
    exit 1
fi

# Pre-pull base images to speed up first start
echo "Pre-pulling base Docker images..."
docker pull python:3.11-slim &
docker pull redis:7-alpine &
docker pull mongo:7.0 &
wait

echo "After install completed successfully"
