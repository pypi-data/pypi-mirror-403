"""Logging configuration."""

from __future__ import annotations

import logging

from rich.logging import RichHandler


def setup_logging(verbose: bool) -> None:
    """Configure logging for the CLI.

    Args:
        verbose: Whether to enable debug logging.
    """
    log_level: int = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
