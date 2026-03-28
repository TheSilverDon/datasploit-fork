"""Logging configuration for DataSploit.

Call ``configure_logging()`` once at startup (done by ``datasploit.py``).
All internal modules obtain a child logger via::

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import sys


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging for the datasploit namespace.

    Args:
        verbose: When True, sets level to DEBUG and includes the logger name
                 in the output.  When False (default), INFO level with a
                 compact format is used.
    """
    level = logging.DEBUG if verbose else logging.INFO

    fmt = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if verbose
        else "[%(levelname)s] %(message)s"
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger("datasploit")
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False
