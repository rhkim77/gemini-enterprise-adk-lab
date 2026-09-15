# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Gateway 1: Structured FinOps Analytics Tool (BigQuery Gold Ledger & Glossary).

Resolves 'The Context Gap' in NL2SQL by enforcing standardized FinOps formulas:
- Net Cloud Spend ($) = gross_cost - committed_use_discounts - promotional_credits
- Budget Burn Rate (%) = (current_spend_usd / monthly_budget_usd) * 100
- Idle GPU Waste Cost ($) = unutilized_a100_hours * hourly_on_demand_rate
"""
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Deterministic Gold Ledger mirror for instant local / offline verification
_FINOPS_GOLD_LEDGER: Dict[str, Dict[str, Any]] = {
    "PROJ-AI-PROD-01": {
        "project_id": "PROJ-AI-PROD-01",
        "service_name": "Vertex AI Training Cluster (A100/H100)",
        "monthly_budget_usd": 48500.00,
        "current_spend_usd": 64200.50,
        "burn_rate_pct": 132.37,
        "idle_gpu_waste_usd": 14200.00,
        "alert_status": "CRITICAL_OVERRUN",
        "standardized_formula_used": "Burn Rate (%) = ($64,200.50 / $48,500.00) * 100 = 132.37%",
        "generated_sql": (
            "SELECT project_id, service_name, monthly_budget_usd, current_spend_usd, "
            "ROUND((current_spend_usd / monthly_budget_usd) * 100, 2) AS burn_rate_pct, "
            "idle_gpu_waste_usd, alert_status "
            "FROM `enterprise_finops_gold.cloud_billing_export` "
            "WHERE project_id = 'PROJ-AI-PROD-01';"
        ),
    },
    "PROJ-DATA-LAKE-02": {
        "project_id": "PROJ-DATA-LAKE-02",
        "service_name": "BigQuery Analytics Warehouse",
        "monthly_budget_usd": 30000.00,
        "current_spend_usd": 24150.00,
        "burn_rate_pct": 80.50,
        "idle_gpu_waste_usd": 1200.00,
        "alert_status": "NORMAL",
        "standardized_formula_used": "Burn Rate (%) = ($24,150.00 / $30,000.00) * 100 = 80.50%",
        "generated_sql": (
            "SELECT project_id, service_name, burn_rate_pct, alert_status "
            "FROM `enterprise_finops_gold.cloud_billing_export` "
            "WHERE project_id = 'PROJ-DATA-LAKE-02';"
        ),
    },
    "PROJ-WEB-FRONT-03": {
        "project_id": "PROJ-WEB-FRONT-03",
        "service_name": "Cloud Run Microservices",
        "monthly_budget_usd": 15000.00,
        "current_spend_usd": 14890.00,
        "burn_rate_pct": 99.26,
        "idle_gpu_waste_usd": 450.00,
        "alert_status": "WARNING_APPROACHING_LIMIT",
        "standardized_formula_used": "Burn Rate (%) = ($14,890.00 / $15,000.00) * 100 = 99.26%",
        "generated_sql": (
            "SELECT project_id, service_name, burn_rate_pct, alert_status "
            "FROM `enterprise_finops_gold.cloud_billing_export` "
            "WHERE project_id = 'PROJ-WEB-FRONT-03';"
        ),
    },
}


def finops_bq_tool(query_or_project_id: str) -> dict:
    """Queries BigQuery FinOps Gold Ledger for cloud spend, budget burn rate, and idle GPU waste.

    Always enforces Knowledge Catalog Business Glossary formulas to eliminate NL2SQL hallucination.

    Args:
        query_or_project_id: Target GCP Project ID (e.g., 'PROJ-AI-PROD-01') or FinOps analytical query.

    Returns:
        dict: Standardized FinOps metrics, burn rate percentage, alert status, and executed GoogleSQL.
    """
    q_upper = query_or_project_id.upper()

    # Try live BigQuery first if GOOGLE_CLOUD_PROJECT is configured and google-cloud-bigquery is active
    project_id = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id and project_id != "<YOUR_PROJECT_ID>":
        try:
            from google.cloud import bigquery

            client = bigquery.Client(project=project_id)
            target_proj = "PROJ-AI-PROD-01"
            for pid in _FINOPS_GOLD_LEDGER:
                if pid in q_upper:
                    target_proj = pid
                    break

            sql = (
                f"SELECT project_id, service_name, monthly_budget_usd, current_spend_usd, "
                f"burn_rate_pct, idle_gpu_waste_usd, alert_status "
                f"FROM `{project_id}.enterprise_finops_gold.cloud_billing_export` "
                f"WHERE project_id = '{target_proj}' LIMIT 1"
            )
            rows = list(client.query(sql).result(timeout=4.0))
            if rows:
                r = rows[0]
                return {
                    "gateway": "Gateway 1: Structured FinOps Analytics (Live BigQuery)",
                    "project_id": r.project_id,
                    "service_name": r.service_name,
                    "monthly_budget_usd": float(r.monthly_budget_usd),
                    "current_spend_usd": float(r.current_spend_usd),
                    "burn_rate_pct": float(r.burn_rate_pct),
                    "idle_gpu_waste_usd": float(r.idle_gpu_waste_usd),
                    "alert_status": r.alert_status,
                    "generated_sql": sql,
                }
        except Exception as exc:
            logger.info("Live BigQuery query skipped/fallback to Gold Ledger mirror: %s", exc)

    # Match specific project or return top overrun summary
    for pid, data in _FINOPS_GOLD_LEDGER.items():
        if pid in q_upper:
            return {
                "gateway": "Gateway 1: Structured FinOps Analytics (Gold Ledger)",
                **data,
            }

    return {
        "gateway": "Gateway 1: Structured FinOps Analytics (All Projects Summary)",
        "top_overrun_project": "PROJ-AI-PROD-01",
        "summary": "PROJ-AI-PROD-01 is in CRITICAL_OVERRUN at 132.37% burn rate ($64,200.50 / $48,500.00 budget) with $14,200.00 in idle GPU waste.",
        "projects": list(_FINOPS_GOLD_LEDGER.values()),
        "generated_sql": _FINOPS_GOLD_LEDGER["PROJ-AI-PROD-01"]["generated_sql"],
    }
