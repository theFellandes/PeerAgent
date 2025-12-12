#!/bin/bash
# Before Install Script for CodeDeploy

set -e

echo "=== Before Install ==="

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Clean up old deployment
if [ -d "/opt/peeragent" ]; then
    echo "Cleaning up old deployment..."
    cd /opt/peeragent
    docker-compose down --remove-orphans || true
fi

echo "Before install complete"
