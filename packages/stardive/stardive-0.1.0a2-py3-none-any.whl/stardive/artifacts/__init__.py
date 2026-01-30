"""
Artifact utilities and storage for Stardive.

This package provides artifact kinds, hashing/serialization helpers, basic
secret detection, and a simple SQLite-backed artifact store.
"""

from .enums import ArtifactKind, SecretDetectionMode
from .serializer import (
    SecretDetectedError,
    compute_hash,
    compute_text_hash,
    detect_secrets,
    serialize_canonical,
)
from .storage import ArtifactStorage, SQLiteArtifactStorage

__all__ = [
    "ArtifactKind",
    "SecretDetectionMode",
    "SecretDetectedError",
    "compute_hash",
    "compute_text_hash",
    "serialize_canonical",
    "detect_secrets",
    "ArtifactStorage",
    "SQLiteArtifactStorage",
]
