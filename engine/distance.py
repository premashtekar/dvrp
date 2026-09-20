# engine/distance.py
"""Distance utilities for the DVRP engine.
Provides Euclidean distance and a cached distance matrix per scenario.
The matrix is a 2‑D list indexed by point indices.
"""

from __future__ import annotations

import math
from typing import List, Tuple

Point = Tuple[float, float]

def euclidean(a: Point, b: Point) -> float:
    """Return Euclidean distance between two points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])

def build_matrix(points: List[Point]) -> List[List[float]]:
    """Build a full distance matrix for a list of points.
    The matrix is symmetric and diagonal = 0.
    """
    n = len(points)
    mat: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = euclidean(points[i], points[j])
            mat[i][j] = d
            mat[j][i] = d
    return mat
