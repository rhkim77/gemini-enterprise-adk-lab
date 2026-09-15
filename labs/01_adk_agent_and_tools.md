# Lab 01 (Task 2): ADK 2.0 에이전트 및 3대 분리형 도구 게이트웨이 구현

* **실습 ID**: `Cymbal Enterprise AI Hub` — Task 2 / 5
* **소요 시간**: 약 30분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. 엔터프라이즈 에이전트 설계 시 단일 통합 도구(Monolithic Tooling) 대신 **3대 분리형 도구 게이트웨이(Decoupled Tool Gateways)**를 채택하는 엔지니어링 이유를 이해합니다.
2. **Gateway 1 (`finops_bq_tool`)**: Knowledge Catalog 표준 수식을 강제하여 NL2SQL 환각을 차단하는 구조를 점검합니다.
3. **Gateway 2 (`it_policy_rag_tool`)**: **코사인 유사도 `>= 0.70` 품질 게이트**, **인접 청크 윈도우 스티칭(`N-1 ~ N+1`)**, **도메인 외 질의 인증 거절 가드레일(Certified Refusal)** 구현을 확인합니다.
4. **Gateway 3 (`it_servicedesk_tool`)**: `MOCK`/`LIVE` 이중 모드 및 **Two-Phase Commit (2PC) HITL 승인 락(`lock:user:{id}:mutation`)** 동작을 확인합니다.
5. Cymbal Enterprise AI Hub 자동 검증 스크립트(`scripts/validate_agent.py`)를 실행하여 **5개 항목 전원 PASS (5/5)**를 달성합니다.

---

## 🏗️ 왜 3대 분리형 도구 게이트웨이로 구성하는가?

Gemini Enterprise에 연동되는 에이전트가 Raw SQL 테이블 스키마나 수천 줄의 PDF 청크 원문을 루트 에이전트(`LlmAgent`) 프롬프트에 직접 쏟아부으면 **Context Window 오염**과 **Instruction-Skipping(지시 건너뛰기)**이 발생합니다.

도구를 데이터 모달리티별로 3개의 게이트웨이(`app/tools/`)로 격리하면 각 게이트웨이가 고유한 결정론적 가드레일을 먼저 수행한 뒤 정제된 요약본만 코디네이터(`app/agent.py`)에 반환합니다:

| 게이트웨이 | 구현 파일 | 핵심 환각 차단 메커니즘 (Anti-Hallucination) |
| :--- | :--- | :--- |
| **Gateway 1: 정형 FinOps 분석** | [`app/tools/finops_bq_tool.py`](../app/tools/finops_bq_tool.py) | 표준 공식(`Burn Rate % = Spend / Budget * 100`)을 강제 적용하여 LLM의 임의 수식 추정을 원천 차단 (`[확인됨 / Verified]`). |
| **Gateway 2: 비정형 규정 Vector RAG** | [`app/tools/it_policy_rag_tool.py`](../app/tools/it_policy_rag_tool.py) | 앞뒤 인접 청크(`N-1` ~ `N+1`)를 결합하여 사전 안전 수칙 누락을 막고, 유사도 `0.70` 미만 질의는 지정된 인증 거절 문장만 반환. |
| **Gateway 3: 실시간 ITSM 액션 API** | [`app/tools/it_servicedesk_tool.py`](../app/tools/it_servicedesk_tool.py) | 외부 인프라 변경 요청 시 **2PC 멱등성 락(`lock:user:{id}:mutation`)**과 **HITL 승인 플래그(`PENDING_HITL_APPROVAL`)** 강제. |

---

## 🔍 Step 1: 코디네이터 에이전트 라우팅 규칙 확인 (`app/agent.py`)

`app/agent.py` 파일을 열어 `SYSTEM_INSTRUCTION`에 정의된 디스패치 규칙을 확인합니다:

```bash
cat app/agent.py
```

* **단일 도구 거절 강제 (Single-Tool Refusal Enforcement)**: 사내 규정과 무관한 도메인 외 질문(예: *"사무실 에스프레소 머신 청소 방법 알려줘"*)이 입력되면 `it_policy_rag_tool`은 다음 인증 거절 문장을 반환합니다:
  > `"I cannot find certified corporate IT or security policies for this request in our technical repository."`
  코디네이터 에이전트는 어떠한 사족이나 인사말도 덧붙이지 않고 위 문장만 단독 출력하도록 통제됩니다.
* **병렬 도구 디스패치 (`PARALLEL_DISPATCH`)**: 특정 프로젝트(`PROJ-AI-PROD-01`)의 실시간 ITSM 장애 티켓과 FinOps 예산 소진율을 동시에 감사하라는 요청이 오면, **Turn 1에서 Gateway 1과 Gateway 3을 동시에 병렬 호출**하여 응답 지연시간을 단축합니다.
* **자정 기준 캐시 무효화 (`validate_and_update_temporal_cache`)**: 날짜가 변경되면 전날 캐시된 예산 초과 프로젝트 ID(`top_overrun_project`)를 자동으로 초기화합니다.

---

## 🧪 Step 2: Cymbal Enterprise AI Hub 자동 검증 테스트 스위트 실행

`scripts/validate_agent.py`를 실행하여 3대 게이트웨이, 윈도우 스티칭, 거절 가드레일, 캐시 무효화가 모두 정상 작동하는지 검증합니다:

```bash
python3 scripts/validate_agent.py
```

---

## ✅ Check my progress: Task 2 완료 검증

터미널 출력 결과에서 아래 **5 PASSED, 0 FAILED** 요약이 나타나는지 확인합니다:

```text
================================================================================
🧪 GEMINI ENTERPRISE ADK LAB - AUTOMATED VALIDATION SUITE
Project ID: local-lab-project | ITSM Mode: MOCK
================================================================================

[TEST 1/5] Gateway 1: FinOps Analytics (Budget Burn Rate & Spend Overrun)...
  [PASS] Completed in 0.00s — Standardized FinOps metrics verified.

[TEST 2/5] Gateway 2: IT Security Policy Vector RAG (Window Stitching SEC-POL-2026-FW)...
  [PASS] Completed in 0.00s — Adjacent chunks N-1~N+1 stitched & HTTPS citation verified.

[TEST 3/5] Gateway 2: Out-of-Domain Refusal Gate (Espresso Machine Repair)...
  [PASS] Completed in 0.00s — Certified refusal guardrail enforced strictly.

[TEST 4/5] Gateway 3: Dual-Mode IT Service Desk Telemetry & Ticket Creation...
  [PASS] Completed in 0.00s — Dual-mode ticket created with 2PC lock & HITL flag.

[TEST 5/5] Coordinator Governance: Temporal Cache Invalidation Callback...
  [PASS] Completed in 0.00s — Stale cross-day session cache purged successfully.

================================================================================
📊 VALIDATION SUMMARY: 5 PASSED, 0 FAILED (TOTAL: 5)
================================================================================
🎉 All ADK Agent gateways and quality guardrails verified! Ready for Gemini Enterprise.
```

> **🎉 Task 2 완료!** 이제 [Lab 02: Dual-Contract 서빙 & 로컬 스튜디오 테스트](02_dual_contract_and_studio.md)로 이동하세요.
