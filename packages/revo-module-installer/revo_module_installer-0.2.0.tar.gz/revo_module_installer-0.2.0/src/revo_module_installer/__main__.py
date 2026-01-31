"""Module entrypoint."""

from __future__ import annotations

from revo_module_installer.cli import app


def main() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    main()
