"""Command line interface for Revo modules."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Annotated, TypedDict

from platformdirs import user_cache_path
from rich.console import Console
from rich.table import Table
import typer

from revo_module_installer.config.load import load_manifest_index, load_registry_index
from revo_module_installer.config.manifest import (
    ManifestEntry,
    ManifestIndex,
)
from revo_module_installer.config.registry import (
    RegistryEntry,
    RegistryIndex,
)
from revo_module_installer.constants import (
    LOCAL_REGISTRY_ENVIRONMENT_VALUE,
    LOCAL_REGISTRY_ENVIRONMENT_VARIABLE,
    LOCAL_REGISTRY_FALLBACK_VALUE,
    LOCAL_REGISTRY_FALLBACK_VARIABLE,
    REGISTRY_REPOSITORY_URL,
)
from revo_module_installer.logging import setup_logging

app: typer.Typer = typer.Typer(help="Revo modules CLI.")
modules_app: typer.Typer = typer.Typer(help="Manage modules.")
app.add_typer(modules_app, name="modules")
console: Console = Console()
logger: logging.Logger = logging.getLogger(__name__)


class InstallPlanEntry(TypedDict):
    """Install plan entry derived from a manifest entry."""

    id: str
    action: str
    artifact_path: str
    ref_type: str | None
    ref_value: str | None
    anchor: str | None


class InstallPlan(TypedDict):
    """Install plan for a module."""

    module_id: str
    module_name: str
    registry_version: str
    manifest_version: str
    entries: list[InstallPlanEntry]


def allow_local_registry_fallback() -> bool:
    """Determine whether local registry fallback is allowed."""
    environment_value: str | None = os.getenv(LOCAL_REGISTRY_ENVIRONMENT_VARIABLE)
    fallback_value: str | None = os.getenv(LOCAL_REGISTRY_FALLBACK_VARIABLE)
    return (
        environment_value == LOCAL_REGISTRY_ENVIRONMENT_VALUE
        and fallback_value == LOCAL_REGISTRY_FALLBACK_VALUE
    )


def main_callback(verbose: bool = False) -> None:
    """Configure logging for CLI commands.

    Args:
        verbose: Enable debug logging.
    """
    setup_logging(verbose)


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Revo modules CLI entrypoint.

    Args:
        verbose: Enable debug logging.
    """
    main_callback(verbose)


def build_registry_table(
    registry_entries: list[RegistryEntry],
    *,
    show_description: bool,
) -> Table:
    """Build a rich table for registry entries.

    Args:
        registry_entries: Entries from the registry index.
        show_description: Whether to show descriptions.

    Returns:
        Rich table representation of entries.
    """
    table: Table = Table(title="Registry entries")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    if show_description:
        table.add_column("Description")
    table.add_column("Manifest URL", overflow="fold")

    for registry_entry in registry_entries:
        row: list[str] = [
            registry_entry.id,
            registry_entry.name,
        ]
        if show_description:
            row.append(registry_entry.description)
        row.append(registry_entry.manifest_url)
        table.add_row(*row)
    return table


def find_registry_entry(
    registry_entries: list[RegistryEntry],
    module_id: str,
) -> RegistryEntry | None:
    """Find a registry entry by ID.

    Args:
        registry_entries: Entries from the registry index.
        module_id: Module identifier to search for.

    Returns:
        Matching registry entry or None.
    """
    for registry_entry in registry_entries:
        if registry_entry.id == module_id:
            return registry_entry
    return None


def build_install_plan(
    registry_entry: RegistryEntry,
    manifest_index: ManifestIndex,
    registry_version: str,
) -> InstallPlan:
    """Build an install plan from registry and manifest metadata.

    Args:
        registry_entry: Registry metadata for the module.
        manifest_index: Parsed manifest data.
        registry_version: Version of the registry index.

    Returns:
        Install plan dictionary.
    """
    plan_entries: list[InstallPlanEntry] = []
    for manifest_entry in manifest_index.entries:
        plan_entry: InstallPlanEntry = {
            "id": manifest_entry.id,
            "action": manifest_entry.action,
            "artifact_path": manifest_entry.artifact_path,
            "ref_type": manifest_entry.ref_type,
            "ref_value": manifest_entry.ref_value,
            "anchor": manifest_entry.anchor,
        }
        plan_entries.append(plan_entry)

    plan: InstallPlan = {
        "module_id": registry_entry.id,
        "module_name": registry_entry.name,
        "registry_version": registry_version,
        "manifest_version": manifest_index.version,
        "entries": plan_entries,
    }
    return plan


def render_manifest_table(manifest_entries: list[ManifestEntry]) -> Table:
    """Build a rich table for manifest entries.

    Args:
        manifest_entries: Entries from the manifest index.

    Returns:
        Rich table representation of manifest entries.
    """
    table: Table = Table(title="Manifest actions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Action", style="magenta")
    table.add_column("Artifact", overflow="fold")
    table.add_column("Ref", overflow="fold")
    table.add_column("Anchor", overflow="fold")

    for manifest_entry in manifest_entries:
        ref_summary_parts: list[str] = []
        if manifest_entry.ref_type:
            ref_summary_parts.append(manifest_entry.ref_type)
        if manifest_entry.ref_value:
            ref_summary_parts.append(manifest_entry.ref_value)
        ref_summary: str = ":".join(ref_summary_parts) if ref_summary_parts else "-"
        anchor_value: str = manifest_entry.anchor or "-"
        table.add_row(
            manifest_entry.id,
            manifest_entry.action,
            manifest_entry.artifact_path,
            ref_summary,
            anchor_value,
        )
    return table


def default_plan_path(module_id: str) -> Path:
    """Return the default install plan output path.

    Args:
        module_id: Module identifier to scope the plan.

    Returns:
        Path to the install plan file.
    """
    cache_root: Path = user_cache_path("revo-modules")
    return cache_root / "plans" / f"{module_id}.json"


def write_install_plan(plan: InstallPlan, output_path: Path) -> None:
    """Write the install plan to a JSON file.

    Args:
        plan: Install plan to serialize.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: str = json.dumps(plan, indent=2, sort_keys=True)
    output_path.write_text(payload, encoding="utf-8")


@modules_app.command("list")
def list_modules(
    registry_url: Annotated[
        str,
        typer.Option(
            "--registry-url",
            help="Registry repository or index URL.",
        ),
    ] = REGISTRY_REPOSITORY_URL,
    show_description: Annotated[
        bool,
        typer.Option(
            "--show-description",
            help="Show module descriptions in the table.",
        ),
    ] = False,
    allow_local_fallback: Annotated[
        bool,
        typer.Option(
            "--allow-local-fallback",
            help="Allow using the bundled example registry in tests.",
        ),
    ] = False,
    local_registry_path: Annotated[
        Path | None,
        typer.Option(
            "--local-registry-path",
            help="Override path to the bundled example registry file.",
        ),
    ] = None,
) -> None:
    """List registry modules."""
    effective_fallback: bool = allow_local_fallback or allow_local_registry_fallback()
    registry_index: RegistryIndex = load_registry_index(
        registry_url,
        allow_local_fallback=effective_fallback,
        local_registry_path=local_registry_path,
    )
    entry_count: int = len(registry_index.entries)
    console.print(f"Registry entries: {entry_count}")
    console.print(
        build_registry_table(
            registry_index.entries,
            show_description=show_description,
        ),
    )


@modules_app.command("install")
def install_modules(
    module_id: Annotated[
        str,
        typer.Argument(help="Module ID to install."),
    ],
    registry_url: Annotated[
        str,
        typer.Option(
            "--registry-url",
            help="Registry repository or index URL.",
        ),
    ] = REGISTRY_REPOSITORY_URL,
    manifest_url: Annotated[
        str | None,
        typer.Option(
            "--manifest-url",
            help="Override manifest URL instead of registry metadata.",
        ),
    ] = None,
    allow_local_fallback: Annotated[
        bool,
        typer.Option(
            "--allow-local-fallback",
            help="Allow using the bundled example registry in tests.",
        ),
    ] = False,
    local_registry_path: Annotated[
        Path | None,
        typer.Option(
            "--local-registry-path",
            help="Override path to the bundled example registry file.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate and display the plan without writing output.",
        ),
    ] = False,
    plan_output: Annotated[
        Path | None,
        typer.Option(
            "--plan-output",
            help="Write the install plan to a JSON file.",
        ),
    ] = None,
) -> None:
    """Install modules by generating an install plan."""
    effective_fallback: bool = allow_local_fallback or allow_local_registry_fallback()
    registry_index: RegistryIndex = load_registry_index(
        registry_url,
        allow_local_fallback=effective_fallback,
        local_registry_path=local_registry_path,
    )
    registry_entry: RegistryEntry | None = find_registry_entry(
        registry_index.entries,
        module_id,
    )
    if registry_entry is None:
        console.print(f"[red]Module not found:[/] {module_id}")
        raise typer.Exit(code=1)

    selected_manifest_url: str = manifest_url or registry_entry.manifest_url
    manifest_index: ManifestIndex = load_manifest_index(selected_manifest_url)
    plan: InstallPlan = build_install_plan(
        registry_entry,
        manifest_index,
        registry_index.version,
    )
    console.print(
        f"Planning install for [bold]{registry_entry.name}[/] "
        f"({registry_entry.id})",
    )
    console.print(render_manifest_table(manifest_index.entries))

    if dry_run:
        console.print("Dry run complete. No files were written.")
        return

    output_path: Path = plan_output or default_plan_path(registry_entry.id)
    write_install_plan(plan, output_path)
    logger.info("Wrote install plan to %s", output_path)
    console.print(f"Install plan written to {output_path}")
