"""
Main SimplexClient class for the Simplex SDK.

This module provides the SimplexClient, which is the primary entry point
for interacting with the Simplex API.
"""

from __future__ import annotations

import json
from typing import Any

from simplex._http_client import HttpClient
from simplex.errors import WorkflowError
from simplex.types import RunWorkflowResponse, SessionStatusResponse


class SimplexClient:
    """
    Main client for interacting with the Simplex API.

    This is the primary entry point for the SDK. It provides a flat API
    for all Simplex API functionality.

    Example:
        >>> from simplex import SimplexClient
        >>> client = SimplexClient(api_key="your-api-key")
        >>>
        >>> # Run a workflow
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
        ...     print("Scraper outputs:", status["scraper_outputs"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.simplex.sh",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the Simplex client.

        Args:
            api_key: Your Simplex API key (required)
            base_url: Base URL for the API (default: "https://api.simplex.sh")
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)

        Raises:
            ValueError: If api_key is not provided
        """
        if not api_key:
            raise ValueError("api_key is required")

        self._http_client = HttpClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

    def run_workflow(
        self,
        workflow_id: str,
        variables: dict[str, Any] | None = None,
        metadata: str | None = None,
        webhook_url: str | None = None,
    ) -> RunWorkflowResponse:
        """
        Run a workflow by its ID.

        Args:
            workflow_id: The ID of the workflow to run
            variables: Dictionary of variables to pass to the workflow
            metadata: Optional metadata string to attach to the workflow run
            webhook_url: Optional webhook URL for status updates

        Returns:
            RunWorkflowResponse with session_id and other details

        Raises:
            WorkflowError: If the workflow fails to start

        Example:
            >>> result = client.run_workflow(
            ...     "workflow-id",
            ...     variables={"email": "user@example.com"}
            ... )
            >>> print(f"Session ID: {result['session_id']}")
        """
        request_data: dict[str, Any] = {"workflow_id": workflow_id}

        if variables is not None:
            request_data["variables"] = variables
        if metadata is not None:
            request_data["metadata"] = metadata
        if webhook_url is not None:
            request_data["webhook_url"] = webhook_url

        try:
            response: RunWorkflowResponse = self._http_client.post(
                "/run_workflow",
                data=request_data,
            )
            return response
        except Exception as e:
            if isinstance(e, WorkflowError):
                raise
            raise WorkflowError(f"Failed to run workflow: {e}", workflow_id=workflow_id)

    def get_session_status(self, session_id: str) -> SessionStatusResponse:
        """
        Get the status of a session.

        Use this method to poll for workflow completion. The session is complete
        when `in_progress` is False.

        Args:
            session_id: The session ID to check

        Returns:
            SessionStatusResponse with status, metadata, and scraper outputs

        Raises:
            WorkflowError: If retrieving status fails

        Example:
            >>> status = client.get_session_status("session-123")
            >>> if not status["in_progress"]:
            ...     if status["success"]:
            ...         print("Success! Outputs:", status["scraper_outputs"])
            ...     else:
            ...         print("Failed")
        """
        try:
            response: SessionStatusResponse = self._http_client.get(
                f"/session/{session_id}/status"
            )
            return response
        except Exception as e:
            if isinstance(e, WorkflowError):
                raise
            raise WorkflowError(
                f"Failed to get session status: {e}",
                session_id=session_id,
            )

    def download_session_files(
        self,
        session_id: str,
        filename: str | None = None,
    ) -> bytes:
        """
        Download files from a session.

        Downloads files that were created or downloaded during a workflow session.
        If no filename is specified, all files are downloaded as a zip archive.

        Args:
            session_id: ID of the session to download files from
            filename: Optional specific filename to download

        Returns:
            File content as bytes

        Raises:
            WorkflowError: If file download fails

        Example:
            >>> # Download all files as zip
            >>> zip_data = client.download_session_files("session-123")
            >>> with open("files.zip", "wb") as f:
            ...     f.write(zip_data)
            >>>
            >>> # Download specific file
            >>> pdf_data = client.download_session_files("session-123", "report.pdf")
        """
        try:
            params: dict[str, str] = {"session_id": session_id}
            if filename:
                params["filename"] = filename

            content = self._http_client.download_file("/download_session_files", params=params)

            # Check if the response is a JSON error
            try:
                text = content.decode("utf-8")
                data = json.loads(text)
                if isinstance(data, dict) and data.get("succeeded") is False:
                    raise WorkflowError(
                        data.get("error") or "Failed to download session files",
                        session_id=session_id,
                    )
            except (UnicodeDecodeError, json.JSONDecodeError):
                # Binary data (the file), which is what we want
                pass

            return content
        except WorkflowError:
            raise
        except Exception as e:
            raise WorkflowError(
                f"Failed to download session files: {e}",
                session_id=session_id,
            )

    def retrieve_session_replay(self, session_id: str) -> bytes:
        """
        Retrieve the session replay video for a completed session.

        Downloads a video (MP4) recording of the browser session after it
        has completed.

        Args:
            session_id: ID of the session to retrieve replay for

        Returns:
            Video content as bytes (MP4 format)

        Raises:
            WorkflowError: If retrieving session replay fails

        Example:
            >>> video_data = client.retrieve_session_replay("session-123")
            >>> with open("replay.mp4", "wb") as f:
            ...     f.write(video_data)
        """
        try:
            content = self._http_client.download_file(f"/retrieve_session_replay/{session_id}")
            return content
        except Exception as e:
            if isinstance(e, WorkflowError):
                raise
            raise WorkflowError(
                f"Failed to retrieve session replay: {e}",
                session_id=session_id,
            )

    def retrieve_session_logs(self, session_id: str) -> Any | None:
        """
        Retrieve the session logs for a session.

        Returns None if the session is still running or shutting down.
        Logs are only available for completed sessions.

        Args:
            session_id: ID of the session to retrieve logs for

        Returns:
            Parsed JSON logs containing session events and details,
            or None if the session is still running

        Raises:
            WorkflowError: If retrieving session logs fails

        Example:
            >>> logs = client.retrieve_session_logs("session-123")
            >>> if logs is None:
            ...     print("Session is still running, logs not yet available")
            ... else:
            ...     print(f"Got {len(logs)} log entries")
        """
        try:
            content = self._http_client.download_file(f"/retrieve_session_logs/{session_id}")
            text = content.decode("utf-8")
            response = json.loads(text)
            return response.get("logs")
        except json.JSONDecodeError as e:
            raise WorkflowError(
                f"Failed to parse session logs: {e}",
                session_id=session_id,
            )
        except Exception as e:
            if isinstance(e, WorkflowError):
                raise
            raise WorkflowError(
                f"Failed to retrieve session logs: {e}",
                session_id=session_id,
            )
