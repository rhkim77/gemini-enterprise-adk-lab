#!/usr/bin/env bash
# ============================================================================
# GSP-ADK-GE-2026: One-Click Environment & BigQuery Bootstrap Script
# Seeds 100 Enterprise Records across 3 Gateways (32 FinOps + 36 Policy + 32 ITSM)
# ============================================================================
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}
REGION=${REGION:-"us-central1"}
BQ_FINOPS_DATASET=${BQ_FINOPS_DATASET:-"enterprise_finops_gold"}
BQ_TELEMETRY_DATASET=${BQ_TELEMETRY_DATASET:-"agent_telemetry"}

echo "============================================================================"
echo "🚀 Starting One-Click Bootstrap for Project: ${PROJECT_ID:-LOCAL_MODE} (${REGION})"
echo "============================================================================"

# 1. Enable Required Google Cloud APIs
if [ -n "${PROJECT_ID}" ] && [ "${PROJECT_ID}" != "<YOUR_PROJECT_ID>" ]; then
  echo "[Step 1/4] Enabling Google Cloud APIs..."
  gcloud services enable \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}" || echo "⚠️ API enablement skipped or already active."

  # 2. Create BigQuery Datasets
  echo "[Step 2/4] Creating BigQuery Datasets (${BQ_FINOPS_DATASET}, ${BQ_TELEMETRY_DATASET})..."
  bq --location=US mk -d --if_not_exists "${PROJECT_ID}:${BQ_FINOPS_DATASET}" || true
  bq --location=US mk -d --if_not_exists "${PROJECT_ID}:${BQ_TELEMETRY_DATASET}" || true
else
  echo "[Step 1-2/4] Skipping remote GCP API/Dataset creation (PROJECT_ID not configured)."
fi

# 3. Create Python Virtual Environment & Install Pinned Dependencies via Corp Airlock
echo "[Step 3/4] Setting up Python Virtual Environment (.venv) via Corp Airlock (gpkg setup + uv)..."
gpkg setup || true
if command -v uv &> /dev/null; then
  uv venv .venv --clear
  uv pip install -r requirements.txt
else
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# 4. Seed 100 Enterprise Records (32 FinOps, 36 Policy Chunks, 32 ITSM Incidents)
echo "[Step 4/4] Seeding 100 Enterprise Records into BigQuery / Local Gold Ledger..."
.venv/bin/python3 scripts/seed_bigquery.py

echo "============================================================================"
echo "✅ Environment Bootstrap & 100-Record Dataset Seeding Complete! Ready for Lab 01."
echo "============================================================================"
