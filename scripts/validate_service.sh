#!/bin/bash
# Validate Service Hook for AWS CodeDeploy
# Verifies the application is running correctly after deployment

set -e

echo "==============================================="
echo "PeerAgent - Service Validation"
echo "==============================================="

APP_DIR="/opt/peeragent"
API_URL="http://localhost:8000"
UI_URL="http://localhost:8501"

cd ${APP_DIR}

# Check if all containers are running
echo "Checking container status..."
REQUIRED_SERVICES=("api" "worker" "mongo" "redis")
FAILED_SERVICES=()

for service in "${REQUIRED_SERVICES[@]}"; do
    if docker compose ps ${service} 2>/dev/null | grep -q "running\|Up"; then
        echo "✅ ${service}: Running"
    else
        echo "❌ ${service}: Not running"
        FAILED_SERVICES+=("${service}")
    fi
done

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo ""
    echo "Error: Some required services are not running: ${FAILED_SERVICES[*]}"
    echo "Container logs:"
    docker compose logs --tail=50
    exit 1
fi

# Check API health endpoint
echo ""
echo "Checking API health..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${API_URL}/health || echo "000")
    
    if [ "${HTTP_CODE}" = "200" ]; then
        echo "✅ API health check passed"
        break
    fi
    
    echo "Waiting for API... (${RETRY_COUNT}/${MAX_RETRIES}) - HTTP ${HTTP_CODE}"
    sleep 3
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ "${HTTP_CODE}" != "200" ]; then
    echo "❌ API health check failed with HTTP ${HTTP_CODE}"
    echo "API logs:"
    docker compose logs api --tail=50
    exit 1
fi

# Check detailed health
echo ""
echo "Checking detailed health status..."
HEALTH_RESPONSE=$(curl -s ${API_URL}/health)
echo "Health response: ${HEALTH_RESPONSE}"

# Verify Redis connectivity
REDIS_STATUS=$(echo ${HEALTH_RESPONSE} | grep -o '"redis":[^,}]*' | grep -o '"[^"]*"$' | tr -d '"' || echo "unknown")
if [ "${REDIS_STATUS}" = "connected" ]; then
    echo "✅ Redis: Connected"
else
    echo "⚠️ Redis: ${REDIS_STATUS}"
fi

# Verify MongoDB connectivity  
MONGO_STATUS=$(echo ${HEALTH_RESPONSE} | grep -o '"mongodb":[^,}]*' | grep -o '"[^"]*"$' | tr -d '"' || echo "unknown")
if [ "${MONGO_STATUS}" = "connected" ]; then
    echo "✅ MongoDB: Connected"
else
    echo "⚠️ MongoDB: ${MONGO_STATUS}"
fi

# Test a simple API endpoint
echo ""
echo "Testing classify endpoint..."
CLASSIFY_RESPONSE=$(curl -s "${API_URL}/v1/agent/classify?task=write%20python%20code")

if echo "${CLASSIFY_RESPONSE}" | grep -q "classification"; then
    echo "✅ Classify endpoint working"
else
    echo "⚠️ Classify endpoint returned unexpected response"
fi

# Check UI (optional)
echo ""
echo "Checking UI status..."
UI_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${UI_URL}/_stcore/health 2>/dev/null || echo "000")

if [ "${UI_CODE}" = "200" ]; then
    echo "✅ UI is accessible"
else
    echo "⚠️ UI health check returned: ${UI_CODE} (may still be starting)"
fi

# Summary
echo ""
echo "==============================================="
echo "Validation Summary"
echo "==============================================="
echo "API: ${API_URL} ✅"
echo "Docs: ${API_URL}/docs"
echo "UI: ${UI_URL}"
echo ""
echo "All critical services are running!"
echo "Deployment validated successfully."
echo "==============================================="

exit 0
