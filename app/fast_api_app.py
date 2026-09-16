# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Dual-Contract FastAPI Server for Enterprise FinOps & IT Hub Coordinator Agent.

Simultaneously exposes:
1. A2A Protocol Endpoints (`/.well-known/agent-card.json` & `POST /a2a/enterprise_hub_agent`)
2. Vertex AI Reasoning Engine Contract (`POST /api/reasoning_engine`)
3. Interactive Operations Web Studio (`/studio` & `POST /api/chat`)

Executes queries via the genuine Google ADK 2.0 `InMemoryRunner` (`root_agent` + `gemini-2.5-flash`)
with automatic resilient fallback to the Deterministic Hybrid Router in offline/unauthenticated labs.
"""
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import MODEL, root_agent
from app.app_utils.a2a import _extract_oauth_from_request, attach_a2a_routes
from app.app_utils.reasoning_engine_adapter import attach_reasoning_engine_routes
from app.tools.finops_bq_tool import finops_bq_tool
from app.tools.it_policy_rag_tool import CERTIFIED_REFUSAL_MESSAGE, it_policy_rag_tool
from app.tools.it_servicedesk_tool import (
    get_current_oauth_context,
    it_servicedesk_tool,
    set_current_oauth_context,
)

logger = logging.getLogger(__name__)

# Initialize genuine Google ADK 2.0 InMemoryRunner
_ADK_RUNNER = None
try:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    _ADK_RUNNER = InMemoryRunner(agent=root_agent, app_name="enterprise_hub_agent")
except Exception as exc:
    logger.warning("ADK InMemoryRunner initialization warning: %s", exc)

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


def _extract_sql_and_citations(tool_responses: List[Dict[str, Any]], final_text: str) -> tuple[str, List[str]]:
    """Extracts executed GoogleSQL and GCS HTTPS citation URLs from tool payloads."""
    generated_sql = ""
    gcs_links: List[str] = []
    for tr in tool_responses:
        resp_obj = tr.get("response", {})
        if isinstance(resp_obj, dict) and "generated_sql" in resp_obj:
            generated_sql = resp_obj["generated_sql"]
        resp_str = json.dumps(resp_obj) if isinstance(resp_obj, dict) else str(resp_obj)
        for lnk in re.findall(r"(https?://storage\.cloud\.google\.com/[^\s\)\"'\\]+)", resp_str):
            if lnk not in gcs_links:
                gcs_links.append(lnk)
    for lnk in re.findall(r"(https?://storage\.cloud\.google\.com/[^\s\)\"'\\]+)", final_text):
        if lnk not in gcs_links:
            gcs_links.append(lnk)
    return generated_sql, gcs_links


def _build_plotly_spec(is_finops_or_parallel: bool) -> Optional[Dict[str, Any]]:
    """Builds interactive Plotly chart spec for FinOps budget burn rate visualization."""
    if not is_finops_or_parallel:
        return None
    return {
        "title": "Enterprise Cloud Budget Burn Rate (%) vs Governance Threshold",
        "data": [
            {
                "x": [
                    "PROJ-AI-PROD-01 (AI Cluster)",
                    "PROJ-LLM-SERVE-04 (LLM Inference)",
                    "PROJ-WEB-FRONT-03 (Cloud Run)",
                    "PROJ-DATA-LAKE-02 (BigQuery)",
                    "Governance Freeze Limit",
                ],
                "y": [132.37, 128.50, 99.26, 80.50, 120.0],
                "type": "bar",
                "marker": {"color": ["#EF4444", "#EF4444", "#F59E0B", "#10B981", "#6366F1"]},
            }
        ],
        "layout": {
            "title": "Cloud FinOps Budget Burn Rate (% of Monthly Budget)",
            "yaxis": {"title": "Burn Rate (%)"},
            "margin": {"t": 40, "b": 40, "l": 50, "r": 20},
        },
    }


async def _try_adk_runner_execution(
    message: str, session_id: str, oauth_ctx: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """Attempts live execution through Google ADK 2.0 InMemoryRunner + Gemini 2.5 Flash."""
    if _ADK_RUNNER is None:
        return None
    if os.getenv("USE_ADK_LLM", "true").lower() == "false":
        return None

    has_api_key = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    project_id = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT", "")
    has_vertex = bool(project_id and project_id != "<YOUR_PROJECT_ID>")

    if not (has_api_key or has_vertex):
        return None

    user_id = oauth_ctx.get("user_email") or "enterprise_user"
    session = await _ADK_RUNNER.session_service.get_session(
        app_name="enterprise_hub_agent", user_id=user_id, session_id=session_id
    )
    if not session:
        session = await _ADK_RUNNER.session_service.create_session(
            app_name="enterprise_hub_agent", user_id=user_id, session_id=session_id
        )

    tool_calls: List[Dict[str, Any]] = []
    tool_responses: List[Dict[str, Any]] = []
    final_text_parts: List[str] = []

    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=message)])
    async for event in _ADK_RUNNER.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_msg,
        state_delta={"oauth_context": oauth_ctx},
    ):
        f_calls = event.get_function_calls()
        if f_calls:
            for fc in f_calls:
                tool_calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})

        f_resps = event.get_function_responses()
        if f_resps:
            for fr in f_resps:
                tool_responses.append({"name": fr.name, "response": fr.response})

        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    final_text_parts.append(part.text)

    final_text = "\n\n".join(final_text_parts).strip()
    if not final_text:
        return None

    # Enforce strict single-sentence output if certified refusal guardrail was triggered
    for tr in tool_responses:
        if CERTIFIED_REFUSAL_MESSAGE in str(tr.get("response", "")):
            final_text = CERTIFIED_REFUSAL_MESSAGE
            break

    called_names = {tc["name"] for tc in tool_calls}
    if CERTIFIED_REFUSAL_MESSAGE in final_text:
        dispatch_mode = "CERTIFIED_REFUSAL_GUARDRAIL (ADK 2.0 Runner)"
    elif len(called_names) >= 2:
        dispatch_mode = f"PARALLEL_DISPATCH (ADK 2.0 Runner: {' + '.join(sorted(called_names))})"
    elif len(called_names) == 1:
        dispatch_mode = f"SINGLE_TOOL_DISPATCH (ADK 2.0 Runner: {list(called_names)[0]})"
    else:
        dispatch_mode = "ADK_DIRECT_SYNTHESIS"

    is_finops_chart = "finops_bq_tool" in called_names or "burn rate" in message.lower()
    generated_sql, gcs_links = _extract_sql_and_citations(tool_responses, final_text)

    return {
        "final_text": final_text,
        "execution_engine": f"ADK_2.0_RUNNER ({MODEL})",
        "dispatch_mode": dispatch_mode,
        "tool_calls": tool_calls,
        "tool_responses": tool_responses,
        "generated_sql": generated_sql,
        "gcs_links": gcs_links,
        "plotly_spec": _build_plotly_spec(is_finops_chart),
    }


async def execute_agent_query(
    message: str,
    session_id: str = "default",
    oauth_context: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Executes the ADK coordinator across the 3 decoupled tool gateways (with OAuth 2.0 propagation)."""
    start_time = time.time()
    if oauth_context:
        set_current_oauth_context(
            token=oauth_context.get("token", ""),
            user_email=oauth_context.get("user_email", ""),
            source=oauth_context.get("source", "API_REQUEST"),
        )
    active_oauth = get_current_oauth_context()

    # 1. Primary Path: Genuine Google ADK 2.0 InMemoryRunner execution
    try:
        adk_result = await _try_adk_runner_execution(message, session_id, active_oauth)
        if adk_result:
            return {
                "session_id": session_id,
                "message": message,
                "oauth2_delegation_status": (
                    "VERIFIED_BEARER_TOKEN" if active_oauth.get("token") else "LOCAL_SESSION_IDENTITY"
                ),
                "authenticated_user": active_oauth.get("user_email") or "studio-developer@cymbal.enterprise",
                **adk_result,
                "latency_ms": int((time.time() - start_time) * 1000),
            }
    except Exception as exc:
        logger.info("ADK LLM live call skipped/fallback to Deterministic Hybrid Router: %s", exc)

    # 2. Resilient Deterministic Hybrid Router (Offline / Zero-Quota Lab Guarantee)
    msg_lower = message.lower()
    tool_calls: List[Dict[str, Any]] = []
    tool_responses: List[Dict[str, Any]] = []
    final_sections: List[str] = []
    dispatch_mode = "SINGLE_TOOL_DISPATCH"

    # Bilingual Out-of-Domain or Policy RAG detection
    out_of_domain = any(
        w in msg_lower
        for w in [
            "coffee", "espresso", "descale", "oil change", "f-150", "recipe", "weather", "vacation",
            "커피", "에스프레소", "석회", "청소", "날씨", "점심", "구내식당", "휴가",
        ]
    )
    is_policy_query = any(
        w in msg_lower
        for w in [
            "sec-pol", "fin-pol", "net-pol", "data-pol", "sop", "policy", "firewall", "vpc-sc",
            "psc-i", "dlp", "manual", "방화벽", "보안", "규정", "포트", "매뉴얼", "절차", "마스킹",
        ]
    )
    is_finops_query = any(
        w in msg_lower
        for w in [
            "burn rate", "finops", "budget", "spend", "overrun", "idle", "gpu", "proj-ai-prod-01",
            "proj-llm-serve-04", "예산", "소진율", "비용", "지출", "낭비",
        ]
    )
    is_ticket_query = any(
        w in msg_lower
        for w in [
            "ticket", "incident", "open", "servicedesk", "approval", "audit", "compare", "inc-2026",
            "티켓", "인시던트", "장애", "승인", "감사", "비교",
        ]
    )

    if out_of_domain:
        rag_res = it_policy_rag_tool(message)
        tool_calls.append({"name": "it_policy_rag_tool", "args": {"query": message}})
        tool_responses.append({"name": "it_policy_rag_tool", "response": rag_res})
        return {
            "session_id": session_id,
            "message": message,
            "final_text": CERTIFIED_REFUSAL_MESSAGE,
            "execution_engine": "DETERMINISTIC_HYBRID_ROUTER (ADK Tool Direct)",
            "dispatch_mode": "CERTIFIED_REFUSAL_GUARDRAIL",
            "oauth2_delegation_status": (
                "VERIFIED_BEARER_TOKEN" if active_oauth.get("token") else "LOCAL_SESSION_IDENTITY"
            ),
            "authenticated_user": active_oauth.get("user_email") or "studio-developer@cymbal.enterprise",
            "tool_calls": tool_calls,
            "tool_responses": tool_responses,
            "generated_sql": "",
            "gcs_links": [],
            "plotly_spec": None,
            "latency_ms": int((time.time() - start_time) * 1000),
        }

    is_ticket_creation = is_ticket_query and any(
        w in msg_lower for w in ["open a", "open ticket", "firewall ticket", "create", "생성", "오픈 티켓", "발행"]
    )
    is_parallel_audit = (is_finops_query and is_ticket_query) and not is_ticket_creation

    # Parallel Dispatch: FinOps Burn Rate + Live IT Service Desk Incidents
    if is_parallel_audit:
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
            f"- **OAuth 2.0 Requester Audit**: `{itsm_res.get('authenticated_requester')}` (`{itsm_res.get('oauth2_delegation_status')}`)\n"
            f"- **Active Service Desk Incidents ({itsm_res['active_incidents_count']})**:\n"
            + "\n".join([f"  - `{t['ticket_id']}` [{t['type']}]: {t['detail']}" for t in itsm_res.get("open_tickets", [])])
        )
    elif is_ticket_creation:
        dispatch_mode = "SINGLE_TOOL_ACTION (Gateway 3 2PC HITL Ticket + OAuth Delegation)"
        itsm_res = it_servicedesk_tool("PROJ-AI-PROD-01", action_type="FIREWALL_OPEN", justification=message)
        tool_calls.append({"name": "it_servicedesk_tool", "args": {"project_id": "PROJ-AI-PROD-01", "action_type": "FIREWALL_OPEN"}})
        tool_responses.append({"name": "it_servicedesk_tool", "response": itsm_res})
        final_sections.append(
            f"### 🎫 2-Phase Commit HITL Ticket Created\n"
            f"- **Ticket ID**: `{itsm_res['ticket_id']}`\n"
            f"- **Status**: `{itsm_res['status']}` (Approver: {itsm_res['required_approver']})\n"
            f"- **Authenticated Requester (OAuth 2.0)**: `{itsm_res['authenticated_requester']}`\n"
            f"- **OAuth Delegation Audit**: `{itsm_res['oauth2_delegation_status']}`\n"
            f"- **2PC Idempotency Lock**: `{itsm_res['idempotency_2pc_lock']}`"
        )
    elif is_policy_query:
        dispatch_mode = "SINGLE_TOOL_RAG (Gateway 2 Vector RAG + Window Stitching)"
        rag_res = it_policy_rag_tool(message)
        tool_calls.append({"name": "it_policy_rag_tool", "args": {"query": message}})
        tool_responses.append({"name": "it_policy_rag_tool", "response": rag_res})
        final_sections.append(rag_res)
    else:
        dispatch_mode = "SINGLE_TOOL_ANALYTICS (Gateway 1 FinOps Gold Ledger)"
        fin_res = finops_bq_tool(message)
        tool_calls.append({"name": "finops_bq_tool", "args": {"query_or_project_id": message}})
        tool_responses.append({"name": "finops_bq_tool", "response": fin_res})
        if "burn_rate_pct" in fin_res:
            final_sections.append(
                f"### 📊 Cloud FinOps Analytics: {fin_res['project_id']}\n"
                f"- **Department / Service**: {fin_res.get('department', 'Enterprise')} / {fin_res['service_name']}\n"
                f"- **Monthly Budget**: `${fin_res['monthly_budget_usd']:,.2f}` | **Current Spend**: `${fin_res['current_spend_usd']:,.2f}`\n"
                f"- **Budget Burn Rate**: **`{fin_res['burn_rate_pct']}%`** (`{fin_res['alert_status']}`)\n"
                f"- **Idle GPU Waste**: `${fin_res['idle_gpu_waste_usd']:,.2f}`"
            )
        else:
            final_sections.append(fin_res.get("summary", str(fin_res)))

    final_text = "\n\n".join(final_sections)
    generated_sql, gcs_links = _extract_sql_and_citations(tool_responses, final_text)
    is_finops_chart = is_finops_query or dispatch_mode.startswith("PARALLEL")

    return {
        "session_id": session_id,
        "message": message,
        "final_text": final_text,
        "execution_engine": "DETERMINISTIC_HYBRID_ROUTER (ADK Tool Direct)",
        "dispatch_mode": dispatch_mode,
        "oauth2_delegation_status": (
            "VERIFIED_BEARER_TOKEN" if active_oauth.get("token") else "LOCAL_SESSION_IDENTITY"
        ),
        "authenticated_user": active_oauth.get("user_email") or "studio-developer@cymbal.enterprise",
        "tool_calls": tool_calls,
        "tool_responses": tool_responses,
        "generated_sql": generated_sql,
        "gcs_links": gcs_links,
        "plotly_spec": _build_plotly_spec(is_finops_chart),
        "latency_ms": int((time.time() - start_time) * 1000),
    }


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/studio/")


@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "agent": "enterprise_hub_agent",
        "adk_runner_active": _ADK_RUNNER is not None,
        "contracts": ["A2A", "ReasoningEngine"],
    }


@app.post("/api/chat")
async def studio_chat(req: ChatRequest, request: Request) -> Dict[str, Any]:
    oauth_info = _extract_oauth_from_request(request, source="STUDIO_WEB_UI")
    return await execute_agent_query(req.message, req.session_id or "default", oauth_context=oauth_info)
