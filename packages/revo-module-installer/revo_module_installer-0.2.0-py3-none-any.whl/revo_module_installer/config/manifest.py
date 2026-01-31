"""Pydantic configuration models."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field


def _default_manifest_history() -> list[ManifestHistoryEntry]:
    """Return default manifest history entries.

    Returns:
        Default manifest history list.
    """
    return []


class ManifestEntry(BaseModel):
    """Represents a single entry in a manifest file."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str
    description: str | None = None
    ref_type: Literal["git", "git_branch", "git_tag", "url"] | None = None
    ref_value: str | None = None
    artifact_path: str
    action: Literal["add", "add_overwrite", "append_replace"]
    anchor: str | None = None


class ManifestHistoryEntry(BaseModel):
    """Represents a manifest history entry."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    version: str
    manifest_url: str


class ManifestIndex(BaseModel):
    """Represents yaml file for a modules manifest."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    version: str
    entries: list[ManifestEntry]
    manifest_history: list[ManifestHistoryEntry] = Field(
        default_factory=_default_manifest_history,
    )
