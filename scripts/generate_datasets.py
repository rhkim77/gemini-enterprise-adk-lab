#!/usr/bin/env python3
# ============================================================================
# GSP-ADK-GE-2026: Enterprise Raw Dataset Generator (30+ Records per Gateway)
# Generates:
#   - data/finops_billing_ledger.json       (32 Enterprise Cloud Projects)
#   - data/it_security_policy_chunks.json   (36 Chunks across 12 Policies for N-1~N+1 Stitching)
#   - data/it_servicedesk_incidents.json    (32 Live ITSM Incidents & 2PC Tickets)
# ============================================================================
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# 1. Gateway 1 Dataset: 32 Enterprise FinOps Cloud Billing Projects
# ----------------------------------------------------------------------------
FINOPS_PROJECTS = [
    ("PROJ-AI-PROD-01", "AI Research", "Vertex AI Training Cluster (H100)", "us-central1", 48500.00, 64200.50, 14200.00),
    ("PROJ-DATA-LAKE-02", "Data Platform", "BigQuery Analytics Warehouse", "us-central1", 30000.00, 24150.00, 1200.00),
    ("PROJ-WEB-FRONT-03", "Digital Marketing", "Cloud Run Microservices", "us-east1", 15000.00, 14890.00, 450.00),
    ("PROJ-LLM-SERVE-04", "AI Research", "Vertex AI Agent Engine Runtime", "us-central1", 60000.00, 78900.00, 18500.00),
    ("PROJ-RETAIL-POS-05", "Retail Core", "Cloud Spanner Global Ledger", "global", 45000.00, 41200.00, 0.00),
    ("PROJ-FINTECH-PAY-06", "FinTech Security", "GKE Autopilot Payment Gateway", "us-east1", 52000.00, 66800.00, 8900.00),
    ("PROJ-ERP-SAP-07", "Enterprise ERP", "Compute Engine SAP HANA Nodes", "europe-west1", 85000.00, 82100.00, 3400.00),
    ("PROJ-SUPPLY-CHAIN-08", "Supply Chain", "BigQuery Omni AWS S3 Federation", "us-central1", 22000.00, 19800.00, 600.00),
    ("PROJ-IOT-STREAM-09", "Cloud Infra", "Cloud Bigtable Telemetry Ingestion", "us-central1", 38000.00, 49100.00, 7200.00),
    ("PROJ-FRAUD-DET-10", "FinTech Security", "Vertex AI Real-Time Feature Store", "us-east1", 41000.00, 53400.00, 11300.00),
    ("PROJ-CUST-360-11", "Digital Marketing", "AlloyDB Vector Search Cluster", "us-central1", 28000.00, 21500.00, 950.00),
    ("PROJ-HR-PORTAL-12", "Enterprise ERP", "Cloud SQL Enterprise Plus", "asia-northeast3", 12000.00, 8400.00, 200.00),
    ("PROJ-SEC-SIEM-13", "FinTech Security", "Chronicle Security Operations", "global", 55000.00, 54200.00, 0.00),
    ("PROJ-DEV-SANDBOX-14", "AI Research", "Vertex AI Workbench Notebooks", "us-central1", 18000.00, 26700.00, 12400.00),
    ("PROJ-MEDIA-GEN-15", "Digital Marketing", "Imagen 3 & Veo Rendering Farm", "us-central1", 35000.00, 46200.00, 9800.00),
    ("PROJ-LOGISTICS-OPT-16", "Supply Chain", "Cloud Fleet Routing API & GKE", "europe-west1", 27000.00, 22400.00, 800.00),
    ("PROJ-HEALTH-NLP-17", "AI Research", "Healthcare NLP & Med-PaLM Cluster", "us-central1", 65000.00, 81900.00, 15600.00),
    ("PROJ-DATA-GOV-18", "Data Platform", "Dataplex Knowledge Catalog & DLP", "global", 19000.00, 14200.00, 0.00),
    ("PROJ-API-GW-19", "Cloud Infra", "Apigee X Multi-Region Proxy", "global", 32000.00, 31500.00, 0.00),
    ("PROJ-MOBILE-APP-20", "Retail Core", "Firebase & Cloud Functions Backend", "us-east1", 14000.00, 9800.00, 300.00),
    ("PROJ-REC-ENGINE-21", "Retail Core", "Discovery Engine Retail Search", "global", 42000.00, 48900.00, 4100.00),
    ("PROJ-BATCH-ETL-22", "Data Platform", "Cloud Dataflow Streaming Pipelines", "us-central1", 36000.00, 33100.00, 2100.00),
    ("PROJ-DR-BACKUP-23", "Cloud Infra", "Cloud Storage Multi-Region Archive", "global", 25000.00, 11200.00, 0.00),
    ("PROJ-VOICE-BOT-24", "Customer Support", "Gemini Multimodal Live API Nodes", "us-central1", 29000.00, 37800.00, 6400.00),
    ("PROJ-DOC-AI-25", "Enterprise ERP", "Document AI Invoice Parser", "us-east1", 16000.00, 15400.00, 500.00),
    ("PROJ-QA-PERF-26", "Cloud Infra", "Load Testing GKE Ephemeral Cluster", "us-central1", 21000.00, 28900.00, 11200.00),
    ("PROJ-PARTNER-EDI-27", "Supply Chain", "Pub/Sub & Cloud Integration Connectors", "europe-west1", 17500.00, 13900.00, 0.00),
    ("PROJ-CORP-NET-28", "Cloud Infra", "Cloud Interconnect & NCC Hub", "global", 40000.00, 38500.00, 0.00),
    ("PROJ-RISK-SIM-29", "FinTech Security", "Monte Carlo Risk HPC Cluster", "us-east1", 70000.00, 91000.00, 19400.00),
    ("PROJ-LOYALTY-DB-30", "Retail Core", "Memorystore for Redis Cluster", "asia-northeast3", 23000.00, 19200.00, 750.00),
    ("PROJ-SEARCH-ENT-31", "Enterprise ERP", "Gemini Enterprise Agentspace Tenant", "global", 50000.00, 47500.00, 1500.00),
    ("PROJ-OPS-MON-32", "Cloud Infra", "Cloud Monitoring & OpenTelemetry", "global", 15000.00, 12100.00, 0.00),
]

finops_records = []
for pid, dept, svc, reg, budget, spend, waste in FINOPS_PROJECTS:
    burn_rate = round((spend / budget) * 100, 2)
    if burn_rate >= 120.0:
        status = "CRITICAL_OVERRUN"
    elif burn_rate >= 95.0:
        status = "WARNING_APPROACHING_LIMIT"
    elif burn_rate >= 50.0:
        status = "NORMAL"
    else:
        status = "UNDERSPEND_OPTIMAL"

    finops_records.append({
        "project_id": pid,
        "department": dept,
        "service_name": svc,
        "region": reg,
        "monthly_budget_usd": budget,
        "current_spend_usd": spend,
        "burn_rate_pct": burn_rate,
        "idle_gpu_waste_usd": waste,
        "alert_status": status,
        "report_date": "2026-09-15",
        "standardized_formula_used": f"Burn Rate (%) = (${spend:,.2f} / ${budget:,.2f}) * 100 = {burn_rate}%",
    })

with open(os.path.join(DATA_DIR, "finops_billing_ledger.json"), "w", encoding="utf-8") as f:
    json.dump(finops_records, f, indent=2, ensure_ascii=False)
print(f"✅ Generated Gateway 1 dataset: {len(finops_records)} FinOps project records.")


# ----------------------------------------------------------------------------
# 2. Gateway 2 Dataset: 36 Policy Chunks (12 Policies × 3 Adjacent Chunks N-1, N, N+1)
# ----------------------------------------------------------------------------
POLICIES_SPEC = [
    (
        "SEC-POL-2026-FW",
        "Production Firewall Port Opening & VPC-SC Ingress Policy",
        ["firewall", "port", "tcp", "443", "8443", "ingress", "sec-pol-2026-fw"],
        "[PRE-REQUISITE SAFETY CHECK: SEC-POL-2026-FW] Before requesting any production firewall port opening (TCP 443/8443) or VPC-SC ingress rule modification, the requester must obtain Level-2 Security Architect approval and verify that the target subnet utilizes Private Service Connect Interface (PSC-I).",
        "[EXECUTION SOP: SEC-POL-2026-FW] Step 1: Submit ticket via it_servicedesk_tool with action_type=FIREWALL_OPEN. Step 2: Attach Squid Proxy egress routing table if outbound internet access is required inside VPC-SC perimeter. Step 3: Verify automated firewall audit log within 15 minutes.",
        "[POST-CHANGE AUDIT & ROLLBACK: SEC-POL-2026-FW] Any firewall rule that exhibits anomalous egress traffic exceeding 10GB/hour will be automatically rolled back via 2-Phase Commit (2PC) compensation lock (lock:user:id:mutation).",
    ),
    (
        "FIN-POL-2026-GPU",
        "H100/A100 GPU Quota Governance & FinOps Overrun Freeze Policy",
        ["gpu", "quota", "a100", "h100", "overrun", "burn rate", "fin-pol-2026-gpu"],
        "[PRE-REQUISITE GOVERNANCE CHECK: FIN-POL-2026-GPU] Projects exceeding 120% Budget Burn Rate (such as PROJ-AI-PROD-01 at 132.37% or PROJ-LLM-SERVE-04 at 131.50%) are automatically flagged for GPU quota freeze.",
        "[EXECUTION SOP: FIN-POL-2026-GPU] Step 1: Run finops_bq_tool to audit idle GPU waste USD. Step 2: Reclaim unattached A100/H100 Workbench instances. Step 3: Submit a 2PC HITL ticket (action_type=GPU_QUOTA_INCREASE) signed by the VP of AI Research.",
        "[POST-CHANGE AUDIT & ROLLBACK: FIN-POL-2026-GPU] Approved emergency GPU allocations are monitored every 6 hours; if GPU utilization drops below 40%, nodes are automatically preempted and scaled down to zero.",
    ),
    (
        "NET-POL-2026-PSCI",
        "Private Service Connect Interface (PSC-I) & Squid Proxy Outbound Routing Standard",
        ["psc-i", "squid", "proxy", "southbound", "outbound", "internet", "net-pol-2026-psci"],
        "[PRE-REQUISITE NETWORK CHECK: NET-POL-2026-PSCI] Vertex AI Agent Engine uses PSC-I strictly for southbound private VPC connectivity. Direct public internet egress from VPC-SC protected agents is blocked by default.",
        "[EXECUTION SOP: NET-POL-2026-PSCI] Step 1: Provision a dedicated Proxy VM running Squid on TCP port 3128 inside the customer VPC with IPv4 forwarding enabled (net.ipv4.ip_forward=1). Step 2: Configure Internal Load Balancer (ILB) and route Agent Engine egress traffic through the Squid proxy.",
        "[POST-CHANGE AUDIT & ROLLBACK: NET-POL-2026-PSCI] All outbound domain requests passing through Squid Proxy TCP 3128 are logged to Cloud Logging and inspected against Chronicle SIEM threat feeds.",
    ),
    (
        "IAM-POL-2026-OAUTH",
        "Gemini Enterprise End-User OAuth 2.0 Identity Delegation Policy",
        ["oauth", "serversideoauth2", "redirect", "authorization", "identity", "iam-pol-2026-oauth"],
        "[PRE-REQUISITE IDENTITY CHECK: IAM-POL-2026-OAUTH] Agents executing queries against user-scoped datasets (BigQuery ACLs, Google Drive, Jira) must never use over-privileged service accounts; OAuth 2.0 delegation is mandatory.",
        "[EXECUTION SOP: IAM-POL-2026-OAUTH] Step 1: Add https://vertexaisearch.cloud.google.com/oauth-redirect to Authorized Redirect URIs in GCP OAuth Credentials. Step 2: Register a serverSideOauth2 resource in Discovery Engine API (/v1alpha/projects/{PROJECT_ID}/locations/global/authorizations).",
        "[POST-CHANGE AUDIT & ROLLBACK: IAM-POL-2026-OAUTH] OAuth refresh tokens are encrypted at rest via Cloud KMS and automatically revoked if a user's corporate Google Workspace account is suspended.",
    ),
    (
        "DATA-POL-2026-DLP",
        "Cloud DLP & Model Armor Pre-Inference Prompt Injection & PII Guardrail Policy",
        ["dlp", "pii", "spii", "model armor", "injection", "guardrail", "data-pol-2026-dlp"],
        "[PRE-REQUISITE PRIVACY CHECK: DATA-POL-2026-DLP] All user prompts submitted via Gemini Enterprise must undergo pre-model inspection (<150ms SLA) for PII/SPII (SSN, Credit Card, API Keys) and Jailbreak/Prompt Injection attempts.",
        "[EXECUTION SOP: DATA-POL-2026-DLP] Step 1: Attach Google Cloud Model Armor GuardrailPlugin to the ADK root_agent. Step 2: Configure de-identification templates to mask sensitive entities with [REDACTED_PII] prior to LLM token generation.",
        "[POST-CHANGE AUDIT & ROLLBACK: DATA-POL-2026-DLP] Any session triggering 3 consecutive Model Armor high-severity prompt injection blocks is immediately terminated and reported to SecOps.",
    ),
    (
        "SEC-POL-2026-CMEK",
        "Customer-Managed Encryption Keys (Cloud KMS CMEK) Rotation & Compliance Standard",
        ["cmek", "kms", "encryption", "key rotation", "sec-pol-2026-cmek"],
        "[PRE-REQUISITE CRYPTO CHECK: SEC-POL-2026-CMEK] All Tier-1 BigQuery Gold tables, Vertex AI Agent Engine staging buckets, and Cloud Spanner databases must be encrypted using HSM-backed Cloud KMS CMEK keys.",
        "[EXECUTION SOP: SEC-POL-2026-CMEK] Step 1: Create a symmetric encryption key in Cloud KMS with a 90-day automatic rotation schedule. Step 2: Grant roles/cloudkms.cryptoKeyEncrypterDecrypter to the Vertex AI and Discovery Engine service agents.",
        "[POST-CHANGE AUDIT & ROLLBACK: SEC-POL-2026-CMEK] If a KMS key version is destroyed or disabled, dependent ADK agents immediately enter safe read-only fail-closed mode.",
    ),
    (
        "DB-POL-2026-SPANNER",
        "Cloud Spanner & AlloyDB Zero-Downtime Cross-Region Failover SOP",
        ["spanner", "alloydb", "failover", "database", "rto", "db-pol-2026-spanner"],
        "[PRE-REQUISITE DATABASE CHECK: DB-POL-2026-SPANNER] Production transactional databases supporting retail POS and FinTech ledgers must maintain multi-region read-write quorum with RTO < 5 seconds.",
        "[EXECUTION SOP: DB-POL-2026-SPANNER] Step 1: Verify witness node health in us-central1 and us-east1. Step 2: Execute point-in-time recovery (PITR) validation weekly. Step 3: Route read-only analytical queries from ADK agents to read replicas.",
        "[POST-CHANGE AUDIT & ROLLBACK: DB-POL-2026-SPANNER] Database mutation locks exceeding 3,000ms trigger automatic connection pool shedding to preserve core checkout availability.",
    ),
    (
        "K8S-POL-2026-GKE",
        "GKE Autopilot Binary Authorization & Container Image Signing Standard",
        ["gke", "kubernetes", "binary authorization", "container", "docker", "k8s-pol-2026-gke"],
        "[PRE-REQUISITE CONTAINER CHECK: K8S-POL-2026-GKE] Unverified or unsigned Docker images are strictly prohibited from running on production Cloud Run or GKE Autopilot clusters.",
        "[EXECUTION SOP: K8S-POL-2026-GKE] Step 1: Build container images via Cloud Build (gcloud builds submit). Step 2: Scan image vulnerabilities via Artifact Analysis (zero CRITICAL CVEs allowed). Step 3: Attest image signature via Binary Authorization.",
        "[POST-CHANGE AUDIT & ROLLBACK: K8S-POL-2026-GKE] Any runtime container drift or unauthorized shell execution inside a pod triggers immediate pod eviction and forensic snapshot capture.",
    ),
    (
        "API-POL-2026-APIGEE",
        "Apigee X API Gateway mTLS & Custom Header Passthrough Architecture",
        ["apigee", "api gateway", "mtls", "header", "rate limit", "api-pol-2026-apigee"],
        "[PRE-REQUISITE GATEWAY CHECK: API-POL-2026-APIGEE] External partner and A2A agent invocations crossing organizational boundaries must terminate TLS at Apigee X with mutual TLS (mTLS) client certificate verification.",
        "[EXECUTION SOP: API-POL-2026-APIGEE] Step 1: Configure SpikeArrest policy at 500 requests/second per tenant. Step 2: When integrating Gemini Enterprise with Apigee-proxied A2A endpoints, configure OAuth 2.0 Bearer token validation instead of custom API key headers.",
        "[POST-CHANGE AUDIT & ROLLBACK: API-POL-2026-APIGEE] Clients exceeding HTTP 429 quota thresholds for more than 60 seconds are dynamically rate-limited at the Cloud Armor edge.",
    ),
    (
        "DR-POL-2026-BCP",
        "Enterprise Business Continuity & Disaster Recovery (BCP/DR) Drill Standard",
        ["disaster recovery", "dr", "bcp", "backup", "outage", "dr-pol-2026-bcp"],
        "[PRE-REQUISITE DR CHECK: DR-POL-2026-BCP] All mission-critical AI agents and data pipelines must undergo bi-annual regional blackout simulation drills.",
        "[EXECUTION SOP: DR-POL-2026-BCP] Step 1: Drain traffic from primary region (us-central1) using Cloud Load Balancing global weights. Step 2: Promote secondary region (us-east1) Agent Engine endpoints. Step 3: Validate BigQuery cross-region dataset replication.",
        "[POST-CHANGE AUDIT & ROLLBACK: DR-POL-2026-BCP] Post-drill RTO and RPO telemetry reports must be archived in the compliance vault within 24 hours of drill completion.",
    ),
    (
        "AI-POL-2026-ADK",
        "Google ADK 2.0 Agent Architecture & Dual-Contract Release Governance",
        ["adk", "google-adk", "agent-card", "text/plain", "a2a", "ai-pol-2026-adk"],
        "[PRE-REQUISITE AI GOVERNANCE CHECK: AI-POL-2026-ADK] All custom agents registered in Gemini Enterprise must pin google-adk==2.8.0 and mcp<2.0.0 (mcp==1.29.1) to ensure deterministic runtime stability.",
        "[EXECUTION SOP: AI-POL-2026-ADK] Step 1: Structure tools into 3 Decoupled Gateways (SQL Analytics, Vector RAG, Action API). Step 2: Ensure /.well-known/agent-card.json advertises defaultInputModes: ['text/plain']. Step 3: Pass validate_agent.py with 5/5 score.",
        "[POST-CHANGE AUDIT & ROLLBACK: AI-POL-2026-ADK] Every agent turn must asynchronously log user query, invoked tool names, and TTFT latency to BigQuery dataset agent_telemetry.",
    ),
    (
        "LOG-POL-2026-SIEM",
        "Chronicle SIEM & BigQuery Agent Telemetry 365-Day Audit Retention Policy",
        ["logging", "siem", "chronicle", "audit", "telemetry", "retention", "log-pol-2026-siem"],
        "[PRE-REQUISITE AUDIT CHECK: LOG-POL-2026-SIEM] Enterprise regulatory compliance mandates immutable 365-day retention for all AI agent tool invocations, SQL queries generated, and HITL approvals.",
        "[EXECUTION SOP: LOG-POL-2026-SIEM] Step 1: Enable BigQueryAgentAnalyticsPlugin on all ADK apps. Step 2: Route Cloud Audit Logs (DATA_READ, DATA_WRITE) from BigQuery and Discovery Engine to a locked Cloud Storage bucket with Object Retention Lock.",
        "[POST-CHANGE AUDIT & ROLLBACK: LOG-POL-2026-SIEM] Unauthorized attempts to delete or alter agent_telemetry tables trigger an immediate P1 SecOps incident and IAM permission freeze.",
    ),
]

policy_chunks_records = []
for pol_id, title, keywords, chunk1, chunk2, chunk3 in POLICIES_SPEC:
    gcs_url = f"https://storage.cloud.google.com/cymbal-enterprise-policies/{pol_id}-v2.pdf"
    policy_chunks_records.extend([
        {
            "policy_id": pol_id,
            "policy_title": title,
            "chunk_index": 1,
            "similarity_score": 0.89,
            "keywords": keywords,
            "chunk_text": chunk1,
            "gcs_url": gcs_url,
        },
        {
            "policy_id": pol_id,
            "policy_title": title,
            "chunk_index": 2,
            "similarity_score": 0.95,
            "keywords": keywords,
            "chunk_text": chunk2,
            "gcs_url": gcs_url,
        },
        {
            "policy_id": pol_id,
            "policy_title": title,
            "chunk_index": 3,
            "similarity_score": 0.87,
            "keywords": keywords,
            "chunk_text": chunk3,
            "gcs_url": gcs_url,
        },
    ])

with open(os.path.join(DATA_DIR, "it_security_policy_chunks.json"), "w", encoding="utf-8") as f:
    json.dump(policy_chunks_records, f, indent=2, ensure_ascii=False)
print(f"✅ Generated Gateway 2 dataset: {len(policy_chunks_records)} policy chunks across {len(POLICIES_SPEC)} policies.")


# ----------------------------------------------------------------------------
# 3. Gateway 3 Dataset: 32 Live IT Service Desk Incidents & 2PC Tickets
# ----------------------------------------------------------------------------
INCIDENT_TEMPLATES = [
    ("INC-2026-88401", "PROJ-AI-PROD-01", "VPC_SC_EGRESS_BLOCK", "P1_CRITICAL", "INVESTIGATING", "Cloud Network SecOps", "SEC-POL-2026-FW", "Agent Engine southbound connection blocked; requires Squid Proxy VM on TCP 3128 inside VPC-SC perimeter."),
    ("INC-2026-88402", "PROJ-AI-PROD-01", "GPU_QUOTA_FREEZE", "P1_CRITICAL", "ACTIVE_RESTRICTION", "FinOps Governance Board", "FIN-POL-2026-GPU", "H100 provisioning restricted automatically due to 132.37% FinOps budget burn rate overrun."),
    ("INC-2026-88403", "PROJ-DATA-LAKE-02", "DLP_PII_MASKING_AUDIT", "P3_MEDIUM", "RESOLVED", "Data Privacy Team", "DATA-POL-2026-DLP", "Routine Model Armor scan verified 100% redaction of customer SSN patterns in BigQuery staging tables."),
    ("INC-2026-88404", "PROJ-WEB-FRONT-03", "CLOUD_RUN_AUTOSCALE_WARN", "P2_HIGH", "INVESTIGATING", "SRE Core Infrastructure", "FIN-POL-2026-GPU", "Cloud Run microservice burn rate reached 99.26% ($14,890 / $15,000 budget); approaching freeze threshold."),
    ("INC-2026-88405", "PROJ-LLM-SERVE-04", "GPU_QUOTA_FREEZE", "P1_CRITICAL", "PENDING_HITL_APPROVAL", "FinOps Governance Board", "FIN-POL-2026-GPU", "Emergency request for 16x H100 GPUs pending Level-2 VP approval; current spend at 131.50% ($78,900)."),
    ("INC-2026-88406", "PROJ-RETAIL-POS-05", "SPANNER_LATENCY_SPIKE", "P2_HIGH", "AUTO_REMEDIATED", "Database SRE Team", "DB-POL-2026-SPANNER", "Transient read latency spike (18ms) resolved automatically via read-replica query routing."),
    ("INC-2026-88407", "PROJ-FINTECH-PAY-06", "FIREWALL_OPEN_REQUEST", "P1_CRITICAL", "PENDING_HITL_APPROVAL", "Cloud Network SecOps", "SEC-POL-2026-FW", "Request to open TCP 8443 for payment settlement gateway; 2PC lock active awaiting SecOps sign-off."),
    ("INC-2026-88408", "PROJ-ERP-SAP-07", "CMEK_KEY_ROTATION_DUE", "P3_MEDIUM", "INVESTIGATING", "IAM & Identity Team", "SEC-POL-2026-CMEK", "90-day HSM CMEK encryption key rotation scheduled for SAP HANA persistent disks."),
    ("INC-2026-88409", "PROJ-SUPPLY-CHAIN-08", "BIGLAKE_S3_SYNC_DELAY", "P3_MEDIUM", "RESOLVED", "Data Platform", "NET-POL-2026-PSCI", "Cross-cloud AWS S3 BigLake Iceberg table metadata refresh completed in 4.2 seconds."),
    ("INC-2026-88410", "PROJ-IOT-STREAM-09", "BIGTABLE_HOTSPOT_ALERT", "P2_HIGH", "INVESTIGATING", "SRE Core Infrastructure", "FIN-POL-2026-GPU", "Bigtable cluster burn rate at 129.21% ($49,100) due to uncompacted row key prefix scans."),
    ("INC-2026-88411", "PROJ-FRAUD-DET-10", "MODEL_ARMOR_INJECTION_BLOCK", "P1_CRITICAL", "AUTO_REMEDIATED", "SecOps Threat Intel", "DATA-POL-2026-DLP", "Blocked 42 automated prompt injection attempts targeting real-time fraud scoring endpoint."),
    ("INC-2026-88412", "PROJ-CUST-360-11", "ALLOYDB_VECTOR_INDEX_REBUILD", "P4_LOW", "RESOLVED", "Database SRE Team", "DB-POL-2026-SPANNER", "HNSW vector index rebuild completed with 0.94 recall accuracy."),
    ("INC-2026-88413", "PROJ-HR-PORTAL-12", "OAUTH_REDIRECT_URI_MISMATCH", "P2_HIGH", "INVESTIGATING", "IAM & Identity Team", "IAM-POL-2026-OAUTH", "OAuth 2.0 token exchange failed; missing https://vertexaisearch.cloud.google.com/oauth-redirect in client config."),
    ("INC-2026-88414", "PROJ-SEC-SIEM-13", "LOG_RETENTION_LOCK_VERIFY", "P4_LOW", "RESOLVED", "SecOps Compliance", "LOG-POL-2026-SIEM", "Verified 365-day immutable retention lock on agent_telemetry audit bucket."),
    ("INC-2026-88415", "PROJ-DEV-SANDBOX-14", "IDLE_WORKBENCH_GPU_WASTE", "P1_CRITICAL", "ACTIVE_RESTRICTION", "FinOps Governance Board", "FIN-POL-2026-GPU", "Detected $12,400 in idle unattached A100 Workbench notebooks (148.33% burn rate); auto-stop scheduled."),
    ("INC-2026-88416", "PROJ-MEDIA-GEN-15", "QUOTA_EXCEEDED_IMAGEN", "P2_HIGH", "PENDING_HITL_APPROVAL", "AI Platform Engineering", "FIN-POL-2026-GPU", "Media rendering farm exceeded monthly budget ($46,200 / $35,000); requesting temporary quota extension."),
    ("INC-2026-88417", "PROJ-LOGISTICS-OPT-16", "GKE_BINAUTHZ_BLOCK", "P2_HIGH", "AUTO_REMEDIATED", "DevSecOps Team", "K8S-POL-2026-GKE", "Blocked deployment of unsigned container image in logistics routing namespace."),
    ("INC-2026-88418", "PROJ-HEALTH-NLP-17", "HIPAA_DLP_GUARDRAIL_TRIP", "P1_CRITICAL", "INVESTIGATING", "Data Privacy Team", "DATA-POL-2026-DLP", "PHI entity detected in clinical note summarization prompt; masked via Cloud DLP template."),
    ("INC-2026-88419", "PROJ-DATA-GOV-18", "GLOSSARY_FORMULA_SYNC", "P4_LOW", "RESOLVED", "Data Governance", "AI-POL-2026-ADK", "Updated Net Transaction Revenue and Burn Rate formulas in Knowledge Catalog Business Glossary."),
    ("INC-2026-88420", "PROJ-API-GW-19", "APIGEE_MTLS_CERT_EXPIRY", "P2_HIGH", "PENDING_HITL_APPROVAL", "Cloud Network SecOps", "API-POL-2026-APIGEE", "Partner A2A mTLS client certificate expires in 7 days; renewal ticket created with 2PC lock."),
    ("INC-2026-88421", "PROJ-MOBILE-APP-20", "FIREBASE_AUTH_RATE_LIMIT", "P3_MEDIUM", "RESOLVED", "Mobile Platform Team", "API-POL-2026-APIGEE", "SpikeArrest policy mitigated credential stuffing burst from external IP range."),
    ("INC-2026-88422", "PROJ-REC-ENGINE-21", "DISCOVERY_ENGINE_INDEX_LAG", "P2_HIGH", "INVESTIGATING", "AI Platform Engineering", "AI-POL-2026-ADK", "Retail product catalog datastore incremental indexing lag at 14 minutes; scaling worker nodes."),
    ("INC-2026-88423", "PROJ-BATCH-ETL-22", "DATAFLOW_SHUFFLE_QUOTA", "P3_MEDIUM", "AUTO_REMEDIATED", "Data Platform", "FIN-POL-2026-GPU", "Dataflow streaming pipeline auto-scaled down after peak midnight ETL window."),
    ("INC-2026-88424", "PROJ-DR-BACKUP-23", "BCP_FAILOVER_DRILL_PASS", "P4_LOW", "RESOLVED", "SRE Core Infrastructure", "DR-POL-2026-BCP", "Q3 regional failover drill between us-central1 and us-east1 completed with 3.8s RTO."),
    ("INC-2026-88425", "PROJ-VOICE-BOT-24", "LIVE_API_WEBSOCKET_DROP", "P2_HIGH", "INVESTIGATING", "AI Platform Engineering", "NET-POL-2026-PSCI", "Investigating intermittent WebSocket disconnects on Multimodal Live API session pool."),
    ("INC-2026-88426", "PROJ-DOC-AI-25", "INVOICE_PARSER_CONFIDENCE", "P3_MEDIUM", "RESOLVED", "Enterprise ERP", "AI-POL-2026-ADK", "Document AI confidence threshold tuned to 0.88 for international vendor invoices."),
    ("INC-2026-88427", "PROJ-QA-PERF-26", "EPHEMERAL_GKE_OVERRUN", "P1_CRITICAL", "ACTIVE_RESTRICTION", "FinOps Governance Board", "FIN-POL-2026-GPU", "QA load testing cluster left running over weekend (137.62% burn rate, $11,200 waste); cluster cordoned."),
    ("INC-2026-88428", "PROJ-PARTNER-EDI-27", "PUBSUB_DEAD_LETTER_QUEUE", "P3_MEDIUM", "INVESTIGATING", "Supply Chain", "API-POL-2026-APIGEE", "18 EDI order messages routed to dead-letter topic due to schema validation mismatch."),
    ("INC-2026-88429", "PROJ-CORP-NET-28", "BGP_SESSION_FLAP_NCC", "P2_HIGH", "AUTO_REMEDIATED", "Cloud Network SecOps", "NET-POL-2026-PSCI", "Network Connectivity Center (NCC) router automatically converged onto redundant interconnect link."),
    ("INC-2026-88430", "PROJ-RISK-SIM-29", "HPC_CLUSTER_BUDGET_BREACH", "P1_CRITICAL", "PENDING_HITL_APPROVAL", "FinOps Governance Board", "FIN-POL-2026-GPU", "Monte Carlo HPC simulation breached 130% budget ($91,000 spend); 2PC HITL lock awaiting CFO sign-off."),
    ("INC-2026-88431", "PROJ-LOYALTY-DB-30", "REDIS_MEMORY_EVICTION", "P3_MEDIUM", "RESOLVED", "Database SRE Team", "DB-POL-2026-SPANNER", "Memorystore Redis maxmemory-policy adjusted to volatile-lru to prevent session drops."),
    ("INC-2026-88432", "PROJ-SEARCH-ENT-31", "A2A_AGENT_CARD_MIME_FIX", "P2_HIGH", "RESOLVED", "AI Platform Engineering", "AI-POL-2026-ADK", "Fixed Gemini Enterprise A2A registration error by updating defaultInputModes to ['text/plain']."),
]

itsm_records = []
for tid, pid, itype, sev, status, team, pol, detail in INCIDENT_TEMPLATES:
    itsm_records.append({
        "ticket_id": tid,
        "project_id": pid,
        "type": itype,
        "severity": sev,
        "status": status,
        "assigned_team": team,
        "policy_reference": pol,
        "idempotency_2pc_lock": f"lock:user:{pid}:{itype}",
        "detail": detail,
        "created_at": "2026-09-15T06:30:00Z",
    })

with open(os.path.join(DATA_DIR, "it_servicedesk_incidents.json"), "w", encoding="utf-8") as f:
    json.dump(itsm_records, f, indent=2, ensure_ascii=False)
print(f"✅ Generated Gateway 3 dataset: {len(itsm_records)} IT Service Desk incident records.")
