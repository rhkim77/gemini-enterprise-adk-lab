# 🔧 트러블슈팅 가이드 (Troubleshooting Guide)

> `Cymbal Enterprise AI Hub` 실습 중 발생할 수 있는 문제와 해결 방법입니다.
> 아래 증상 목록에서 본인이 마주한 오류 메시지를 찾아 해당 섹션으로 이동하세요.

## 🚦 가장 먼저 실행할 진단 명령어

막혔다면 **무조건 이것부터** 실행하세요. 대부분의 문제는 이 한 줄로 원인이 특정됩니다.

```bash
curl -s "http://localhost:8000/healthz?deep=true" | jq .
```

* `"adk_runner_active": true` → ADK 경로 정상. 문제는 다른 곳에 있습니다 ([§3](#3-bigquery--데이터-문제), [§4](#4-네트워크--포트-문제) 참조).
* `"status": "degraded"` → 응답 안의 **`last_adk_error`와 `remediation` 배열을 그대로 읽으세요.** 조치 방법이 명시되어 있습니다. ([§1](#1-adk-실행-경로-문제) 참조)

> [!IMPORTANT]
> `?deep=true` 없이 `/healthz`만 호출하면 `adk_runner_active`가 `null`로 반환됩니다. 이는 의도된 동작입니다. 얕은 헬스체크는 **Runner 객체가 만들어졌는지**만 알 수 있을 뿐, 실제로 동작하는지는 알 수 없기 때문에 거짓 초록불을 주지 않도록 설계되었습니다.

---

## 1. ADK 실행 경로 문제

에이전트가 응답은 하지만 **실제로는 ADK LLM이 아니라 결정론적 폴백 라우터**가 답하고 있는 상황입니다. 이것이 본 실습에서 가장 흔하고 가장 발견하기 어려운 문제 유형입니다.

### 1-1. `execution_engine`이 `DETERMINISTIC_HYBRID_ROUTER`로 표시됨

| | |
|---|---|
| **증상** | 스튜디오 UI의 Engine 배지가 `DETERMINISTIC_HYBRID_ROUTER`. 또는 `/healthz?deep=true`가 `"status": "degraded"` 반환 |
| **원인** | `.env`에 `GOOGLE_GENAI_USE_VERTEXAI` 누락 (가장 흔함), 또는 ADC 미인증 |

```bash
# 1) .env에 필수 플래그가 있는지 확인
grep -E "GOOGLE_GENAI_USE_VERTEXAI|GOOGLE_CLOUD_LOCATION|USE_ADK_LLM|PROJECT_ID" .env

# 2) 누락되었다면 부트스트랩을 재실행 (자동으로 추가됩니다)
./scripts/setup_environment.sh

# 3) 그래도 안 되면 ADC 재인증
gcloud auth application-default login

# 4) 서버 재시작 (.env는 프로세스 시작 시점에만 읽힙니다)
pkill -f "uvicorn app.fast_api_app:app" || true
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
```

> [!WARNING]
> `.env`를 수정한 뒤에는 **반드시 서버를 재시작**해야 합니다. 환경변수는 프로세스가 뜰 때 한 번만 읽습니다.

### 1-2. `ValueError: No API key was provided.`

| | |
|---|---|
| **원인** | `GOOGLE_GENAI_USE_VERTEXAI="TRUE"`가 없어 `google-genai` SDK가 Vertex AI(ADC 인증)가 아니라 **Gemini Developer API 모드**로 부팅됨 |
| **해결** | [1-1](#1-1-execution_engine이-deterministic_hybrid_router로-표시됨)과 동일 |

`PROJECT_ID`만 설정하면 될 것 같지만 그렇지 않습니다. `google-genai`는 백엔드 선택을 **오직 `GOOGLE_GENAI_USE_VERTEXAI` 플래그로만** 판단합니다.

### 1-3. `DynamicNodeFailError: Dynamic node enterprise_hub_agent failed`

| | |
|---|---|
| **원인** | ADK 1.x가 설치됨. ADK 2.x는 생명주기 콜백을 `callback(callback_context=...)` 형태로 **키워드 호출**하지만 1.x는 계약이 다릅니다 |
| **해결** | 아래 |

```bash
# 설치된 ADK 버전 확인 (2.8.0 이상이어야 함)
uv pip list --python .venv/bin/python3 | grep -E "google-adk|google-genai"

# 버전이 낮다면 requirements.txt 기준으로 재설치
uv pip install --python .venv/bin/python3 -r requirements.txt --upgrade
```

### 1-4. 한국어로 질문했는데 영어로만 답변함

폴백 라우터가 동작 중일 가능성이 높습니다. 폴백 라우터는 키워드 매칭 기반이라 자연스러운 다국어 응답을 생성하지 못합니다. → [1-1](#1-1-execution_engine이-deterministic_hybrid_router로-표시됨) 진단 실행

---

## 2. 인증 · 권한 문제

### 2-1. `google.auth.exceptions.DefaultCredentialsError`

```bash
gcloud auth application-default login
```

> [!NOTE]
> `gcloud auth login`과 `gcloud auth application-default login`은 **서로 다른 인증**입니다. 전자는 `gcloud` CLI용, 후자는 Python SDK(BigQuery·Vertex AI·ADK)용입니다. 실습에는 **둘 다** 필요합니다.

### 2-2. BigQuery `403 Access Denied` / `Permission denied`

```bash
# 현재 인증된 계정과 대상 프로젝트가 일치하는지 확인
gcloud auth list
gcloud config get-value project
grep PROJECT_ID .env
```

세 값이 모두 같아야 합니다. 다르다면 `.env`의 `PROJECT_ID`를 수정하고 서버를 재시작하세요.

### 2-3. Cloud Run 배포 후 `403 Forbidden`

```bash
gcloud run services add-iam-policy-binding enterprise-hub-agent \
  --region="${REGION}" \
  --member="allUsers" \
  --role="roles/run.invoker"
```

> [!CAUTION]
> `allUsers`는 실습 편의를 위한 설정입니다. 실제 고객사 프로덕션 환경에서는 Gemini Enterprise 서비스 에이전트의 서비스 계정만 `roles/run.invoker`로 바인딩하고, 앞단에 Apigee 또는 IAP를 배치하는 것을 권장합니다.

---

## 3. BigQuery · 데이터 문제

### 3-1. `Not found: Dataset <project>:enterprise_finops_gold`

데이터 시딩이 완료되지 않았거나 다른 프로젝트에 시딩된 상태입니다.

```bash
# .env의 PROJECT_ID와 gcloud 활성 프로젝트가 같은지 확인
grep PROJECT_ID .env && gcloud config get-value project

# 일치하면 시딩 재실행
.venv/bin/python3 scripts/seed_bigquery.py
```

### 3-2. 데이터 건수가 100건이 아님 (`COUNT(*)` 불일치)

```bash
.venv/bin/python3 scripts/seed_bigquery.py
```

> [!TIP]
> 시딩 스크립트는 `WRITE_TRUNCATE` 모드로 동작하므로 **몇 번을 재실행해도 항상 정확히 32 / 36 / 32건(총 100건)** 이 유지됩니다. 중복 적재를 걱정하지 않고 자유롭게 재실행하세요.

### 3-3. 검증 스위트 Test 2·3·4·6이 `0.00s`로 통과함

**통과했지만 정상이 아닙니다.** 라이브 BigQuery를 호출하지 못하고 로컬 JSON 미러로 폴백한 상태입니다. 실제 BigQuery 왕복은 보통 **2~4초**가 걸립니다.

→ [2-1](#2-1-googleauthexceptionsdefaultcredentialserror), [3-1](#3-1-not-found-dataset-projectenterprise_finops_gold) 순서로 확인하세요.

---

## 4. 네트워크 · 포트 문제

### 4-1. `Address already in use` / `[Errno 98]`

이전 랩에서 실행한 uvicorn 프로세스가 아직 살아 있습니다.

```bash
pkill -f "uvicorn app.fast_api_app:app" || true
sleep 1
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
```

### 4-2. `curl: (7) Failed to connect to localhost port 8000`

서버가 뜨지 않았거나 시작 중 크래시했습니다. 백그라운드(`&`)로 실행하면 오류 메시지가 묻히므로, **포그라운드로 다시 실행해서 실제 오류를 확인**하세요.

```bash
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```

### 4-3. Cloud Shell 탭을 닫았더니 서버가 죽음

`&`로 띄운 백그라운드 프로세스는 셸 세션에 종속됩니다. **서버 전용 탭을 하나 열어 포그라운드로 실행**하고, `curl` 테스트는 별도 탭에서 수행하는 것을 권장합니다.

---

## 5. CLI 도구 · 환경 문제

### 5-1. `jq: command not found`

```bash
sudo apt-get install -y jq   # Debian / Ubuntu / Cloud Shell
brew install jq              # macOS
```

### 5-2. `gcloud: command not found`

```bash
curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="$HOME"
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
```

### 5-3. 셸 변수(`PROJECT_ID`, `SERVICE_URL`)가 사라짐

새 터미널을 열거나 Cloud Shell 세션이 재시작되면 `export`한 변수는 사라집니다. 각 랩 상단의 **"이어서 진행하기"** 블록을 실행해 복원하세요.

```bash
cd gemini-enterprise-adk-lab
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
# Lab 03 이후라면 배포된 서비스 URL도 복원
export SERVICE_URL=$(gcloud run services describe enterprise-hub-agent \
  --region="${REGION}" --format="value(status.url)" 2>/dev/null)
```

### 5-4. `UserWarning: [EXPERIMENTAL] feature FeatureName.JSON_SCHEMA_FOR_FUNC_DECL is enabled.`

**정상입니다.** `google-genai` SDK가 Function Calling 시 매번 출력하는 안내 메시지이며 무시해도 됩니다.

---

## 6. Gemini Enterprise 연동 문제

### 6-1. GE 콘솔 등록 시 스키마 검증 오류

Agent Card의 입출력 모드가 `"text"`가 아니라 **`"text/plain"`**이어야 합니다.

```bash
curl -s "${SERVICE_URL}/.well-known/agent-card.json" | jq '.defaultInputModes, .defaultOutputModes'
# 기대 출력: ["text/plain"]
```

### 6-2. GE가 답변은 하는데 우리 에이전트가 호출되지 않음

GE 메인 오케스트레이터가 질의를 우리 에이전트로 **라우팅하지 않고 자체 응답**한 경우입니다. 그럴듯한 답변이 나오기 때문에 성공으로 착각하기 쉽습니다.

```bash
# Cloud Run 수신 로그로 실제 호출 여부를 확인 (이것이 유일한 객관적 증거입니다)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="enterprise-hub-agent" AND httpRequest.requestUrl:"/a2a/"' \
  --project="${PROJECT_ID}" --limit=5 --format="value(timestamp,httpRequest.status)"
```

로그가 비어 있다면 Lab 04 Step 2의 **Agent Description**을 확인하세요. 오케스트레이터는 이 설명문만 보고 라우팅을 결정하므로 `BigQuery`, `FinOps`, `burn rate`, `ITSM`, `firewall SOP` 같은 도메인 키워드가 반드시 포함되어야 합니다.

### 6-3. OAuth 2.0 위임이 동작하지 않음 (요청자가 목 계정으로 표시)

GE 콘솔의 에이전트 설정에서 **`serverSideOauth2`(Authorization) 구성이 활성화**되어 있는지 확인하세요. 미설정 시 GE는 `Authorization` 헤더를 전달하지 않으며, 에이전트는 기본 로컬 신원으로 폴백합니다.

---

## 🆘 그래도 해결되지 않는다면

아래 정보를 모아서 실습 진행자(CE)에게 전달하세요.

```bash
{
  echo "=== 환경 ==="
  gcloud --version | head -n 1
  .venv/bin/python3 --version
  uv pip list --python .venv/bin/python3 | grep -E "google-adk|google-genai|google-cloud-bigquery"
  echo "=== .env (민감정보 제외) ==="
  grep -vE "TOKEN|KEY|SECRET" .env
  echo "=== 딥 헬스체크 ==="
  curl -s "http://localhost:8000/healthz?deep=true"
} > lab_diagnostics.txt 2>&1

cat lab_diagnostics.txt
```
