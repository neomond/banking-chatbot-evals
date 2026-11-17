"""Small statistics helpers: judge-vs-human agreement and confidence intervals."""
from __future__ import annotations

import math
from collections import Counter


def cohen_kappa(a: list, b: list) -> float:
    """Unweighted Cohen's kappa between two raters (e.g. human vs LLM judge)."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    n = len(a)
    p_o = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if p_e == 1 else (p_o - p_e) / (1 - p_e)


def wilson_interval(passed: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% CI for a pass rate. With ~60 cases, a few points of change can be noise; say so in reports."""
    if total == 0:
        return (0.0, 0.0)
    p = passed / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
