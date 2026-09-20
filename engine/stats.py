# engine/stats.py
"""Statistical utilities for DVRP experiment analysis.

Provides:
- mean, std, sem helpers
- Friedman test
- Paired Wilcoxon signed‑rank with Holm correction
- Bootstrap confidence intervals for the mean

All functions operate on plain ``list[float]`` inputs and return ``float``
or ``list[float]`` as appropriate.
"""

from __future__ import annotations

import math
import random
from typing import List, Tuple

import numpy as np
import scipy.stats as stats

# ---------------------------------------------------------------------
# Basic descriptive statistics
# ---------------------------------------------------------------------

def mean(data: List[float]) -> float:
    return float(np.mean(data))


def std(data: List[float], ddof: int = 1) -> float:
    return float(np.std(data, ddof=ddof))


def sem(data: List[float]) -> float:
    """Standard error of the mean."""
    if not data:
        return 0.0
    return std(data, ddof=1) / math.sqrt(len(data))

# ---------------------------------------------------------------------
# Friedman test (non‑parametric repeated measures ANOVA)
# ---------------------------------------------------------------------

def friedman(data: List[List[float]]) -> Tuple[float, float]:
    """Perform the Friedman test.

    ``data`` is a list of groups (strategies) each containing measurements for
    the same set of instances (e.g., runs). Returns ``(statistic, pvalue)``.
    """
    statistic, pvalue = stats.friedmanchisquare(*data)
    return float(statistic), float(pvalue)

# ---------------------------------------------------------------------
# Paired Wilcoxon signed‑rank with Holm correction for multiple comparisons
# ---------------------------------------------------------------------

def wilcoxon_pairwise(data: List[List[float]]) -> List[Tuple[int, int, float, float, bool]]:
    """Run pairwise Wilcoxon tests between each pair of strategies.

    Returns a list of tuples ``(i, j, statistic, pvalue, reject)`` where ``i``
    and ``j`` are strategy indices. Holm correction is applied across all
    comparisons.
    """
    n = len(data)
    raw = []
    for i in range(n):
        for j in range(i + 1, n):
            stat, p = stats.wilcoxon(data[i], data[j])
            raw.append((i, j, float(stat), float(p)))
    # Holm correction
    m = len(raw)
    sorted_raw = sorted(raw, key=lambda x: x[3])  # sort by pvalue
    adjusted = []
    for k, (i, j, stat, p) in enumerate(sorted_raw):
        alpha = 0.05
        threshold = alpha / (m - k)
        reject = p <= threshold
        adjusted.append((i, j, stat, p, reject))
    return adjusted

# ---------------------------------------------------------------------
# Bootstrap confidence interval for the mean
# ---------------------------------------------------------------------

def bootstrap_ci(data: List[float], confidence: float = 0.95, n_boot: int = 2000) -> Tuple[float, float]:
    """Return ``(lower, upper)`` confidence interval for the mean using bootstrapping.
    """
    if not data:
        return 0.0, 0.0
    rng = random.Random(0)
    means = []
    for _ in range(n_boot):
        sample = [rng.choice(data) for _ in data]
        means.append(np.mean(sample))
    lower = np.percentile(means, (1 - confidence) / 2 * 100)
    upper = np.percentile(means, (1 + confidence) / 2 * 100)
    return float(lower), float(upper)
