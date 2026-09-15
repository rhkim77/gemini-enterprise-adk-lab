# Lab 02 (Task 3): Dual-Contract 서빙 레이어 & 대화형 웹 스튜디오 테스트

* **실습 ID**: `GSP-ADK-GE-2026` — Task 3 / 5
* **소요 시간**: 약 25분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. `app/fast_api_app.py`에 구현된 **Dual-Contract 서빙 아키텍처**의 동작 원리를 이해합니다.
2. 단일 FastAPI 컨테이너가 다음 3가지 인터페이스를 동시에 제공하는 것을 확인합니다:
   - **오픈 표준 A2A 프로토콜 엔드포인트** (`GET /.well-known/agent-card.json` & `POST /a2a/enterprise_hub_agent`)
   - **Vertex AI Reasoning Engine 계약 엔드포인트** (`POST /api/reasoning_engine` & `POST /api/stream_reasoning_engine`)
   - **대화형 운영 웹 스튜디오 UI** (`GET /studio` & `POST /api/chat`)
3. 로컬 서버를 구동하고 웹 스튜디오 UI에서 Plotly 시각화와 윈도우 스티칭 근거 링크를 확인합니다.

---

## 🔍 Step 1: Dual-Contract 어댑터 및 A2A 스키마 보정 확인 (`app/app_utils/a2a.py`)

`app/app_utils/a2a.py` 파일을 확인합니다:

```bash
cat app/app_utils/a2a.py
```

### ⚠️ Gemini Enterprise A2A 등록 시 핵심 주의사항(Gotcha) 자동 해결
Gemini Enterprise 콘솔에서 **"Custom agent via A2A"**로 에이전트를 등록할 때, `agent-card.json` 내 `defaultInputModes`나 `defaultOutputModes` 값이 `"text"`로 되어 있으면 스키마 검증 에러가 발생하며 등록이 거부됩니다 (`[확인됨 / Verified: GE Custom Agents Integration Guide]`).

본 프로젝트의 `app/app_utils/a2a.py`는 이를 표준 MIME 타입인 **`"text/plain"`**으로 사전 고정하여 별도 수동 편집 없이 즉시 Gemini Enterprise 검증을 통과하도록 설계되어 있습니다:
```json
"defaultInputModes": ["text/plain"],
"defaultOutputModes": ["text/plain"]
```

---

## 🚀 Step 2: Dual-Contract FastAPI 서버 구동

`.venv` 가상환경의 `uvicorn`을 사용하여 포트 `8000`번으로 서버를 실행합니다:

```bash
.venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &
sleep 2
```

---

## 🧪 Step 3: `curl`을 통한 두 가지 엔터프라이즈 계약 검증

### 3.1 A2A 에이전트 카드 조회 (`GET /.well-known/agent-card.json`)
```bash
curl -s http://localhost:8000/.well-known/agent-card.json | jq .
```
출력된 JSON 내에 `"defaultInputModes": ["text/plain"]`과 3가지 스킬 명세가 포함되어 있는지 확인합니다.

### 3.2 A2A JSON-RPC 원격 호출 검증 (`POST /a2a/enterprise_hub_agent`)
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

### 3.3 Vertex AI Reasoning Engine 동기 호출 계약 검증 (`POST /api/reasoning_engine`)
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

## 🖥️ Step 4: 대화형 운영 웹 스튜디오 UI(`/studio`) 테스트

웹 브라우저에서 아래 주소로 접속합니다:
* **로컬 / Cloud Shell 웹 미리보기**: `http://localhost:8000/studio`
* **Cloudtop 프록시 접속 URL**: `http://<YOUR_HOSTNAME>.c.googlers.com:8000/studio`

화면 상단의 **4가지 Qwiklabs 검증 시나리오 버튼**을 차례대로 클릭하여 결과를 확인합니다:
1. **📊 1. FinOps Burn Rate (Gateway 1)**: `PROJ-AI-PROD-01`의 예산 초과(`132.37%`) Plotly 막대그래프 및 실행된 GoogleSQL 쿼리를 확인합니다.
2. **📜 2. Security Policy RAG + Stitching (Gateway 2)**: `N-1 ~ N+1` 인접 청크가 결합된 방화벽 SOP 전문과 클릭 가능한 HTTPS GCS PDF 링크를 확인합니다.
3. **⚡ 3. Parallel Dispatch Audit (GW1 + GW3)**: 단일 턴에서 BigQuery FinOps와 ITSM 티켓 현황을 동시 조회(`PARALLEL_DISPATCH`)하는 것을 확인합니다.
4. **🛡️ 4. Out-of-Domain Refusal Gate**: 사내 규정 외 질문이 완벽히 차단되는지 확인합니다.

---

## ✅ Check my progress: Task 3 완료 검증

Health Check 엔드포인트를 호출하여 두 계약(`A2A`, `ReasoningEngine`)이 모두 활성 상태인지 확인합니다:

```bash
curl -s http://localhost:8000/healthz
```

**정상 출력 예시:**
```json
{"status":"healthy","agent":"enterprise_hub_agent","contracts":["A2A","ReasoningEngine"]}
```

확인 후 다음 단계 배포를 위해 로컬 백그라운드 서버를 종료합니다:
```bash
pkill -f "uvicorn app.fast_api_app:app" || true
```

> **🎉 Task 3 완료!** 이제 [Lab 03: 클라우드 배포 (Cloud Run & Agent Engine)](03_cloud_deployment.md)으로 이동하세요.
