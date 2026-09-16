# Lab 02 (Task 3): Dual-Contract 서빙 레이어 & 대화형 웹 스튜디오 테스트

* **실습 ID**: `Cymbal Enterprise AI Hub` — Task 3 / 5
* **소요 시간**: 약 25분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. `app/fast_api_app.py`에 구현된 **Google ADK 2.0 `InMemoryRunner` 통합 및 Dual-Contract 서빙 아키텍처**의 동작 원리를 이해합니다.
2. 단일 FastAPI 컨테이너가 다음 3가지 인터페이스를 동시에 제공하며 **OAuth 2.0 `Authorization: Bearer` 헤더**를 추출해 도구까지 전달하는 것을 확인합니다:
   - **오픈 표준 A2A 프로토콜 엔드포인트** (`GET /.well-known/agent-card.json` & `POST /a2a/enterprise_hub_agent`)
   - **Vertex AI Reasoning Engine 계약 엔드포인트** (`POST /api/reasoning_engine` & `POST /api/stream_reasoning_engine`)
   - **대화형 운영 웹 스튜디오 UI** (`GET /studio` & `POST /api/chat`)
3. 로컬 서버를 구동하고 웹 스튜디오 UI에서 5대 검증 시나리오(Plotly 차트, 한국어/영어 윈도우 스티칭 Citation, OAuth 2.0 티켓 감사, 병렬 감사, 도메인 외 거절)를 대화형으로 테스트합니다.

---

## 🔍 Step 1: Dual-Contract 어댑터 및 OAuth 2.0 헤더 추출 확인 (`app/app_utils/a2a.py`)

`app/app_utils/a2a.py` 파일을 확인합니다:

```bash
cat app/app_utils/a2a.py
```

### ⚠️ 핵심 엔지니어링 포인트 2가지
1. **Gemini Enterprise A2A 등록 스키마 보정 (`text/plain`)**:
   Gemini Enterprise 콘솔에서 **"Custom agent via A2A"**로 에이전트를 등록할 때, `agent-card.json` 내 입출력 모드가 `"text"`로 되어 있으면 스키마 검증 에러가 발생합니다. 본 프로젝트는 이를 표준 MIME 타입인 **`"text/plain"`**으로 고정하여 즉시 검증을 통과하도록 설계되어 있습니다:
   ```json
   "defaultInputModes": ["text/plain"],
   "defaultOutputModes": ["text/plain"]
   ```
2. **OAuth 2.0 End-User Identity Delegation 추출 (`_extract_oauth_from_request`)**:
   Gemini Enterprise가 `serverSideOauth2` 설정을 통해 전달하는 `Authorization: Bearer <access_token>` 헤더 및 사용자 이메일을 추출하여 `set_current_oauth_context()`를 통해 ADK 실행 컨텍스트 및 `it_servicedesk_tool`로 전달합니다.

---

## 🚀 Step 2: Dual-Contract FastAPI 서버 구동

> 🔄 **새 터미널에서 시작하셨나요?** 이전 랩의 셸 변수는 사라집니다. 아래를 먼저 실행하세요:
> ```bash
> cd gemini-enterprise-adk-lab
> export PROJECT_ID=$(gcloud config get-value project)
> ```

`.venv` 가상환경의 `uvicorn`을 사용하여 포트 `8000`번으로 서버를 실행합니다:

```bash
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
sleep 2
```

> [!TIP]
> `&`로 띄운 백그라운드 프로세스는 **셸 세션에 종속**됩니다. Cloud Shell 탭을 닫거나 세션이 재시작되면 서버도 함께 종료됩니다. **서버 전용 탭을 하나 열어 `&` 없이 포그라운드로 실행**하고, 아래 `curl` 테스트는 별도 탭에서 수행하면 오류 로그도 실시간으로 볼 수 있어 훨씬 편리합니다.
>
> `Address already in use` 오류가 발생하면 이전 랩의 프로세스가 살아 있는 것입니다: `pkill -f "uvicorn app.fast_api_app:app"`

---

## 🧪 Step 3: `curl`을 통한 두 가지 엔터프라이즈 계약 및 OAuth 2.0 위임 검증

### 3.1 A2A 에이전트 카드 조회 (`GET /.well-known/agent-card.json`)
```bash
curl -s http://localhost:8000/.well-known/agent-card.json | jq .
```
출력된 JSON 내에 `"defaultInputModes": ["text/plain"]`, `"authentication": {"schemes": ["Bearer", "OAuth2"]}` 및 3가지 스킬 명세가 포함되어 있는지 확인합니다.

### 3.2 OAuth 2.0 토큰을 포함한 A2A JSON-RPC 원격 호출 검증 (`POST /a2a/enterprise_hub_agent`)
```bash
curl -s -X POST http://localhost:8000/a2a/enterprise_hub_agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-oauth2-token-cymbal-demo" \
  -H "X-Requester-Email: architect@cymbal.enterprise" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-rpc-101",
    "params": {
      "message": {
        "parts": [{"type": "text", "text": "Open a firewall ticket for PROJ-AI-PROD-01 to enable PSC-I southbound access"}]
      }
    }
  }' | jq .
```
응답 내 `"metadata": {"oauth2_delegated": true}`와 함께 티켓의 `"Authenticated Requester (OAuth 2.0): architect@cymbal.enterprise"`가 기록된 것을 확인합니다.

### 3.3 Vertex AI Reasoning Engine 동기 호출 계약 검증 (`POST /api/reasoning_engine`)
```bash
curl -s -X POST http://localhost:8000/api/reasoning_engine \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-oauth2-token-cymbal-demo" \
  -d '{
    "class_method": "query",
    "input": {
      "input": "Audit live ITSM incidents and compare against FinOps burn rate for PROJ-AI-PROD-01"
    }
  }' | jq .
```

---

## 🖥️ Step 4: 대화형 운영 웹 스튜디오 UI(`/studio`) 테스트

웹 브라우저에서 아래 주소로 접속합니다:
* **로컬 / Cloud Shell 웹 미리보기**: `http://localhost:8000/studio`

화면 상단의 **5가지 Cymbal Enterprise AI Hub 검증 시나리오 버튼**을 차례대로 클릭하여 결과를 확인합니다:
1. **📊 1. FinOps Burn Rate (Gateway 1)**: `PROJ-AI-PROD-01`의 예산 초과(`132.37%`) Plotly 막대그래프 및 실행된 GoogleSQL 쿼리를 확인합니다.
2. **📜 2. Security Policy RAG + Stitching (Gateway 2 - KR/EN)**: 한국어 질의(*"SEC-POL-2026-FW 보안 규정에 따른 방화벽 포트 오픈 절차 알려줘"*)에 대해 코사인 유사도(`>= 0.70`) 검증 후 `N-1 ~ N+1` 인접 청크가 결합된 SOP 전문과 HTTPS GCS PDF 링크를 확인합니다.
3. **🎫 3. 2PC HITL Ticket + OAuth Audit (Gateway 3)**: OAuth 2.0 `Bearer` 토큰이 감사(`VERIFIED_BEARER_TOKEN`)되어 요청자 신원(`developer@cymbal.enterprise`)이 기록된 2PC 락 티켓 생성을 확인합니다.
4. **⚡ 4. Parallel Dispatch Audit (GW1 + GW3)**: 단일 턴에서 BigQuery FinOps와 ITSM 티켓 현황을 동시 조회(`PARALLEL_DISPATCH`)하는 것을 확인합니다.
5. **🛡️ 5. Out-of-Domain Refusal Gate**: 사내 규정 외 질문(*"사무실 에스프레소 커피머신 석회 제거 청소 방법 알려줘"*)이 완벽히 차단되는지 확인합니다.

### ✅ 시나리오별 합격 판정 기준

"잘 나온 것 같다"가 아니라 **아래 값이 화면에 그대로 보이는지**로 판정하세요.

| # | 화면에서 반드시 확인되어야 하는 값 |
|---|---|
| 1 | 예산 소진율 **`132.37%`** + Engine 배지 = **`ADK_2.0_RUNNER`** |
| 2 | 답변이 **한국어**일 것 + `SEC-POL-2026-FW-v2.pdf` 링크 + 3개 청크(`[PRE-REQUISITE SAFETY CHECK]`·`[EXECUTION SOP]`·`[POST-CHANGE AUDIT]`)가 모두 결합되어 출력 |
| 3 | OAuth 배지 = **`VERIFIED_BEARER_TOKEN (developer@cymbal.enterprise)`** + 2PC 락 상태 |
| 4 | 도구 배지에 **`finops_bq_tool`과 `it_servicedesk_tool`이 둘 다** 표시 |
| 5 | **`I cannot find certified corporate IT or security policies for this request in our technical repository.`** — 이 문장 외의 어떠한 추가 설명도 없을 것 |

> [!IMPORTANT]
> **Engine 배지가 `DETERMINISTIC_HYBRID_ROUTER`로 표시된다면 실습이 정상적으로 진행되지 않은 것입니다.** 응답 자체는 그럴듯하게 나오지만 ADK LLM이 아니라 폴백 라우터가 답한 것입니다. 아래 "Check my progress"로 원인을 확인하세요.

> [!NOTE]
> 시나리오 3의 요청자(`developer@cymbal.enterprise`)와 Step 3.2 `curl`의 요청자(`architect@cymbal.enterprise`)는 서로 다릅니다. 이는 **웹 UI 사용자와 외부 A2A 호출자라는 두 개의 서로 다른 신원을 의도적으로 시뮬레이션**한 것이며 오류가 아닙니다.

---

## ✅ Check my progress: Task 3 완료 검증

**딥 헬스체크**(`?deep=true`)를 호출합니다. 이 프로브는 단순히 객체 존재 여부를 보는 것이 아니라 **실제로 에이전트 1턴을 실행**해서 어떤 엔진이 응답했는지를 반환합니다:

```bash
curl -s "http://localhost:8000/healthz?deep=true" | jq .
```

**정상 출력 예시:**
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
  "probe_latency_ms": 1842,
  "adk_runner_active": true
}
```

> [!WARNING]
> **`"status": "degraded"`가 반환된다면 Task 3은 완료되지 않은 것입니다.** 이 경우 응답에 포함된 `last_adk_error`(실패 원인)와 `remediation`(조치 방법) 필드를 확인하세요.
>
> 참고로 `?deep=true` 없이 `/healthz`만 호출하면 `adk_runner_active`가 `null`로 반환됩니다. 이는 버그가 아니라 **거짓 초록불을 주지 않기 위한 의도된 설계**입니다. 얕은 헬스체크는 Runner 객체가 만들어졌는지만 알 수 있을 뿐, 그것이 실제로 동작하는지는 알 수 없습니다.

확인 후 다음 단계 배포를 위해 로컬 백그라운드 서버를 종료합니다:
```bash
pkill -f "uvicorn app.fast_api_app:app" || true
```

> 🔧 막히셨나요? → [트러블슈팅 가이드](TROUBLESHOOTING.md)

> **🎉 Task 3 완료!** 이제 [Lab 03: 클라우드 배포 (Cloud Run & Agent Engine)](03_cloud_deployment.md)으로 이동하세요.
