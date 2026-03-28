from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Optional

from termcolor import colored

from .collector import CollectorModule
from .config import load_config, get_config_value
from .registry import CollectorRegistry
from .result import ModuleResult, ResultStatus
from .types import TargetType

logger = logging.getLogger(__name__)

_DEFAULT_MAX_WORKERS = 10
_DEFAULT_MODULE_TIMEOUT = 30  # seconds


def _runner_config() -> tuple[int, int]:
    """Return (max_workers, module_timeout) from config, with defaults."""
    try:
        workers = int(get_config_value("runner_max_workers") or _DEFAULT_MAX_WORKERS)
    except (ValueError, TypeError):
        workers = _DEFAULT_MAX_WORKERS
    try:
        timeout = int(get_config_value("runner_module_timeout") or _DEFAULT_MODULE_TIMEOUT)
    except (ValueError, TypeError):
        timeout = _DEFAULT_MODULE_TIMEOUT
    return workers, timeout


class CollectorRunner:
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._config = load_config()

    def run(
        self,
        category: TargetType,
        target: str,
        output: Optional[str] = None,
    ) -> dict[str, ModuleResult]:
        """Execute all eligible collectors for *category* concurrently.

        Returns a mapping of ``module_key → ModuleResult`` for every
        collector that was run (skipped collectors are included with
        ``ResultStatus.SKIPPED``).
        """
        collectors = self.registry.get_collectors(category)
        if not collectors:
            logger.warning("No collectors found for %s targets.", category.value)
            print(colored(f"[-] No collectors found for {category.value} targets.", "yellow"))
            return {}

        # Partition: eligible vs. skipped
        eligible: list[CollectorModule] = []
        skipped_results: dict[str, ModuleResult] = {}

        for collector in collectors:
            if not collector.enabled:
                logger.debug("Skipping %s (disabled).", collector.name)
                print(colored(f"[-] Skipping {collector.name} (disabled).", "yellow"))
                skipped_results[collector.key] = ModuleResult(
                    module_key=collector.key, module_name=collector.name,
                    category=collector.category, target=target,
                    status=ResultStatus.SKIPPED, error_msg="disabled",
                )
                continue

            missing = collector.missing_prerequisites()
            if missing:
                missing_list = ", ".join(missing)
                logger.debug("Skipping %s: missing config keys [%s].", collector.name, missing_list)
                print(colored(f"[-] Skipping {collector.name}: missing config keys [{missing_list}].", "yellow"))
                skipped_results[collector.key] = ModuleResult(
                    module_key=collector.key, module_name=collector.name,
                    category=collector.category, target=target,
                    status=ResultStatus.SKIPPED,
                    error_msg=f"missing keys: {missing_list}",
                )
                continue

            eligible.append(collector)

        if not eligible:
            logger.warning("All collectors for %s were skipped.", category.value)
            print(colored(f"[-] All collectors for {category.value} were skipped.", "yellow"))
            return skipped_results

        max_workers, module_timeout = _runner_config()
        print(colored(
            f"[+] Running {len(eligible)} collectors for {category.value} target '{target}' "
            f"(workers={max_workers}, timeout={module_timeout}s).",
            "green",
        ))

        results: dict[str, ModuleResult] = dict(skipped_results)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_collector = {
                pool.submit(self._run_collector, c, target): c
                for c in eligible
            }
            completed = 0
            total = len(eligible)
            for future in as_completed(future_to_collector, timeout=None):
                collector = future_to_collector[future]
                completed += 1
                try:
                    result = future.result(timeout=module_timeout)
                except FutureTimeoutError:
                    logger.warning("Collector %s timed out after %ds.", collector.name, module_timeout)
                    print(colored(f"[-] {collector.name} timed out.", "red"))
                    result = ModuleResult(
                        module_key=collector.key, module_name=collector.name,
                        category=collector.category, target=target,
                        status=ResultStatus.ERROR,
                        error_msg=f"timed out after {module_timeout}s",
                        duration_s=float(module_timeout),
                    )
                except Exception as exc:
                    logger.warning("Collector %s raised an unexpected error: %s", collector.name, exc)
                    result = ModuleResult(
                        module_key=collector.key, module_name=collector.name,
                        category=collector.category, target=target,
                        status=ResultStatus.ERROR, error_msg=str(exc),
                    )

                results[collector.key] = result
                logger.debug(
                    "[%d/%d] %s → %s (%.2fs)",
                    completed, total, collector.name, result.status.value, result.duration_s,
                )

        return results

    def _run_collector(self, collector: CollectorModule, target: str) -> ModuleResult:
        collector.banner()
        return collector.run(target)


_runner: Optional[CollectorRunner] = None


def get_runner() -> CollectorRunner:
    global _runner
    if _runner is None:
        _runner = CollectorRunner()
    return _runner
