"""Settings for the Gradio adapter."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GradioSettings:
    """Settings for configuring the Gradio server."""

    server_port: int = 7860
    share: bool = False
    input_max_chars: int = 2000
    rate_limit_requests: int = 8
    rate_limit_window_seconds: int = 60
