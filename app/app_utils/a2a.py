# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Attach Agent2Agent (A2A) Protocol Endpoints with Gemini Enterprise Hardening.

Guarantees that GET /.well-known/agent-card.json outputs `defaultInputModes: ["text/plain"]`
and `defaultOutputModes: ["text/plain"]` so Gemini Enterprise UI validation succeeds without error.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def get_hardened_agent_card(base_url: str, agent_name: str = "enterprise_hub_agent") -> Dict[str, Any]:
    """Returns a Gemini Enterprise-hardened A2A Agent Card with explicit text/plain MIME types."""
    rpc_url = f"{base_url.rstrip('/')}/a2a/{agent_name}"
    return {
        "name": agent_name,
        "description": (
            "Enterprise Cloud FinOps & IT Hub Coordinator Agent. Orchestrates BigQuery FinOps burn rate "
            "analytics, IT Security SOP Vector RAG with window stitching (SEC-POL-2026-FW), and 2PC HITL "
            "Service Desk ticket creation."
        ),
        "url": rpc_url,
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        # CRITICAL GOTCHA FIX FOR GEMINI ENTERPRISE REGISTRATION:
        # Must use standard MIME type 'text/plain' instead of 'text'
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [
            {
                "id": "finops_burn_rate_audit",
                "name": "Cloud FinOps Budget & Idle GPU Waste Audit",
                "description": "Queries BigQuery FinOps Gold Ledger using standardized burn rate formulas.",
                "tags": ["finops", "bigquery", "cloud-billing"],
                "examples": ["Check budget burn rate and idle GPU waste for PROJ-AI-PROD-01"],
            },
            {
                "id": "it_security_policy_rag",
                "name": "IT Security Policy Vector RAG (Window Stitching)",
                "description": "Retrieves certified firewall & VPC-SC SOPs with N-1~N+1 window stitching.",
                "tags": ["security", "rag", "vpc-sc", "firewall"],
                "examples": ["What is the SOP for firewall port opening under SEC-POL-2026-FW?"],
            },
            {
                "id": "it_servicedesk_action",
                "name": "IT Service Desk 2PC Ticket Creation",
                "description": "Creates HITL approval tickets for firewall openings or GPU quota increases.",
                "tags": ["itsm", "servicenow", "hitl"],
                "examples": ["Open a firewall ticket for PROJ-AI-PROD-01 to enable PSC-I southbound access"],
            },
        ],
    }


def attach_a2a_routes(app: FastAPI, agent_name: str = "enterprise_hub_agent") -> None:
    """Mounts Gemini Enterprise A2A discovery and JSON-RPC endpoints onto FastAPI."""

    @app.get(f"/a2a/{agent_name}/.well-known/agent-card.json")
    @app.get("/.well-known/agent-card.json")
    async def serve_agent_card(request: Request) -> JSONResponse:
        base_url = os.getenv("APP_URL") or str(request.base_url).rstrip("/")
        return JSONResponse(content=get_hardened_agent_card(base_url=base_url, agent_name=agent_name))

    @app.post(f"/a2a/{agent_name}")
    async def handle_a2a_jsonrpc(request: Request) -> JSONResponse:
        body = await request.json()
        rpc_id = body.get("id", "1")
        params = body.get("params", {})
        message_obj = params.get("message", {})
        parts = message_obj.get("parts", [])
        user_text = ""
        for p in parts:
            if isinstance(p, dict) and "text" in p:
                user_text += p["text"] + " "
        if not user_text:
            user_text = str(params.get("input", "Check status of PROJ-AI-PROD-01"))

        # Delegate to our unified chat executor
        from app.fast_api_app import execute_agent_query

        result = await execute_agent_query(user_text.strip())
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "id": f"task-{rpc_id}",
                    "status": {"state": "completed"},
                    "artifacts": [
                        {
                            "parts": [{"type": "text", "text": result["final_text"]}],
                        }
                    ],
                },
            }
        )
