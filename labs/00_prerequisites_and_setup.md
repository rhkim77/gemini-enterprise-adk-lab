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
4. Python 가상환경(`.venv`)을 구성하고 `google-adk==2.8.0` 및 `mcp<2.0.0` 버전을 설치하여 MCP 세션 모듈 충돌을 방지합니다.

---

## 🛠️ Step 1: 실습 디렉토리 이동 및 프로젝트 ID 확인

터미널(또는 Google Cloud Shell)을 열고 실습 디렉토리로 이동합니다:

```bash
cd gemini-enterprise-adk-lab
```

현재 활성화된 Google Cloud Project ID를 확인합니다:

```bash
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
* `ITSM_MODE="MOCK"`이 기본 설정되어 있어, 별도의 외부 ITSM 과금 없이 로컬/Cloud Shell에서 OAuth 2.0 신원 위임 및 2PC HITL 티켓 생성을 100% 동일하게 검증할 수 있습니다.

---

## 🚀 Step 3: 원클릭 부트스트랩 스크립트 실행 (`setup_environment.sh`)

스크립트에 실행 권한을 부여하고 실행합니다:

```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

### 스크립트 내부 자동 수행 내역
1. **GCP 필수 API 활성화**: Vertex AI, Discovery Engine(Gemini Enterprise), BigQuery, Cloud Run, Cloud Build API를 활성화합니다.
2. **BigQuery 데이터셋 생성**: `enterprise_finops_gold` (비즈니스 데이터 및 벡터 임베딩) 및 `agent_telemetry` (에이전트 실행 감사 로그) 데이터셋을 생성합니다.
3. **핵심 테이블 100건 데이터 시딩(Seeding)**:
   - `enterprise_finops_gold.cloud_billing_export` (**32건**): 8개 엔터프라이즈 부서 산하 32개 프로젝트의 월 예산, 당월 지출액, 표준 공식이 적용된 예산 소진율(Burn Rate %), 유휴 GPU 낭비 비용 데이터를 적재합니다 (`PROJ-AI-PROD-01`은 `132.37% CRITICAL_OVERRUN` 상태).
   - `enterprise_finops_gold.it_security_policy_embeddings` (**36건**): **인접 청크 윈도우 스티칭(`N-1 ~ N+1`)** 검증을 위해 12대 보안/운영 규정(`SEC-POL-2026-FW`, `FIN-POL-2026-GPU`, `NET-POL-2026-PSCI`, `DATA-POL-2026-DLP` 등) × 3개 연속 청크 = 총 36개 청크를 적재합니다.
   - `enterprise_finops_gold.itsm_realtime_incidents` (**32건**): 실시간 서비스 데스크 장애 티켓(`INC-2026-88401` ~ `INC-2026-88432`) 및 2PC 락 상태를 적재합니다.
4. **Python 가상환경 구축**: `uv` (또는 `python3 -m venv`)를 통해 `.venv` 가상환경을 생성하고 필수 패키지를 설치합니다.

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

> **🎉 Task 1 완료!** 이제 [Lab 01: ADK 2.0 에이전트 및 3대 도구 게이트웨이 구현](01_adk_agent_and_tools.md)으로 이동하세요.
