#!/usr/bin/env python3
# ============================================================================
# GSP-ADK-GE-2026: Automated Lab Activity Verification Suite (Check my progress)
# Verifies all 3 Decoupled Tool Gateways, Refusal Guardrail & Cache Invalidation
# ============================================================================
import os
import sys
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.finops_bq_tool import finops_bq_tool
from app.tools.it_policy_rag_tool import it_policy_rag_tool
from app.tools.it_servicedesk_tool import it_servicedesk_tool
from app.agent import validate_and_update_temporal_cache


def run_validation_suite():
    project_id = os.getenv("PROJECT_ID", "local-lab-project")
    itsm_mode = os.getenv("ITSM_MODE", "MOCK")

    print("=" * 80)
    print("🧪 GEMINI ENTERPRISE ADK LAB - AUTOMATED VALIDATION SUITE")
    print(f"Project ID: {project_id} | ITSM Mode: {itsm_mode}")
    print("=" * 80)

    passed = 0
    failed = 0

    # Test 1: Gateway 1 - Structured FinOps Analytics Tool
    print("\n[TEST 1/5] Gateway 1: FinOps Analytics (Budget Burn Rate & Spend Overrun)...")
    t0 = time.time()
    res1 = finops_bq_tool("PROJ-AI-PROD-01")
    elapsed = time.time() - t0
    if "PROJ-AI-PROD-01" in str(res1) and ("132.37" in str(res1) or "CRITICAL_OVERRUN" in str(res1)):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Standardized FinOps metrics verified.")
        passed += 1
    else:
        print(f"  [FAIL] Unexpected response: {res1}")
        failed += 1

    # Test 2: Gateway 2 - IT Security Policy Vector RAG (Window Stitching N-1 ~ N+1)
    print("\n[TEST 2/5] Gateway 2: IT Security Policy Vector RAG (Window Stitching SEC-POL-2026-FW)...")
    t0 = time.time()
    res2 = it_policy_rag_tool("SEC-POL-2026-FW firewall port open procedure")
    elapsed = time.time() - t0
    if (
        "[PRE-REQUISITE SAFETY CHECK]" in str(res2)
        and "[EXECUTION SOP: SEC-POL-2026-FW]" in str(res2)
        and "https://storage.cloud.google.com/" in str(res2)
    ):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Adjacent chunks N-1~N+1 stitched & HTTPS citation verified.")
        passed += 1
    else:
        print(f"  [FAIL] Window stitching or citation missing: {res2}")
        failed += 1

    # Test 3: Gateway 2 - Certified Out-of-Domain Refusal Guardrail
    print("\n[TEST 3/5] Gateway 2: Out-of-Domain Refusal Gate (Espresso Machine Repair)...")
    t0 = time.time()
    res3 = it_policy_rag_tool("How do I descale the office espresso coffee machine?")
    elapsed = time.time() - t0
    expected_refusal = "I cannot find certified corporate IT or security policies for this request in our technical repository."
    if expected_refusal in str(res3):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Certified refusal guardrail enforced strictly.")
        passed += 1
    else:
        print(f"  [FAIL] Out-of-domain query was not blocked properly: {res3}")
        failed += 1

    # Test 4: Gateway 3 - Dual-Mode IT Service Desk Action Gateway
    print("\n[TEST 4/5] Gateway 3: Dual-Mode IT Service Desk Telemetry & Ticket Creation...")
    t0 = time.time()
    res4 = it_servicedesk_tool(
        project_id="PROJ-AI-PROD-01",
        action_type="FIREWALL_OPEN",
        justification="Enable PSC-I southbound connectivity for Vertex AI Agent Engine",
    )
    elapsed = time.time() - t0
    if "INC-2026-" in str(res4) and "PENDING_HITL_APPROVAL" in str(res4):
        print(f"  [PASS] Completed in {elapsed:.2f}s — Dual-mode ticket created with 2PC lock & HITL flag.")
        passed += 1
    else:
        print(f"  [FAIL] Service desk ticket creation failed: {res4}")
        failed += 1

    # Test 5: Temporal Cache Invalidation Callback
    print("\n[TEST 5/5] Coordinator Governance: Temporal Cache Invalidation Callback...")
    mock_state = {"top_overrun_project": "PROJ-OLD-99", "top_overrun_date": "2026-01-01"}
    updated_state = validate_and_update_temporal_cache(mock_state, current_date_str="2026-09-15")
    if updated_state.get("top_overrun_project") is None and updated_state.get("top_overrun_date") == "2026-09-15":
        print("  [PASS] Completed in 0.00s — Stale cross-day session cache purged successfully.")
        passed += 1
    else:
        print(f"  [FAIL] Cache invalidation failed: {updated_state}")
        failed += 1

    print("\n" + "=" * 80)
    print(f"📊 VALIDATION SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL: 5)")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)
    print("🎉 All ADK Agent gateways and quality guardrails verified! Ready for Gemini Enterprise.")


if __name__ == "__main__":
    run_validation_suite()
