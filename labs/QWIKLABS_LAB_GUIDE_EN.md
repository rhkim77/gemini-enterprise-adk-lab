# Cymbal Enterprise AI Hub: Building and Integrating a Google ADK 2.0 Enterprise Agent with Gemini Enterprise

> **CE Qwiklabs Official Lab Guide** (Compliant with `go/ceqwiklabs-lab-guide-template`)
> * **Duration**: `2 hours` (120 minutes)
> * **Credits**: `1 Credit`
> * **Level**: `Intermediate / Advanced`
> * **Template Reference**: [`go/ceqwiklabs-lab-guide-template`](https://docs.google.com/document/d/1KyWEGliGq01sUCYAeJ71TQExE7IGjTqhuGO_NvHu8BU) | [`go/ceqwiklabs-lab-instructions`](https://docs.google.com/document/d/1epntgNQo7lcmJhm9a5VFazeVPXjrBprp6V1XvLBmdzw)
> * **Korean Version (한국어 가이드)**: **[labs/QWIKLABS_LAB_GUIDE.md](QWIKLABS_LAB_GUIDE.md)**

---

## Overview

In this lab, you take on the role of a Cloud AI Architect at **Cymbal Enterprise** to build, validate, and deploy an enterprise-grade Coordinator Agent (`enterprise_hub_agent`) using the **Google Agent Development Kit (`google-adk` 2.0)** and integrate it with **Gemini Enterprise (formerly Google Agentspace)**.

To prevent context pollution and LLM instruction-skipping when combining structured financial SQL data with unstructured security documents and live service desk actions, you implement a **Three Decoupled Enterprise Tool Gateways** pattern backed by a **100-record live BigQuery dataset (`enterprise_finops_gold`)**. You also configure a **Dual-Contract FastAPI serving layer** that simultaneously exposes the open-standard **Agent2Agent (A2A) protocol (`/.well-known/agent-card.json`)** and the **Vertex AI Reasoning Engine contract (`/api/reasoning_engine`)**, deploy the container to **Google Cloud Run**, and configure **OAuth 2.0 (`serverSideOauth2`) delegation** in Gemini Enterprise.

---

## Objectives

In this lab, you learn how to perform the following tasks:

* Bootstrap the Google Cloud environment and automatically seed **100 enterprise test records** (`32` FinOps billing records, `36` IT security SOP vector chunks, and `32` real-time ITSM incident logs) into **BigQuery (`enterprise_finops_gold`)**.
* Configure and validate a **Google ADK (`google-adk`) 2.0 Root Coordinator Agent (`enterprise_hub_agent`)** equipped with **Three Decoupled Enterprise Tool Gateways (`finops_bq_tool`, `it_policy_rag_tool`, `it_servicedesk_tool`)** and a temporal midnight cache-invalidation callback (`before_agent_callback`).
* Launch the **Dual-Contract FastAPI serving runtime** (`InMemoryRunner` + A2A + Reasoning Engine) and interactively test 5 enterprise scenarios in the **Web Studio (`/studio`)**.
* Deploy the containerized ADK agent to **Google Cloud Run (Track A)** and/or **Vertex AI Agent Engine (Track B)**.
* Configure an **OAuth 2.0 authorization resource (`serverSideOauth2`)** in the Discovery Engine API and register the custom agent in the **Gemini Enterprise** portal.

---

## Setup and requirements

> **TCD Public Fragment Reference**: `[[import start_qwiklabs]]`

### Before you click the Start Lab button

Read these instructions. Labs are timed and you cannot pause them. The timer, which starts when you click **Start Lab**, shows how long Google Cloud resources will be made available to you.

This Qwiklabs hands-on lab lets you do the lab activities yourself in a real cloud environment, not in a simulation or demo environment. It does so by giving you new, temporary credentials that you use to sign in and access Google Cloud for the duration of the lab.

### What you need

To complete this lab, you need:

* Access to a standard internet browser (Chrome browser recommended).
* An Incognito browser window to avoid credential conflicts.
* Time to complete the lab (approximately 90–120 minutes).

> **Note**: If you already have your own personal Google Cloud account or project, do not use it for this lab to avoid incurring charges. Always use the temporary credentials from the **Connection Details** panel.

### How to start your lab and sign in to the Google Cloud Console

1. Click the **Start Lab** button. On the left is a panel populated with the temporary credentials that you must use for this lab.
2. Copy the **Username**, and then click **Open Google Console**.
3. On the **Choose an account** page, click **Use Another Account**.
4. Paste the **Username** and **Password** from the Connection Details panel.
5. Accept the terms and conditions. Do not add recovery options or two-factor authentication.

### Activate Cloud Shell

> **TCD Public Fragment Reference**: `[[import activate_cloud_shell]]`

1. In the Google Cloud Console, click **Activate Cloud Shell** (`>_`) in the top-right toolbar.
2. Click **Continue**.
3. To list the active account name, execute the following command:

| Command |
| :--- |
| `gcloud auth list` |

| Output (do not copy) |
| :--- |
| `ACTIVE: *`<br>`ACCOUNT: student-01-xxxxxxxxxxxx@qwiklabs.net` |

4. To list the active Qwiklabs project ID, execute the following command:

| Command |
| :--- |
| `gcloud config list project` |

| Output (do not copy) |
| :--- |
| `[core]`<br>`project = qwiklabs-gcp-xx-xxxxxxxxxxxx` |

---

## Task 1. Bootstrap the Lab Environment and Seed Enterprise Datasets to BigQuery

In this task, you verify Git and Google Cloud SDK (`gcloud`) credentials, clone the `Cymbal Enterprise AI Hub` repository, configure `.env`, and run the one-click bootstrap script (`scripts/setup_environment.sh`) to provision the BigQuery `enterprise_finops_gold` dataset and seed all 100 enterprise records.

### Sub-Task 1.1. Verify Git, Google Cloud SDK (`gcloud`), and Project Environment Variable

1. To verify `git` and `gcloud` installation and export your active project ID, execute the following command:

| Command |
| :--- |
| `git --version || (sudo apt-get update && sudo apt-get install -y git)`<br>`gcloud --version`<br>`export PROJECT_ID=$(gcloud config get-value project)`<br>`echo "Active Project ID: ${PROJECT_ID}"` |

| Output (do not copy) |
| :--- |
| `git version 2.39.5`<br>`Google Cloud SDK 512.0.0`<br>`Active Project ID: qwiklabs-gcp-xx-xxxxxxxxxxxx` |

### Sub-Task 1.2. Clone the Repository and Configure `.env`

1. To clone the lab repository and bind your active Qwiklabs project ID into `.env`, execute the following command:

| Command |
| :--- |
| `git clone https://github.com/rhkim77/gemini-enterprise-adk-lab.git`<br>`cd gemini-enterprise-adk-lab`<br>`cp .env.example .env`<br>`sed -i "s/<YOUR_PROJECT_ID>/${PROJECT_ID}/g" .env`<br>`grep -E "GOOGLE_CLOUD_PROJECT|BQ_FINOPS_DATASET" .env` |

| Output (do not copy) |
| :--- |
| `GOOGLE_CLOUD_PROJECT="qwiklabs-gcp-xx-xxxxxxxxxxxx"`<br>`BQ_FINOPS_DATASET="enterprise_finops_gold"` |

### Sub-Task 1.3. Execute the One-Click Environment Bootstrap (`setup_environment.sh`)

1. To enable the required Google Cloud APIs, create the `.venv` Python environment, and automatically seed the 100 enterprise records into BigQuery, execute the following command:

| Command |
| :--- |
| `chmod +x scripts/setup_environment.sh`<br>`./scripts/setup_environment.sh` |

| Output (do not copy) |
| :--- |
| `  -> [OK] cloud_billing_export seeded: 32 rows`<br>`  -> [OK] it_security_policy_embeddings seeded: 36 rows`<br>`  -> [OK] itsm_realtime_incidents seeded: 32 rows`<br>`  -> [SUCCESS] Total 100 enterprise records seeded and verified in BigQuery!` |

### Sub-Task 1.4. Verify the 100 Seeded Records in BigQuery

1. To verify the row counts across all three tables in BigQuery `enterprise_finops_gold`, execute the following command:

| Command |
| :--- |
| `bq query --use_legacy_sql=false "SELECT 'cloud_billing_export' AS table_name, COUNT(*) AS row_count FROM \`${PROJECT_ID}.enterprise_finops_gold.cloud_billing_export\` UNION ALL SELECT 'it_security_policy_embeddings', COUNT(*) FROM \`${PROJECT_ID}.enterprise_finops_gold.it_security_policy_embeddings\` UNION ALL SELECT 'itsm_realtime_incidents', COUNT(*) FROM \`${PROJECT_ID}.enterprise_finops_gold.itsm_realtime_incidents\`"` |

| Output (do not copy) |
| :--- |
| `+-------------------------------+-----------+`<br>`|          table_name           | row_count |`<br>`+-------------------------------+-----------+`<br>`| cloud_billing_export          |        32 |`<br>`| it_security_policy_embeddings |        36 |`<br>`| itsm_realtime_incidents       |        32 |`<br>`+-------------------------------+-----------+` |

> ✅ **Check my progress**
> **Click Check my progress to verify the objective.**

---

## Task 2. Implement and Validate the Google ADK 2.0 Coordinator Agent & 3 Tool Gateways

In this task, you inspect the Three Decoupled Enterprise Tool Gateways (`app/tools/`) and the Root Coordinator Agent (`app/agent.py`), and run the automated 10-point verification suite (`scripts/validate_agent.py`).

### Sub-Task 2.1. Inspect the 3 Tool Gateways and Root Coordinator Agent

1. To locate the three tool gateway function signatures at once, execute the following command:

| Command |
| :--- |
| `grep -n "^def .*_tool" app/tools/*.py` |

| Output (do not copy) |
| :--- |
| `app/tools/finops_bq_tool.py:77:def finops_bq_tool(query_or_project_id: str) -> dict:`<br>`app/tools/it_policy_rag_tool.py:154:def it_policy_rag_tool(query: str) -> str:`<br>`app/tools/it_servicedesk_tool.py:106:def it_servicedesk_tool(` |

2. To inspect the Gateway 1 signature and its **docstring**, execute the following command. Google ADK passes the **entire docstring through to the Gemini Function Calling schema as the `description` field**, so a tool docstring is not a comment - it is the only API specification the model ever reads:

| Command |
| :--- |
| `grep -n -A 12 "^def finops_bq_tool" app/tools/finops_bq_tool.py` |

**Output (do not copy)**

```text
77:def finops_bq_tool(query_or_project_id: str) -> dict:
78-    """Queries BigQuery FinOps Gold Ledger (`enterprise_finops_gold.cloud_billing_export`, 32 Projects).
79-
80-    Always enforces Knowledge Catalog Business Glossary formulas to eliminate NL2SQL hallucination.
81-
82-    Args:
83-        query_or_project_id: Target GCP Project ID (e.g., 'PROJ-AI-PROD-01' .. 'PROJ-OPS-MON-32'),
84-            department name (e.g., 'AI Research', 'FinTech Security'), or alert status ('CRITICAL_OVERRUN').
85-
86-    Returns:
87-        dict: Standardized FinOps metrics, burn rate percentage, alert status, dataset count, and executed GoogleSQL.
88-    """
```

3. To inspect the Root Coordinator Agent definition in `app/agent.py`, execute the following command:

| Command |
| :--- |
| `grep -n -A 6 "^root_agent = Agent(" app/agent.py` |

**Output (do not copy)**

```text
122:root_agent = Agent(
123-    name="enterprise_hub_agent",
124-    model=Gemini(model=MODEL, retry_options=retry_cfg),
125-    instruction=SYSTEM_INSTRUCTION,
126-    tools=[finops_bq_tool, it_policy_rag_tool, it_servicedesk_tool],
127-    before_agent_callback=validate_and_update_temporal_cache,
128-)
```

> **How to read this**: the first parameter of the function bound to `before_agent_callback` must be named exactly
> `callback_context`. The ADK 2.x runtime invokes it **by keyword** as `callback(callback_context=...)`, so a different
> parameter name raises `TypeError` and the agent silently degrades to the deterministic router.

### Sub-Task 2.2. Execute the Automated Verification Suite (`validate_agent.py`)

1. To validate all 100 records, live BigQuery queries, window stitching, certified refusal guardrails, and Dual-Contract routes, execute the following command:

| Command |
| :--- |
| `.venv/bin/python3 scripts/validate_agent.py` |

**Output (do not copy)**

```text
====================================================================================
🧪 CYMBAL ENTERPRISE AI HUB - AUTOMATED VALIDATION SUITE (100-RECORD DATASET)
Project ID: qwiklabs-gcp-xx-xxxxxxxxxxxx | ITSM Mode: MOCK
====================================================================================

[TEST 1/10] Dataset Scale Audit (>= 30 Records per Gateway)...
  • Gateway 1 (FinOps Projects):      32 records (Target >= 30)
  • Gateway 2 (Policy RAG Chunks):    36 chunks across 12 policies (Target >= 30)
  • Gateway 3 (ITSM Incidents):       32 records (Target >= 30)
  • Total Enterprise Dataset Records: 100 records
  [PASS] All 3 gateways meet the 30+ realistic enterprise record threshold.

[TEST 2/10] Gateway 1: FinOps Analytics (Project & Department Queries across 32 Projects)...
  [PASS] Completed in 2.97s — Multi-project & department SQL aggregations verified.

[TEST 3/10] Gateway 2: IT Policy RAG Window Stitching (Bilingual KR/EN & Cosine Sim >= 0.70)...
  [PASS] Completed in 2.78s — Adjacent chunks N-1~N+1 stitched & Bilingual Cosine Similarity verified.

[TEST 4/10] Gateway 2: Expanded Policy Corpus Query (NET-POL-2026-PSCI & DLP Policy)...
  [PASS] Completed in 2.78s — Expanded policies retrieved with 3-chunk window stitching.

[TEST 5/10] Gateway 2: Out-of-Domain Refusal Gate (Espresso Machine & Personal Cloud Photos)...
  [PASS] Completed in 0.00s — Certified refusal guardrail enforced strictly (EN & KR).

[TEST 6/10] Gateway 3: Expanded ITSM Incident Lookup (INC-2026-88415 & P1_CRITICAL Filter)...
  [PASS] Completed in 2.68s — Specific ticket lookup & P1 Critical filter (9 P1 incidents) verified.

[TEST 7/10] Gateway 3: Dual-Mode 2PC HITL Ticket Creation & OAuth 2.0 Delegation Audit...
  [PASS] Completed in 0.00s — 2PC lock, HITL flag & OAuth 2.0 identity (architect@cymbal.enterprise) verified.

[TEST 8/10] Coordinator Governance, ADK Callback Contract & A2A Agent Card Schema...
  [PASS] Completed in 0.00s — ADK callback contract `callback(callback_context=...)` honored, cache purged & A2A Card schema verified.

[TEST 9/10] Documentation Drift: Dependency Pin Consistency (requirements.txt <-> labs/03)...
  [PASS] Completed in 0.00s — Dependency pins consistent across requirements.txt and labs/03.

[TEST 10/10] Lab Structure Integrity: Completion Checkpoints & Troubleshooting Links...
  [PASS] Completed in 0.00s — All 5 labs expose a checkpoint & troubleshooting link.

====================================================================================
📊 VALIDATION SUMMARY: 10 PASSED, 0 FAILED (TOTAL: 10 TESTS | 100 DATA RECORDS)
====================================================================================
🎉 All 100 enterprise dataset records, 3 gateways, OAuth delegation & ADK 2.0 runner verified!
```

> **Note**: Two `Out-of-domain query blocked by refusal guardrail ...` warning lines may appear before the suite header.
> They confirm the TEST 5 refusal guardrail is working and are not errors.

> ✅ **Check my progress**
> **Click Check my progress to verify the objective.**

---

## Task 3. Launch the Dual-Contract Runtime and Test Scenarios in the Web Studio

In this task, you start the Dual-Contract FastAPI server (`app/fast_api_app.py`), verify the deep health check and A2A Agent Card JSON endpoint, and test the 5 core scenarios in the interactive Web Studio (`/studio`).

### Sub-Task 3.1. Start the Dual-Contract FastAPI Server and Verify Deep Health Check

1. To launch the server in the background on port `8000` and inspect `/healthz?deep=true`, execute the following command:

| Command |
| :--- |
| `nohup .venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 > /tmp/hub_server.log 2>&1 &`<br>`sleep 3`<br>`curl -s "http://localhost:8000/healthz?deep=true" | python3 -m json.tool` |

**Output (do not copy)**

```json
{
    "status": "healthy",
    "agent": "enterprise_hub_agent",
    "model": "gemini-2.5-flash",
    "adk_runner_constructed": true,
    "contracts": [
        "A2A",
        "ReasoningEngine"
    ],
    "execution_engine": "ADK_2.0_RUNNER (gemini-2.5-flash)",
    "probe_latency_ms": 2376,
    "adk_runner_active": true
}
```

> **How to read this**: `execution_engine` must say `ADK_2.0_RUNNER`, which means the request was served by the real ADK path.
> If it says `DETERMINISTIC_HYBRID_ROUTER`, the ADK call failed and the app silently fell back to the deterministic router;
> in that case `status` becomes `degraded` and the `last_adk_error` and `remediation` fields are returned as well.
> `probe_latency_ms` includes a live Gemini call, so it varies between roughly 1,500-4,000 ms.

### Sub-Task 3.2. Verify the A2A Agent Card (`/.well-known/agent-card.json`)

1. To inspect the A2A discovery payload required by Gemini Enterprise, execute the following command:

| Command |
| :--- |
| `curl -s "http://localhost:8000/.well-known/agent-card.json" | python3 -m json.tool` |

**Output (do not copy)**

```json
{
    "name": "enterprise_hub_agent",
    "description": "Enterprise Cloud FinOps & IT Hub Coordinator Agent. Orchestrates BigQuery FinOps burn rate analytics, IT Security SOP Vector RAG with window stitching (SEC-POL-2026-FW), and 2PC HITL Service Desk ticket creation with OAuth 2.0 identity delegation.",
    "url": "http://localhost:8000/a2a/enterprise_hub_agent",
    "version": "2.0.0",
    "capabilities": {
        "streaming": false,
        "pushNotifications": false,
        "stateTransitionHistory": true
    },
    "defaultInputModes": [
        "text/plain"
    ],
    "defaultOutputModes": [
        "text/plain"
    ]
}
```

### Sub-Task 3.3. Test the 5 Core Scenarios in Cloud Shell Web Preview (`/studio`)

1. Click **Web Preview** in the top-right corner of Cloud Shell and select **Preview on port 8000**.
2. Append `/studio` to the URL in your browser tab (`https://<CLOUD_SHELL_PROXY_URL>/studio`).
3. Click through the 5 preset scenario buttons in the left sidebar to test:
   * **Scenario 1**: FinOps burn rate for `PROJ-AI-PROD-01` (department `AI Research`) returns `132.37%` (`CRITICAL_OVERRUN`) with `$14,200.00` idle GPU waste, plus interactive Plotly chart rendering.
   * **Scenario 2**: Security SOP Vector RAG with Adjacent Window Stitching (`SEC-POL-2026-FW` `chunk_index` 1-3).
   * **Scenario 3**: OAuth 2.0 2-Phase Commit (`PENDING_HITL_APPROVAL`) firewall ticket creation.
   * **Scenario 4**: Multi-Gateway parallel enterprise audit.
   * **Scenario 5**: Out-of-domain query Certified Refusal (`Cosine Sim < 0.70`).

> ✅ **Check my progress**
> **Click Check my progress to verify the objective.**

---

## Task 4. Deploy the ADK Agent to Google Cloud Run (Track A)

In this task, you containerize and deploy the `Cymbal Enterprise AI Hub` runtime to **Google Cloud Run** to obtain a publicly accessible HTTPS A2A Agent Card URL.

### Sub-Task 4.1. Build and Deploy to Cloud Run (`deploy_cloud_run.sh`)

1. To build and deploy the service `enterprise-hub-agent` to Cloud Run (`us-central1`), execute the following command:

| Command |
| :--- |
| `chmod +x scripts/deploy_cloud_run.sh`<br>`./scripts/deploy_cloud_run.sh` |

| Output (do not copy) |
| :--- |
| `Deploying container to Cloud Run service [enterprise-hub-agent]... Done.`<br>`Service URL: https://enterprise-hub-agent-xxxxxxxxxx-uc.a.run.app` |

### Sub-Task 4.2. Verify the Live Cloud Run HTTPS A2A Endpoint

1. To verify the external HTTPS A2A Agent Card on Cloud Run, execute the following command:

| Command |
| :--- |
| `export SERVICE_URL=$(gcloud run services describe enterprise-hub-agent --region us-central1 --format="value(status.url)")`<br>`curl -s "${SERVICE_URL}/.well-known/agent-card.json" | python3 -m json.tool` |

**Output (do not copy)**

```text
Deployed Cloud Run URL: https://enterprise-hub-agent-xxxxxxxxxx-uc.a.run.app
```
```json
{
    "name": "enterprise_hub_agent",
    "url": "https://enterprise-hub-agent-xxxxxxxxxx-uc.a.run.app/a2a/enterprise_hub_agent",
    "version": "2.0.0",
    "defaultInputModes": [
        "text/plain"
    ],
    "defaultOutputModes": [
        "text/plain"
    ]
}
```

> ✅ **Check my progress**
> **Click Check my progress to verify the objective.**

---

## Task 5. Configure OAuth 2.0 Delegation and Register the Agent in Gemini Enterprise

In this task, you validate the Discovery Engine `serverSideOauth2` authorization specification (`https://vertexaisearch.cloud.google.com/oauth-redirect`) and register the custom agent in the **Gemini Enterprise** portal.

### Sub-Task 5.1. Run the Lab 04 Completion & OAuth 2.0 Verification Script

1. To verify OAuth 2.0 Redirect URI compliance and end-to-end A2A/Reasoning Engine readiness, execute the following command:

| Command |
| :--- |
| `.venv/bin/python3 scripts/verify_lab04_completion.py` |

| Output (do not copy) |
| :--- |
| `[PASS] 1. A2A Agent Card Schema Compliance (defaultInputModes/defaultOutputModes/skills)`<br>`[PASS] 2. OAuth 2.0 Redirect URI Specification Verified (https://vertexaisearch.cloud.google.com/oauth-redirect)`<br>`[PASS] 3. Dual-Contract Endpoints (/a2a/enterprise_hub_agent & /api/reasoning_engine) Verified`<br>`[PASS] 4. End-to-End OAuth Token Forwarding & HITL Audit Log Verified`<br>`🎉 Lab 04 Verification PASSED! Ready for Gemini Enterprise Portal!` |

### Sub-Task 5.2. Register the Custom Agent in Gemini Enterprise Console

1. In the Google Cloud Console, navigate to **Gemini Enterprise (AI Applications)** and select your Enterprise App.
2. Click **Agents** ➔ **+ Add agent** ➔ **Custom agent via A2A**.
3. Paste the JSON output from `${SERVICE_URL}/.well-known/agent-card.json`, bind your `serverSideOauth2` resource (`cymbal-hub-oauth-auth`), and click **Save / Publish**.

> ✅ **Check my progress**
> **Click Check my progress to verify the objective.**

---

## Congratulations!

You have successfully built, validated, deployed, and integrated the **Cymbal Enterprise AI Hub** agent using **Google ADK (`google-adk` 2.0)**, **BigQuery (`enterprise_finops_gold` — 100 records)**, **Cloud Run**, and **Gemini Enterprise**.

### End your lab

When you have completed your lab, click **End Lab** in the top-left panel.
