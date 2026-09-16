# Lab 00 (Task 1): 환경 설정 및 원클릭 데이터 부트스트랩

* **실습 ID**: `Cymbal Enterprise AI Hub` — Task 1 / 5
* **소요 시간**: 약 15분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. Google Cloud 환경을 초기화하고 `.env` 파일에 프로젝트 환경변수를 구성합니다.
2. 필수 Google Cloud API 5종(`aiplatform`, `discoveryengine`, `bigquery`, `run`, `cloudbuild`)을 활성화합니다.
3. 원클릭 부트스트랩 스크립트(`scripts/setup_environment.sh`)를 실행하여 **BigQuery FinOps 청구 원장(Gold Ledger, 32건)**, **IT 보안 규정 Vector Embedding 테이블(36건)**, 그리고 **실시간 ITSM 인시던트 테이블(32건)** 등 총 100건의 엔터프라이즈 실전 데이터셋을 자동 시딩합니다 (`[확인됨 / Verified: scripts/seed_bigquery.py]`).
4. Python 가상환경(`.venv`)을 구성하고 `requirements.txt`에 고정된 의존성(`google-adk` 2.8 계열, `mcp` 1.x)을 설치하여 MCP 세션 모듈 충돌을 방지합니다. **버전은 `requirements.txt`가 단일 기준(SSOT)이며**, 문서의 다른 곳에 적힌 버전과 다를 경우 항상 `requirements.txt`가 우선합니다.

---

## 🛠️ Step 0: Google Cloud SDK (`gcloud`) 설치 확인 및 인증 (사전 필수 작업)

프로젝트 ID 확인(`gcloud config get-value project`), GCP API 활성화, 그리고 Python SDK(`google-cloud-bigquery`, `google-adk`)를 통한 BigQuery 100건 데이터 적재를 수행하려면 **Google Cloud SDK (`gcloud` 및 `bq` CLI)**가 우선 설치 및 인증되어 있어야 합니다 (`[확인됨 / Verified]`).

> 💡 **Google Cloud Shell 사용자**: Cloud Shell에는 Google Cloud SDK와 자격 증명이 이미 기본 내장되어 있으므로 바로 **Step 1**으로 이동하셔도 됩니다. 로컬 PC, 사내 Cloudtop, 또는 신규 Linux VM 환경인 경우 아래 절차를 먼저 수행하세요.

### 1) `gcloud` SDK 설치 여부 및 PATH 확인
```bash
# gcloud 버전 확인 (미설치 또는 PATH 누락 시 아래 설치 명령어 실행)
gcloud --version
```
만약 `command not found` 에러가 발생한다면 아래 원클릭 명령어로 Google Cloud SDK를 설치하고 `PATH`에 등록합니다:
```bash
# Linux / macOS 환경 Google Cloud SDK 무인 설치 및 PATH 적용
curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="$HOME"
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
```

### 2) CLI 로그인 및 Application Default Credentials (ADC) 인증
`gcloud` CLI 명령어뿐만 아니라, Python 기반 BigQuery 적재 스크립트(`scripts/seed_bigquery.py`) 및 ADK 에이전트가 Google Cloud API를 호출할 수 있도록 **반드시 아래 두 가지 인증을 모두 완료**합니다:

```bash
# 1. gcloud CLI 사용자 계정 로그인
gcloud auth login

# 2. [필수] Python SDK(BigQuery / Vertex AI / ADK)용 Application Default Credentials(ADC) 인증
gcloud auth application-default login

# 3. 실습을 진행할 대상 Google Cloud Project ID 설정
gcloud config set project <YOUR_PROJECT_ID>
```

### 3) 보조 CLI 도구 확인 (`jq`)

Lab 02·03에서 JSON 응답을 검증할 때 `jq`를 사용합니다. Cloud Shell에는 기본 내장되어 있습니다.

```bash
jq --version
```

`command not found`가 발생하면 설치합니다:
```bash
sudo apt-get install -y jq   # Debian / Ubuntu
brew install jq              # macOS
```

> 💡 `uv`는 **선택 사항**입니다. 설치되어 있으면 부트스트랩 스크립트가 자동으로 사용하고, 없으면 표준 `python3 -m venv`로 폴백하므로 별도 설치가 필요하지 않습니다.

---

## 🛠️ Step 1: 실습 디렉토리 이동 및 프로젝트 ID 확인

터미널을 열고 실습 디렉토리로 이동한 뒤, `gcloud`에 설정된 현재 프로젝트 ID를 환경변수로 불러옵니다:

```bash
cd gemini-enterprise-adk-lab

export PROJECT_ID=$(gcloud config get-value project)
echo "현재 활성 GCP Project ID: ${PROJECT_ID}"
```

---

## ⚙️ Step 2: `.env` 환경변수 파일 구성

환경변수 템플릿 파일(`.env.example`)을 복사하여 `.env` 파일을 생성하고, `<YOUR_PROJECT_ID>`를 현재 프로젝트 ID로 치환합니다:

```bash
cp .env.example .env
sed -i "s/<YOUR_PROJECT_ID>/${PROJECT_ID}/g" .env
```

생성된 `.env` 파일을 확인합니다:
```bash
cat .env
```
* `USE_ADK_LLM="true"`가 기본 설정되어 있어, GCP 인증 또는 Gemini API 키가 활성화된 환경에서는 실제 **Google ADK `InMemoryRunner` + `gemini-2.5-flash` 모델**이 Tool Calling을 수행합니다 (오프라인 환경에서는 결정론적 하이브리드 라우터로 자동 폴백).
* ⚠️ **`GOOGLE_GENAI_USE_VERTEXAI="TRUE"` 및 `GOOGLE_CLOUD_LOCATION="us-central1"`은 필수 항목입니다.** 이 두 값이 없으면 `google-genai` SDK가 Vertex AI(ADC 인증)가 아닌 **Gemini Developer API 모드**로 부팅되어 `ValueError: No API key was provided.` 예외가 발생하고, 애플리케이션은 이를 내부에서 흡수한 뒤 **조용히 결정론적 라우터로 폴백**합니다 (실제 ADK LLM이 동작하지 않음). 이전 버전의 `.env`를 재사용하는 경우 반드시 두 줄을 추가하세요.
* `ITSM_MODE="MOCK"`이 기본 설정되어 있어, 별도의 외부 ITSM 과금 없이 로컬/Cloud Shell에서 OAuth 2.0 신원 위임 및 2PC HITL 티켓 생성을 100% 동일하게 검증할 수 있습니다.

---

## 🚀 Step 3: 원클릭 부트스트랩 스크립트 실행 (`setup_environment.sh`)

스크립트에 실행 권한을 부여하고 실행합니다:

```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

> [!TIP]
> **재실행 안전(Idempotent)**: 이 스크립트는 몇 번을 다시 실행해도 안전합니다. BigQuery 테이블은 매번 덮어쓰기(`WRITE_TRUNCATE`)되므로 **항상 정확히 32 / 36 / 32건(총 100건)** 이 유지되며, 이미 생성된 `.venv`와 활성화된 API는 자동으로 건너뜁니다. 중간에 오류가 났다면 원인을 해결한 뒤 그냥 처음부터 다시 실행하세요.

### 스크립트 내부 자동 수행 내역
스크립트는 **Preflight → Step 1~4** 순서로 실행되며, 각 단계는 실패 시 명확한 원인 메시지를 출력하고 중단됩니다.

0. **[Preflight] `gcloud` SDK 및 인증 검증**: Google Cloud SDK 설치 여부를 확인하고(미검출 시 `~/google-cloud-sdk`, `/opt`, `/usr/local/bin` 등 표준 경로를 자동 탐색해 `PATH`에 추가), Application Default Credentials(ADC) 인증 상태와 활성 `PROJECT_ID`를 점검한 뒤 `.env` 파일을 자동 구성합니다.
1. **[Step 1/4] GCP 필수 API 활성화**: Vertex AI, Discovery Engine(Gemini Enterprise), BigQuery, Cloud Run, Cloud Build API를 활성화합니다 (`PROJECT_ID` 미설정 시 로컬 모드로 스킵).
2. **[Step 2/4] Python 가상환경 구축**: `uv` (또는 `python3 -m venv`)를 통해 `.venv` 가상환경을 생성하고 `requirements.txt`의 필수 패키지(`google-adk`, `google-genai`, `fastapi` 등)를 설치합니다.
3. **[Step 3/4] BigQuery 데이터셋 생성 및 핵심 테이블 100건 데이터 시딩(Seeding)**: `enterprise_finops_gold` (비즈니스 데이터 및 벡터 임베딩), `agent_telemetry` (에이전트 실행 감사 로그) 데이터셋을 생성한 뒤 아래 3개 테이블을 적재합니다.
   - `enterprise_finops_gold.cloud_billing_export` (**32건**): 8개 엔터프라이즈 부서 산하 32개 프로젝트의 월 예산, 당월 지출액, 표준 공식이 적용된 예산 소진율(Burn Rate %), 유휴 GPU 낭비 비용 데이터를 적재합니다 (`PROJ-AI-PROD-01`은 `132.37% CRITICAL_OVERRUN` 상태).
   - `enterprise_finops_gold.it_security_policy_embeddings` (**36건**): **인접 청크 윈도우 스티칭(`N-1 ~ N+1`)** 검증을 위해 12대 보안/운영 규정(`SEC-POL-2026-FW`, `FIN-POL-2026-GPU`, `NET-POL-2026-PSCI`, `DATA-POL-2026-DLP` 등) × 3개 연속 청크 = 총 36개 청크를 적재합니다.
   - `enterprise_finops_gold.itsm_realtime_incidents` (**32건**): 실시간 서비스 데스크 장애 티켓(`INC-2026-88401` ~ `INC-2026-88432`) 및 2PC 락 상태를 적재합니다.
4. **[Step 4/4] 자동 검증 스위트 실행**: `scripts/validate_agent.py`를 자동 실행하여 3대 도구 게이트웨이, OAuth 2.0 위임, ADK 콜백 계약, 그리고 문서 드리프트까지 포함한 **10개 테스트**를 즉시 검증합니다. (별도로 수동 실행할 필요 없이 부트스트랩 종료 시점에 `10 PASSED, 0 FAILED` 결과를 확인할 수 있습니다.)

---

## ✅ Check my progress: Task 1 완료 검증

아래 BigQuery 확인 쿼리를 실행하여 3개 테이블(총 100건)이 정상적으로 생성 및 적재되었는지 확인합니다:

```bash
bq query --project_id=${PROJECT_ID} --use_legacy_sql=false \
"SELECT '1_cloud_billing_export' AS table_name, COUNT(*) AS row_count FROM \`enterprise_finops_gold.cloud_billing_export\`
 UNION ALL
 SELECT '2_it_security_policy_embeddings', COUNT(*) FROM \`enterprise_finops_gold.it_security_policy_embeddings\`
 UNION ALL
 SELECT '3_itsm_realtime_incidents', COUNT(*) FROM \`enterprise_finops_gold.itsm_realtime_incidents\`
 ORDER BY table_name;"
```

**정상 출력 예시 (총 100건):**
```text
+---------------------------------+-----------+
|           table_name            | row_count |
+---------------------------------+-----------+
| 1_cloud_billing_export          |        32 |
| 2_it_security_policy_embeddings |        36 |
| 3_itsm_realtime_incidents       |        32 |
+---------------------------------+-----------+
```

> 🔧 막히셨나요? → [트러블슈팅 가이드](TROUBLESHOOTING.md)

> **🎉 Task 1 완료!** 이제 [Lab 01: ADK 2.0 에이전트 및 3대 도구 게이트웨이 구현](01_adk_agent_and_tools.md)으로 이동하세요.
