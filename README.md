# Cymbal Enterprise AI Hub: Gemini Enterprise 기반 Google ADK 2.0 엔터프라이즈 에이전트 구축 및 연동 가이드 (v2.3.0 — Rev. 2026.09.16)

> 🇰🇷 **한국어 기본 문서 (Current)** | 🇺🇸 **[English Version (README_EN.md)](README_EN.md)**
> 🎓 **CE Qwiklabs 공식 단일 통합 Lab Guide (`go/ceqwiklabs-lab-guide-template` 표준)**: **[🇰🇷 한국어 Qwiklabs 가이드 (labs/QWIKLABS_LAB_GUIDE.md)](labs/QWIKLABS_LAB_GUIDE.md)** | **[🇺🇸 English Qwiklabs Guide (labs/QWIKLABS_LAB_GUIDE_EN.md)](labs/QWIKLABS_LAB_GUIDE_EN.md)** | **[CE Qwiklabs 번들 (`qwiklabs_bundle/`)](qwiklabs_bundle/README.md)**

![Lab Banner](https://img.shields.io/badge/Google_Cloud-Enterprise_AI_Hub-4285F4?style=for-the-badge&logo=google-cloud)
![ADK Version](https://img.shields.io/badge/Google_ADK-2.8.0-34A853?style=for-the-badge)
![Gemini Enterprise](https://img.shields.io/badge/Gemini_Enterprise-A2A_%26_Agent_Engine-FBBC04?style=for-the-badge)
![Revision](https://img.shields.io/badge/Revision-v2.3.0_(2026.09.16)-8E24AA?style=for-the-badge)

* **프로젝트 명칭**: `Cymbal Enterprise AI Hub` (엔터프라이즈 FinOps 및 IT 통합 코디네이터 에이전트)
* **리비전 정보 (Revision)**: `v2.3.0` (`Rev. 2026-09-16` — 실습 일관성 강화: 딥 헬스체크(`/healthz?deep=true`), Lab 04 완료 검증, 트러블슈팅 가이드, 문서 드리프트 자동 검출 테스트 2종 추가)
* **소요 시간**: 약 2시간 (총 5개 모듈 구성)
* **난이도**: 중급 / 고급 (Intermediate / Advanced)

---

## 📌 1. 워크샵 개요 및 비즈니스 시나리오

**Gemini Enterprise(구 Google Agentspace)**를 도입한 엔터프라이즈 기업들은 임직원들이 단일 통합 포털에서 자연어로 사내 데이터베이스를 조회하고, 공인된 보안/운영 매뉴얼의 근거 링크(Citation)를 확인하며, 로그인한 사용자 본인의 권한(OAuth 2.0)으로 IT 서비스 데스크 티켓을 즉시 발행할 수 있는 **도메인 특화 AI 에이전트**를 필요로 합니다.

본 핸즈온 워크샵에서 여러분은 **Cymbal Enterprise의 클라우드 AI 아키텍트**가 되어, **Google ADK (`google-adk`) 2.0** 기반의 **엔터프라이즈 클라우드 FinOps 및 IT 통합 코디네이터 에이전트(`enterprise_hub_agent`)**를 From-the-Scratch로 구축합니다.

특히 단일 FastAPI 컨테이너에서 **오픈 표준 Agent2Agent (A2A) 프로토콜**과 **Vertex AI Reasoning Engine 네이티브 계약**을 동시에 노출하는 **Dual-Contract 서빙 아키텍처**를 구현하고, 이를 **Gemini Enterprise 콘솔**에 등록하여 End-to-End로 검증합니다.

---

## 🏗️ 2. 전체 시스템 아키텍처 (3대 분리형 도구 게이트웨이 + Dual-Contract 런타임)

단일 루트 에이전트(`LlmAgent`)에 모든 Raw SQL과 비정형 청크를 직접 연결할 경우 발생하는 **컨텍스트 오염(Context Pollution)**과 **지시 건너뛰기(Instruction-Skipping)**를 방지하기 위해, 데이터 모달리티별로 특화된 **3대 분리형 도구 게이트웨이(Decoupled Tool Gateways)** 패턴을 적용합니다 (`[확인됨 / Verified: Google ADK Enterprise Design Pattern]`).

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

### 💡 왜 3대 분리형 게이트웨이(Decoupled Tool Gateways)로 구성하는가?
1. **Gateway 1 (`finops_bq_tool` — 정형 데이터 분석 & Context Gap 해소)**:
   - LLM이 임의로 SQL 수식을 추정하지 못하도록 **Knowledge Catalog 비즈니스 용어사전 표준 공식**(`예산 소진율 % = 당월 지출액 / 월 예산 * 100`)을 강제하여 NL2SQL 환각을 원천 차단합니다.
2. **Gateway 2 (`it_policy_rag_tool` — 비정형 규정 Vector RAG & 윈도우 스티칭)**:
   - 보안/방화벽 매뉴얼(`SEC-POL-2026-FW`) 검색 시 코사인 유사도 `>= 0.70` 품질 게이트를 적용하고, 앞뒤로 연결된 **인접 청크(`N-1 ~ N+1`)를 자동 결합(Window Stitching)**하여 사전 안전 수칙 누락을 방지합니다.
   - 유사도 `0.70` 미만의 도메인 외 질의(예: 사내 에스프레소 머신 수리 문의) 시 **인증된 거절 문장(Certified Refusal)만 단독 출력**하도록 통제합니다.
3. **Gateway 3 (`it_servicedesk_tool` — 실시간 상태 조회 & 2PC HITL 티켓 발행)**:
   - 클라우드 인프라 과금 없이 로컬/Cloud Shell에서 즉시 검증 가능한 **`MOCK` 모드**와 실제 ITSM API를 호출하는 **`LIVE` 모드**를 지원하며, 방화벽 오픈 및 GPU 쿼터 증설 시 **2-Phase Commit (2PC) 멱등성 락(`lock:user:{id}:mutation`)**과 **HITL 승인 플래그(`PENDING_HITL_APPROVAL`)**를 강제합니다.

---

## 📊 3. 엔터프라이즈 실전 테스트 데이터셋 구성 및 BigQuery 자동 적재

본 프로젝트는 에이전트의 정형 데이터 분석(NL2SQL), 비정형 보안 규정 검색(Vector RAG), 그리고 실시간 인프라 변경 거버넌스(ITSM Action)를 실제 운영 환경과 동일한 수준으로 검증할 수 있도록 `data/` 디렉토리에 **총 100건의 엔터프라이즈 실전 테스트 데이터셋**을 기본 준비해 두었습니다.

준비된 테스트 데이터는 사내 8개 핵심 부서 산하 32개 클라우드 프로젝트의 **월별 예산, 실시간 지출액, 표준 공식 기반의 예산 소진율(Burn Rate %) 및 유휴 GPU 낭비 비용 데이터**, 방화벽 개방·VPC-SC 망분리·OAuth 권한 위임·DLP 마스킹 등 12대 핵심 보안/인프라 규정을 문맥 단절 없이 검색하기 위해 **사전 안전 점검부터 실행 절차, 사후 감사 및 롤백까지 연속된 청크(Chunk) 단위로 구조화한 36건의 정책 문서 데이터**, 그리고 네트워크 차단이나 GPU 쿼터 동결 등 **인프라 전반에서 발생한 32건의 실시간 서비스 데스크 장애 티켓 및 2-Phase Commit(2PC) 승인 대기 이력**으로 구성되어 있습니다.

실습 환경 초기화 스크립트(`scripts/setup_environment.sh`)를 실행하면 활성 Google Cloud 프로젝트를 자동으로 감지하여, 이 100건의 JSON 데이터를 BigQuery `enterprise_finops_gold` 데이터셋 내의 각 테이블(`cloud_billing_export`, `it_security_policy_embeddings`, `itsm_realtime_incidents`)에 100% 자동으로 적재(Seeding)하므로 별도의 수동 데이터 입력 없이 즉시 End-to-End 에이전트 테스트를 수행할 수 있습니다.

---

## ⚡ 4. 빠른 시작 가이드 (Quickstart)

실습 환경을 빠르게 구성하고 로컬 웹 스튜디오와 자동 검증 스위트를 즉시 실행하려면 아래 명령어를 순서대로 입력합니다:

```bash
# 0. [사전 필수] Git CLI 및 Google Cloud SDK (gcloud) 설치 확인 & 자격 증명 인증
# (Cloud Shell에는 git과 gcloud가 기본 내장되어 있습니다. 로컬 PC / 신규 VM인 경우 아래 확인)
git --version || sudo apt-get update && sudo apt-get install -y git
gcloud --version || (curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts && export PATH="$HOME/google-cloud-sdk/bin:$PATH")
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>

# 1. 저장소 복제 및 디렉토리 이동
# (Private 저장소인 경우 GitHub CLI `gh auth login` 또는 SSH Key 인증이 필요하며, Public 전환 시 인증 없이 즉시 복제됩니다)
git clone https://github.com/rhkim77/gemini-enterprise-adk-lab.git
cd gemini-enterprise-adk-lab

# 2. 환경변수(.env) 파일 설정 (현재 활성 GCP 프로젝트 ID 자동 바인딩)
cp .env.example .env
export PROJECT_ID=$(gcloud config get-value project)
sed -i "s/<YOUR_PROJECT_ID>/${PROJECT_ID}/g" .env

# 3. 원클릭 부트스트랩 실행 (gcloud SDK 자동 검증, 100건 데이터셋 BigQuery 적재 및 .venv 설치)
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# 4. Cymbal Enterprise AI Hub 자동 검증 테스트 스위트 실행 (8개 항목 / 100건 데이터셋 전체 PASS 확인)
.venv/bin/python3 scripts/validate_agent.py

# 5. Dual-Contract FastAPI 서버 및 대화형 웹 스튜디오 구동 (포트 8000)
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```

* **로컬 브라우저 접속**: `http://localhost:8000/studio` (Google Cloud Shell의 경우 우측 상단 **[웹 미리보기 → 포트 8000에서 미리보기]** 클릭)
* **A2A Agent Card JSON 확인**: `http://localhost:8000/.well-known/agent-card.json`

---

## 📚 5. Cymbal Enterprise AI Hub 단계별 구축 가이드 (총 5개 모듈)

각 가이드 문서에는 단계별 명령어와 함께 구축 완료 여부를 즉시 검증할 수 있는 **자동 검증 스위트(`validate_agent.py`)** 스크립트가 포함되어 있습니다.

> 🔧 **실습 중 막히셨나요?** 증상별 원인과 해결 방법을 정리한 **[트러블슈팅 가이드](labs/TROUBLESHOOTING.md)**를 참고하세요. 대부분의 문제는 딥 헬스체크 한 줄(`curl -s "http://localhost:8000/healthz?deep=true" | jq .`)로 원인이 특정됩니다.

| 단계 (Module) | 가이드 문서 링크 | 핵심 구현 목표 및 검증 항목 | 소요 시간 |
| :--- | :--- | :--- | :--- |
| **Task 1 (Lab 00)** | [**Lab 00: 환경 설정 및 원클릭 부트스트랩**](labs/00_prerequisites_and_setup.md) | • `.env` 환경변수 설정 및 GCP 필수 API 5종 활성화<br/>• `setup_environment.sh` 실행 (`scripts/seed_bigquery.py`를 통해 **총 100건의 엔터프라이즈 실전 데이터셋** BigQuery/로컬 자동 시딩)<br/>• `uv` / `venv` 기반 의존성 고정 — 버전은 [`requirements.txt`](requirements.txt)가 단일 기준(SSOT) (`[확인됨 / Verified]`) | **15분** |
| **Task 2 (Lab 01)** | [**Lab 01: ADK 2.0 에이전트 및 3대 도구 구현**](labs/01_adk_agent_and_tools.md) | • `app/agent.py` 코디네이터 에이전트(단일/병렬 디스패치 프롬프트) 및 자정 기준 캐시 무효화 콜백(`before_agent_callback`) 구현<br/>• 3대 도구(`finops_bq_tool`, `it_policy_rag_tool` 한국어/영어 바이링구얼 코사인 유사도, `it_servicedesk_tool` OAuth 2.0 신원 위임) 연동 검증<br/>• `scripts/validate_agent.py` 자동 검증 테스트 스위트 **10/10 PASS (100 Records Verified)** 달성 | **30분** |
| **Task 3 (Lab 02)** | [**Lab 02: Dual-Contract 서빙 & 웹 스튜디오 테스트**](labs/02_dual_contract_and_studio.md) | • `app/fast_api_app.py`를 통해 **ADK `InMemoryRunner`** 구동 및 **A2A(`/.well-known/agent-card.json`)**와 **Reasoning Engine(`/api/reasoning_engine`)** 동시 마운트<br/>• 로컬 웹 스튜디오(`/studio`, 포트 8000)에서 5대 검증 시나리오(Plotly 차트, 윈도우 스티칭 Citation, OAuth 2.0 2PC 티켓 감사, 병렬 감사, 도메인 외 거절) 대화형 테스트 | **25분** |
| **Task 4 (Lab 03)** | [**Lab 03: 클라우드 배포 (Cloud Run & Agent Engine)**](labs/03_cloud_deployment.md) | • **배포 트랙 A (Cloud Run)**: 컨테이너 이미지 빌드 후 Cloud Run 배포 및 외부 HTTPS A2A Agent Card URL 확보<br/>• **배포 트랙 B (Vertex AI Agent Engine)**: `vertexai.agent_engines.create(AdkApp)`를 통한 완전 관리형 런타임 배포 | **20분** |
| **Task 5 (Lab 04)** | [**Lab 04: Gemini Enterprise 연동 & OAuth 2.0 설정**](labs/04_gemini_enterprise_integration.md) | • **OAuth 2.0 권한 위임**: Discovery Engine API에 `serverSideOauth2` 리소스 등록 (`redirect_uri`: `https://vertexaisearch.cloud.google.com/oauth-redirect`)<br/>• **Gemini Enterprise 콘솔 등록 (2가지 트랙 비교 실습)**:<br/>  - *Track A (Custom agent via A2A)*: Cloud Run 에이전트 카드 등록 (`defaultInputModes: ["text/plain"]` 스키마 보정 내장)<br/>  - *Track B (Custom agent via Agent Engine)*: Reasoning Engine ID 직접 바인딩<br/>• **E2E 시연 및 Teardown**: Gemini Enterprise 웹 앱에서 통합 질의 테스트 후 `teardown.sh` 리소스 정리 | **30분** |

---

## 🧹 6. 실습 리소스 정리 (Teardown)

실습을 모두 마친 후 불필요한 클라우드 과금을 방지하기 위해 정리 스크립트를 실행합니다:

```bash
chmod +x scripts/teardown.sh
./scripts/teardown.sh
```
* **삭제 대상**: BigQuery 데이터셋 2개(`enterprise_finops_gold`, `agent_telemetry`), Cloud Run 컨테이너 서비스(`enterprise-hub-agent`).

---

## 📜 7. 라이선스
Copyright 2026 Google LLC. Apache License 2.0 규정에 따라 제공됩니다.
