# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Enterprise Cloud FinOps & IT Hub Coordinator Agent (enterprise_hub_agent).

Orchestrates 3 Decoupled Tool Gateways via Google ADK 2.0:
1. Gateway 1: Structured FinOps Analytics (`finops_bq_tool`)
2. Gateway 2: IT Security Policy Vector RAG with Window Stitching (`it_policy_rag_tool`)
3. Gateway 3: Dual-Mode IT Service Desk & Quota Action Gateway (`it_servicedesk_tool`)
"""
import datetime
import logging
import os
from typing import Any, Optional

try:
    from dotenv import load_dotenv

    # NOTE: override=False (the default) on purpose — real environment variables
    # must win over the local .env file. This keeps behaviour identical across
    # local runs, Cloud Run (--set-env-vars) and Agent Engine (env_vars=...),
    # and lets participants override a single value ad hoc, e.g.
    #   USE_ADK_LLM=false .venv/bin/uvicorn app.fast_api_app:app
    # Every other module in this project already loads dotenv this way; agent.py
    # previously used override=True, which silently ignored such overrides.
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.agents import Agent
    from google.adk.apps import App
    from google.adk.models import Gemini
    from google.genai import types
except ImportError:
    class Agent:
        def __init__(self, name, model=None, instruction="", tools=None, before_agent_callback=None):
            self.name = name
            self.model = model
            self.instruction = instruction
            self.tools = tools or []
            self.before_agent_callback = before_agent_callback

    class App:
        def __init__(self, name="enterprise_hub_agent", root_agent=None, agent=None, plugins=None):
            self.name = name
            self.root_agent = root_agent or agent
            self.plugins = plugins or []

    class Gemini:
        def __init__(self, model, retry_options=None):
            self.model = model
            self.retry_options = retry_options

    class _Types:
        class HttpRetryOptions:
            def __init__(self, attempts=3):
                self.attempts = attempts

    types = _Types()

from .tools.finops_bq_tool import finops_bq_tool
from .tools.it_policy_rag_tool import it_policy_rag_tool
from .tools.it_servicedesk_tool import it_servicedesk_tool

logger = logging.getLogger(__name__)

MODEL = os.getenv("AGENT_MODEL", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = """You are the Enterprise Cloud FinOps & IT Hub Coordinator Agent (`enterprise_hub_agent`), integrated into Gemini Enterprise.
You orchestrate 3 specialized, decoupled tool gateways to assist employees, FinOps analysts, and security engineers:

1. `finops_bq_tool`: Structured FinOps Analytics gateway querying BigQuery (`enterprise_finops_gold.cloud_billing_export`).
   - Always report standardized business formulas verbatim (Budget Burn Rate %, Idle GPU Waste USD, Alert Status).

2. `it_policy_rag_tool`: Vector similarity search with adjacent context window stitching (`N-1` to `N+1`) over corporate IT & Security manuals (`SEC-POL-2026-FW`, `FIN-POL-2026-GPU`, `NET-POL-2026-PSCI`, `DATA-POL-2026-DLP`).
   - Always include the clickable HTTPS GCS citation URL (`https://storage.cloud.google.com/...`) in your final response.

3. `it_servicedesk_tool`: Real-time IT Service Desk telemetry and 2-Phase Commit (2PC) HITL ticket creation (`FIREWALL_OPEN`, `GPU_QUOTA_INCREASE`, `STATUS_CHECK`) with OAuth 2.0 user identity delegation.

DISPATCH & GROUNDING PROTOCOLS:
- SINGLE-TOOL DISPATCH: Route direct policy or technical questions to `it_policy_rag_tool` first. If `it_policy_rag_tool` returns the certified refusal message ("I cannot find certified corporate IT or security policies for this request in our technical repository."), reply ONLY with that exact refusal sentence without adding unverified advice.
- PARALLEL TOOL DISPATCH: When asked to audit a project's live incidents alongside its FinOps budget burn rate (e.g., for `PROJ-AI-PROD-01`), invoke BOTH `finops_bq_tool` AND `it_servicedesk_tool` concurrently in Turn 1.
- STRICT GROUNDING: Base every sentence strictly on returned tool payloads. Never fabricate ticket IDs, budget figures, or policy links.
"""


def validate_and_update_temporal_cache(
    callback_context: Any = None, current_date_str: Optional[str] = None
) -> Any:
    """Purges cached overrun project state if the calendar day has rolled over.

    IMPORTANT: The first parameter MUST be named `callback_context` because Google ADK 2.x
    invokes lifecycle callbacks using a keyword argument: `callback(callback_context=ctx)`.
    Renaming it breaks the ADK runtime with a `TypeError` (`[확인됨 / Verified: adk/agents/base_agent.py`]).

    Supports both:
    1. ADK `before_agent_callback(callback_context: CallbackContext)` lifecycle execution
    2. Direct dictionary invocation `validate_and_update_temporal_cache(state_dict, date_str)` for unit testing
    """
    is_callback_ctx = hasattr(callback_context, "state") and not isinstance(callback_context, dict)
    session_state = callback_context.state if is_callback_ctx else callback_context

    if session_state is None:
        return None

    today_str = current_date_str or datetime.date.today().isoformat()
    cached_date = session_state.get("top_overrun_date")

    if cached_date and cached_date != today_str:
        logger.info("Temporal cache invalidation: purging stale top_overrun_project from %s", cached_date)
        session_state["top_overrun_project"] = None
        session_state["top_overrun_date"] = today_str
    elif not cached_date:
        session_state["top_overrun_date"] = today_str

    # ADK before_agent_callback must return None so normal agent execution proceeds
    return None if is_callback_ctx else session_state


retry_options = getattr(types, "HttpRetryOptions", None)
retry_cfg = retry_options(attempts=3) if retry_options else None

root_agent = Agent(
    name="enterprise_hub_agent",
    model=Gemini(model=MODEL, retry_options=retry_cfg),
    instruction=SYSTEM_INSTRUCTION,
    tools=[finops_bq_tool, it_policy_rag_tool, it_servicedesk_tool],
    before_agent_callback=validate_and_update_temporal_cache,
)

_plugins = []
_project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
_dataset_id = os.environ.get("BQ_TELEMETRY_DATASET", "agent_telemetry")
_location = os.environ.get("REGION", "us-central1")

try:
    from google.adk.plugins.bigquery_agent_analytics_plugin import (
        BigQueryAgentAnalyticsPlugin,
        BigQueryLoggerConfig,
    )

    if _project_id and _project_id != "<YOUR_PROJECT_ID>":
        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(),
            )
        )
except ImportError:
    logger.info("BigQueryAgentAnalyticsPlugin not installed; continuing with standard telemetry.")

app = App(
    name="enterprise_hub_agent",
    root_agent=root_agent,
    plugins=_plugins,
)
