#!/usr/bin/env bash
# ============================================================================
# Cymbal Enterprise AI Hub: One-Click Environment & BigQuery Bootstrap Script
# Verifies Google Cloud SDK (gcloud/ADC), Seeds 100 Records into BigQuery & Validates
# ============================================================================
set -e

# ----------------------------------------------------------------------------
# [Preflight Step 0] Verify Google Cloud SDK (gcloud) & Add to PATH
# ----------------------------------------------------------------------------
echo "============================================================================"
echo "🔍 [Preflight] Checking Google Cloud SDK (gcloud) & Authentication..."
echo "============================================================================"

# Search standard gcloud installation paths and append to PATH if needed
for CANDIDATE_DIR in \
  "$HOME/google-cloud-sdk/bin" \
  "/usr/local/google/home/$USER/google-cloud-sdk/bin" \
  "/google/google-cloud-sdk/bin" \
  "/opt/google-cloud-sdk/bin" \
  "/usr/local/bin"; do
  if [ -x "${CANDIDATE_DIR}/gcloud" ] && [[ ":$PATH:" != *":${CANDIDATE_DIR}:"* ]]; then
    export PATH="${CANDIDATE_DIR}:${PATH}"
  fi
done

if ! command -v gcloud &> /dev/null; then
  echo "⚠️  [WARNING] Google Cloud SDK ('gcloud') was not found in PATH."
  echo "👉 Attempting automatic non-interactive installation of Google Cloud SDK..."
  if command -v curl &> /dev/null; then
    curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="$HOME"
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
  else
    echo "❌ ERROR: Neither 'gcloud' nor 'curl' is available. Please install Google Cloud SDK first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
fi

GCLOUD_BIN=$(command -v gcloud)
echo "✅ Google Cloud SDK detected: $(${GCLOUD_BIN} --version | head -n 1) (${GCLOUD_BIN})"

# Ensure non-interactive execution for gcloud prompts
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Ensure .env exists from template if not created yet
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

# [Migration] Legacy .env files (< v2.2.0) lack the Vertex AI backend flags. Without them
# google-genai boots in Gemini Developer API mode and raises "No API key was provided.",
# which the app absorbs and silently downgrades to the deterministic router.
if [ -f .env ]; then
  if ! grep -q "GOOGLE_GENAI_USE_VERTEXAI" .env; then
    printf '\n# [Auto-added by setup_environment.sh] Route google-genai through Vertex AI (ADC)\nGOOGLE_GENAI_USE_VERTEXAI="TRUE"\n' >> .env
    echo "🔧 Migrated legacy .env: added GOOGLE_GENAI_USE_VERTEXAI=\"TRUE\""
  fi
  if ! grep -q "GOOGLE_CLOUD_LOCATION" .env; then
    printf 'GOOGLE_CLOUD_LOCATION="us-central1"\n' >> .env
    echo "🔧 Migrated legacy .env: added GOOGLE_CLOUD_LOCATION=\"us-central1\""
  fi
fi

# Auto-detect active GCP Project ID if PROJECT_ID is unset or still set to placeholder
DETECTED_PROJECT=$("${GCLOUD_BIN}" config get-value project --quiet 2>/dev/null || echo "")

if [ -f .env ]; then
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

# Check Application Default Credentials (ADC) required by Python BigQuery & ADK SDKs
ADC_FILE="${HOME}/.config/gcloud/application_default_credentials.json"
if [ ! -f "${ADC_FILE}" ] && [ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
  echo "ℹ️  Note: Local ADC file (${ADC_FILE}) not found. Using Cloudtop / Cloud Shell Metadata Server credentials."
fi

REGION=${REGION:-"us-central1"}
BQ_FINOPS_DATASET=${BQ_FINOPS_DATASET:-"enterprise_finops_gold"}
BQ_TELEMETRY_DATASET=${BQ_TELEMETRY_DATASET:-"agent_telemetry"}

echo "============================================================================"
echo "🚀 Starting One-Click Bootstrap for Project: ${PROJECT_ID:-LOCAL_MODE} (${REGION})"
echo "============================================================================"

# 1. Enable Required Google Cloud APIs
if [ -n "${PROJECT_ID}" ] && [ "${PROJECT_ID}" != "<YOUR_PROJECT_ID>" ]; then
  echo "[Step 1/4] Enabling Google Cloud APIs (BigQuery, Vertex AI, Discovery Engine, Cloud Run)..."
  "${GCLOUD_BIN}" services enable \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}" --quiet 2>/dev/null || echo "⚠️ API enablement skipped or already active."
else
  echo "[Step 1/4] Skipping gcloud services enable (PROJECT_ID not configured)."
fi

# 2. Create Python Virtual Environment & Install Pinned Dependencies
echo "[Step 2/4] Verifying Python Virtual Environment (.venv)..."
export PATH="$HOME/.local/bin:$PATH"
if [ -x ".venv/bin/python3" ] && .venv/bin/python3 -c "import google.adk, google.cloud.bigquery, fastapi" &>/dev/null; then
  echo "  ✅ Existing .venv verified with google-adk, google-cloud-bigquery, and fastapi installed."
else
  echo "  📦 Installing dependencies into .venv (uv if available, otherwise python3 -m venv + pip)..."
  if command -v uv &> /dev/null; then
    uv venv .venv
    uv pip install -r requirements.txt
  else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
  fi
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
