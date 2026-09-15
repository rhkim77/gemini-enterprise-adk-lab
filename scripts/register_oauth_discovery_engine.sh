#!/usr/bin/env bash
# ============================================================================
# GSP-ADK-GE-2026: Register OAuth 2.0 serverSideOauth2 Resource in Discovery Engine
# Enables End-User Identity Delegation from Gemini Enterprise to ADK Agent
# ============================================================================
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
AUTH_ID=${AUTH_ID:-"enterprise-hub-oauth-auth"}
OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID:-"YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com"}
OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET:-"YOUR_OAUTH_CLIENT_SECRET"}

echo "============================================================================"
echo "🔐 Registering OAuth 2.0 Authorization Resource in Discovery Engine..."
echo "Project: ${PROJECT_ID} | Authorization ID: ${AUTH_ID}"
echo "Redirect URI required in GCP Console: https://vertexaisearch.cloud.google.com/oauth-redirect"
echo "============================================================================"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token --project="${PROJECT_ID}")" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/authorizations?authorizationId=${AUTH_ID}" \
  -d "{
    \"name\": \"projects/${PROJECT_ID}/locations/global/authorizations/${AUTH_ID}\",
    \"serverSideOauth2\": {
      \"clientId\": \"${OAUTH_CLIENT_ID}\",
      \"clientSecret\": \"${OAUTH_CLIENT_SECRET}\",
      \"authorizationUri\": \"https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/bigquery.readonly%20https://www.googleapis.com/auth/cloud-platform\",
      \"tokenUri\": \"https://oauth2.googleapis.com/token\"
    }
  }"

echo -e "\n============================================================================"
echo "✅ OAuth Resource Registered! Reference Name for Gemini Enterprise Console:"
echo "projects/${PROJECT_ID}/locations/global/authorizations/${AUTH_ID}"
echo "============================================================================"
