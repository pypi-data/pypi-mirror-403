"""HTTP upload logic for trace files."""

import asyncio
import io
import os
import tarfile
from pathlib import Path

import httpx

DEFAULT_ENDPOINT = "https://claudetraces.dev/api/trace"


class UploadError(Exception):
    """Raised when trace upload fails."""

    pass


def get_endpoint() -> str:
    """Get the trace upload endpoint from env var or default."""
    return os.environ.get("CLAUDE_TRACES_ENDPOINT", DEFAULT_ENDPOINT)


def create_tar_gz_bundle(
    trace_path: Path,
    session_id: str,
    subagents_dir: Path | None = None,
) -> bytes:
    """
    Create a tar.gz archive containing the main trace and optionally subagents.

    The archive structure:
    - {session_id}.jsonl (main trace)
    - {session_id}/ (subagents folder, if exists)

    Args:
        trace_path: Path to the main .jsonl trace file
        session_id: Session ID
        subagents_dir: Optional path to subagents directory

    Returns:
        Compressed tar.gz bytes
    """
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        # Add main trace file
        tar.add(trace_path, arcname=f"{session_id}.jsonl")

        # Add subagents directory if it exists
        if subagents_dir and subagents_dir.is_dir():
            for subagent_file in subagents_dir.iterdir():
                if subagent_file.is_file() and subagent_file.suffix == ".jsonl":
                    tar.add(
                        subagent_file,
                        arcname=f"{session_id}/{subagent_file.name}",
                    )

    buffer.seek(0)
    return buffer.read()


async def post_trace(
    trace_path: Path,
    session_id: str,
    api_key: str,
    project_path: str,
    subagents_dir: Path | None = None,
    timeout: float = 30.0,
) -> None:
    """
    POST a tar.gz bundle containing trace files to the configured endpoint.

    Args:
        trace_path: Path to the .jsonl trace file
        session_id: Session ID
        api_key: API key for authentication
        project_path: Encoded project path (e.g., "-Users-foo-bar")
        subagents_dir: Optional path to subagents directory
        timeout: Request timeout in seconds

    Raises:
        UploadError: If the file doesn't exist or upload fails
    """
    if not trace_path.exists():
        raise UploadError(f"Trace file not found: {trace_path}")

    # Create tar.gz bundle (run in thread to avoid blocking event loop)
    bundle = await asyncio.to_thread(
        create_tar_gz_bundle, trace_path, session_id, subagents_dir
    )
    endpoint = get_endpoint()

    headers = {
        "Content-Type": "application/gzip",
        "X-API-Key": api_key,
        "X-Project-Path": project_path,
        "X-Session-Id": session_id,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            endpoint,
            content=bundle,
            headers=headers,
        )

        if response.status_code == 401:
            raise UploadError("Invalid API key")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                raise UploadError(f"Bad request: {error_data.get('error', 'Unknown error')}")
            except ValueError:
                raise UploadError(f"Bad request: {response.text}")
        elif not response.is_success:
            raise UploadError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )
