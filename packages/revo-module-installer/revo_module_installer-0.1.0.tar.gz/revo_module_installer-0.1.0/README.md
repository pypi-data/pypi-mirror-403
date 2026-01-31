# Revo Modules

Revo Modules is a Python CLI for listing and installing module bundles from a
registry. It is built with Typer and uses Pydantic models for configuration.

## Requirements

- Python 3.12+
- uv

## Setup

```bash
uv sync
```

## Usage

```bash
uv run revo --help
```

List modules from the default registry repository.

```bash
uv run revo modules list
```

Show module descriptions in the output.

```bash
uv run revo modules list --show-description
```

Generate an install plan for a specific module.

```bash
uv run revo modules install example-module
```

Write the plan to a specific path and skip writing files.

```bash
uv run revo modules install example-module --plan-output ./plan.json --dry-run
```

By default the install plan is written under the user cache directory in
`revo-modules/plans/<module_id>.json`. Use `--plan-output` to override the path
or `--dry-run` to avoid writing the plan.

## Registry sources

Registry URLs can point to:

- GitHub repositories, which are resolved to raw registry files.
- Direct HTTP(S) URLs to registry YAML files.
- Local files via `file://` URLs or file paths.
- Bundled package examples via `package://example_registry.yml`.

Manifest URLs support the same URL forms. GitHub blob URLs are automatically
converted to raw content URLs.

### Local registry fallback for tests

For testing purposes, you can allow a fallback to the bundled example registry by
setting the following environment variables:

```bash
export REVO_MODULES_ENV=test
export REVO_MODULES_ALLOW_LOCAL_REGISTRY_FALLBACK=1
```

The bundled registry entry points to `package://example_manifest.yml`, so the
example manifest stays self-contained for offline testing.

## Demo repository

The `demo_repo/` folder is a fictional project that we use to manually validate
module installs. It includes a `.just/justfile` with a known anchor for the
example manifest. Run the CLI against it with the local registry fallback:

```bash
cd demo_repo
REVO_MODULES_ENV=test REVO_MODULES_ALLOW_LOCAL_REGISTRY_FALLBACK=1 \
  uv run revo modules install example-module
```

## Testing

```bash
uv run pytest
```

## Development

Format and lint with Ruff.

```bash
uv run ruff format .
uv run ruff check .
```

Type check with Pyright.

```bash
uv run pyright
```

Run pre-commit checks.

```bash
just precommit
```
