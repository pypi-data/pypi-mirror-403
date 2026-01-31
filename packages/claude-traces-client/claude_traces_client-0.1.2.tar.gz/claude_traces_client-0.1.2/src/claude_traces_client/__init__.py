"""claude_traces_client: Extract and upload Claude Code traces."""

from .wrapper import traced, TraceUploadError
from .uploader import UploadError

__all__ = ["traced", "TraceUploadError", "UploadError"]
