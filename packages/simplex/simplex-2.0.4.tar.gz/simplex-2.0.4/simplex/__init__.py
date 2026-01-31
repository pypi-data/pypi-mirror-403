"""
Simplex Python SDK

Official Python SDK for the Simplex API - A workflow automation platform.

Example usage:
    >>> from simplex import SimplexClient
    >>> client = SimplexClient(api_key="your-api-key")
    >>> result = client.run_workflow("workflow-id", variables={"key": "value"})
    >>>
    >>> # Poll for completion
    >>> import time
    >>> while True:
    ...     status = client.get_session_status(result["session_id"])
    ...     if not status["in_progress"]:
    ...         break
    ...     time.sleep(1)
    >>>
    >>> if status["success"]:
    ...     print("Outputs:", status["scraper_outputs"])
"""

from simplex.client import SimplexClient
from simplex.errors import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    SimplexError,
    ValidationError,
    WorkflowError,
)
from simplex.types import (
    FileMetadata,
    RunWorkflowResponse,
    SessionStatusResponse,
)

__version__ = "2.0.4"
__all__ = [
    "SimplexClient",
    "SimplexError",
    "NetworkError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "WorkflowError",
    "FileMetadata",
    "SessionStatusResponse",
    "RunWorkflowResponse",
]
