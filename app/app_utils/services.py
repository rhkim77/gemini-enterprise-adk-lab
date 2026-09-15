"""Session and Artifact Service Builders for ADK Runtime."""
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService

SESSION_SERVICE_URI = "memory://"
ARTIFACT_SERVICE_URI = "memory://"

_session_service = InMemorySessionService()
_artifact_service = InMemoryArtifactService()


def get_session_service():
    return _session_service


def get_artifact_service():
    return _artifact_service
