# Lab 03 (Task 4): 클라우드 배포 (Cloud Run 컨테이너 & Vertex AI Agent Engine)

* **실습 ID**: `Cymbal Enterprise AI Hub` — Task 4 / 5
* **소요 시간**: 약 20분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. Dual-Contract 컨테이너 이미지를 빌드하여 **Google Cloud Run**에 서버리스로 배포하고, Gemini Enterprise A2A 등록에 사용할 공인 HTTPS 엔드포인트를 확보합니다.
2. 컨테이너 관리 부담 없이 완전 관리형으로 배포하는 **Vertex AI Agent Engine (`AdkApp`)** 네이티브 배포 패턴을 학습합니다.
3. 배포된 Cloud Run 서비스의 실시간 A2A Agent Card(`/.well-known/agent-card.json`) 응답을 검증합니다.

---

## ☁️ 옵션 A: Google Cloud Run 컨테이너 배포 (A2A 등록 및 웹 스튜디오 동시 활용 권장)

Google Cloud Run은 트래픽에 따른 자동 확장과 기본 HTTPS 인증서를 제공합니다. 본 컨테이너는 A2A 엔드포인트(`/.well-known/agent-card.json`)와 웹 스튜디오 UI(`/studio`)를 함께 내장하고 있어, Gemini Enterprise 연동과 시각적 디버깅을 동시에 수행하기에 가장 적합합니다 (`[확인됨 / Verified: labs/04 Reference Pattern]`).

### Step 1: 배포 환경변수 설정
```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export SERVICE_NAME="enterprise-hub-agent"
```

### Step 2: Google Cloud Build를 통한 컨테이너 이미지 빌드
```bash
gcloud builds submit --project="${PROJECT_ID}" \
  --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
```

### Step 3: Google Cloud Run 서비스 배포
```bash
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ITSM_MODE=MOCK,AGENT_MODEL=gemini-2.5-flash"
```

### Step 4: 배포된 HTTPS 서비스 URL 확보 및 `APP_URL` 업데이트
```bash
export SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')

echo "🚀 배포된 Cloud Run HTTPS URL: ${SERVICE_URL}"
```

A2A Agent Card가 자신의 공인 HTTPS RPC 주소를 정확히 광고하도록 `APP_URL` 환경변수를 업데이트합니다:
```bash
gcloud run services update "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --update-env-vars "APP_URL=${SERVICE_URL}"
```

---

## ⚡ 옵션 B: Vertex AI Agent Engine (`AdkApp`) 완전 관리형 배포

인프라/컨테이너 관리 부담(Zero-Ops) 없이 **VPC Service Controls (VPC-SC)** 및 **Private Service Connect Interface (PSC-I)** 기반의 엄격한 사내망 격리가 필요한 경우, `root_agent`를 **Vertex AI Agent Engine**에 직접 배포할 수 있습니다 (`[확인됨 / Verified: GE Custom Agents Integration Guide]`).

아래 Python 배포 코드 패턴을 참고하세요:
```python
import vertexai
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp
from app.agent import root_agent

PROJECT_ID = "your-gcp-project-id"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-ae-staging"

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# ADK root_agent를 관리형 AdkApp 런타임으로 래핑
adk_app = AdkApp(agent=root_agent, enable_tracing=True)

remote_agent = agent_engines.create(
    agent_engine=adk_app,
    requirements=[
        "google-adk==2.8.0",
        "mcp==1.29.1",
        "google-cloud-aiplatform[agent_engines,adk]>=1.82.0",
        "google-genai>=1.5.0",
    ],
    display_name="enterprise-hub-adk-agent",
    description="Enterprise Cloud FinOps & IT Hub Coordinator Agent",
)
print("배포된 Agent Engine 리소스 이름:", remote_agent.resource_name)
# 출력 형식: projects/{PROJECT_NUMBER}/locations/us-central1/reasoningEngines/{ENGINE_ID}
```

---

## ✅ Check my progress: Task 4 완료 검증

배포된 Cloud Run HTTPS 주소의 Agent Card 엔드포인트를 조회하여 공인 HTTPS `url`과 `"text/plain"` 입출력 모드가 정상 출력되는지 확인합니다:

```bash
curl -s "${SERVICE_URL}/.well-known/agent-card.json" | jq .
```

**정상 출력 예시:**
```json
{
  "name": "enterprise_hub_agent",
  "url": "https://enterprise-hub-agent-xxxx-uc.a.run.app/a2a/enterprise_hub_agent",
  "defaultInputModes": [
    "text/plain"
  ],
  "defaultOutputModes": [
    "text/plain"
  ]
}
```

> **🎉 Task 4 완료!** 이제 본 워크샵의 핵심 단계인 [Lab 04: Gemini Enterprise 에이전트 등록 및 OAuth 2.0 연동](04_gemini_enterprise_integration.md)으로 이동하세요.
