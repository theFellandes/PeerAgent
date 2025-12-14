#!/bin/bash
# Application Stop Hook for AWS CodeDeploy
# Gracefully stops the PeerAgent application stack

set -e

echo "==============================================="
echo "PeerAgent - Stopping Application"
echo "==============================================="

APP_DIR="/opt/peeragent"

cd ${APP_DIR} 2>/dev/null || {
    echo "Application directory not found. Nothing to stop."
    exit 0
}

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "No docker-compose.yml found. Trying docker compose directly..."
fi

# Gracefully stop Celery workers first (allow task completion)
echo "Stopping Celery workers gracefully..."
docker compose exec -T worker celery -A src.worker.celery_app control shutdown 2>/dev/null || true

# Wait for workers to finish current tasks (max 30 seconds)
echo "Waiting for workers to finish current tasks..."
WORKER_TIMEOUT=30
WORKER_COUNT=0

while [ ${WORKER_COUNT} -lt ${WORKER_TIMEOUT} ]; do
    RUNNING_WORKERS=$(docker compose exec -T worker celery -A src.worker.celery_app inspect active 2>/dev/null | grep -c "celery@" || echo "0")
    
    if [ "${RUNNING_WORKERS}" = "0" ]; then
        echo "All workers have stopped."
        break
    fi
    
    echo "Waiting for workers... (${WORKER_COUNT}/${WORKER_TIMEOUT})"
    sleep 1
    WORKER_COUNT=$((WORKER_COUNT + 1))
done

# Stop all containers
echo "Stopping Docker containers..."
docker compose down --remove-orphans

# Optionally remove volumes (uncomment if needed)
# docker compose down -v

# Verify all containers are stopped
echo "Verifying containers are stopped..."
if docker compose ps -q | grep -q .; then
    echo "Warning: Some containers may still be running"
    docker compose ps
else
    echo "All containers stopped successfully"
fi

# Clean up dangling images (optional, keep for faster restarts)
# echo "Cleaning up unused images..."
# docker image prune -f

echo ""
echo "==============================================="
echo "PeerAgent stopped successfully!"
echo "==============================================="
