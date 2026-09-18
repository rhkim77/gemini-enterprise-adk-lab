#!/usr/bin/env python3
# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Track B: deploy root_agent to the Vertex AI Agent Engine managed runtime.

Encapsulates labs/03_cloud_deployment.md "Option B" so the Qwiklabs lab can be
completed with a single command instead of a copy-pasted Python snippet.

Track A (Cloud Run) and Track B (Agent Engine) are alternatives, not a sequence.
Track A gives you a container you own and an A2A HTTPS endpoint; Track B gives
you a zero-ops managed runtime addressable as a `reasoningEngines/` resource.
Only Track B can sit behind VPC-SC / PSC-I without you running the network.

Usage:
    .venv/bin/python3 scripts/deploy_agent_engine.py --dry-run   # change nothing
    .venv/bin/python3 scripts/deploy_agent_engine.py             # deploy
    .venv/bin/python3 scripts/deploy_agent_engine.py --list      # list engines
    .venv/bin/python3 scripts/deploy_agent_engine.py --delete <resource_name>

Overridable via environment or .env: PROJECT_ID, REGION, STAGING_BUCKET.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

DISPLAY_NAME = "enterprise-hub-adk-agent"
DESCRIPTION = "Enterprise Cloud FinOps & IT Hub Coordinator Agent"

# IMPORTANT: keep this list in sync with requirements.txt.
# Deploying a different SDK combination than the one verified locally is the
# single most common cause of "works locally, fails on Agent Engine".
# ADK 2.x specifically is required - 1.x uses a different lifecycle-callback
# contract and will break `before_agent_callback` wiring silently.
# The [agent_engines,adk] extras are what pull in the managed-runtime packaging
# code; plain google-cloud-aiplatform cannot deploy an AdkApp.
REQUIREMENTS = [
    "google-adk>=2.8.0,<3.0.0",
    "mcp>=1.30.0,<2.0.0",
    "google-cloud-aiplatform[agent_engines,adk]>=1.82.0",
    "google-genai>=2.23.0,<3.0.0",
]


def _load_dotenv() -> None:
    """Loads .env without requiring python-dotenv, and never clobbers real env vars."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # .env.example quotes its values, so strip the quotes before exporting.
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _fail(message: str, hint: str = "") -> None:
    print("\n[ERROR] " + message, file=sys.stderr)
    if hint:
        print("   -> " + hint, file=sys.stderr)
    sys.exit(1)


def _resolve_config() -> Tuple[str, str, str]:
    project_id = os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    region = (
        os.environ.get("REGION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION")
        or "us-central1"
    )
    if not project_id or project_id.startswith("<"):
        _fail(
            "PROJECT_ID could not be resolved.",
            "Copy .env.example to .env and set PROJECT_ID, or export PROJECT_ID=<id>.",
        )
    staging_bucket = os.environ.get("STAGING_BUCKET") or "gs://" + project_id + "-ae-staging"
    if not staging_bucket.startswith("gs://"):
        staging_bucket = "gs://" + staging_bucket
    return project_id, region, staging_bucket


def _ensure_staging_bucket(project_id: str, region: str, staging_bucket: str) -> None:
    """Creates the Agent Engine staging bucket if it is absent.

    Agent Engine uploads the pickled AdkApp and its dependency manifest here. A
    missing bucket surfaces as an opaque 404 from the create() call, so check it
    up front and fail with an actionable message instead.
    """
    bucket_name = staging_bucket[len("gs://"):].rstrip("/")
    try:
        from google.cloud import storage
    except ImportError:
        print("  [WARN] google-cloud-storage not installed; skipping bucket precheck.")
        print("         If deployment fails, create the bucket manually:")
        print("         gcloud storage buckets create " + staging_bucket + " --location=" + region)
        return

    client = storage.Client(project=project_id)
    if client.lookup_bucket(bucket_name) is not None:
        print("  [OK] Staging bucket already exists: " + staging_bucket)
        return
    print("  [..] Creating staging bucket " + staging_bucket + " in " + region + " ...")
    client.create_bucket(bucket_name, location=region)
    print("  [OK] Staging bucket created: " + staging_bucket)


# `import vertexai.agent_engines` succeeds even when the [agent_engines] extra is
# absent, because the module itself ships in the base package. The extra is what
# supplies cloudpickle (used to serialize the AdkApp) and the OpenTelemetry
# exporters that enable_tracing=True requires. Without the preflight below the
# failure surfaces minutes later inside create(), as an opaque ModuleNotFoundError
# raised from the packaging step.
_EXTRA_MODULES = {
    "cloudpickle": "serializes the AdkApp for upload",
    "opentelemetry.sdk": "required by AdkApp(enable_tracing=True)",
}


def _import_sdk():
    try:
        import vertexai
        from vertexai import agent_engines
        from vertexai.agent_engines import AdkApp
    except ImportError as exc:
        _fail(
            "Vertex AI Agent Engine SDK is unavailable (" + str(exc) + ").",
            'Install the extras: pip install "google-cloud-aiplatform[agent_engines,adk]>=1.82.0"',
        )

    import importlib.util

    missing = [
        name + " (" + why + ")"
        for name, why in _EXTRA_MODULES.items()
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        _fail(
            "The [agent_engines] extra is not installed. Missing: " + ", ".join(missing),
            'Run: pip install -r requirements.txt   '
            '(it pins google-cloud-aiplatform[agent_engines,adk]>=1.82.0)',
        )

    return vertexai, agent_engines, AdkApp


def cmd_list(agent_engines) -> int:
    engines = list(agent_engines.list())
    if not engines:
        print("  (no Agent Engine instances found in this project/location)")
        return 0
    for engine in engines:
        print("  - " + engine.resource_name)
        print("      display_name: " + str(getattr(engine, "display_name", "(n/a)")))
    return 0


def cmd_delete(agent_engines, resource_name: str) -> int:
    print("  [..] Deleting " + resource_name + " ...")
    # force=True also removes the child sessions the managed runtime created;
    # without it the delete fails while any session still references the engine.
    agent_engines.delete(resource_name=resource_name, force=True)
    print("  [OK] Deleted " + resource_name)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy root_agent to Vertex AI Agent Engine.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the resolved configuration and exit without deploying.")
    parser.add_argument("--list", action="store_true",
                        help="List existing Agent Engine instances and exit.")
    parser.add_argument("--delete", metavar="RESOURCE_NAME", default=None,
                        help="Delete an Agent Engine instance by resource name and exit.")
    args = parser.parse_args()

    _load_dotenv()
    project_id, region, staging_bucket = _resolve_config()

    print("=" * 70)
    print(" [Cymbal Enterprise AI Hub] Vertex AI Agent Engine deployment (Track B)")
    print("=" * 70)
    print("  -> Project ID     : " + project_id)
    print("  -> Location       : " + region)
    print("  -> Staging bucket : " + staging_bucket)
    print("  -> Display name   : " + DISPLAY_NAME)
    print("=" * 70)

    if args.dry_run:
        print("[DRY RUN] No changes will be made. This run would:")
        print("  1. Ensure staging bucket " + staging_bucket + " exists")
        print("  2. vertexai.init(project=" + project_id + ", location=" + region + ")")
        print("  3. Wrap app.agent.root_agent in AdkApp(enable_tracing=True)")
        print("  4. agent_engines.create(...) with requirements:")
        for requirement in REQUIREMENTS:
            print("       - " + requirement)
        print("     and env_vars:")
        print("       - GOOGLE_GENAI_USE_VERTEXAI=TRUE")
        print("       - GOOGLE_CLOUD_LOCATION=" + region)
        print("       - USE_ADK_LLM=true")
        print("       - ITSM_MODE=MOCK")
        print("")
        print("[DRY RUN] Complete. Re-run without --dry-run to deploy.")
        return 0

    vertexai, agent_engines, AdkApp = _import_sdk()
    vertexai.init(project=project_id, location=region, staging_bucket=staging_bucket)

    if args.list:
        return cmd_list(agent_engines)
    if args.delete:
        return cmd_delete(agent_engines, args.delete)

    print("")
    print("[1/3] Verifying staging bucket ...")
    _ensure_staging_bucket(project_id, region, staging_bucket)

    print("")
    print("[2/3] Loading root_agent and wrapping it in AdkApp ...")
    # Imported late and from the repo root so that a missing .env or a broken
    # tool import fails here with a readable traceback, rather than halfway
    # through a multi-minute remote build.
    sys.path.insert(0, str(REPO_ROOT))
    from app.agent import root_agent

    adk_app = AdkApp(agent=root_agent, enable_tracing=True)
    print("  [OK] Wrapped agent '" + str(root_agent.name) + "' (model: "
          + str(getattr(root_agent, "model", "n/a")) + ")")

    print("")
    print("[3/3] Creating the Agent Engine instance ...")
    print("  This provisions a managed runtime and typically takes 5-10 minutes.")
    remote_agent = agent_engines.create(
        agent_engine=adk_app,
        requirements=REQUIREMENTS,
        env_vars={
            # Agent Engine runs with its own service identity; the Vertex AI
            # backend flag must be injected here just as it is for Cloud Run.
            # Without it the managed runtime boots in Gemini Developer API mode
            # and silently degrades to the deterministic fallback router.
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_LOCATION": region,
            "USE_ADK_LLM": "true",
            "ITSM_MODE": "MOCK",
        },
        display_name=DISPLAY_NAME,
        description=DESCRIPTION,
    )

    print("")
    print("=" * 70)
    print(" [OK] Agent Engine deployment complete")
    print("=" * 70)
    print("  Resource name: " + remote_agent.resource_name)
    print("  Format       : projects/{PROJECT_NUMBER}/locations/"
          + region + "/reasoningEngines/{ENGINE_ID}")
    print("")
    print("  Save it for the Gemini Enterprise registration step:")
    print('    export AGENT_ENGINE_RESOURCE="' + remote_agent.resource_name + '"')
    print("")
    print("  Tear it down when finished (managed runtimes bill while idle):")
    print("    .venv/bin/python3 scripts/deploy_agent_engine.py --delete "
          + remote_agent.resource_name)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
