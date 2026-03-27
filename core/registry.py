from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Iterable, List

from termcolor import colored

from .collector import CollectorModule
from .types import CATEGORY_PACKAGES, PREFIX_BY_CATEGORY, TargetType


class CollectorRegistry:
    """Discover and cache collector modules across all categories."""

    def __init__(self, categories: Iterable[TargetType] | None = None):
        _ensure_project_root_on_path()
        self._collectors: Dict[TargetType, List[CollectorModule]] = {}
        categories = list(categories) if categories else list(TargetType)
        collector_count = 0
        for category in categories:
            self._collectors[category] = self._discover_for_category(category)
            collector_count += len(self._collectors[category])
        print(colored(f"[+] Discovered {collector_count} collectors across {len(categories)} categories.", "green"))

    def _discover_for_category(self, category: TargetType) -> List[CollectorModule]:
        collectors: List[CollectorModule] = []
        package_name = CATEGORY_PACKAGES[category]
        prefix = PREFIX_BY_CATEGORY[category]

        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError:
            print(colored(f"[-] Could not import package '{package_name}' for category '{category.value}'.", "red"))
            return collectors

        package_path = Path(package.__file__).resolve().parent
        for _, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
            if is_pkg or not module_name.startswith(prefix):
                continue
            module = import_module_from_package(package_name, module_name)
            if module is None:
                continue
            try:
                collector = CollectorModule.from_module(module_name, category.value, module)
            except Exception as exc:
                print(colored(f"[-] Skipping {package_name}.{module_name}: {exc}", "yellow"))
                continue
            collectors.append(collector)

        collectors.sort(key=lambda c: c.name.lower())
        return collectors

    def categories(self) -> Iterable[TargetType]:
        return self._collectors.keys()

    def get_collectors(self, category: TargetType) -> List[CollectorModule]:
        return list(self._collectors.get(category, []))


def import_module_from_package(package: str, module_name: str):
    try:
        return importlib.import_module(f"{package}.{module_name}")
    except Exception as exc:
        print(colored(f"[-] Failed to import module {package}.{module_name}: {exc}", "red"))
        return None


def _ensure_project_root_on_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
