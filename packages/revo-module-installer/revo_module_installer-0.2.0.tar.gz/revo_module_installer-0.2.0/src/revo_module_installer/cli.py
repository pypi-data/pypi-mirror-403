"""Command line interface for Revo modules."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Annotated, TypedDict

from platformdirs import user_cache_path
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.table import Table
import typer

from revo_module_installer.config.load import (
    get_local_example_registry_path,
    load_manifest_index,
    load_registry_index,
)
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


@app.callback(invoke_without_command=True)
def main(
    context: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Revo modules CLI entrypoint.

    Args:
        context: Typer context for the current command.
        verbose: Enable debug logging.
    """
    main_callback(verbose)
    if context.invoked_subcommand is not None:
        return
    run_default_module_install()


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


def build_search_table(registry_entries: list[RegistryEntry]) -> Table:
    """Build a search-focused table for registry entries.

    Args:
        registry_entries: Entries from the registry index.

    Returns:
        Rich table representation for searching entries.
    """
    table: Table = Table(title="Available modules")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    for registry_entry in registry_entries:
        table.add_row(registry_entry.name, registry_entry.description)
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


def find_registry_entry_by_name(
    registry_entries: list[RegistryEntry],
    module_name: str,
) -> RegistryEntry | None:
    """Find a registry entry by name.

    Args:
        registry_entries: Entries from the registry index.
        module_name: Module name to search for.

    Returns:
        Matching registry entry or None.
    """
    normalized_name: str = module_name.casefold()
    for registry_entry in registry_entries:
        if registry_entry.name.casefold() == normalized_name:
            return registry_entry
    return None


def filter_registry_entries(
    registry_entries: list[RegistryEntry],
    search_query: str,
) -> list[RegistryEntry]:
    """Filter registry entries by name or description.

    Args:
        registry_entries: Entries from the registry index.
        search_query: Search text to match.

    Returns:
        Filtered list of registry entries.
    """
    trimmed_query: str = search_query.strip()
    if not trimmed_query:
        return registry_entries
    normalized_query: str = trimmed_query.casefold()
    return [
        registry_entry
        for registry_entry in registry_entries
        if normalized_query in registry_entry.name.casefold()
        or normalized_query in registry_entry.description.casefold()
    ]


def format_search_results(
    registry_entries: list[RegistryEntry],
    *,
    max_results: int = 10,
) -> str:
    """Format registry entries for interactive search display.

    Args:
        registry_entries: Entries from the registry index.
        max_results: Maximum number of entries to display.

    Returns:
        Formatted search results.
    """
    if not registry_entries:
        return "No matches yet."

    limited_entries: list[RegistryEntry] = registry_entries[:max_results]
    lines: list[str] = [
        f"{registry_entry.name} — {registry_entry.description}"
        for registry_entry in limited_entries
    ]
    remaining_count: int = len(registry_entries) - len(limited_entries)
    if remaining_count > 0:
        lines.append(f"... and {remaining_count} more")
    return "\n".join(lines)


def prompt_for_search_query(
    registry_entries: list[RegistryEntry],
) -> str:
    """Prompt for a module search query with live-updating results.

    Args:
        registry_entries: Entries from the registry index.

    Returns:
        Search query string.
    """
    prompt_session: PromptSession[str] = PromptSession()

    def bottom_toolbar() -> str:
        """Render live search results in the prompt toolbar."""
        search_text: str = prompt_session.default_buffer.text
        matched_entries: list[RegistryEntry] = filter_registry_entries(
            registry_entries,
            search_text,
        )
        return format_search_results(matched_entries)

    return prompt_session.prompt(
        "Search modules by name or description (press Enter to show all): ",
        bottom_toolbar=bottom_toolbar,
    )


def confirm_module_installation(registry_entry: RegistryEntry) -> bool:
    """Confirm installation for a single registry entry.

    Args:
        registry_entry: Registry metadata for the module.

    Returns:
        True when the user confirms the install.
    """
    return typer.confirm(
        f"Install {registry_entry.name} ({registry_entry.id})?",
        default=True,
    )


def prompt_for_module_name() -> str:
    """Prompt for a module name to install.

    Returns:
        Module name provided by the user.
    """
    return typer.prompt("Module name to install")


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


def resolve_manifest_index(
    registry_entry: RegistryEntry,
    manifest_url_override: str | None,
) -> ManifestIndex:
    """Resolve the manifest index for a registry entry.

    Args:
        registry_entry: Registry metadata for the module.
        manifest_url_override: Optional manifest URL override.

    Returns:
        Parsed manifest index.
    """
    selected_manifest_url: str = (
        manifest_url_override or registry_entry.manifest_url
    )
    return load_manifest_index(selected_manifest_url)


def execute_install_plan(
    registry_entry: RegistryEntry,
    registry_index: RegistryIndex,
    manifest_index: ManifestIndex,
    *,
    dry_run: bool,
    plan_output: Path | None,
) -> None:
    """Render and optionally write the install plan.

    Args:
        registry_entry: Registry metadata for the module.
        registry_index: Parsed registry data.
        manifest_index: Parsed manifest data.
        dry_run: Whether to skip writing output.
        plan_output: Optional path to write the plan.
    """
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


def run_default_module_install() -> None:
    """Prompt for a module name and install it."""
    registry_index: RegistryIndex = load_registry_index(
        REGISTRY_REPOSITORY_URL,
        allow_local_fallback=allow_local_registry_fallback(),
        local_registry_path=None,
    )
    console.print(build_search_table(registry_index.entries))
    search_query: str = prompt_for_search_query(registry_index.entries)
    matched_entries: list[RegistryEntry] = filter_registry_entries(
        registry_index.entries,
        search_query,
    )
    if not matched_entries:
        console.print("[red]No modules matched that search.[/]")
        raise typer.Exit(code=1)

    registry_entry: RegistryEntry | None = None
    if len(matched_entries) == 1:
        registry_entry = matched_entries[0]
        if not confirm_module_installation(registry_entry):
            console.print("Cancelled install.")
            raise typer.Exit(code=0)
    else:
        console.print(build_search_table(matched_entries))
        module_name: str = prompt_for_module_name()
        registry_entry = find_registry_entry_by_name(
            matched_entries,
            module_name,
        )
        if registry_entry is None:
            console.print(f"[red]Module not found:[/] {module_name}")
            raise typer.Exit(code=1)

    manifest_index: ManifestIndex = resolve_manifest_index(
        registry_entry,
        manifest_url_override=None,
    )
    execute_install_plan(
        registry_entry,
        registry_index,
        manifest_index,
        dry_run=False,
        plan_output=None,
    )


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
        local_example_registry_path: Path = get_local_example_registry_path()
        local_registry_index: RegistryIndex = load_registry_index(
            str(local_example_registry_path),
        )
        local_registry_entry: RegistryEntry | None = find_registry_entry(
            local_registry_index.entries,
            module_id,
        )
        if local_registry_entry is None:
            console.print(f"[red]Module not found:[/] {module_id}")
            raise typer.Exit(code=1)
        console.print(
            "[yellow]Module not found in remote registry; "
            "using the bundled example registry.[/]",
        )
        registry_entry = local_registry_entry
        registry_index = local_registry_index

    manifest_index: ManifestIndex = resolve_manifest_index(
        registry_entry,
        manifest_url_override=manifest_url,
    )
    execute_install_plan(
        registry_entry,
        registry_index,
        manifest_index,
        dry_run=dry_run,
        plan_output=plan_output,
    )
