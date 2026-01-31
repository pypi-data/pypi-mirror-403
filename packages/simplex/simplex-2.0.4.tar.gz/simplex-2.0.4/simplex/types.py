"""
Type definitions for the Simplex SDK.

This module contains TypedDict classes used for type hinting throughout the SDK.
"""

from __future__ import annotations

from typing import Any, TypedDict


class FileMetadata(TypedDict):
    """
    Metadata for a file downloaded or created during a session.

    Attributes:
        filename: The filename
        download_url: The URL the file was downloaded from
        file_size: File size in bytes
        download_timestamp: ISO timestamp when the file was downloaded/created
    """

    filename: str
    download_url: str
    file_size: int
    download_timestamp: str


class SessionStatusResponse(TypedDict, total=False):
    """
    Response from polling session status.

    Attributes:
        in_progress: Whether the session is still running
        success: Whether the session completed successfully (None while in progress)
        metadata: Custom metadata provided when the session was started
        workflow_metadata: Metadata from the workflow definition
        file_metadata: Metadata for files downloaded during the session
        scraper_outputs: Scraper outputs collected during the session, keyed by output name
        paused: Whether the session is currently paused
        paused_key: The pause key if the session is paused
    """

    in_progress: bool
    success: bool | None
    metadata: dict[str, Any]
    workflow_metadata: dict[str, Any]
    file_metadata: list[FileMetadata]
    scraper_outputs: dict[str, Any]
    paused: bool
    paused_key: str


class RunWorkflowResponse(TypedDict):
    """
    Response from running a workflow.

    Attributes:
        succeeded: Whether the workflow started successfully
        message: Human-readable status message
        session_id: Unique identifier for this workflow session
        vnc_url: URL for VNC access to the workflow session
        logs_url: URL for viewing session logs
    """

    succeeded: bool
    message: str
    session_id: str
    vnc_url: str
    logs_url: str
