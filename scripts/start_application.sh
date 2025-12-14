#!/bin/bash
# Application Start Hook for AWS CodeDeploy
# Starts the PeerAgent application stack

set -e

echo "==============================================="
echo "PeerAgent - Starting Application"
echo "==============================================="

APP_DIR="/opt/peeragent"
LOG_DIR="/var/log/peeragent"

# Create log directory
mkdir -p ${LOG_DIR}
chown -R peeragent:peeragent ${LOG_DIR} || true

cd ${APP_DIR}

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables..."
    set -a
    source .env
    set +a
fi

# Check if required environment variables are set
if [ -z "${OPENAI_API_KEY}" ] && [ -z "${GOOGLE_API_KEY}" ] && [ -z "${ANTHROPIC_API_KEY}" ]; then
    echo "WARNING: No LLM API keys found. At least one of OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY should be set."
fi

# Stop any running containers
echo "Stopping existing containers..."
docker compose down || true

# Pull latest images
echo "Pulling Docker images..."
docker compose pull || true

# Build images if needed
echo "Building Docker images..."
docker compose build --no-cache

# Start the stack
echo "Starting Docker containers..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to become healthy..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    if docker compose ps | grep -q "healthy"; then
        echo "Services are healthy!"
        break
    fi
    
    echo "Waiting for services... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

# Verify API is responding
echo "Verifying API health..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "${API_HEALTH}" = "200" ]; then
    echo "✅ API is healthy!"
else
    echo "⚠️ API health check returned: ${API_HEALTH}"
fi

# Display running containers
echo ""
echo "Running containers:"
docker compose ps

# Display logs location
echo ""
echo "Application logs available at:"
echo "  - API logs: docker compose logs api"
echo "  - Worker logs: docker compose logs worker"
echo "  - All logs: docker compose logs -f"

echo ""
echo "==============================================="
echo "PeerAgent started successfully!"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - UI: http://localhost:8501"
echo "==============================================="
