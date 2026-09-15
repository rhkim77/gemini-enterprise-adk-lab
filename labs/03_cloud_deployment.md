# Lab 03 (Task 4): Cloud Deployment (Cloud Run & Vertex AI Agent Engine)

* **Lab ID**: `GSP-ADK-GE-2026` — Task 4 of 5
* **Estimated Time**: 20 Minutes
* **Level**: Intermediate / Advanced

---

## 🎯 Objectives

In this task, you will:
1. Build and deploy the Dual-Contract container to **Google Cloud Run** (`gcloud run deploy`) so that it is accessible over HTTPS by **Gemini Enterprise A2A Registration**.
2. Learn the alternative zero-ops deployment pattern using **Vertex AI Agent Engine (`AdkApp`)** for native One Platform API integration.
3. Verify the live HTTPS Cloud Run Agent Card endpoint (`/.well-known/agent-card.json`).

---

## ☁️ Option A: Deploy Dual-Contract Container to Google Cloud Run (Recommended for A2A & Web Studio)

Google Cloud Run provides serverless auto-scaling with built-in HTTPS endpoints. Because our container serves both A2A (`/.well-known/agent-card.json`) and the Web Studio (`/studio`), Cloud Run is ideal when you want visual debugging alongside Gemini Enterprise integration (`[확인됨 / Verified: labs/04 Reference Pattern]`).

### Step 1: Set Deployment Variables
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export SERVICE_NAME="enterprise-hub-agent"
```

### Step 2: Build Container Image via Google Cloud Build
```bash
gcloud builds submit --project="${PROJECT_ID}" \
  --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
```

### Step 3: Deploy to Google Cloud Run
```bash
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ITSM_MODE=MOCK,AGENT_MODEL=gemini-2.5-flash"
```

### Step 4: Retrieve and Export Your Live HTTPS Service URL
```bash
export SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')

echo "🚀 Live Cloud Run HTTPS URL: ${SERVICE_URL}"
```

Update the `APP_URL` environment variable on Cloud Run so that the A2A Agent Card advertises its own public HTTPS RPC URL:
```bash
gcloud run services update "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --update-env-vars "APP_URL=${SERVICE_URL}"
```

---

## ⚡ Option B: Deploy Directly to Vertex AI Agent Engine (`AdkApp` Managed Runtime)

If your organization requires strict **VPC Service Controls (VPC-SC)** and **Private Service Connect Interface (PSC-I)** without managing container ingress, you can deploy `root_agent` directly to **Vertex AI Agent Engine** (`[확인됨 / Verified: GE Custom Agents Integration Guide]`).

Review the deployment Python snippet below (`deploy_to_agent_engine.py` pattern):
```python
import vertexai
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp
from app.agent import root_agent

PROJECT_ID = "your-gcp-project-id"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-ae-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# Wrap ADK root_agent in managed AdkApp runtime
adk_app = AdkApp(agent=root_agent, enable_tracing=True)

remote_agent = agent_engines.create(
    agent_engine=adk_app,
    requirements=[
        "google-adk==2.8.0",
        "mcp==1.29.1",
        "google-cloud-aiplatform[agent_engines,adk]>=1.82.0",
        "google-genai>=1.5.0",
    ],
    display_name="enterprise-hub-adk-agent",
    description="Enterprise Cloud FinOps & IT Hub Coordinator Agent",
)
print("Deployed Agent Engine Resource Name:", remote_agent.resource_name)
# Format: projects/{PROJECT_NUMBER}/locations/us-central1/reasoningEngines/{ENGINE_ID}
```

---

## ✅ Check my progress: Verify Task 4

Query your live Cloud Run HTTPS Agent Card endpoint to confirm it advertises the public HTTPS `url` and `"text/plain"` input/output modes:

```bash
curl -s "${SERVICE_URL}/.well-known/agent-card.json" | jq .
```

**Expected Output Snippet:**
```json
{
  "name": "enterprise_hub_agent",
  "url": "https://enterprise-hub-agent-xxxx-uc.a.run.app/a2a/enterprise_hub_agent",
  "defaultInputModes": [
    "text/plain"
  ],
  "defaultOutputModes": [
    "text/plain"
  ]
}
```

> **🎉 Task 4 Complete!** Proceed to the centerpiece of our workshop: [Lab 04: Gemini Enterprise Integration & OAuth 2.0 Delegation](04_gemini_enterprise_integration.md).
