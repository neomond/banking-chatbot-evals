"""Release gate policy. Isolated so the threshold is not buried in the runner."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatePolicy:
    max_critical_failures: int = 0
    min_pass_rate: float = 0.90

    def passed(self, critical_failures: int, pass_rate: float) -> bool:
        return critical_failures <= self.max_critical_failures and pass_rate >= self.min_pass_rate

    def as_dict(self, *, passed: bool) -> dict:
        return {
            "max_critical_failures": self.max_critical_failures,
            "min_pass_rate": self.min_pass_rate,
            "passed": passed,
        }


DEFAULT_GATE = GatePolicy()
