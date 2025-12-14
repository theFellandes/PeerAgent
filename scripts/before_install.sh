#!/bin/bash
# Before Install Hook for AWS CodeDeploy
# Prepares the server for deployment

set -e

echo "==============================================="
echo "PeerAgent - Before Install"
echo "==============================================="

# Update system packages
echo "Updating system packages..."
apt-get update -y

# Install required dependencies
echo "Installing dependencies..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    docker.io \
    docker-compose-v2 \
    curl \
    git

# Start Docker service if not running
echo "Starting Docker service..."
systemctl start docker || true
systemctl enable docker || true

# Create application directory
APP_DIR="/opt/peeragent"
echo "Creating application directory: ${APP_DIR}"
mkdir -p ${APP_DIR}

# Clean up old deployment (keep logs)
echo "Cleaning up old deployment..."
rm -rf ${APP_DIR}/src
rm -rf ${APP_DIR}/tests
rm -rf ${APP_DIR}/ui
rm -f ${APP_DIR}/*.py
rm -f ${APP_DIR}/*.txt
rm -f ${APP_DIR}/*.toml
rm -f ${APP_DIR}/*.yml
rm -f ${APP_DIR}/*.yaml
rm -f ${APP_DIR}/Dockerfile*

# Create peeragent user if doesn't exist
if ! id "peeragent" &>/dev/null; then
    echo "Creating peeragent user..."
    useradd -r -s /bin/false peeragent
fi

# Add peeragent to docker group
usermod -aG docker peeragent || true

echo "Before install completed successfully"
