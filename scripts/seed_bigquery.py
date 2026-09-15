#!/usr/bin/env python3
# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Seeds all 100 enterprise test records into BigQuery (`enterprise_finops_gold`).

Tables seeded:
1. `cloud_billing_export` (32 enterprise FinOps project records)
2. `it_security_policy_embeddings` (36 policy chunks across 12 policies)
3. `itsm_realtime_incidents` (32 IT Service Desk incidents & 2PC locks)
"""
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def seed_bigquery() -> None:
    project_id = os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset_id = os.getenv("BQ_FINOPS_DATASET", "enterprise_finops_gold")

    finops_path = DATA_DIR / "finops_billing_ledger.json"
    policy_path = DATA_DIR / "it_security_policy_chunks.json"
    itsm_path = DATA_DIR / "it_servicedesk_incidents.json"

    with open(finops_path, "r", encoding="utf-8") as f:
        finops_records = json.load(f)
    with open(policy_path, "r", encoding="utf-8") as f:
        policy_records = json.load(f)
    with open(itsm_path, "r", encoding="utf-8") as f:
        itsm_records = json.load(f)

    print(
        f"📦 Loaded local JSON datasets: "
        f"FinOps={len(finops_records)} rows, "
        f"Policy Chunks={len(policy_records)} rows, "
        f"ITSM Incidents={len(itsm_records)} rows "
        f"(Total={len(finops_records) + len(policy_records) + len(itsm_records)} records)."
    )

    if not project_id or project_id == "<YOUR_PROJECT_ID>":
        print("⚠️ No active GOOGLE_CLOUD_PROJECT set; skipping live BigQuery upload (local JSON Gold Ledger active).")
        return

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project_id)
        dataset_ref = f"{project_id}.{dataset_id}"
        client.create_dataset(dataset_ref, exists_ok=True)

        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
        )

        # 1. Seed FinOps Billing Export (32 rows)
        table_finops = f"{dataset_ref}.cloud_billing_export"
        job1 = client.load_table_from_json(finops_records, table_finops, job_config=job_config)
        job1.result()
        print(f"✅ Seeded {len(finops_records)} rows into BigQuery table `{table_finops}`")

        # 2. Seed IT Security Policy Embeddings (36 rows)
        table_policy = f"{dataset_ref}.it_security_policy_embeddings"
        job2 = client.load_table_from_json(policy_records, table_policy, job_config=job_config)
        job2.result()
        print(f"✅ Seeded {len(policy_records)} rows into BigQuery table `{table_policy}`")

        # 3. Seed ITSM Realtime Incidents (32 rows)
        table_itsm = f"{dataset_ref}.itsm_realtime_incidents"
        job3 = client.load_table_from_json(itsm_records, table_itsm, job_config=job_config)
        job3.result()
        print(f"✅ Seeded {len(itsm_records)} rows into BigQuery table `{table_itsm}`")

    except Exception as exc:
        print(f"⚠️ Live BigQuery load encountered non-fatal warning (using local JSON Gold Ledger): {exc}")


if __name__ == "__main__":
    seed_bigquery()
