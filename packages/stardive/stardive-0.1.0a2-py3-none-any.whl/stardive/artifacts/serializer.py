from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, List

from .enums import SecretDetectionMode


class SecretDetectedError(ValueError):
    """Raised when secret-like values are detected in STRICT mode."""


def serialize_canonical(content: Any) -> str:
    """
    Serialize content to a canonical JSON string.

    This is used for deterministic hashing and storage of JSON artifacts.
    """
    try:
        return json.dumps(
            content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
    except TypeError as exc:
        raise TypeError(f"Content is not JSON-serializable: {exc}") from exc


def compute_hash(content: Any) -> str:
    """
    Compute a stable SHA256 hash for JSON-serializable content.

    Returns a digest string prefixed with 'sha256:'.
    """
    serialized = serialize_canonical(content)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_text_hash(text: str) -> str:
    """Compute a SHA256 hash for raw text content."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


_SUSPICIOUS_KEYS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "private_key",
}


def _iter_secret_paths(
    content: Any, prefix: str = "", max_depth: int = 6
) -> Iterable[str]:
    if max_depth < 0:
        return []

    if isinstance(content, dict):
        for key, value in content.items():
            key_str = str(key)
            path = f"{prefix}.{key_str}" if prefix else key_str
            if key_str.lower() in _SUSPICIOUS_KEYS:
                yield path
            yield from _iter_secret_paths(value, path, max_depth - 1)
    elif isinstance(content, list):
        for idx, value in enumerate(content):
            path = f"{prefix}[{idx}]"
            yield from _iter_secret_paths(value, path, max_depth - 1)
    elif isinstance(content, str):
        if "-----BEGIN" in content or content.strip().startswith("sk-"):
            yield prefix or "<root>"


def detect_secrets(content: Any, mode: SecretDetectionMode) -> List[str]:
    """
    Best-effort secret detection for JSON-like content.

    Returns a list of paths where secret-like values were detected.
    """
    if mode == SecretDetectionMode.DISABLED:
        return []

    return list(_iter_secret_paths(content))
