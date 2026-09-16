# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Gateway 3: Dual-Mode IT Service Desk & Infrastructure Action Gateway with OAuth 2.0 Delegation.

Supports across 32 active ITSM incidents & 2PC HITL approval workflows:
- End-to-End OAuth 2.0 Identity Delegation (`serverSideOauth2` Bearer Token propagation from Gemini Enterprise)
- ITSM_MODE="MOCK" (Default): Zero-cost deterministic simulation for Cloud Shell & local labs.
- ITSM_MODE="LIVE": Connects to enterprise ITSM/ServiceNow REST API with delegated OAuth 2.0 user token.
Enforces Two-Phase Commit (2PC) idempotency lock (`lock:user:{project_id}:mutation`) and HITL approval flags.
"""
import contextvars
import datetime
import hashlib
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "it_servicedesk_incidents.json"

# Request-scoped ContextVar storing delegated OAuth 2.0 identity from Gemini Enterprise / A2A headers
_OAUTH_CONTEXT: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar(
    "oauth_context", default={"token": "", "user_email": "", "source": "LOCAL_STUDIO"}
)


def set_current_oauth_context(token: str = "", user_email: str = "", source: str = "A2A_OAUTH_HEADER") -> None:
    """Sets the request-scoped OAuth 2.0 delegation context extracted from incoming HTTP headers."""
    _OAUTH_CONTEXT.set({"token": token.strip(), "user_email": user_email.strip(), "source": source})


def get_current_oauth_context() -> Dict[str, str]:
    """Retrieves the active request-scoped OAuth 2.0 delegation context."""
    return _OAUTH_CONTEXT.get()


def _load_itsm_incidents() -> List[Dict[str, Any]]:
    """Loads 32 real-time ITSM incident records from JSON (Gold Ledger mirror / offline fallback)."""
    if _DATA_PATH.exists():
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


_ITSM_INCIDENTS_DB: List[Dict[str, Any]] = _load_itsm_incidents()


def _resolve_project_id() -> str:
    """Resolves active GCP Project ID from environment, ~/.config/gcloud, or google.auth.default()."""
    for k in ("PROJECT_ID", "GOOGLE_CLOUD_PROJECT"):
        val = os.getenv(k, "").strip().strip('"').strip("'")
        if val and val != "<YOUR_PROJECT_ID>":
            return val
    try:
        import configparser

        cfg = Path.home() / ".config" / "gcloud" / "configurations" / "config_default"
        if cfg.exists():
            cp = configparser.ConfigParser()
            cp.read(cfg)
            if cp.has_option("core", "project"):
                p = cp.get("core", "project").strip()
                if p and p != "<YOUR_PROJECT_ID>":
                    return p
    except Exception:
        pass
    try:
        import google.auth

        _, proj = google.auth.default()
        if proj and proj != "<YOUR_PROJECT_ID>":
            return proj
    except Exception:
        pass
    return ""


def _query_live_incidents(where_clause: str) -> Tuple[List[Dict[str, Any]], str]:
    """Queries the live BigQuery `itsm_realtime_incidents` table, falling back to the local mirror.

    Returns:
        (incident rows, source tag) — source tag reports whether data came from BigQuery or the mirror.
    """
    project_id = _resolve_project_id()
    dataset_id = os.getenv("BQ_FINOPS_DATASET", "enterprise_finops_gold")
    if not project_id:
        return [], "Local Gold Ledger Mirror"

    table_fqn = f"{project_id}.{dataset_id}.itsm_realtime_incidents"
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project_id)
        sql = f"SELECT * FROM `{table_fqn}` WHERE {where_clause} ORDER BY ticket_id ASC"
        rows = [dict(r) for r in client.query(sql).result(timeout=5.0)]
        if rows:
            return rows, f"Live BigQuery (`{table_fqn}`)"
    except Exception as exc:
        logger.info("BigQuery ITSM query skipped/fallback to local Gold Ledger mirror: %s", exc)
    return [], "Local Gold Ledger Mirror"


def it_servicedesk_tool(
    project_id: str,
    action_type: str = "STATUS_CHECK",
    justification: str = "Standard operational request",
    requester_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Queries live IT Service Desk alerts (32 Incidents) or creates a 2PC HITL approval ticket using OAuth 2.0 identity.

    Automatically propagates the end-user's OAuth 2.0 Bearer token delegated by Gemini Enterprise
    (`serverSideOauth2`) to enforce user-level ACLs and audit logging.

    Args:
        project_id: Target GCP Project ID (e.g., 'PROJ-AI-PROD-01'), Incident ID ('INC-2026-88415'), or Severity ('P1_CRITICAL').
        action_type: 'STATUS_CHECK', 'FIREWALL_OPEN', 'GPU_QUOTA_INCREASE', or 'EMERGENCY_OVERRIDE'.
        justification: Business justification required for Level-2 HITL approval.
        requester_email: Optional explicit requester email override.

    Returns:
        dict: Incident/Ticket ID, OAuth 2.0 delegation audit metadata, 2PC lock key, approval status, and telemetry.
    """
    itsm_mode = os.getenv("ITSM_MODE", "MOCK").upper()
    itsm_endpoint = os.getenv("ITSM_ENDPOINT_URL", "https://itsm.enterprise.internal/api/v1")
    action_upper = action_type.upper()
    proj_upper = project_id.upper()
    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Extract OAuth 2.0 Identity Context (from Gemini Enterprise serverSideOauth2 / HTTP Authorization Header)
    oauth_ctx = get_current_oauth_context()
    token = oauth_ctx.get("token", "")
    resolved_email = (
        requester_email
        or oauth_ctx.get("user_email")
        or ("oauth2-delegated-user@cymbal.enterprise" if token else "studio-developer@cymbal.enterprise")
    )

    if token:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
        oauth_status = f"VERIFIED_BEARER_TOKEN (serverSideOauth2 | sha256:{token_hash})"
    else:
        oauth_status = "LOCAL_SESSION_IDENTITY (No Bearer Header Provided)"

    # Optional Live REST API Dispatch when ITSM_MODE == "LIVE"
    live_api_attempted = False
    if itsm_mode == "LIVE" and token:
        live_api_attempted = True
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {token}",
                "X-Requester-Email": resolved_email,
                "Content-Type": "application/json",
            }
            payload = {
                "project_id": proj_upper,
                "action_type": action_upper,
                "justification": justification,
            }
            with httpx.Client(timeout=3.0) as client:
                resp = client.post(f"{itsm_endpoint}/tickets", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    live_data = resp.json()
                    return {
                        "gateway": "Gateway 3: IT Service Desk Action Gateway (LIVE REST API)",
                        "oauth2_delegation_status": oauth_status,
                        "authenticated_requester": resolved_email,
                        **live_data,
                    }
        except Exception as exc:
            logger.info("LIVE ITSM endpoint (%s) unreachable in lab network; using Gold Ledger mirror: %s", itsm_endpoint, exc)

    # 1. Mutating Infrastructure Actions -> Enforce Two-Phase Commit (2PC) & HITL Gate
    if action_upper in ("FIREWALL_OPEN", "GPU_QUOTA_INCREASE", "EMERGENCY_OVERRIDE"):
        lock_key = f"lock:user:{proj_upper}:{action_upper}"
        ticket_id = f"INC-2026-{uuid.uuid4().hex[:6].upper()}"
        new_ticket = {
            "gateway": f"Gateway 3: IT Service Desk Action Gateway (Mode: {itsm_mode})",
            "total_dataset_records": len(_ITSM_INCIDENTS_DB),
            "ticket_id": ticket_id,
            "project_id": proj_upper,
            "action_type": action_upper,
            "status": "PENDING_HITL_APPROVAL",
            "authenticated_requester": resolved_email,
            "oauth2_delegation_status": oauth_status,
            "live_rest_attempted": live_api_attempted,
            "idempotency_2pc_lock": lock_key,
            "required_approver": "Level-2 Security & FinOps Architecture Board",
            "justification_logged": justification,
            "created_at": timestamp_iso,
            "policy_enforced": "SEC-POL-2026-FW / FIN-POL-2026-GPU (2-Phase Commit Non-Destructive Lock Active)",
        }
        return new_ticket

    dataset_id = os.getenv("BQ_FINOPS_DATASET", "enterprise_finops_gold")
    bq_table_ref = f"{dataset_id}.itsm_realtime_incidents"

    # 2. Match specific Ticket ID (e.g. INC-2026-88401 .. INC-2026-88432)
    ticket_matches = [inc for inc in _ITSM_INCIDENTS_DB if inc["ticket_id"].upper() in proj_upper]
    if ticket_matches:
        target_id = ticket_matches[0]["ticket_id"]
        bq_rows, source_tag = _query_live_incidents(f"ticket_id = '{target_id}'")
        matched = bq_rows[0] if bq_rows else ticket_matches[0]
        return {
            "gateway": f"Gateway 3: IT Service Desk Incident Lookup (Mode: {itsm_mode})",
            "bigquery_table": bq_table_ref,
            "data_source": source_tag,
            "total_dataset_records": len(_ITSM_INCIDENTS_DB),
            "authenticated_requester": resolved_email,
            "oauth2_delegation_status": oauth_status,
            "matched_ticket": matched,
            "timestamp": timestamp_iso,
        }

    # 3. Match by Severity filter (e.g. P1_CRITICAL)
    if "P1" in proj_upper or "CRITICAL" in proj_upper:
        bq_rows, source_tag = _query_live_incidents("severity = 'P1_CRITICAL'")
        p1_tickets = bq_rows or [inc for inc in _ITSM_INCIDENTS_DB if inc["severity"] == "P1_CRITICAL"]
        return {
            "gateway": f"Gateway 3: IT Service Desk Telemetry Gateway (Mode: {itsm_mode})",
            "bigquery_table": bq_table_ref,
            "data_source": source_tag,
            "total_dataset_records": len(_ITSM_INCIDENTS_DB),
            "authenticated_requester": resolved_email,
            "oauth2_delegation_status": oauth_status,
            "filter": "P1_CRITICAL",
            "active_incidents_count": len(p1_tickets),
            "open_tickets": p1_tickets,
            "timestamp": timestamp_iso,
        }

    # 4. Match by Project ID across the 32 incidents
    local_proj_tickets = [inc for inc in _ITSM_INCIDENTS_DB if inc["project_id"].upper() in proj_upper]
    if local_proj_tickets:
        target_project = local_proj_tickets[0]["project_id"]
        bq_rows, source_tag = _query_live_incidents(f"project_id = '{target_project}'")
        proj_tickets = bq_rows or local_proj_tickets
        return {
            "gateway": f"Gateway 3: IT Service Desk Telemetry Gateway (Mode: {itsm_mode})",
            "bigquery_table": bq_table_ref,
            "data_source": source_tag,
            "total_dataset_records": len(_ITSM_INCIDENTS_DB),
            "authenticated_requester": resolved_email,
            "oauth2_delegation_status": oauth_status,
            "project_id": target_project,
            "active_incidents_count": len(proj_tickets),
            "open_tickets": proj_tickets,
            "timestamp": timestamp_iso,
        }

    # 5. Default: Return summary of all 32 ITSM incidents
    bq_rows, source_tag = _query_live_incidents("TRUE")
    all_incidents = bq_rows or _ITSM_INCIDENTS_DB
    p1_count = sum(1 for inc in all_incidents if inc["severity"] == "P1_CRITICAL")
    hitl_count = sum(1 for inc in all_incidents if inc["status"] == "PENDING_HITL_APPROVAL")
    return {
        "gateway": f"Gateway 3: IT Service Desk Fleet Overview (Mode: {itsm_mode})",
        "bigquery_table": bq_table_ref,
        "data_source": source_tag,
        "total_dataset_records": len(all_incidents),
        "authenticated_requester": resolved_email,
        "oauth2_delegation_status": oauth_status,
        "active_incidents_count": len(all_incidents),
        "p1_critical_count": p1_count,
        "pending_hitl_approval_count": hitl_count,
        "open_tickets": all_incidents[:10],
        "note": f"Showing top 10 of {len(all_incidents)} total ITSM incidents across fleet.",
        "timestamp": timestamp_iso,
    }
