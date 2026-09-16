# Lab 01 (Task 2): ADK 2.0 에이전트 및 3대 분리형 도구 게이트웨이 구현

* **실습 ID**: `Cymbal Enterprise AI Hub` — Task 2 / 5
* **소요 시간**: 약 30분
* **난이도**: 중급 / 고급

---

## 🎯 실습 목표 (Objectives)

이번 Task에서는 다음 작업을 수행합니다:
1. 엔터프라이즈 에이전트 설계 시 단일 통합 도구(Monolithic Tooling) 대신 **3대 분리형 도구 게이트웨이(Decoupled Tool Gateways)**를 채택하는 엔지니어링 이유를 이해합니다.
2. **Gateway 1 (`finops_bq_tool`)**: Knowledge Catalog 표준 수식을 강제하여 32개 프로젝트의 NL2SQL 환각을 차단하는 구조를 점검합니다.
3. **Gateway 2 (`it_policy_rag_tool`)**: **한국어/영어 바이링구얼(Bilingual) 코사인 유사도 `>= 0.70` 품질 게이트**, **인접 청크 윈도우 스티칭(`N-1 ~ N+1`)**, **도메인 외 질의 인증 거절 가드레일(Certified Refusal)** 구현을 확인합니다.
4. **Gateway 3 (`it_servicedesk_tool`)**: Gemini Enterprise로부터 전달된 **OAuth 2.0 `serverSideOauth2` 사용자 신원(`Bearer` 토큰 및 이메일) 추출·감사** 및 **Two-Phase Commit (2PC) HITL 승인 락(`lock:user:{id}:mutation`)** 동작을 확인합니다.
5. Cymbal Enterprise AI Hub 자동 검증 스크립트(`scripts/validate_agent.py`)를 실행하여 **8개 항목 전원 PASS (8/8 PASS | 100 Records Verified)**를 달성합니다.

---

## 🏗️ 왜 3대 분리형 도구 게이트웨이로 구성하는가?

Gemini Enterprise에 연동되는 에이전트가 Raw SQL 테이블 스키마나 수천 줄의 PDF 청크 원문을 루트 에이전트(`LlmAgent`) 프롬프트에 직접 쏟아부으면 **Context Window 오염**과 **Instruction-Skipping(지시 건너뛰기)**이 발생합니다.

도구를 데이터 모달리티별로 3개의 게이트웨이(`app/tools/`)로 격리하면 각 게이트웨이가 고유한 결정론적 가드레일을 먼저 수행한 뒤 정제된 요약본만 코디네이터(`app/agent.py`)에 반환합니다:

| 게이트웨이 | 구현 파일 | 핵심 환각 차단 및 거버넌스 메커니즘 |
| :--- | :--- | :--- |
| **Gateway 1: 정형 FinOps 분석** | [`app/tools/finops_bq_tool.py`](../app/tools/finops_bq_tool.py) | 표준 공식(`Burn Rate % = Spend / Budget * 100`)을 32개 프로젝트에 강제 적용하여 LLM의 임의 수식 추정을 원천 차단 (`[확인됨 / Verified]`). |
| **Gateway 2: 비정형 규정 Vector RAG** | [`app/tools/it_policy_rag_tool.py`](../app/tools/it_policy_rag_tool.py) | 한국어/영어 바이링구얼 코사인 유사도(`>= 0.70`) 계산 후 인접 청크(`N-1` ~ `N+1`)를 결합하며, 도메인 외 질의는 지정된 인증 거절 문장만 단독 반환. |
| **Gateway 3: 실시간 ITSM 액션 & OAuth** | [`app/tools/it_servicedesk_tool.py`](../app/tools/it_servicedesk_tool.py) | Gemini Enterprise가 위임한 **OAuth 2.0 사용자 신원(`authenticated_requester`)**을 티켓에 기록하고 **2PC 멱등성 락(`lock:user:{id}:mutation`)** 강제. |

---

## 🔍 Step 1: 코디네이터 에이전트 및 ADK Callback 바인딩 확인 (`app/agent.py`)

`app/agent.py` 파일을 열어 `root_agent` 선언과 `before_agent_callback` 바인딩을 확인합니다:

```bash
cat app/agent.py
```

* **실제 ADK `Agent` 및 `before_agent_callback` 바인딩**:
  ```python
  root_agent = Agent(
      name="enterprise_hub_agent",
      model=Gemini(model=MODEL, retry_options=retry_cfg),
      instruction=SYSTEM_INSTRUCTION,
      tools=[finops_bq_tool, it_policy_rag_tool, it_servicedesk_tool],
      before_agent_callback=validate_and_update_temporal_cache,
  )
  ```
  - 에이전트가 실행되기 직전(`before_agent_callback`), `validate_and_update_temporal_cache` 콜백이 자동 호출되어 날짜가 변경된 경우 전날 캐시된 예산 초과 프로젝트 상태(`top_overrun_project`)를 즉시 초기화합니다.
* **단일 도구 거절 강제 (Single-Tool Refusal Enforcement)**: 사내 규정과 무관한 도메인 외 질문(예: *"사무실 에스프레소 커피머신 청소 방법 알려줘"*)이 입력되면 `it_policy_rag_tool`은 코사인 유사도 `< 0.70`으로 판정하여 다음 인증 거절 문장을 반환합니다:
  > `"I cannot find certified corporate IT or security policies for this request in our technical repository."`
* **병렬 도구 디스패치 (`PARALLEL_DISPATCH`)**: 특정 프로젝트(`PROJ-AI-PROD-01`)의 실시간 ITSM 장애 티켓과 FinOps 예산 소진율을 비교 분석하라는 요청이 오면, **Turn 1에서 Gateway 1과 Gateway 3을 동시에 병렬 호출**하여 응답 지연시간을 단축합니다.

---

## 🧪 Step 2: Cymbal Enterprise AI Hub 자동 검증 테스트 스위트 실행

`scripts/validate_agent.py`를 실행하여 100건 데이터셋, 3대 게이트웨이, 한국어/영어 바이링구얼 코사인 유사도 RAG, OAuth 2.0 신원 위임 감사, 그리고 ADK 콜백 바인딩이 모두 정상 작동하는지 검증합니다:

```bash
.venv/bin/python3 scripts/validate_agent.py
```

---

## ✅ Check my progress: Task 2 완료 검증

터미널 출력 결과에서 아래 **8 PASSED, 0 FAILED (TOTAL: 8 TESTS | 100 DATA RECORDS)** 요약이 나타나는지 확인합니다:

```text
====================================================================================
🧪 CYMBAL ENTERPRISE AI HUB - AUTOMATED VALIDATION SUITE (100-RECORD DATASET)
Project ID: local-lab-project | ITSM Mode: MOCK
====================================================================================

[TEST 1/8] Dataset Scale Audit (>= 30 Records per Gateway)...
  • Gateway 1 (FinOps Projects):      32 records (Target >= 30)
  • Gateway 2 (Policy RAG Chunks):    36 chunks across 12 policies (Target >= 30)
  • Gateway 3 (ITSM Incidents):       32 records (Target >= 30)
  • Total Enterprise Dataset Records: 100 records
  [PASS] All 3 gateways meet the 30+ realistic enterprise record threshold.

[TEST 2/8] Gateway 1: FinOps Analytics (Project & Department Queries across 32 Projects)...
  [PASS] Completed in 0.00s — Multi-project & department SQL aggregations verified.

[TEST 3/8] Gateway 2: IT Policy RAG Window Stitching (Bilingual KR/EN & Cosine Sim >= 0.70)...
  [PASS] Completed in 0.00s — Adjacent chunks N-1~N+1 stitched & Bilingual Cosine Similarity verified.

[TEST 4/8] Gateway 2: Expanded Policy Corpus Query (NET-POL-2026-PSCI & DLP Policy)...
  [PASS] Completed in 0.00s — Expanded policies retrieved with 3-chunk window stitching.

[TEST 5/8] Gateway 2: Out-of-Domain Refusal Gate (Espresso Machine & Personal Cloud Photos)...
  [PASS] Completed in 0.00s — Certified refusal guardrail enforced strictly (EN & KR).

[TEST 6/8] Gateway 3: Expanded ITSM Incident Lookup (INC-2026-88415 & P1_CRITICAL Filter)...
  [PASS] Completed in 0.00s — Specific ticket lookup & P1 Critical filter (9 P1 incidents) verified.

[TEST 7/8] Gateway 3: Dual-Mode 2PC HITL Ticket Creation & OAuth 2.0 Delegation Audit...
  [PASS] Completed in 0.00s — 2PC lock, HITL flag & OAuth 2.0 identity (architect@cymbal.enterprise) verified.

[TEST 8/8] Coordinator Governance, ADK Callback Contract & A2A Agent Card Schema...
  [PASS] Completed in 0.00s — ADK callback contract `callback(callback_context=...)` honored, cache purged & A2A Card schema verified.

====================================================================================
📊 VALIDATION SUMMARY: 8 PASSED, 0 FAILED (TOTAL: 8 TESTS | 100 DATA RECORDS)
====================================================================================
🎉 All 100 enterprise dataset records, 3 gateways, OAuth delegation & ADK 2.0 runner verified!
```

> **🎉 Task 2 완료!** 이제 [Lab 02: Dual-Contract 서빙 & 로컬 스튜디오 테스트](02_dual_contract_and_studio.md)로 이동하세요.
