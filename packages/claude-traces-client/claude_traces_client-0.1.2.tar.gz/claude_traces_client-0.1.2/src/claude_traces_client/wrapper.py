"""Async iterator wrapper for tracing."""

import logging
import os
from collections.abc import AsyncIterator

from claude_code_sdk import Message, SystemMessage

from .paths import encode_project_path, get_trace_file_path, get_project_traces_dir
from .uploader import post_trace, UploadError

logger = logging.getLogger(__name__)


class TraceUploadError(Exception):
    """Raised when trace upload fails."""

    pass


async def traced(
    messages: AsyncIterator[Message],
    *,
    project_path: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
) -> AsyncIterator[Message]:
    """
    Wrap a Claude SDK message iterator to upload traces after completion.

    Requires an API key for authenticated uploads. The API key can be provided
    directly or via the CLAUDE_TRACES_API_KEY environment variable.

    The endpoint is read from CLAUDE_TRACES_ENDPOINT env var.
    Default: https://claudetraces.dev/api/trace

    Usage:
        async for msg in traced(query(prompt="Hello"), api_key="sk_..."):
            print(msg)

    Args:
        messages: AsyncIterator from query() or ClaudeSDKClient
        project_path: Project path for trace lookup (default: cwd)
        api_key: API key for authentication (default: from CLAUDE_TRACES_API_KEY env var)
        timeout: Upload timeout in seconds

    Yields:
        Messages unchanged from the underlying iterator

    Raises:
        TraceUploadError: If API key is missing
    """
    # Resolve API key from env var if not provided
    resolved_api_key = api_key or os.environ.get("CLAUDE_TRACES_API_KEY")
    if not resolved_api_key:
        raise TraceUploadError(
            "API key required. Set CLAUDE_TRACES_API_KEY environment variable "
            "or pass api_key parameter."
        )

    # Resolve project path
    if project_path is None:
        project_path = os.getcwd()

    session_id: str | None = None

    async for msg in messages:
        # Capture session_id from the first SystemMessage (init)
        if isinstance(msg, SystemMessage) and msg.subtype == "init":
            session_id = msg.data.get("session_id")

        yield msg

    # After iteration completes, upload the trace
    if session_id:
        trace_path = get_trace_file_path(session_id, project_path)
        project_dir = get_project_traces_dir(project_path)
        subagents_dir = project_dir / session_id

        # Encode project path for storage
        encoded_project_path = encode_project_path(project_path)

        try:
            await post_trace(
                trace_path=trace_path,
                session_id=session_id,
                api_key=resolved_api_key,
                project_path=encoded_project_path,
                subagents_dir=subagents_dir if subagents_dir.exists() else None,
                timeout=timeout,
            )
        except (UploadError, Exception) as e:
            logger.warning(f"Failed to upload trace {session_id}: {e}")
    else:
        logger.warning("No session_id captured from messages, skipping trace upload")
