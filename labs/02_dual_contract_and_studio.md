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

`.venv` 가상환경의 `uvicorn`을 사용하여 포트 `8000`번으로 서버를 실행합니다:

```bash
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
sleep 2
```

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

---

## ✅ Check my progress: Task 3 완료 검증

Health Check 엔드포인트를 호출하여 ADK Runner 활성화 여부(`adk_runner_active: true`)와 두 계약(`A2A`, `ReasoningEngine`)이 모두 정상인지 확인합니다:

```bash
curl -s http://localhost:8000/healthz | jq .
```

**정상 출력 예시:**
```json
{
  "status": "healthy",
  "agent": "enterprise_hub_agent",
  "adk_runner_active": true,
  "contracts": [
    "A2A",
    "ReasoningEngine"
  ]
}
```

확인 후 다음 단계 배포를 위해 로컬 백그라운드 서버를 종료합니다:
```bash
pkill -f "uvicorn app.fast_api_app:app" || true
```

> **🎉 Task 3 완료!** 이제 [Lab 03: 클라우드 배포 (Cloud Run & Agent Engine)](03_cloud_deployment.md)으로 이동하세요.
