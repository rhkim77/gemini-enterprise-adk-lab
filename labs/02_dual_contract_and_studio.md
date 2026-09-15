# Lab 02 (Task 3): Dual-Contract Serving & Interactive Web Studio

* **Lab ID**: `GSP-ADK-GE-2026` — Task 3 of 5
* **Estimated Time**: 25 Minutes
* **Level**: Intermediate / Advanced

---

## 🎯 Objectives

In this task, you will:
1. Understand the **Dual-Contract Serving Architecture** implemented in `app/fast_api_app.py`.
2. Verify that a single FastAPI container simultaneously serves:
   - **Open-Standard A2A Protocol Endpoints** (`GET /.well-known/agent-card.json` & `POST /a2a/enterprise_hub_agent`)
   - **Vertex AI Reasoning Engine Contract** (`POST /api/reasoning_engine` & `POST /api/stream_reasoning_engine`)
   - **Interactive Operations Web Studio UI** (`GET /studio` & `POST /api/chat`)
3. Launch the local server and test 4 operational scenarios visually using Plotly charts and SQL/Citation inspectors.

---

## 🔍 Step 1: Review the Dual-Contract Adapter Code

Inspect `app/app_utils/a2a.py` to see how the Agent Card is dynamically constructed:

```bash
cat app/app_utils/a2a.py
```

### ⚠️ Crucial Gemini Enterprise Gotcha Fixed Automatically
When registering an A2A agent in **Gemini Enterprise Console**, if `defaultInputModes` or `defaultOutputModes` contains `"text"` instead of a valid MIME type, the console rejects the Agent Card during schema validation (`[확인됨 / Verified: GE Custom Agents Integration Guide]`).

Our implementation in `app/app_utils/a2a.py` explicitly hardens this field:
```json
"defaultInputModes": ["text/plain"],
"defaultOutputModes": ["text/plain"]
```

---

## 🚀 Step 2: Start the Dual-Contract FastAPI Server

Activate your virtual environment (if created via `setup_environment.sh`) or run `uvicorn` directly:

```bash
source .venv/bin/activate 2>/dev/null || true
uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
sleep 2
```

---

## 🧪 Step 3: Test Both Enterprise Contracts via `curl`

### 3.1 Verify the A2A Agent Card (`GET /.well-known/agent-card.json`)
```bash
curl -s http://localhost:8000/.well-known/agent-card.json | jq .
```
Confirm that `"defaultInputModes": ["text/plain"]` and the 3 skills (`finops_burn_rate_audit`, `it_security_policy_rag`, `it_servicedesk_action`) appear in the JSON output.

### 3.2 Verify A2A JSON-RPC Invocation (`POST /a2a/enterprise_hub_agent`)
```bash
curl -s -X POST http://localhost:8000/a2a/enterprise_hub_agent \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-rpc-101",
    "params": {
      "message": {
        "parts": [{"type": "text", "text": "What is the firewall port open procedure under policy SEC-POL-2026-FW?"}]
      }
    }
  }' | jq .
```

### 3.3 Verify Vertex AI Reasoning Engine Contract (`POST /api/reasoning_engine`)
```bash
curl -s -X POST http://localhost:8000/api/reasoning_engine \
  -H "Content-Type: application/json" \
  -d '{
    "class_method": "query",
    "input": {
      "input": "Audit live ITSM incidents and compare against FinOps burn rate for PROJ-AI-PROD-01"
    }
  }' | jq .
```

---

## 🖥️ Step 4: Explore the Interactive Operations Web Studio UI

Open your browser to:
* **Local / Cloud Shell Web Preview**: `http://localhost:8000/studio`
* **Cloudtop Proxy URL**: `http://ryansbox.c.googlers.com:8000/studio`

Click each of the **4 Qwiklabs Verification Scenario Buttons** at the top of the studio:
1. **📊 1. FinOps Burn Rate (Gateway 1)**: Renders the Plotly bar chart showing `PROJ-AI-PROD-01` at `132.37%` overrun alongside executed GoogleSQL.
2. **📜 2. Security Policy RAG + Stitching (Gateway 2)**: Displays stitched chunks `N-1 ~ N+1` and the clickable HTTPS GCS link.
3. **⚡ 3. Parallel Dispatch Audit (GW1 + GW3)**: Demonstrates concurrent execution (`PARALLEL_DISPATCH`) across BigQuery FinOps and Service Desk telemetry.
4. **🛡️ 4. Out-of-Domain Refusal Gate**: Verifies that non-enterprise queries are strictly blocked.

---

## ✅ Check my progress: Verify Task 3

Run the health check endpoint to confirm both contracts are active:

```bash
curl -s http://localhost:8000/healthz
```

**Expected Output:**
```json
{"status":"healthy","agent":"enterprise_hub_agent","contracts":["A2A","ReasoningEngine"]}
```

> **🎉 Task 3 Complete!** Proceed to [Lab 03: Cloud Deployment (Cloud Run & Agent Engine)](03_cloud_deployment.md).
