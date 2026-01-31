# Revo Modules

Revo Modules is a CLI for discovering and installing module bundles from a
registry.

## Setup

Install the CLI with uv (recommended) or pip.

```bash
uv tool install revo-module-installer
```

```bash
pip install revo-module-installer
```

## Usage

```bash
revo --help
```

Search and install a module interactively (the default command lists module
names and descriptions, then installs the selected entry).

```bash
revo
```

List modules from the default registry repository.

```bash
revo modules list --show-description
```

Generate an install plan for a specific module ID.

```bash
revo modules install example-module
```

Write the plan to a specific path and skip writing files.

```bash
revo modules install example-module --plan-output ./plan.json --dry-run
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

## Contributing

For contributor-focused guidelines, setup and development workflows,
see [CONTRIBUTING.md](CONTRIBUTING.md).
