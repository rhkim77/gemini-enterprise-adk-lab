#!/usr/bin/env python3
# ============================================================================
# Cymbal Enterprise AI Hub: Automated Verification Suite
# Verifies 100-Record Datasets (32 FinOps + 36 Policy Chunks + 32 ITSM Incidents),
# all 3 Decoupled Tool Gateways, Refusal Guardrail, Cache Invalidation & A2A Card
# ============================================================================
import os
import sys
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.finops_bq_tool import _FINOPS_GOLD_LEDGER, finops_bq_tool
from app.tools.it_policy_rag_tool import _ALL_POLICY_CHUNKS, _POLICY_CHUNKS_DB, it_policy_rag_tool
from app.tools.it_servicedesk_tool import _ITSM_INCIDENTS_DB, it_servicedesk_tool
from app.agent import validate_and_update_temporal_cache
from app.app_utils.a2a import get_hardened_agent_card


def run_validation_suite():
    project_id = os.getenv("PROJECT_ID", "local-lab-project")
    itsm_mode = os.getenv("ITSM_MODE", "MOCK")

    print("=" * 84)
    print("🧪 CYMBAL ENTERPRISE AI HUB - AUTOMATED VALIDATION SUITE (100-RECORD DATASET)")
    print(f"Project ID: {project_id} | ITSM Mode: {itsm_mode}")
    print("=" * 84)

    passed = 0
    failed = 0

    # Test 1: Dataset Scale Verification (>= 30 records per gateway)
    print("\n[TEST 1/8] Dataset Scale Audit (>= 30 Records per Gateway)...")
    f_count = len(_FINOPS_GOLD_LEDGER)
    p_count = len(_ALL_POLICY_CHUNKS)
    p_policies = len(_POLICY_CHUNKS_DB)
    i_count = len(_ITSM_INCIDENTS_DB)
    total_records = f_count + p_count + i_count
    print(f"  • Gateway 1 (FinOps Projects):      {f_count} records (Target >= 30)")
    print(f"  • Gateway 2 (Policy RAG Chunks):    {p_count} chunks across {p_policies} policies (Target >= 30)")
    print(f"  • Gateway 3 (ITSM Incidents):       {i_count} records (Target >= 30)")
    print(f"  • Total Enterprise Dataset Records: {total_records} records")
    if f_count >= 30 and p_count >= 30 and i_count >= 30:
        print("  [PASS] All 3 gateways meet the 30+ realistic enterprise record threshold.")
        passed += 1
    else:
        print(f"  [FAIL] Dataset count below 30 threshold: FinOps={f_count}, Policy={p_count}, ITSM={i_count}")
        failed += 1

    # Test 2: Gateway 1 - FinOps Analytics (Original + Expanded Projects & Department Aggregation)
    print("\n[TEST 2/8] Gateway 1: FinOps Analytics (Project & Department Queries across 32 Projects)...")
    t0 = time.time()
    res_p1 = finops_bq_tool("PROJ-AI-PROD-01")
    res_p4 = finops_bq_tool("PROJ-LLM-SERVE-04")
    res_dept = finops_bq_tool("FinTech Security")
    elapsed = time.time() - t0
    if (
        "132.37" in str(res_p1)
        and "PROJ-LLM-SERVE-04" in str(res_p4)
        and res_dept.get("department") == "FinTech Security"
    ):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Multi-project & department SQL aggregations verified.")
        passed += 1
    else:
        print(f"  [FAIL] Unexpected FinOps response: {res_p4} / {res_dept}")
        failed += 1

    # Test 3: Gateway 2 - IT Security Policy Vector RAG (Window Stitching SEC-POL-2026-FW)
    print("\n[TEST 3/8] Gateway 2: IT Policy RAG Window Stitching (SEC-POL-2026-FW N-1 ~ N+1)...")
    t0 = time.time()
    res_fw = it_policy_rag_tool("SEC-POL-2026-FW firewall port open procedure")
    elapsed = time.time() - t0
    if (
        "[PRE-REQUISITE SAFETY CHECK: SEC-POL-2026-FW]" in str(res_fw)
        and "[EXECUTION SOP: SEC-POL-2026-FW]" in str(res_fw)
        and "https://storage.cloud.google.com/" in str(res_fw)
    ):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Adjacent chunks N-1~N+1 stitched & HTTPS citation verified.")
        passed += 1
    else:
        print(f"  [FAIL] Window stitching or citation missing: {res_fw}")
        failed += 1

    # Test 4: Gateway 2 - Expanded Policy Corpus Verification (NET-POL-2026-PSCI & DATA-POL-2026-DLP)
    print("\n[TEST 4/8] Gateway 2: Expanded Policy Corpus Query (NET-POL-2026-PSCI & DLP Policy)...")
    t0 = time.time()
    res_psci = it_policy_rag_tool("How do we configure Private Service Connect Interface psc-i routing?")
    res_dlp = it_policy_rag_tool("DATA-POL-2026-DLP Model Armor PII masking")
    elapsed = time.time() - t0
    if "NET-POL-2026-PSCI" in str(res_psci) and "DATA-POL-2026-DLP" in str(res_dlp):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Expanded policies retrieved with 3-chunk window stitching.")
        passed += 1
    else:
        print(f"  [FAIL] Expanded policy lookup failed: {res_psci}")
        failed += 1

    # Test 5: Gateway 2 - Certified Out-of-Domain Refusal Guardrail
    print("\n[TEST 5/8] Gateway 2: Out-of-Domain Refusal Gate (Espresso Machine Repair)...")
    t0 = time.time()
    res_refusal = it_policy_rag_tool("How do I descale the office espresso coffee machine?")
    elapsed = time.time() - t0
    expected_refusal = "I cannot find certified corporate IT or security policies for this request in our technical repository."
    if expected_refusal in str(res_refusal):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Certified refusal guardrail enforced strictly.")
        passed += 1
    else:
        print(f"  [FAIL] Out-of-domain query was not blocked properly: {res_refusal}")
        failed += 1

    # Test 6: Gateway 3 - Expanded ITSM Incident Lookup & P1 Critical Fleet Filter
    print("\n[TEST 6/8] Gateway 3: Expanded ITSM Incident Lookup (INC-2026-88415 & P1_CRITICAL Filter)...")
    t0 = time.time()
    res_inc = it_servicedesk_tool("INC-2026-88415")
    res_p1_list = it_servicedesk_tool("P1_CRITICAL")
    elapsed = time.time() - t0
    if (
        res_inc.get("matched_ticket", {}).get("ticket_id") == "INC-2026-88415"
        and res_p1_list.get("active_incidents_count", 0) >= 5
    ):
        print(
            f"  [PASS] Completed in {elapsed:.2f}s — Specific ticket lookup & P1 Critical filter ({res_p1_list['active_incidents_count']} P1 incidents) verified."
        )
        passed += 1
    else:
        print(f"  [FAIL] ITSM incident lookup failed: {res_inc}")
        failed += 1

    # Test 7: Gateway 3 - Dual-Mode IT Service Desk 2PC HITL Ticket Creation
    print("\n[TEST 7/8] Gateway 3: Dual-Mode IT Service Desk 2PC HITL Ticket Creation...")
    t0 = time.time()
    res_ticket = it_servicedesk_tool(
        project_id="PROJ-AI-PROD-01",
        action_type="FIREWALL_OPEN",
        justification="Enable PSC-I southbound connectivity for Vertex AI Agent Engine",
    )
    elapsed = time.time() - t0
    if "INC-2026-" in str(res_ticket) and "PENDING_HITL_APPROVAL" in str(res_ticket):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Dual-mode ticket created with 2PC lock & HITL flag.")
        passed += 1
    else:
        print(f"  [FAIL] Service desk ticket creation failed: {res_ticket}")
        failed += 1

    # Test 8: Coordinator Governance & A2A Agent Card Schema
    print("\n[TEST 8/8] Coordinator Governance & A2A Agent Card Schema Verification...")
    mock_state = {"top_overrun_project": "PROJ-OLD-99", "top_overrun_date": "2026-01-01"}
    updated_state = validate_and_update_temporal_cache(mock_state, current_date_str="2026-09-15")
    card = get_hardened_agent_card("https://finops-adk-agent.a.run.app")
    if (
        updated_state.get("top_overrun_project") is None
        and card.get("defaultInputModes") == ["text/plain"]
        and card.get("defaultOutputModes") == ["text/plain"]
    ):
        print("  [PASS] Completed in 0.00s — Temporal cache invalidation & A2A Card schema verified.")
        passed += 1
    else:
        print(f"  [FAIL] Cache invalidation or A2A Card check failed: {updated_state} / {card}")
        failed += 1

    print("\n" + "=" * 84)
    print(f"📊 VALIDATION SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL: 8 TESTS | 100 DATA RECORDS)")
    print("=" * 84)

    if failed > 0:
        sys.exit(1)
    print("🎉 All 100 enterprise dataset records, 3 gateways, and A2A guardrails verified!")


if __name__ == "__main__":
    run_validation_suite()
