"""Report generation for DataSploit v2.0.

Consumes the ``dict[str, ModuleResult]`` returned by ``CollectorRunner.run()``
and writes structured output files.

Supported formats
-----------------
* ``json``  — machine-readable, single consolidated file
* ``html``  — human-readable single-page report with Bootstrap 5 styling
* ``text``  — per-module plain-text files (legacy, unchanged)
* ``all``   — all three formats above
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from termcolor import colored

from .result import ModuleResult, ResultStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_target(target: str) -> str:
    """Sanitise a target string for use in a filename."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in target)


def _serialize(obj: Any) -> Any:
    """Best-effort JSON serialisation for arbitrary module data."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_serialize(i) for i in obj]
    return str(obj)


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def write_json_report(
    results: dict[str, ModuleResult],
    target: str,
    output_dir: Path,
) -> Path:
    """Write a consolidated JSON report and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = _build_summary(results)
    payload = {
        "datasploit_version": "2.0",
        "target": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "modules": [
            {
                "key":        r.module_key,
                "name":       r.module_name,
                "category":   r.category,
                "status":     r.status.value,
                "duration_s": round(r.duration_s, 3),
                "data":       _serialize(r.data),
                "error":      r.error_msg,
            }
            for r in results.values()
        ],
    }

    path = output_dir / f"report_{_safe_target(target)}_{_timestamp()}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    logger.info("JSON report written to %s", path)
    print(colored(f"[+] JSON report → {path}", "green"))
    return path


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

_STATUS_BADGE = {
    ResultStatus.SUCCESS:   ("success",  "✓"),
    ResultStatus.NO_RESULT: ("warning",  "–"),
    ResultStatus.SKIPPED:   ("secondary","⊘"),
    ResultStatus.API_ERROR: ("warning",  "⚠"),
    ResultStatus.ERROR:     ("danger",   "✗"),
}

# Minimal Bootstrap 5 CDN-free inline stylesheet
_INLINE_CSS = """
body{font-family:system-ui,sans-serif;background:#f8f9fa;color:#212529}
.container{max-width:1100px;margin:auto;padding:2rem}
h1{font-size:1.6rem;font-weight:700;margin-bottom:.25rem}
.meta{color:#6c757d;font-size:.85rem;margin-bottom:1.5rem}
.stats{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem}
.stat-card{background:#fff;border:1px solid #dee2e6;border-radius:.5rem;
           padding:.75rem 1.25rem;min-width:120px;text-align:center}
.stat-card .num{font-size:1.75rem;font-weight:700}
.stat-card .lbl{font-size:.75rem;color:#6c757d;text-transform:uppercase}
.module-card{background:#fff;border:1px solid #dee2e6;border-radius:.5rem;
             margin-bottom:.75rem;overflow:hidden}
.module-header{display:flex;align-items:center;gap:.75rem;padding:.65rem 1rem;
               cursor:pointer;user-select:none}
.module-header:hover{background:#f1f3f5}
.badge{display:inline-block;padding:.2em .55em;border-radius:.3rem;
       font-size:.75rem;font-weight:600;color:#fff}
.bg-success{background:#198754}.bg-warning{background:#ffc107;color:#212529!important}
.bg-secondary{background:#6c757d}.bg-danger{background:#dc3545}
.module-name{font-weight:600;flex:1}
.duration{font-size:.8rem;color:#6c757d;margin-left:auto}
.module-body{display:none;padding:.75rem 1rem;border-top:1px solid #dee2e6}
.module-body.open{display:block}
pre{background:#f8f9fa;border:1px solid #dee2e6;border-radius:.35rem;
    padding:.75rem;font-size:.78rem;overflow-x:auto;white-space:pre-wrap;
    word-break:break-all;max-height:400px;overflow-y:auto}
.error-msg{color:#dc3545;font-size:.85rem}
"""

_INLINE_JS = """
document.querySelectorAll('.module-header').forEach(function(h){
  h.addEventListener('click',function(){
    var b=this.nextElementSibling;
    b.classList.toggle('open');
  });
});
"""


def write_html_report(
    results: dict[str, ModuleResult],
    target: str,
    output_dir: Path,
) -> Path:
    """Write a self-contained HTML report and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = _build_summary(results)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = [
        "<!DOCTYPE html><html lang='en'><head>",
        "<meta charset='UTF-8'>",
        f"<title>DataSploit Report — {target}</title>",
        f"<style>{_INLINE_CSS}</style>",
        "</head><body><div class='container'>",
        f"<h1>DataSploit Report</h1>",
        f"<div class='meta'>Target: <strong>{target}</strong> &nbsp;·&nbsp; {generated}</div>",
        "<div class='stats'>",
    ]

    stat_defs = [
        ("total",     summary["total"],     "#212529"),
        ("success",   summary["success"],   "#198754"),
        ("no_result", summary["no_result"], "#e67e00"),
        ("skipped",   summary["skipped"],   "#6c757d"),
        ("api_error", summary["api_error"], "#e67e00"),
        ("error",     summary["error"],     "#dc3545"),
    ]
    for key, val, color in stat_defs:
        lines.append(
            f"<div class='stat-card'>"
            f"<div class='num' style='color:{color}'>{val}</div>"
            f"<div class='lbl'>{key.replace('_',' ')}</div>"
            f"</div>"
        )
    lines.append("</div>")  # .stats

    for r in sorted(results.values(), key=lambda x: x.module_name.lower()):
        badge_cls, badge_icon = _STATUS_BADGE.get(r.status, ("secondary", "?"))
        body_parts: list[str] = []
        if r.error_msg:
            body_parts.append(f"<p class='error-msg'>{r.error_msg}</p>")
        if r.data:
            serialised = json.dumps(_serialize(r.data), indent=2, default=str)
            body_parts.append(f"<pre>{_html_escape(serialised)}</pre>")
        elif not r.error_msg:
            body_parts.append("<p style='color:#6c757d'>No data returned.</p>")

        lines += [
            "<div class='module-card'>",
            "<div class='module-header'>",
            f"<span class='badge bg-{badge_cls}'>{badge_icon} {r.status.value}</span>",
            f"<span class='module-name'>{r.module_name}</span>",
            f"<span class='duration'>{r.duration_s:.2f}s</span>",
            "</div>",
            "<div class='module-body'>",
            *body_parts,
            "</div>",
            "</div>",
        ]

    lines += [
        f"<script>{_INLINE_JS}</script>",
        "</div></body></html>",
    ]

    path = output_dir / f"report_{_safe_target(target)}_{_timestamp()}.html"
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("HTML report written to %s", path)
    print(colored(f"[+] HTML report → {path}", "green"))
    return path


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _build_summary(results: dict[str, ModuleResult]) -> dict[str, int]:
    counts: dict[str, int] = {s.value: 0 for s in ResultStatus}
    for r in results.values():
        counts[r.status.value] += 1
    counts["total"] = len(results)
    return counts


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def write_reports(
    results: dict[str, ModuleResult],
    target: str,
    output_format: str,
    output_dir: Path | None = None,
) -> None:
    """Write one or more report formats based on *output_format*.

    Args:
        results:       Aggregated results from ``CollectorRunner.run()``.
        target:        The OSINT target string (used in filenames).
        output_format: One of ``"json"``, ``"html"``, ``"text"``, ``"all"``.
        output_dir:    Directory to write reports into.  Defaults to
                       ``./reports/``.
    """
    fmt = (output_format or "").lower()
    if not fmt:
        return

    dest = output_dir or (Path.cwd() / "reports")

    if fmt in ("json", "all"):
        write_json_report(results, target, dest)
    if fmt in ("html", "all"):
        write_html_report(results, target, dest)
    if fmt in ("text", "all"):
        _write_text_reports(results, target, dest)


def _write_text_reports(
    results: dict[str, ModuleResult],
    target: str,
    output_dir: Path,
) -> None:
    """Write per-module text files for collectors that support it."""
    from .collector import CollectorModule  # local import to avoid circular at module level
    for r in results.values():
        if r.status != ResultStatus.SUCCESS or r.data is None:
            continue
        # The CollectorModule instance isn't stored in ModuleResult; re-obtain
        # it via the registry to call write_text_report().
        # We do a best-effort lookup — if the module can't be found we skip.
        try:
            from .registry import CollectorRegistry
            from .types import TargetType
            registry = CollectorRegistry.__new__(CollectorRegistry)
            # Directly import the module to call write_text_report
            import importlib
            from .types import CATEGORY_PACKAGES
            for cat, pkg in CATEGORY_PACKAGES.items():
                try:
                    mod = importlib.import_module(f"{pkg}.{r.module_key}")
                    cm = CollectorModule.from_module(r.module_key, r.category, mod)
                    cm.write_text_report(target, r.data, output_dir)
                    break
                except Exception:
                    continue
        except Exception as exc:
            logger.debug("Could not write text report for %s: %s", r.module_key, exc)
