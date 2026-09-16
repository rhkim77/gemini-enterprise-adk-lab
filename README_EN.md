# Cymbal Enterprise AI Hub: Building & Registering an Enterprise ADK 2.0 Agent in Gemini Enterprise (v2.1.0 — Rev. 2026.09.16)

> 🇰🇷 **[한국어 기본 문서 보기 (README.md)](README.md)** | 🇺🇸 **English Version (Current)**

![Lab Banner](https://img.shields.io/badge/Google_Cloud-Enterprise_AI_Hub-4285F4?style=for-the-badge&logo=google-cloud)
![ADK Version](https://img.shields.io/badge/Google_ADK-2.8.0-34A853?style=for-the-badge)
![Gemini Enterprise](https://img.shields.io/badge/Gemini_Enterprise-A2A_%26_Agent_Engine-FBBC04?style=for-the-badge)
![Revision](https://img.shields.io/badge/Revision-v2.1.0_(2026.09.16)-8E24AA?style=for-the-badge)

* **Revision**: `v2.1.0` (`Rev. 2026-09-16` — Genuine ADK 2.0 `InMemoryRunner`, OAuth 2.0 Delegation & Bilingual Cosine RAG)
* **Duration**: 2 Hours (120 Minutes)
* **Level**: Intermediate / Advanced
* **Lab Format**: Hands-on Cloud Skills Lab (Enterprise Production Architecture)
* **Structural Reference**: Modeled after [hajekim/build-with-gemini-day1-agent](https://github.com/hajekim/build-with-gemini-day1-agent)

---

## 📌 Lab Overview & Business Scenario

Enterprise organizations adopting **Gemini Enterprise (formerly Google Agentspace)** need to empower employees with custom, domain-specific AI agents that can securely query internal databases, retrieve corporate policies with verified citations, and execute IT/FinOps workflows on behalf of the logged-in user.

In this hands-on lab, you act as a **Cloud Enterprise Architect** for **Cymbal Enterprise**. You will build, test, deploy, and register the **Enterprise FinOps & IT Hub Coordinator Agent (`enterprise_hub_agent`)** using **Google ADK (`google-adk`) 2.0**, exposing it to **Gemini Enterprise** via both **Native Vertex AI Agent Engine** and the open-standard **Agent2Agent (A2A) Protocol**.

---

## 🏗️ End-to-End Architecture (3 Decoupled Tool Gateways + Dual-Contract Runtime)

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Gemini Enterprise Unified Portal"]
        EndUser["Enterprise Employee"]
        GEApp["Gemini Enterprise Web UI"]
        OAuth["OAuth 2.0 Delegation<br/>(serverSideOauth2 Resource)"]
        EndUser -->|"Natural Language Query"| GEApp --> OAuth
    end

    subgraph RuntimeLayer ["2. Dual-Contract ADK Serving Layer (Cloud Run / Agent Engine)"]
        direction TB
        FastAPI["FastAPI Application (app/fast_api_app.py)"]
        A2A["A2A Endpoint<br/>GET /.well-known/agent-card.json<br/>POST /a2a/enterprise_hub_agent"]
        RE["Reasoning Engine Contract<br/>POST /api/reasoning_engine<br/>POST /api/stream_reasoning_engine"]
        Coordinator["ADK Root Coordinator (enterprise_hub_agent)<br/>Model: gemini-2.5-flash<br/>Turn Callback: Temporal Cache Invalidation"]

        OAuth -->|"Track A: Custom Agent via A2A<br/>Track B: Custom Agent via Agent Engine"| FastAPI
        FastAPI --> A2A & RE --> Coordinator
    end

    subgraph Gateways ["3. Three Decoupled Enterprise Tool Gateways"]
        direction LR
        subgraph GW1 ["Gateway 1: Structured FinOps Analytics"]
            ToolFinOps["finops_bq_tool"]
            BQTable["BigQuery FinOps Gold Ledger<br/>(cloud_billing_export, budget_burn_rate)"]
            Glossary["Standardized FinOps Formulas<br/>(Net Spend, Burn Rate %, Idle Waste)"]
            ToolFinOps --> BQTable & Glossary
        end

        subgraph GW2 ["Gateway 2: IT Security SOP Vector RAG"]
            ToolRAG["it_policy_rag_tool"]
            VectorSearch["BQ Vector Search (Cosine Sim >= 0.70)"]
            Stitching["Adjacent Window Stitcher<br/>(Chunks N-1 to N+1)"]
            Refusal["Certified Refusal Guardrail<br/>(Out-of-Domain Block)"]
            ToolRAG --> VectorSearch --> Stitching
            VectorSearch -.->|"Sim < 0.70"| Refusal
        end

        subgraph GW3 ["Gateway 3: Live IT Service Desk API"]
            ToolITSM["it_servicedesk_tool"]
            MockEngine["Deterministic MOCK Engine<br/>(Zero-Cost Cloud Shell Default)"]
            LiveAPI["Enterprise ITSM REST API<br/>(Firewall & GPU Quota 2PC Mutation)"]
            ToolITSM --> MockEngine & LiveAPI
        end

        Coordinator -->|"Single / Parallel Dispatch"| ToolFinOps & ToolRAG & ToolITSM
    end

    subgraph Observability ["4. Enterprise Audit & Governance"]
        TelemetryPlugin["BigQueryAgentAnalyticsPlugin"]
        TelemetryDS["BigQuery Audit Dataset (agent_telemetry)"]
        Coordinator -.-> TelemetryPlugin --> TelemetryDS
    end

    classDef primary fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px,color:#174ea6;
    classDef runtime fill:#e6f4ea,stroke:#1e8e3e,stroke-width:2px,color:#0d652d;
    classDef gateway fill:#fef7e0,stroke:#f29900,stroke-width:2px,color:#b06000;
    classDef guard fill:#fce8e6,stroke:#d93025,stroke-width:2px,color:#a50e0e;
    class GEApp,OAuth primary;
    class FastAPI,Coordinator,A2A,RE runtime;
    class ToolFinOps,ToolRAG,ToolITSM gateway;
    class Glossary,Refusal,TelemetryPlugin guard;
```

---

## 📚 Lab Curriculum & Tasks (Step-by-Step Guide)

| Task | Lab Guide Link | Core Objectives & Deliverables | Duration |
| :--- | :--- | :--- | :--- |
| **Task 1 (Lab 00)** | [**00: Environment Setup & One-Click Bootstrap**](labs/00_prerequisites_and_setup.md) | Configure `.env`, enable GCP APIs, run `setup_environment.sh` to create BigQuery FinOps & IT Policy tables, and pin `google-adk==2.8.0` & `mcp==1.29.1`. | 15 mins |
| **Task 2 (Lab 01)** | [**01: ADK 2.0 Agent & 3 Decoupled Tool Gateways**](labs/01_adk_agent_and_tools.md) | Implement `enterprise_hub_agent` (`app/agent.py`), build the 3 specialized gateways (`finops_bq_tool`, `it_policy_rag_tool` with `N-1~N+1` window stitching & refusal guardrail, `it_servicedesk_tool`), and pass `validate_agent.py`. | 30 mins |
| **Task 3 (Lab 02)** | [**02: Dual-Contract Serving & Local Studio Test**](labs/02_dual_contract_and_studio.md) | Mount both A2A (`/.well-known/agent-card.json`) and Reasoning Engine (`/api/reasoning_engine`) contracts on FastAPI, test 4 scenarios in Web Studio (`/studio`), and inspect BigQuery telemetry logs. | 25 mins |
| **Task 4 (Lab 03)** | [**03: Cloud Deployment (Cloud Run & Agent Engine)**](labs/03_cloud_deployment.md) | Deploy the Dual-Contract container to **Google Cloud Run** (`gcloud run deploy`) and/or **Vertex AI Agent Engine** (`AdkApp`), verifying live endpoints via `curl`. | 20 mins |
| **Task 5 (Lab 04)** | [**04: Gemini Enterprise Integration & OAuth 2.0**](labs/04_gemini_enterprise_integration.md) | Register OAuth 2.0 `serverSideOauth2` resource in Discovery Engine, register the agent in **Gemini Enterprise Console** via **Track A (A2A)** and **Track B (Agent Engine)**, run E2E employee queries, and execute `teardown.sh`. | 30 mins |

---

## ⚡ 2-Minute Quickstart

```bash
# 1. Configure Environment
cp .env.example .env
export PROJECT_ID=$(gcloud config get-value project)
sed -i "s/<YOUR_PROJECT_ID>/${PROJECT_ID}/g" .env

# 2. Run One-Click Bootstrap (Creates BigQuery datasets/tables & Python venv via Corp Airlock)
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# 3. Run Automated Validation Suite (Verifies all 3 gateways + refusal guardrail)
source .venv/bin/activate
python3 scripts/validate_agent.py

# 4. Launch Local Dual-Contract Server & Web Studio UI
uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000/studio` in your browser to test the agent interactively.
