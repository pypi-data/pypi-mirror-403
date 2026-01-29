"""Type definitions for Sora MCP server."""

from typing import Literal

# Sora model versions
SoraModel = Literal[
    "sora-2",
    "sora-2-pro",
]

# Video size options
VideoSize = Literal["small", "large"]

# Video duration options (in seconds)
VideoDuration = Literal[10, 15, 25]

# Video orientation options
VideoOrientation = Literal["landscape", "portrait", "square"]

# Default model
DEFAULT_MODEL: SoraModel = "sora-2"

# Default settings
DEFAULT_SIZE: VideoSize = "large"
DEFAULT_DURATION: VideoDuration = 15
DEFAULT_ORIENTATION: VideoOrientation = "landscape"
