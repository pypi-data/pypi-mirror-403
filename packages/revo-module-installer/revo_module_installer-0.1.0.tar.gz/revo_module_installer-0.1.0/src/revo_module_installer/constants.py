"""Shared constants for the Revo modules package."""

from typing import Final

REGISTRY_REPOSITORY_URL: Final[str] = (
    "https://github.com/revodatanl/revo-module-registry"
)
REGISTRY_INDEX_FILENAME: Final[str] = "registry.yml"
LOCAL_REGISTRY_ENVIRONMENT_VARIABLE: Final[str] = "REVO_MODULES_ENV"
LOCAL_REGISTRY_ENVIRONMENT_VALUE: Final[str] = "test"
LOCAL_REGISTRY_FALLBACK_VARIABLE: Final[str] = (
    "REVO_MODULES_ALLOW_LOCAL_REGISTRY_FALLBACK"
)
LOCAL_REGISTRY_FALLBACK_VALUE: Final[str] = "1"
