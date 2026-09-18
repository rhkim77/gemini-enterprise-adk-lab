#!/usr/bin/env bash
# ============================================================================
# Cymbal Enterprise AI Hub — Track A: Google Cloud Run deployment
#
# Encapsulates labs/03_cloud_deployment.md "Option A" Steps 1-4 so the Qwiklabs
# lab can be completed with a single command.
#
# Usage:
#   ./scripts/deploy_cloud_run.sh              # build + deploy + verify
#   ./scripts/deploy_cloud_run.sh --dry-run    # print the commands, change nothing
#
# Overridable: PROJECT_ID, REGION, SERVICE_NAME
# ============================================================================
set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

# gcloud is on PATH in Cloud Shell, but a local workstation may keep it in the
# per-user SDK directory. Mirror the auto-discovery in setup_environment.sh so
# the two scripts never disagree about which gcloud they use.
if ! command -v gcloud >/dev/null 2>&1; then
  for candidate in "${HOME}/google-cloud-sdk/bin" "/usr/lib/google-cloud-sdk/bin" "/snap/bin"; do
    if [ -x "${candidate}/gcloud" ]; then
      export PATH="${candidate}:${PATH}"
      break
    fi
  done
fi
if ! command -v gcloud >/dev/null 2>&1; then
  echo "❌ gcloud CLI not found. Install the Google Cloud SDK, or run this in Cloud Shell." >&2
  exit 1
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-enterprise-hub-agent}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
  echo "❌ PROJECT_ID could not be resolved. Run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi

# IMPORTANT: GOOGLE_GENAI_USE_VERTEXAI=TRUE is not optional.
# The local .env is excluded from the image (.dockerignore), so without this the
# google-genai SDK boots in Gemini Developer API mode inside the container and
# the agent silently degrades to the deterministic fallback router — the service
# still answers, so the failure is invisible unless you probe /healthz?deep=true.
# Keep this list in sync with labs/03_cloud_deployment.md Step 3.
ENV_VARS="PROJECT_ID=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},GOOGLE_GENAI_USE_VERTEXAI=TRUE"
ENV_VARS="${ENV_VARS},GOOGLE_CLOUD_LOCATION=${REGION}"
ENV_VARS="${ENV_VARS},USE_ADK_LLM=true"
ENV_VARS="${ENV_VARS},ITSM_MODE=MOCK"
ENV_VARS="${ENV_VARS},AGENT_MODEL=gemini-2.5-flash"

echo "======================================================================"
echo " [Cymbal Enterprise AI Hub] Cloud Run deployment"
echo "======================================================================"
echo "  -> Project ID : ${PROJECT_ID}"
echo "  -> Region     : ${REGION}"
echo "  -> Service    : ${SERVICE_NAME}"
echo "  -> Image      : ${IMAGE}"
echo "======================================================================"

if [ "${DRY_RUN}" = "1" ]; then
  echo "[DRY RUN] No changes will be made. Commands that would run:"
  echo
  echo "gcloud builds submit --project=${PROJECT_ID} --tag ${IMAGE}"
  echo
  echo "gcloud run deploy ${SERVICE_NAME} --project=${PROJECT_ID} --image ${IMAGE} \\"
  echo "  --platform managed --region ${REGION} --allow-unauthenticated \\"
  echo "  --set-env-vars ${ENV_VARS}"
  echo
  echo "gcloud run services update ${SERVICE_NAME} --project=${PROJECT_ID} \\"
  echo "  --region=${REGION} --update-env-vars APP_URL=<SERVICE_URL>"
  echo
  echo "[DRY RUN] Complete."
  exit 0
fi

echo "[1/4] Building the container image with Cloud Build (this takes 3-4 minutes)..."
gcloud builds submit --project="${PROJECT_ID}" --tag "${IMAGE}"

echo "[2/4] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "${ENV_VARS}"

SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" --region="${REGION}" --format='value(status.url)')"

if [ -z "${SERVICE_URL}" ]; then
  echo "❌ Deployment finished but no service URL was returned." >&2
  exit 1
fi

# The A2A Agent Card must advertise its own public HTTPS RPC address, otherwise
# Gemini Enterprise registers a URL it cannot call back.
echo "[3/4] Updating APP_URL so the Agent Card advertises its public address..."
gcloud run services update "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --update-env-vars "APP_URL=${SERVICE_URL}" \
  --quiet >/dev/null

echo "[4/4] Running the deep health probe against the deployed revision..."
# A responding Agent Card only proves the container started. The deep probe runs
# one real agent turn and is the only way to tell ADK apart from the fallback.
PROBE="$(curl -s --max-time 60 "${SERVICE_URL}/healthz?deep=true" || true)"
ENGINE="$(printf '%s' "${PROBE}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('execution_engine','UNKNOWN'))" 2>/dev/null || echo "UNREACHABLE")"
STATUS="$(printf '%s' "${PROBE}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")"

echo "======================================================================"
echo "Service URL: ${SERVICE_URL}"
echo "Health     : ${STATUS}"
echo "Engine     : ${ENGINE}"
echo "======================================================================"

case "${ENGINE}" in
  ADK_2.0_RUNNER*)
    echo "✅ Deployment verified — the deployed revision is serving through the real ADK runner."
    echo "   Agent Card: ${SERVICE_URL}/.well-known/agent-card.json"
    echo
    echo "   Export this for Task 5:"
    echo "     export SERVICE_URL=\"${SERVICE_URL}\""
    ;;
  UNREACHABLE)
    echo "⚠️  Deployed, but the health endpoint could not be reached."
    echo "   Retry: curl -s \"${SERVICE_URL}/healthz?deep=true\" | jq ."
    echo "   See labs/TROUBLESHOOTING.md section 4."
    ;;
  *)
    echo "⚠️  Deployed, but the agent is DEGRADED (engine: ${ENGINE})."
    echo "   The container is up yet ADK is not executing. Almost always a missing env var."
    echo "   Repair:"
    echo "     gcloud run services update ${SERVICE_NAME} --project=${PROJECT_ID} --region=${REGION} \\"
    echo "       --update-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=${REGION},USE_ADK_LLM=true"
    echo "   See labs/TROUBLESHOOTING.md section 1."
    ;;
esac
