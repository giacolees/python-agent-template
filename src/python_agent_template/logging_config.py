"""Centralized logging configuration for the python-agent-template pipeline."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger for the pipeline.

    Parameters
    ----------
    level : str, optional
        Logging level name (e.g. ``"DEBUG"``, ``"INFO"``, ``"WARNING"``),
        by default ``"INFO"``.

    Returns
    -------
    None
        This function configures logging as a side effect and returns
        nothing.

    Raises
    ------
    ValueError
        If `level` is not a recognized logging level name.
    """
    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        msg = f"Unknown logging level: {level!r}"
        raise ValueError(msg)

    logging.basicConfig(
        level=numeric_level,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
