"""Stream-project registry package."""

from .builder import build_default_stream_project_registry
from .registry import StreamProjectRegistry

__all__ = [
    "StreamProjectRegistry",
    "build_default_stream_project_registry",
]
