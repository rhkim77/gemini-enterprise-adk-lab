# Lab 01 (Task 2): ADK 2.0 Agent & 3 Decoupled Tool Gateways

* **Lab ID**: `GSP-ADK-GE-2026` — Task 2 of 5
* **Estimated Time**: 30 Minutes
* **Level**: Intermediate / Advanced

---

## 🎯 Objectives

In this task, you will:
1. Understand why enterprise agents require **3 Decoupled Tool Gateways** instead of monolithic direct tooling.
2. Inspect and verify **Gateway 1 (`finops_bq_tool`)** for deterministic SQL formula enforcement.
3. Inspect and verify **Gateway 2 (`it_policy_rag_tool`)** featuring **Cosine Similarity `>= 0.70` Quality Gate**, **Adjacent Context Window Stitching (`N-1 ~ N+1`)**, and **Certified Out-of-Domain Refusal Guardrail**.
4. Inspect and verify **Gateway 3 (`it_servicedesk_tool`)** featuring Dual-Mode (`MOCK`/`LIVE`) execution and **Two-Phase Commit (2PC) HITL Approval Locks**.
5. Execute the Qwiklabs automated test runner (`scripts/validate_agent.py`) to achieve a **5/5 PASS** score.

---

## 🏗️ Why 3 Decoupled Tool Gateways? (Architectural Deep Dive)

When integrating an ADK agent into **Gemini Enterprise**, connecting raw database tables and un-stitched vector chunks directly to a single root prompt causes **Context Window Pollution** and **Instruction-Skipping**.

By isolating tools into 3 specialized gateways (`app/tools/`), each modality enforces its own deterministic quality guardrail before returning clean summaries to the coordinator (`app/agent.py`):

| Gateway | Implementation File | Primary Anti-Hallucination Mechanism |
| :--- | :--- | :--- |
| **Gateway 1: Structured FinOps Analytics** | [`app/tools/finops_bq_tool.py`](../app/tools/finops_bq_tool.py) | Enforces Knowledge Catalog Glossary formulas (`Burn Rate % = Spend / Budget * 100`) to eliminate NL2SQL math errors (`[확인됨 / Verified]`). |
| **Gateway 2: IT Security SOP Vector RAG** | [`app/tools/it_policy_rag_tool.py`](../app/tools/it_policy_rag_tool.py) | Stitches adjacent chunks (`N-1` to `N+1`) so safety prerequisites are never cut off, and blocks out-of-domain queries (`Sim < 0.70`) with a hard-coded certified refusal string. |
| **Gateway 3: Live IT Service Desk API** | [`app/tools/it_servicedesk_tool.py`](../app/tools/it_servicedesk_tool.py) | Isolates external mutations behind a **2PC Idempotency Lock (`lock:user:{id}:mutation`)** and requires Level-2 HITL approval (`PENDING_HITL_APPROVAL`). |

---

## 🔍 Step 1: Inspect the Root Coordinator & Dispatch Rules (`app/agent.py`)

Open `app/agent.py` and review the `SYSTEM_INSTRUCTION` block:

```bash
cat app/agent.py
```

Key architectural features built into `enterprise_hub_agent`:
- **Single-Tool Refusal Enforcement**: If a user asks an out-of-domain question (e.g., *"How do I descale the office espresso coffee machine?"*), `it_policy_rag_tool` returns:
  > `"I cannot find certified corporate IT or security policies for this request in our technical repository."`
  The coordinator is strictly instructed to output **only** that exact sentence without adding conversational filler.
- **Parallel Tool Dispatch (`PARALLEL_DISPATCH`)**: When asked to audit a project's live ITSM incidents alongside its FinOps budget burn rate (`PROJ-AI-PROD-01`), the agent invokes **Gateway 1 and Gateway 3 concurrently in Turn 1**.
- **Temporal Cache Invalidation**: The `validate_and_update_temporal_cache` callback automatically purges cached project state when the calendar date rolls over past midnight.

---

## 🧪 Step 2: Run the Automated Qwiklabs Activity Test Suite

Run `scripts/validate_agent.py` to test all 3 gateways, window stitching, refusal guardrails, and temporal cache invalidation:

```bash
python3 scripts/validate_agent.py
```

---

## ✅ Check my progress: Verify Task 2

Confirm that your terminal displays the following **5 PASSED, 0 FAILED** summary:

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

> **🎉 Task 2 Complete!** Proceed to [Lab 02: Dual-Contract Serving & Local Studio Test](02_dual_contract_and_studio.md).
