"""Configuration loading helpers."""

from __future__ import annotations

from importlib.abc import Traversable
from importlib.resources import files
import logging
import os
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import ParseResult, urlparse

import httpx
from ruamel.yaml import YAML

from revo_module_installer.config.manifest import ManifestIndex
from revo_module_installer.config.registry import RegistryIndex
from revo_module_installer.constants import (
    LOCAL_REGISTRY_ENVIRONMENT_VALUE,
    LOCAL_REGISTRY_ENVIRONMENT_VARIABLE,
    LOCAL_REGISTRY_FALLBACK_VALUE,
    LOCAL_REGISTRY_FALLBACK_VARIABLE,
    REGISTRY_INDEX_FILENAME,
)

LOCAL_EXAMPLE_MANIFEST_FILENAME: Final[str] = "example_manifest.yml"
LOCAL_EXAMPLE_REGISTRY_FILENAME: Final[str] = "example_registry.yml"
REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0

logger: logging.Logger = logging.getLogger(__name__)


def resolve_registry_index_url(registry_repository_url: str) -> str:
    """Resolve a registry index URL from a git repository location.

    Args:
        registry_repository_url: URL to the registry git repository.

    Returns:
        URL to the registry index YAML file.
    """
    parsed_repository_url: ParseResult = urlparse(registry_repository_url)
    if parsed_repository_url.netloc != "github.com":
        return registry_repository_url

    repository_path: str = parsed_repository_url.path.strip("/")
    if repository_path.endswith(".git"):
        repository_path = repository_path[: -len(".git")]

    return (
        f"https://raw.githubusercontent.com/{repository_path}/main/"
        f"{REGISTRY_INDEX_FILENAME}"
    )


def resolve_raw_github_url(resource_url: str) -> str:
    """Convert a GitHub blob URL to a raw content URL.

    Args:
        resource_url: URL that may point to a GitHub blob.

    Returns:
        Raw content URL if the input is a GitHub blob, otherwise the input.
    """
    parsed_url: ParseResult = urlparse(resource_url)
    if parsed_url.netloc in {"raw.githubusercontent.com", ""}:
        return resource_url

    if parsed_url.netloc != "github.com":
        return resource_url

    path_parts: list[str] = parsed_url.path.strip("/").split("/")
    if "blob" not in path_parts:
        return resource_url

    blob_index: int = path_parts.index("blob")
    if blob_index < 2 or blob_index + 2 >= len(path_parts):
        return resource_url

    repository_slug: str = "/".join(path_parts[:blob_index])
    ref_name: str = path_parts[blob_index + 1]
    file_path: str = "/".join(path_parts[blob_index + 2 :])
    return (
        f"https://raw.githubusercontent.com/{repository_slug}/{ref_name}/"
        f"{file_path}"
    )


def get_local_example_registry_path() -> Path:
    """Return the path to the bundled example registry file.

    Returns:
        Filesystem path to the example registry.
    """
    package_root: Path = Path(__file__).resolve().parents[1]
    return package_root / "examples" / LOCAL_EXAMPLE_REGISTRY_FILENAME


def get_local_example_manifest_path() -> Path:
    """Return the path to the bundled example manifest file.

    Returns:
        Filesystem path to the example manifest.
    """
    package_root: Path = Path(__file__).resolve().parents[1]
    return package_root / "examples" / LOCAL_EXAMPLE_MANIFEST_FILENAME


def _resolve_package_resource_name(parsed_url: ParseResult) -> str:
    """Resolve a resource name from a package URL.

    Args:
        parsed_url: Parsed package URL.

    Returns:
        Resource name within the package data directory.
    """
    if parsed_url.netloc:
        return parsed_url.netloc
    return parsed_url.path.lstrip("/")


def _load_text_from_package(resource_name: str) -> str:
    """Load text from a package example resource.

    Args:
        resource_name: Filename within the package examples directory.

    Returns:
        Text contents of the resource.
    """
    resource_path: Traversable = (
        files("revo_module_installer.examples") / resource_name
    )
    if not resource_path.is_file():
        message: str = f"Package resource not found: {resource_name}"
        raise FileNotFoundError(message)
    return resource_path.read_text(encoding="utf-8")


def _load_text_from_file(resource_path: Path) -> str:
    """Load text from a local file path.

    Args:
        resource_path: Path to the local file.

    Returns:
        Text contents of the file.
    """
    return resource_path.read_text(encoding="utf-8")


def load_text_from_location(resource_url: str) -> str:
    """Load text from HTTP, file, or package locations.

    Args:
        resource_url: URL or path to load.

    Returns:
        Text contents of the resource.
    """
    parsed_url: ParseResult = urlparse(resource_url)
    if parsed_url.scheme in {"http", "https"}:
        response: httpx.Response = httpx.get(
            resource_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text

    if parsed_url.scheme == "file":
        resource_path: Path = Path(parsed_url.path)
        return _load_text_from_file(resource_path)

    if parsed_url.scheme == "package":
        resource_name: str = _resolve_package_resource_name(parsed_url)
        return _load_text_from_package(resource_name)

    resource_path: Path = Path(resource_url)
    if parsed_url.scheme == "" and resource_path.exists():
        return _load_text_from_file(resource_path)

    message: str = f"Unsupported resource location: {resource_url}"
    raise ValueError(message)


def _load_registry_from_text(registry_text: str) -> RegistryIndex:
    """Parse registry YAML content into a registry index.

    Args:
        registry_text: Raw YAML text.

    Returns:
        Parsed registry index.
    """
    yaml_parser: YAML = YAML(typ="rt")
    data: object = cast(Any, yaml_parser).load(registry_text)
    return RegistryIndex.model_validate(data)


def _load_manifest_from_text(manifest_text: str) -> ManifestIndex:
    """Parse manifest YAML content into a manifest index.

    Args:
        manifest_text: Raw YAML text.

    Returns:
        Parsed manifest index.
    """
    yaml_parser: YAML = YAML(typ="rt")
    data: object = cast(Any, yaml_parser).load(manifest_text)
    return ManifestIndex.model_validate(data)


def _load_local_registry(
    local_registry_path: Path | None,
) -> RegistryIndex:
    """Load the local example registry file.

    Args:
        local_registry_path: Path override for the example registry file.

    Returns:
        Parsed registry index.
    """
    resolved_path: Path = (
        local_registry_path
        if local_registry_path is not None
        else get_local_example_registry_path()
    )
    registry_text: str = _load_text_from_file(resolved_path)
    return _load_registry_from_text(registry_text)


def _local_fallback_allowed(allow_local_fallback: bool) -> bool:
    """Check if local fallback is permitted for the current environment.

    Args:
        allow_local_fallback: Whether the caller wants to allow fallback.

    Returns:
        True when fallback is allowed, otherwise False.
    """
    if not allow_local_fallback:
        return False

    environment_value: str | None = os.getenv(LOCAL_REGISTRY_ENVIRONMENT_VARIABLE)
    fallback_value: str | None = os.getenv(LOCAL_REGISTRY_FALLBACK_VARIABLE)
    return (
        environment_value == LOCAL_REGISTRY_ENVIRONMENT_VALUE
        and fallback_value == LOCAL_REGISTRY_FALLBACK_VALUE
    )


def load_registry_index(
    registry_repository_url: str,
    *,
    allow_local_fallback: bool = False,
    local_registry_path: Path | None = None,
) -> RegistryIndex:
    """Load a registry index from a URL.

    Args:
        registry_repository_url: URL to the registry git repository.
        allow_local_fallback: Whether to allow a local example registry fallback.
        local_registry_path: Optional path to the local example registry file.

    Returns:
        Parsed registry index.
    """
    registry_index_url: str = resolve_registry_index_url(registry_repository_url)
    try:
        registry_text: str = load_text_from_location(registry_index_url)
        return _load_registry_from_text(registry_text)
    except (httpx.HTTPError, OSError, ValueError) as exc:
        if not _local_fallback_allowed(allow_local_fallback):
            raise
        logger.info(
            "Falling back to local registry after fetch error: %s",
            exc,
        )
        return _load_local_registry(local_registry_path)


def load_manifest_index(
    manifest_url: str,
) -> ManifestIndex:
    """Load a manifest index from a URL or path.

    Args:
        manifest_url: URL or path to the manifest file.

    Returns:
        Parsed manifest index.
    """
    resolved_url: str = resolve_raw_github_url(manifest_url)
    manifest_text: str = load_text_from_location(resolved_url)
    return _load_manifest_from_text(manifest_text)
