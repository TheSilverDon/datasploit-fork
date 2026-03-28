"""HTTP session factory with a sensible default timeout.

Usage in collector modules::

    from core.http import make_session
    session = make_session()
    response = session.get("https://example.com/api")

The default timeout (15 s) can be overridden per-call::

    session.get(url, timeout=30)

or globally via config.ini::

    [http]
    timeout = 20
"""

from __future__ import annotations

import requests

from .config import get_config_value

_DEFAULT_TIMEOUT = 15  # seconds


def _get_timeout() -> int:
    val = get_config_value("http_timeout")
    try:
        return int(val) if val else _DEFAULT_TIMEOUT
    except (ValueError, TypeError):
        return _DEFAULT_TIMEOUT


class _TimeoutSession(requests.Session):
    """A requests.Session that injects a default timeout on every request."""

    def __init__(self, timeout: int) -> None:
        super().__init__()
        self._default_timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self._default_timeout)
        return super().request(method, url, **kwargs)


def make_session(timeout: int | None = None) -> requests.Session:
    """Return a requests.Session with a default timeout applied to all calls.

    Args:
        timeout: Override the default timeout in seconds.  Reads
                 ``[http] timeout`` from config.ini when omitted.
    """
    return _TimeoutSession(timeout if timeout is not None else _get_timeout())
