#!/usr/bin/env bash
# ============================================================================
# GSP-ADK-GE-2026: Lab Resource Teardown Script
# ============================================================================
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="enterprise-hub-agent"

echo "============================================================================"
echo "🧹 Cleaning up Lab Resources in Project: ${PROJECT_ID}..."
echo "============================================================================"

echo "1. Removing BigQuery datasets (enterprise_finops_gold, agent_telemetry)..."
bq rm -r -f -d "${PROJECT_ID}:enterprise_finops_gold" || true
bq rm -r -f -d "${PROJECT_ID}:agent_telemetry" || true

echo "2. Deleting Cloud Run service (${SERVICE_NAME})..."
gcloud run services delete "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --quiet || true

echo "============================================================================"
echo "✅ Teardown Complete! All billable lab resources have been removed."
echo "============================================================================"
