#!/usr/bin/env python3
# Copyright 2026 Google LLC. Licensed under Apache 2.0.
"""Task 5 completion check: Gemini Enterprise & OAuth 2.0 readiness.

Verifies that the running agent satisfies everything Gemini Enterprise requires
*before* you register it in the console, so that a failed registration can be
diagnosed here instead of inside the GE UI where the errors are opaque.

Checks:
  1. A2A Agent Card schema compliance (defaultInputModes/defaultOutputModes/skills)
  2. OAuth 2.0 redirect URI specification
  3. Dual-Contract endpoints (/a2a/<agent> and /api/reasoning_engine)
  4. End-to-end OAuth token forwarding and 2PC HITL audit

Usage:
    python3 scripts/verify_lab04_completion.py
    python3 scripts/verify_lab04_completion.py --url https://<service>.run.app
    SERVICE_URL=https://<service>.run.app python3 scripts/verify_lab04_completion.py
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

AGENT_NAME = "enterprise_hub_agent"

# Gemini Enterprise always completes the OAuth dance on this fixed address. If the
# OAuth client does not list it as an authorized redirect URI, consent fails with
# redirect_uri_mismatch and the agent never receives a delegated token.
GE_REDIRECT_URI = "https://vertexaisearch.cloud.google.com/oauth-redirect"

# Deliberately a non-credential placeholder: this token only has to be non-empty
# for the passthrough path to engage.
PROBE_TOKEN = "mock-oauth2-token-cymbal-2026"
PROBE_EMAIL = "lab-verifier@cymbal.enterprise"

REPO_ROOT = Path(__file__).resolve().parent.parent


def _request(url: str, payload: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None,
             timeout: float = 90.0) -> Tuple[int, Any]:
    """Performs a GET (payload=None) or JSON POST. Returns (status, parsed_body)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 — surfaced to the participant verbatim
        return 0, f"{type(exc).__name__}: {exc}"


def check_1_agent_card(base_url: str) -> Tuple[bool, str]:
    status, card = _request(f"{base_url}/.well-known/agent-card.json")
    if status != 200 or not isinstance(card, dict):
        return False, f"agent card unreachable (HTTP {status}): {card}"

    problems = []
    # GE rejects the bare value "text"; the MIME type must be spelled out.
    for field in ("defaultInputModes", "defaultOutputModes"):
        if card.get(field) != ["text/plain"]:
            problems.append(f'{field} must be ["text/plain"], got {card.get(field)!r}')
    skills = card.get("skills")
    if not isinstance(skills, list) or not skills:
        problems.append("skills must be a non-empty list")
    url = card.get("url", "")
    if not url.endswith(f"/a2a/{AGENT_NAME}"):
        problems.append(f"url must point at /a2a/{AGENT_NAME}, got {url!r}")
    # A public https:// URL is required for GE to reach the agent. Local runs are
    # expected to be http://localhost, so only warn about that case.
    if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
        problems.append(f"url must be https:// when deployed, got {url!r}")

    if problems:
        return False, "; ".join(problems)
    scheme_note = "local" if url.startswith("http://") else "public HTTPS"
    return True, f"{len(skills)} skills, text/plain I/O, {scheme_note} RPC url"


def check_2_oauth_redirect() -> Tuple[bool, str]:
    script = REPO_ROOT / "scripts" / "register_oauth_discovery_engine.sh"
    if not script.is_file():
        return False, "scripts/register_oauth_discovery_engine.sh is missing"
    text = script.read_text(encoding="utf-8")
    if GE_REDIRECT_URI not in text:
        return False, f"registration script does not reference {GE_REDIRECT_URI}"
    if "serverSideOauth2" not in text:
        return False, "registration script does not declare a serverSideOauth2 resource"
    return True, GE_REDIRECT_URI


def check_3_dual_contract(base_url: str) -> Tuple[bool, str]:
    reached = []
    status, body = _request(
        f"{base_url}/a2a/{AGENT_NAME}",
        payload={"jsonrpc": "2.0", "id": "contract-probe", "method": "message/send",
                 "params": {"message": {"role": "user",
                                        "parts": [{"text": "status check for PROJ-AI-PROD-01"}]}}},
    )
    if status != 200 or not isinstance(body, dict) or "result" not in body:
        return False, f"/a2a/{AGENT_NAME} failed (HTTP {status}): {str(body)[:200]}"
    reached.append(f"/a2a/{AGENT_NAME}")

    status, body = _request(
        f"{base_url}/api/reasoning_engine",
        payload={"input": {"message": "status check for PROJ-AI-PROD-01"}},
    )
    if status != 200:
        return False, f"/api/reasoning_engine failed (HTTP {status}): {str(body)[:200]}"
    reached.append("/api/reasoning_engine")
    return True, " & ".join(reached)


def check_4_oauth_forwarding(base_url: str) -> Tuple[bool, str]:
    """Sends a mutating request with a Bearer header, exactly as GE would."""
    status, body = _request(
        f"{base_url}/a2a/{AGENT_NAME}",
        payload={"jsonrpc": "2.0", "id": "oauth-probe", "method": "message/send",
                 "params": {"message": {"role": "user", "parts": [
                     {"text": "Open a firewall ticket for PROJ-AI-PROD-01 to enable PSC-I southbound access"}]}}},
        headers={"Authorization": f"Bearer {PROBE_TOKEN}",
                 "X-Requester-Email": PROBE_EMAIL},
    )
    if status != 200 or not isinstance(body, dict):
        return False, f"A2A call failed (HTTP {status}): {str(body)[:200]}"

    result = body.get("result", {})
    if not result.get("metadata", {}).get("oauth2_delegated"):
        return False, ("Bearer token was not propagated — metadata.oauth2_delegated is false. "
                       "Check _extract_oauth_from_request() in app/app_utils/a2a.py")

    text = " ".join(
        part.get("text", "")
        for artifact in result.get("artifacts", [])
        for part in artifact.get("parts", [])
    )
    if "PENDING_HITL_APPROVAL" not in text:
        return False, ("OAuth delegation works but the 2PC HITL approval state is absent from the "
                       "response; infrastructure mutations must not auto-approve")
    return True, f"oauth2_delegated=true, PENDING_HITL_APPROVAL enforced for {PROBE_EMAIL}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 5 Gemini Enterprise readiness check")
    parser.add_argument("--url", default=os.getenv("SERVICE_URL", "http://localhost:8000"),
                        help="Base URL of the running agent (default: $SERVICE_URL or http://localhost:8000)")
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    print("=" * 84)
    print(" [Lab 04 Completion Check] Gemini Enterprise & OAuth 2.0 Readiness")
    print(f" Target: {base_url}")
    print("=" * 84)

    checks = [
        ("A2A Agent Card Schema Compliance (defaultInputModes/defaultOutputModes/skills)",
         lambda: check_1_agent_card(base_url)),
        ("OAuth 2.0 Redirect URI Specification", check_2_oauth_redirect),
        (f"Dual-Contract Endpoints (/a2a/{AGENT_NAME} & /api/reasoning_engine)",
         lambda: check_3_dual_contract(base_url)),
        ("End-to-End OAuth Token Forwarding & 2PC HITL Audit",
         lambda: check_4_oauth_forwarding(base_url)),
    ]

    failed = 0
    for index, (title, fn) in enumerate(checks, start=1):
        ok, detail = fn()
        if ok:
            print(f"[PASS] {index}. {title}")
            print(f"       -> {detail}")
        else:
            failed += 1
            print(f"[FAIL] {index}. {title}")
            print(f"       -> {detail}")

    print("=" * 84)
    if failed:
        print(f"❌ Lab 04 verification FAILED ({failed} of {len(checks)} checks).")
        print("   Is the server running?  .venv/bin/uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 &")
        print("   See labs/TROUBLESHOOTING.md for symptom-by-symptom recovery steps.")
        return 1
    print("🎉 Lab 04 Verification PASSED! Ready for the Gemini Enterprise portal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
