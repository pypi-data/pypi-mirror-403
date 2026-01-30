from __future__ import annotations

from enum import Enum


class ArtifactKind(str, Enum):
    """Supported artifact kinds."""

    JSON = "json"
    TEXT = "text"
    BYTES = "bytes"
    FILE = "file"


class SecretDetectionMode(str, Enum):
    """How to handle potential secrets in artifact content."""

    DISABLED = "disabled"
    BEST_EFFORT = "best_effort"
    STRICT = "strict"
