# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Vertex AI Agent Engine (Reasoning Engine) Contract Adapter with OAuth 2.0 Delegation.

Exposes POST /api/reasoning_engine and POST /api/stream_reasoning_engine so that
both Vertex AI Console Playground and Gemini Enterprise Native Agent Engine integration
can invoke the container directly while propagating user OAuth 2.0 credentials.
"""
from __future__ import annotations

import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.app_utils.a2a import _extract_oauth_from_request


def attach_reasoning_engine_routes(app: FastAPI) -> None:
    """Registers /api/reasoning_engine and /api/stream_reasoning_engine endpoints."""

    @app.post("/api/reasoning_engine")
    async def reasoning_engine_sync(request: Request) -> JSONResponse:
        oauth_info = _extract_oauth_from_request(request, source="REASONING_ENGINE_CONTRACT")
        body = await request.json()
        inp = body.get("input", {})
        query_text = inp.get("input") or inp.get("query") or str(inp)
        from app.fast_api_app import execute_agent_query

        result = await execute_agent_query(query_text, oauth_context=oauth_info)
        return JSONResponse(
            content={
                "output": {
                    "response": result["final_text"],
                    "execution_engine": result.get("execution_engine", "ADK_2.0"),
                    "dispatch_mode": result["dispatch_mode"],
                    "tool_calls": result["tool_calls"],
                    "gcs_citations": result["gcs_links"],
                }
            }
        )

    @app.post("/api/stream_reasoning_engine")
    async def reasoning_engine_stream(request: Request) -> StreamingResponse:
        oauth_info = _extract_oauth_from_request(request, source="REASONING_ENGINE_STREAM")
        body = await request.json()
        inp = body.get("input", {})
        query_text = inp.get("input") or inp.get("query") or str(inp)
        from app.fast_api_app import execute_agent_query

        result = await execute_agent_query(query_text, oauth_context=oauth_info)

        async def event_generator():
            yield json.dumps({
                "output": result["final_text"],
                "execution_engine": result.get("execution_engine", "ADK_2.0"),
                "dispatch_mode": result["dispatch_mode"],
            }) + "\n"

        return StreamingResponse(event_generator(), media_type="application/json")
