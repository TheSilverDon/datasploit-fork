from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from types import ModuleType

from termcolor import colored

from .config import get_config_value
from .result import ModuleResult, ResultStatus
from .style import style

logger = logging.getLogger(__name__)


@dataclass
class CollectorModule:
    key: str
    category: str
    module: ModuleType
    name: str
    enabled: bool
    requires: tuple[str, ...]
    description: str
    writes_text: bool

    @classmethod
    def from_module(cls, key: str, category: str, module: ModuleType) -> "CollectorModule":
        if not hasattr(module, "MODULE_NAME") or not hasattr(module, "REQUIRES"):
            raise AttributeError(
                f"Collector {module.__name__} must define MODULE_NAME and REQUIRES"
            )

        raw_name = getattr(module, "MODULE_NAME")
        requires_attr = getattr(module, "REQUIRES")

        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError(f"Collector {module.__name__} has invalid MODULE_NAME")
        if not isinstance(requires_attr, tuple):
            raise ValueError(f"Collector {module.__name__} REQUIRES must be a tuple")

        enabled = bool(getattr(module, "ENABLED", True))
        requires = requires_attr
        description = getattr(module, "DESCRIPTION", module.__doc__ or "")
        writes_text = bool(getattr(module, "WRITE_TEXT_FILE", False))
        name = raw_name.replace("_", " ") if isinstance(raw_name, str) else str(raw_name)
        return cls(
            key=key,
            category=category,
            module=module,
            name=name,
            enabled=enabled,
            requires=requires,
            description=description,
            writes_text=writes_text,
        )

    def missing_prerequisites(self) -> tuple[str, ...]:
        missing: list[str] = []
        for key in self.requires:
            value = get_config_value(key)
            if value is None or str(value).strip() == "":
                missing.append(key)
        return tuple(missing)

    def banner(self) -> None:
        banner_fn = getattr(self.module, "banner", None)
        if callable(banner_fn):
            print(colored(f'{style.BOLD}[>] {banner_fn()}{style.END}', 'blue'))

    def run(self, target: str) -> ModuleResult:
        main_fn = getattr(self.module, "main", None)
        output_fn = getattr(self.module, "output", None)
        if not callable(main_fn) or not callable(output_fn):
            logger.warning("Collector %s is missing main/output functions. Skipping.", self.name)
            return ModuleResult(
                module_key=self.key, module_name=self.name, category=self.category,
                target=target, status=ResultStatus.ERROR,
                error_msg="Missing main() or output() function",
            )

        start = time.monotonic()
        try:
            data = main_fn(target)
        except Exception as exc:
            duration = time.monotonic() - start
            logger.debug("Collector %s raised an exception: %s", self.name, exc, exc_info=True)
            return ModuleResult(
                module_key=self.key, module_name=self.name, category=self.category,
                target=target, status=ResultStatus.ERROR,
                error_msg=str(exc), duration_s=duration,
            )

        duration = time.monotonic() - start

        # Normalise legacy [False, "INVALID_API"] / [False, <msg>] sentinel
        if isinstance(data, list) and len(data) == 2 and data[0] is False:
            return ModuleResult(
                module_key=self.key, module_name=self.name, category=self.category,
                target=target, status=ResultStatus.API_ERROR,
                error_msg=str(data[1]), duration_s=duration,
            )

        status = ResultStatus.NO_RESULT if not data else ResultStatus.SUCCESS

        try:
            output_fn(data, target)
        except Exception as exc:
            logger.debug("Collector %s output() raised: %s", self.name, exc)

        return ModuleResult(
            module_key=self.key, module_name=self.name, category=self.category,
            target=target, status=status, data=data, duration_s=duration,
        )

    def write_text_report(self, target: str, data: object, output_dir: Path | None = None) -> None:
        if not self.writes_text:
            return

        output_text_fn = getattr(self.module, "output_text", None)
        if not callable(output_text_fn):
            return

        text_data = output_text_fn(data)
        if not text_data:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_name = self.name.replace(" ", "_")
        filename = f"text_report_{target}_{safe_name}_{timestamp}.txt"
        output_path = (output_dir or Path.cwd()) / filename
        output_path.write_text(text_data, encoding="utf-8")
        print(colored(f"[+] Text Report written to {output_path}", "green"))
