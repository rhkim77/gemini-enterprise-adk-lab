# Lab 00 (Task 1): 환경 설정 및 원클릭 데이터 부트스트랩

* **실습 ID**: `GSP-ADK-GE-2026` — Task 1 / 5
* **소요 시간**: 약 15분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. Google Cloud 환경을 초기화하고 `.env` 파일에 프로젝트 환경변수를 구성합니다.
2. 필수 Google Cloud API 5종(`aiplatform`, `discoveryengine`, `bigquery`, `run`, `cloudbuild`)을 활성화합니다.
3. 원클릭 부트스트랩 스크립트(`scripts/setup_environment.sh`)를 실행하여 **BigQuery FinOps 청구 원장(Gold Ledger)** 및 **IT 보안 규정 Vector Embedding 테이블**을 자동 생성합니다.
4. Cloudtop Corp Airlock(`gpkg setup` + `uv`) 환경에서 `google-adk==2.8.0` 및 `mcp==1.29.1` 버전을 고정하여 MCP 세션 모듈 충돌을 방지합니다 (`[확인됨 / Verified: CE Engineering Standards]`).

---

## 🛠️ Step 1: 실습 디렉토리 이동 및 프로젝트 ID 확인

터미널(또는 Google Cloud Shell)을 열고 실습 디렉토리로 이동합니다:

```bash
cd /usr/local/google/home/ryunghwa/Dev/GE_test/gemini-enterprise-adk-lab
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
`ITSM_MODE="MOCK"`이 기본 설정되어 있어, 별도의 클라우드 인프라 과금 없이 로컬/Cloud Shell에서 2PC HITL 티켓 생성을 100% 동일하게 검증할 수 있습니다.

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
3. **핵심 테이블 데이터 시딩(Seeding)**:
   - `enterprise_finops_gold.cloud_billing_export`: 프로젝트별 월 예산, 당월 지출액, 표준 공식이 적용된 예산 소진율(Burn Rate %), 유휴 GPU 낭비 비용 데이터를 적재합니다 (`PROJ-AI-PROD-01`은 `132.37% CRITICAL_OVERRUN` 상태).
   - `enterprise_finops_gold.it_security_policy_embeddings`: **인접 청크 윈도우 스티칭(`N-1 ~ N+1`)** 검증을 위해 사전 분할된 사내 방화벽(`SEC-POL-2026-FW`) 및 GPU 쿼터(`FIN-POL-2026-GPU`) 보안 규정 청크를 적재합니다.
4. **Corp Airlock 인증 및 가상환경 구축**: `gpkg setup`으로 Airlock 토큰을 갱신하고 `uv venv .venv` 내부에 필수 패키지를 설치합니다.

---

## ✅ Check my progress: Task 1 완료 검증

아래 BigQuery 확인 쿼리를 실행하여 두 테이블이 정상적으로 생성 및 적재되었는지 확인합니다:

```bash
bq query --project_id=${PROJECT_ID} --use_legacy_sql=false \
"SELECT 'cloud_billing_export' AS table_name, COUNT(*) AS row_count FROM \`enterprise_finops_gold.cloud_billing_export\`
 UNION ALL
 SELECT 'it_security_policy_embeddings', COUNT(*) FROM \`enterprise_finops_gold.it_security_policy_embeddings\`;"
```

**정상 출력 예시:**
```text
+-------------------------------+-----------+
|          table_name           | row_count |
+-------------------------------+-----------+
| cloud_billing_export          |         3 |
| it_security_policy_embeddings |         4 |
+-------------------------------+-----------+
```

> **🎉 Task 1 완료!** 이제 [Lab 01: ADK 2.0 에이전트 및 3대 도구 게이트웨이 구현](01_adk_agent_and_tools.md)으로 이동하세요.
