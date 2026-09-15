# Lab 00 (Task 1): Environment Setup & One-Click Data Bootstrap

* **Lab ID**: `GSP-ADK-GE-2026` — Task 1 of 5
* **Estimated Time**: 15 Minutes
* **Level**: Intermediate / Advanced

---

## 🎯 Objectives

In this task, you will:
1. Initialize your Google Cloud environment and configure your project variables in `.env`.
2. Enable the required Google Cloud APIs (`aiplatform`, `discoveryengine`, `bigquery`, `run`, `cloudbuild`).
3. Run the automated one-click bootstrap script (`scripts/setup_environment.sh`) to seed the **BigQuery FinOps Gold Ledger** and **IT Security Policy Vector Embeddings** tables.
4. Pin `google-adk==2.8.0` and `mcp==1.29.1` to prevent MCP session import conflicts (`[확인됨 / Verified: CE Engineering Standards]`).

---

## 🛠️ Step 1: Clone or Navigate to the Lab Workspace

Open your terminal (or Google Cloud Shell) and navigate to the lab directory:

```bash
cd /usr/local/google/home/ryunghwa/Dev/GE_test/gemini-enterprise-adk-lab
```

Verify your active Google Cloud Project ID:

```bash
export PROJECT_ID=$(gcloud config get-value project)
echo "Active GCP Project ID: ${PROJECT_ID}"
```

---

## ⚙️ Step 2: Configure the `.env` File

Copy the environment template `.env.example` to `.env` and inject your active `PROJECT_ID`:

```bash
cp .env.example .env
sed -i "s/<YOUR_PROJECT_ID>/${PROJECT_ID}/g" .env
```

Inspect your configured `.env` file:
```bash
cat .env
```
Ensure that `ITSM_MODE="MOCK"` is set so that you can test real-time Service Desk ticket creation with **zero cloud infrastructure cost**.

---

## 🚀 Step 3: Execute the One-Click Bootstrap Script

Make the bootstrap script executable and run it:

```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

### What happens under the hood?
1. **API Activation**: Enables Vertex AI, Discovery Engine (Gemini Enterprise), BigQuery, Cloud Run, and Cloud Build APIs.
2. **BigQuery Dataset Creation**: Creates `enterprise_finops_gold` (business data & vector embeddings) and `agent_telemetry` (audit logs).
3. **Table Seeding**:
   - `enterprise_finops_gold.cloud_billing_export`: Contains monthly cloud budgets, actual spend, standardized Burn Rate %, and idle GPU waste metrics across enterprise projects (`PROJ-AI-PROD-01`, `PROJ-DATA-LAKE-02`, `PROJ-WEB-FRONT-03`).
   - `enterprise_finops_gold.it_security_policy_embeddings`: Contains pre-chunked corporate security manuals (`SEC-POL-2026-FW`, `FIN-POL-2026-GPU`) structured for **Adjacent Context Window Stitching (`N-1 ~ N+1`)**.
4. **Dependency Pinning**: Installs `google-adk==2.8.0` and `mcp==1.29.1` inside `.venv` to prevent `ModuleNotFoundError: No module named 'mcp.shared.session'`.

---

## ✅ Check my progress: Verify Task 1

Run the following BigQuery verification query to confirm that both tables are populated and ready:

```bash
bq query --project_id=${PROJECT_ID} --use_legacy_sql=false \
"SELECT 'cloud_billing_export' AS table_name, COUNT(*) AS row_count FROM \`enterprise_finops_gold.cloud_billing_export\`
 UNION ALL
 SELECT 'it_security_policy_embeddings', COUNT(*) FROM \`enterprise_finops_gold.it_security_policy_embeddings\`;"
```

**Expected Output:**
```text
+-------------------------------+-----------+
|          table_name           | row_count |
+-------------------------------+-----------+
| cloud_billing_export          |         3 |
| it_security_policy_embeddings |         4 |
+-------------------------------+-----------+
```

> **🎉 Task 1 Complete!** Proceed to [Lab 01: ADK 2.0 Agent & 3 Decoupled Tool Gateways](01_adk_agent_and_tools.md).
