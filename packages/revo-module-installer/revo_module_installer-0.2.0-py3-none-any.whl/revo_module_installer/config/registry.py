"""Pydantic configuration models."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict


class RegistryEntry(BaseModel):
    """A single registry entry."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    pricing: Literal["paid", "free"] = "free"
    manifest_url: str


class RegistryIndex(BaseModel):
    """Registry index data."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    version: str
    entries: list[RegistryEntry]
