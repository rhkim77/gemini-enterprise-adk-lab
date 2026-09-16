#!/usr/bin/env bash
# ============================================================================
# Cymbal Enterprise AI Hub: One-Click Environment & BigQuery Bootstrap Script
# Seeds 100 Enterprise Records across 3 Gateways (32 FinOps + 36 Policy + 32 ITSM)
# ============================================================================
set -e

# Ensure .env exists from template if not created yet
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

# Resolve gcloud binary path
GCLOUD_BIN=$(command -v gcloud 2>/dev/null || echo "/usr/local/google/home/ryunghwa/google-cloud-sdk/bin/gcloud")

# Auto-detect active GCP Project ID if PROJECT_ID is unset or still set to placeholder
DETECTED_PROJECT=""
if [ -x "${GCLOUD_BIN}" ]; then
  DETECTED_PROJECT=$("${GCLOUD_BIN}" config get-value project 2>/dev/null || echo "")
fi

if [ -f .env ]; then
  # If .env still has <YOUR_PROJECT_ID> and we detected a valid GCP project, auto-populate .env
  if grep -q "<YOUR_PROJECT_ID>" .env && [ -n "${DETECTED_PROJECT}" ] && [ "${DETECTED_PROJECT}" != "(unset)" ]; then
    sed -i "s/<YOUR_PROJECT_ID>/${DETECTED_PROJECT}/g" .env
    echo "🔧 Auto-configured .env with active GCP Project ID: ${DETECTED_PROJECT}"
  fi
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "<YOUR_PROJECT_ID>" ]; then
  PROJECT_ID="${DETECTED_PROJECT}"
fi
export PROJECT_ID
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"

REGION=${REGION:-"us-central1"}
BQ_FINOPS_DATASET=${BQ_FINOPS_DATASET:-"enterprise_finops_gold"}
BQ_TELEMETRY_DATASET=${BQ_TELEMETRY_DATASET:-"agent_telemetry"}

echo "============================================================================"
echo "🚀 Starting One-Click Bootstrap for Project: ${PROJECT_ID:-LOCAL_MODE} (${REGION})"
echo "============================================================================"

# 1. Enable Required Google Cloud APIs
if [ -n "${PROJECT_ID}" ] && [ "${PROJECT_ID}" != "<YOUR_PROJECT_ID>" ] && [ -x "${GCLOUD_BIN}" ]; then
  echo "[Step 1/4] Enabling Google Cloud APIs..."
  "${GCLOUD_BIN}" services enable \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}" 2>/dev/null || echo "⚠️ API enablement skipped or already active."
else
  echo "[Step 1/4] Skipping gcloud services enable (using existing project APIs)."
fi

# 2. Create Python Virtual Environment & Install Pinned Dependencies via Corp Airlock
echo "[Step 2/4] Setting up Python Virtual Environment (.venv) via Corp Airlock (gpkg setup + uv)..."
gpkg setup 2>/dev/null || true
if command -v uv &> /dev/null; then
  uv venv .venv --clear
  uv pip install -r requirements.txt
else
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# 3. Seed 100 Enterprise Records (32 FinOps, 36 Policy Chunks, 32 ITSM Incidents) into BigQuery
echo "[Step 3/4] Creating BigQuery Datasets & Seeding 100 Enterprise JSON Records into BigQuery..."
.venv/bin/python3 scripts/seed_bigquery.py

# 4. Run Automated Verification Suite (8 Tests across 100 Records)
echo "[Step 4/4] Running Automated Verification Suite (validate_agent.py)..."
.venv/bin/python3 scripts/validate_agent.py

echo "============================================================================"
echo "✅ Environment Bootstrap, BigQuery 100-Record Seeding & Verification Complete!"
echo "============================================================================"
