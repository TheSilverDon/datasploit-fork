"""Structured result types for collector module execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultStatus(Enum):
    SUCCESS   = "success"    # main() returned non-empty data
    NO_RESULT = "no_result"  # main() returned empty/None but no error
    SKIPPED   = "skipped"    # collector disabled or missing prerequisites
    API_ERROR = "api_error"  # API key absent or API rejected the request
    ERROR     = "error"      # unhandled exception during execution


@dataclass
class ModuleResult:
    module_key:  str
    module_name: str
    category:    str
    target:      str
    status:      ResultStatus
    data:        Any   = field(default=None)
    error_msg:   str   = field(default="")
    duration_s:  float = field(default=0.0)
