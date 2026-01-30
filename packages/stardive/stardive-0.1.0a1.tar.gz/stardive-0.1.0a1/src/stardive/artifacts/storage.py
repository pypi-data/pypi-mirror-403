from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol

from .enums import ArtifactKind
from .serializer import serialize_canonical


class ArtifactStorage(Protocol):
    """Protocol for artifact storage backends."""

    def store_artifact(self, artifact_ref: Any, content: Any, kind: ArtifactKind) -> str:
        """Store artifact content and return a URI."""

    def retrieve_artifact(self, artifact_ref: Any) -> Any:
        """Retrieve artifact content for the given ArtifactRef."""


@dataclass
class SQLiteArtifactStorage:
    """SQLite-backed artifact storage for JSON/TEXT artifacts."""

    db_path: str
    artifact_dir: str | None = None

    def __post_init__(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if self.artifact_dir is not None:
            os.makedirs(self.artifact_dir, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    content_text TEXT,
                    content_blob BLOB
                )
                """
            )

    def store_artifact(self, artifact_ref: Any, content: Any, kind: ArtifactKind) -> str:
        if kind == ArtifactKind.JSON:
            content_text = serialize_canonical(content)
            content_blob = None
        elif kind == ArtifactKind.TEXT:
            if not isinstance(content, str):
                raise TypeError(f"TEXT artifact must be string, got {type(content)}")
            content_text = content
            content_blob = None
        elif kind in (ArtifactKind.BYTES, ArtifactKind.FILE):
            if isinstance(content, str):
                content = content.encode("utf-8")
            if not isinstance(content, (bytes, bytearray)):
                raise TypeError(f"{kind} artifact must be bytes, got {type(content)}")
            content_text = None
            content_blob = bytes(content)
        else:
            raise TypeError(f"Unsupported artifact kind: {kind}")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts (artifact_id, kind, content_text, content_blob)
                VALUES (?, ?, ?, ?)
                """,
                (artifact_ref.artifact_id, kind.value, content_text, content_blob),
            )

        return f"sqlite://{self.db_path}#{artifact_ref.artifact_id}"

    def retrieve_artifact(self, artifact_ref: Any) -> Any:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT kind, content_text, content_blob FROM artifacts WHERE artifact_id = ?",
                (artifact_ref.artifact_id,),
            ).fetchone()

        if row is None:
            raise KeyError(f"Artifact {artifact_ref.artifact_id} not found")

        kind_value, content_text, content_blob = row
        kind = ArtifactKind(kind_value)

        if kind == ArtifactKind.JSON:
            return json.loads(content_text)
        if kind == ArtifactKind.TEXT:
            return content_text
        if kind in (ArtifactKind.BYTES, ArtifactKind.FILE):
            return content_blob

        raise TypeError(f"Unsupported artifact kind: {kind}")
