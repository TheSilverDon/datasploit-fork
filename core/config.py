from __future__ import annotations

import os
from configobj import ConfigObj
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable


CONFIG_DIR = Path(__file__).resolve().parent.parent
CONFIG_CANDIDATES: Iterable[Path] = (
    CONFIG_DIR / "config.ini",
    CONFIG_DIR / "config.py",
)


@lru_cache(maxsize=1)
def load_config() -> Dict[str, str]:
    """Load the user configuration once and cache the result."""
    for config_path in CONFIG_CANDIDATES:
        if not config_path.exists():
            continue

        config = ConfigObj(str(config_path))
        # ConfigObj returns a ConfigObj instance with string keys and values.
        # Normalise to a simple dictionary to avoid leaking ConfigObj specific
        # behaviour into the rest of the code base.
        return {key: value for key, value in config.items()}

    return {}


def get_config_value(key: str) -> str | None:
    """Fetch a configuration value.

    Lookup order:
    1. Environment variable ``DATASPLOIT_<KEY>`` (upper-cased key)
    2. config.ini / config.py on disk

    This allows API keys to be injected via the environment in CI/CD pipelines
    and container deployments without modifying config files.

    Example::

        DATASPLOIT_SHODAN_API=mykey python datasploit.py -i 1.2.3.4
    """
    env_val = os.environ.get(f"DATASPLOIT_{key.upper()}")
    if env_val:
        return env_val
    return load_config().get(key)
