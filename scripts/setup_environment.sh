#!/usr/bin/env bash
# ============================================================================
# GSP-ADK-GE-2026: One-Click Environment & BigQuery Bootstrap Script
# ============================================================================
set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-"us-central1"}
BQ_FINOPS_DATASET=${BQ_FINOPS_DATASET:-"enterprise_finops_gold"}
BQ_TELEMETRY_DATASET=${BQ_TELEMETRY_DATASET:-"agent_telemetry"}

echo "============================================================================"
echo "🚀 Starting One-Click Bootstrap for Project: ${PROJECT_ID} (${REGION})"
echo "============================================================================"

# 1. Enable Required Google Cloud APIs
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

# 3. Populate Sample FinOps Billing & IT Security Policy RAG Tables in BigQuery
echo "[Step 3/4] Creating and seeding BigQuery Gold tables..."
bq query --project_id="${PROJECT_ID}" --use_legacy_sql=false <<'EOF'
CREATE OR REPLACE TABLE `enterprise_finops_gold.cloud_billing_export` AS
SELECT 'PROJ-AI-PROD-01' AS project_id, 'Vertex AI Training Cluster' AS service_name, 48500.00 AS monthly_budget_usd, 64200.50 AS current_spend_usd, 132.37 AS burn_rate_pct, 14200.00 AS idle_gpu_waste_usd, 'CRITICAL_OVERRUN' AS alert_status, CURRENT_DATE() AS report_date
UNION ALL
SELECT 'PROJ-DATA-LAKE-02', 'BigQuery Analytics Warehouse', 30000.00, 24150.00, 80.50, 1200.00, 'NORMAL', CURRENT_DATE()
UNION ALL
SELECT 'PROJ-WEB-FRONT-03', 'Cloud Run Microservices', 15000.00, 14890.00, 99.26, 450.00, 'WARNING_APPROACHING_LIMIT', CURRENT_DATE();

CREATE OR REPLACE TABLE `enterprise_finops_gold.it_security_policy_embeddings` AS
SELECT
  'SEC-POL-2026-FW' AS policy_id,
  1 AS chunk_index,
  '[PRE-REQUISITE SAFETY CHECK] Before requesting any production firewall port opening (TCP 443/8443) or VPC-SC ingress rule modification, the requester must obtain Level-2 Security Architect approval and verify that the target subnet utilizes Private Service Connect Interface (PSC-I).' AS chunk_text,
  'https://storage.cloud.google.com/cymbal-enterprise-policies/SEC-POL-2026-FW-v2.pdf' AS gcs_url,
  0.89 AS mock_similarity
UNION ALL
SELECT
  'SEC-POL-2026-FW',
  2,
  '[EXECUTION SOP: SEC-POL-2026-FW] Step 1: Submit ticket via it_servicedesk_tool with action_type=FIREWALL_OPEN. Step 2: Attach Squid Proxy egress routing table if outbound internet access is required inside VPC-SC perimeter. Step 3: Verify automated firewall audit log within 15 minutes.' AS chunk_text,
  'https://storage.cloud.google.com/cymbal-enterprise-policies/SEC-POL-2026-FW-v2.pdf',
  0.94
UNION ALL
SELECT
  'SEC-POL-2026-FW',
  3,
  '[POST-CHANGE AUDIT & ROLLBACK] Any firewall rule that exhibits anomalous egress traffic exceeding 10GB/hour will be automatically rolled back via 2-Phase Commit (2PC) compensation lock (lock:user:id:mutation).' AS chunk_text,
  'https://storage.cloud.google.com/cymbal-enterprise-policies/SEC-POL-2026-FW-v2.pdf',
  0.86
UNION ALL
SELECT
  'FIN-POL-2026-GPU',
  1,
  '[GPU QUOTA GOVERNANCE] Projects exceeding 120% Budget Burn Rate (e.g., PROJ-AI-PROD-01) are automatically restricted from provisioning additional A100/H100 GPUs unless an emergency FinOps exception ticket is approved.' AS chunk_text,
  'https://storage.cloud.google.com/cymbal-enterprise-policies/FIN-POL-2026-GPU.pdf',
  0.91;
EOF

# 4. Create Python Virtual Environment & Install Pinned Dependencies via Corp Airlock
echo "[Step 4/4] Setting up Python Virtual Environment (.venv) via Corp Airlock (gpkg setup + uv)..."
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

echo "============================================================================"
echo "✅ Environment Bootstrap Complete! Ready for Task 2 (Lab 01)."
echo "============================================================================"
