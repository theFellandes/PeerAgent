#!/bin/bash
# Stop Application Script for CodeDeploy

set -e

echo "=== Stopping Application ==="

cd /opt/peeragent

# Gracefully stop services
if [ -f docker-compose.yml ]; then
    docker-compose down --timeout 30 || true
fi

echo "Application stopped"
