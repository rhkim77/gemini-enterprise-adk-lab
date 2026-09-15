# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Dual-Contract FastAPI Server for Enterprise FinOps & IT Hub Coordinator Agent.

Simultaneously exposes:
1. A2A Protocol Endpoints (`/.well-known/agent-card.json` & `POST /a2a/enterprise_hub_agent`)
2. Vertex AI Reasoning Engine Contract (`POST /api/reasoning_engine`)
3. Interactive Operations Web Studio (`/studio` & `POST /api/chat`)
"""
import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import attach_reasoning_engine_routes
from app.tools.finops_bq_tool import finops_bq_tool
from app.tools.it_policy_rag_tool import CERTIFIED_REFUSAL_MESSAGE, it_policy_rag_tool
from app.tools.it_servicedesk_tool import it_servicedesk_tool

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cymbal Enterprise AI Hub — FinOps & IT Coordinator Agent",
    description="Dual-Contract (A2A + Reasoning Engine) ADK 2.0 Agent for Gemini Enterprise Integration",
    version="2.0.0",
)

# Mount Dual-Contract Endpoints
attach_a2a_routes(app, agent_name="enterprise_hub_agent")
attach_reasoning_engine_routes(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
if os.path.isdir(WEB_DIR):
    app.mount("/studio", StaticFiles(directory=WEB_DIR, html=True), name="studio")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


async def execute_agent_query(message: str, session_id: str = "default") -> Dict[str, Any]:
    """Executes the ADK coordinator routing logic across the 3 decoupled tool gateways."""
    start_time = time.time()
    msg_lower = message.lower()
    tool_calls = []
    tool_responses = []
    final_sections = []
    dispatch_mode = "SINGLE_TOOL_DISPATCH"

    # 1. Check for Out-of-Domain or Policy RAG queries first (Strict Grounding & Refusal Protocol)
    out_of_domain = any(w in msg_lower for w in ["coffee", "espresso", "descale", "oil change", "f-150", "recipe"])
    is_policy_query = any(w in msg_lower for w in ["sec-pol", "fin-pol", "sop", "policy", "firewall", "vpc-sc", "psc-i", "manual"])
    is_finops_query = any(w in msg_lower for w in ["burn rate", "finops", "budget", "spend", "overrun", "idle", "gpu", "proj-ai-prod-01"])
    is_ticket_query = any(w in msg_lower for w in ["ticket", "incident", "open", "servicedesk", "approval", "audit", "compare"])

    if out_of_domain:
        rag_res = it_policy_rag_tool(message)
        tool_calls.append({"name": "it_policy_rag_tool", "args": {"query": message}})
        tool_responses.append({"name": "it_policy_rag_tool", "response": rag_res})
        return {
            "session_id": session_id,
            "message": message,
            "final_text": CERTIFIED_REFUSAL_MESSAGE,
            "dispatch_mode": "CERTIFIED_REFUSAL_GUARDRAIL",
            "tool_calls": tool_calls,
            "tool_responses": tool_responses,
            "generated_sql": "",
            "gcs_links": [],
            "plotly_spec": None,
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    # 2. Parallel Dispatch: FinOps Burn Rate + Live IT Service Desk Incidents
    if is_finops_query and is_ticket_query:
        dispatch_mode = "PARALLEL_DISPATCH (Gateway 1 FinOps + Gateway 3 ITSM)"
        fin_res = finops_bq_tool("PROJ-AI-PROD-01")
        itsm_res = it_servicedesk_tool("PROJ-AI-PROD-01", action_type="STATUS_CHECK")
        tool_calls.extend([
            {"name": "finops_bq_tool", "args": {"query_or_project_id": "PROJ-AI-PROD-01"}},
            {"name": "it_servicedesk_tool", "args": {"project_id": "PROJ-AI-PROD-01", "action_type": "STATUS_CHECK"}},
        ])
        tool_responses.extend([
            {"name": "finops_bq_tool", "response": fin_res},
            {"name": "it_servicedesk_tool", "response": itsm_res},
        ])
        final_sections.append(
            f"### ⚡ Parallel Dispatch Audit: PROJ-AI-PROD-01 (FinOps + Live ITSM)\n"
            f"- **FinOps Burn Rate**: `{fin_res['burn_rate_pct']}%` (`CRITICAL_OVERRUN` — Spend: `${fin_res['current_spend_usd']:,.2f}` vs Budget: `${fin_res['monthly_budget_usd']:,.2f}`)\n"
            f"- **Idle GPU Waste**: `${fin_res['idle_gpu_waste_usd']:,.2f}`\n"
            f"- **Active Service Desk Incidents ({itsm_res['active_incidents_count']})**:\n"
            + "\n".join([f"  - `{t['ticket_id']}` [{t['type']}]: {t['detail']}" for t in itsm_res.get("open_tickets", [])])
        )
    elif is_policy_query:
        dispatch_mode = "SINGLE_TOOL_RAG (Gateway 2 Vector RAG + Window Stitching)"
        rag_res = it_policy_rag_tool(message)
        tool_calls.append({"name": "it_policy_rag_tool", "args": {"query": message}})
        tool_responses.append({"name": "it_policy_rag_tool", "response": rag_res})
        final_sections.append(rag_res)
    elif is_ticket_query and "open" in msg_lower:
        dispatch_mode = "SINGLE_TOOL_ACTION (Gateway 3 2PC HITL Ticket)"
        itsm_res = it_servicedesk_tool("PROJ-AI-PROD-01", action_type="FIREWALL_OPEN", justification=message)
        tool_calls.append({"name": "it_servicedesk_tool", "args": {"project_id": "PROJ-AI-PROD-01", "action_type": "FIREWALL_OPEN"}})
        tool_responses.append({"name": "it_servicedesk_tool", "response": itsm_res})
        final_sections.append(
            f"### 🎫 2-Phase Commit HITL Ticket Created\n"
            f"- **Ticket ID**: `{itsm_res['ticket_id']}`\n"
            f"- **Status**: `{itsm_res['status']}` (Approver: {itsm_res['required_approver']})\n"
            f"- **2PC Idempotency Lock**: `{itsm_res['idempotency_2pc_lock']}`"
        )
    else:
        dispatch_mode = "SINGLE_TOOL_ANALYTICS (Gateway 1 FinOps Gold Ledger)"
        fin_res = finops_bq_tool(message)
        tool_calls.append({"name": "finops_bq_tool", "args": {"query_or_project_id": message}})
        tool_responses.append({"name": "finops_bq_tool", "response": fin_res})
        if "burn_rate_pct" in fin_res:
            final_sections.append(
                f"### 📊 Cloud FinOps Analytics: {fin_res['project_id']}\n"
                f"- **Service**: {fin_res['service_name']}\n"
                f"- **Monthly Budget**: `${fin_res['monthly_budget_usd']:,.2f}` | **Current Spend**: `${fin_res['current_spend_usd']:,.2f}`\n"
                f"- **Budget Burn Rate**: **`{fin_res['burn_rate_pct']}%`** (`{fin_res['alert_status']}`)\n"
                f"- **Idle GPU Waste**: `${fin_res['idle_gpu_waste_usd']:,.2f}`"
            )
        else:
            final_sections.append(fin_res.get("summary", str(fin_res)))

    final_text = "\n\n".join(final_sections)

    # Extract SQL & GCS links
    generated_sql = ""
    gcs_links = []
    for tr in tool_responses:
        resp_obj = tr.get("response", {})
        if isinstance(resp_obj, dict) and "generated_sql" in resp_obj:
            generated_sql = resp_obj["generated_sql"]
        resp_str = json.dumps(resp_obj) if isinstance(resp_obj, dict) else str(resp_obj)
        links = re.findall(r"(https?://storage\.cloud\.google\.com/[^\s\)\"'\\]+)", resp_str)
        for lnk in links:
            if lnk not in gcs_links:
                gcs_links.append(lnk)

    # Build Plotly Chart for FinOps queries
    plotly_spec = None
    if is_finops_query or dispatch_mode.startswith("PARALLEL"):
        plotly_spec = {
            "title": "Enterprise Cloud Budget Burn Rate (%) vs Threshold",
            "data": [
                {
                    "x": ["PROJ-AI-PROD-01 (AI Cluster)", "PROJ-WEB-FRONT-03 (Cloud Run)", "PROJ-DATA-LAKE-02 (BigQuery)", "Governance Freeze Limit"],
                    "y": [132.37, 99.26, 80.50, 120.0],
                    "type": "bar",
                    "marker": {"color": ["#EF4444", "#F59E0B", "#10B981", "#6366F1"]},
                }
            ],
            "layout": {
                "title": "Cloud FinOps Budget Burn Rate (% of Monthly Budget)",
                "yaxis": {"title": "Burn Rate (%)"},
                "margin": {"t": 40, "b": 40, "l": 50, "r": 20},
            },
        }

    return {
        "session_id": session_id,
        "message": message,
        "final_text": final_text,
        "dispatch_mode": dispatch_mode,
        "tool_calls": tool_calls,
        "tool_responses": tool_responses,
        "generated_sql": generated_sql,
        "gcs_links": gcs_links,
        "plotly_spec": plotly_spec,
        "latency_ms": int((time.time() - start_time) * 1000),
    }


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/studio/")


@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "agent": "enterprise_hub_agent", "contracts": ["A2A", "ReasoningEngine"]}


@app.post("/api/chat")
async def studio_chat(req: ChatRequest) -> Dict[str, Any]:
    return await execute_agent_query(req.message, req.session_id or "default")
