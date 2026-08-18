#!/bin/sh
# ==============================================================================
# AuraXL Backend Health Monitor Script
# Usage: BACKEND_URL="https://auraxl-monitor.onrender.com" ./monitor-health.sh
# ==============================================================================

set -u

# Ensure BACKEND_URL is set
if [ -z "${BACKEND_URL:-}" ]; then
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] ERROR: BACKEND_URL environment variable is not set." >&2
    echo "Usage: BACKEND_URL=\"https://your-backend-url.com\" $0" >&2
    exit 1
fi

TARGET_BASE="${BACKEND_URL%/}"
HEALTH_URL="${TARGET_BASE}/health"

CONNECT_TIMEOUT=5
MAX_TIME=10
TIMESTAMP="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"

# Execute curl request; capture body and HTTP status together
RESPONSE="$(curl -s -S \
    --connect-timeout "${CONNECT_TIMEOUT}" \
    --max-time "${MAX_TIME}" \
    -w "\n%{http_code}" \
    "${HEALTH_URL}" 2>&1)"
CURL_EXIT_CODE=$?

if [ "${CURL_EXIT_CODE}" -ne 0 ]; then
    echo "[${TIMESTAMP}] UNHEALTHY - Connection failed to ${HEALTH_URL} (curl exit code: ${CURL_EXIT_CODE})" >&2
    echo "Detail: ${RESPONSE}" >&2
    exit 1
fi

HTTP_STATUS="$(printf '%s' "${RESPONSE}" | tail -n 1)"
HTTP_BODY="$(printf '%s' "${RESPONSE}" | head -n -1)"

if [ "${HTTP_STATUS}" = "200" ]; then
    echo "[${TIMESTAMP}] HEALTHY - ${HEALTH_URL} returned HTTP 200 OK"
    [ -n "${HTTP_BODY}" ] && echo "Response: ${HTTP_BODY}"
    exit 0
else
    echo "[${TIMESTAMP}] UNHEALTHY - ${HEALTH_URL} returned HTTP ${HTTP_STATUS} (Expected 200)" >&2
    [ -n "${HTTP_BODY}" ] && echo "Response: ${HTTP_BODY}" >&2
    exit 1
fi
