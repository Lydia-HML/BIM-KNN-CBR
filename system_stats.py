from __future__ import annotations

import math
from typing import Iterable, List

from models import Project


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _sample_sd(xs: List[float]) -> float:
    """Sample standard deviation (denominator n-1)."""
    n = len(xs)
    if n <= 1:
        return 0.0
    mu = _mean(xs)
    ss = sum((x - mu) ** 2 for x in xs)
    return math.sqrt(ss / (n - 1))


class MySystem:
    """
    A corrected Python port of CMysystem.cs.

    C# version had a bug: it used (count - avg)^2 repeatedly instead of (x_i - avg)^2.
    This class uses the correct definition.
    """

    def __init__(self) -> None:
        self.projects: List[Project] = []

    def attach(self) -> None:
        """Attach self reference to projects so z-score properties can be computed."""
        for p in self.projects:
            p.system = self

    # ---- Averages ----
    @property
    def avg_procurement(self) -> float:
        return _mean([p.procurement_raw for p in self.projects])

    @property
    def avg_tender_value(self) -> float:
        return _mean([p.tender_value_raw for p in self.projects])

    @property
    def avg_floor(self) -> float:
        return _mean([p.floor_raw for p in self.projects])

    @property
    def avg_basement(self) -> float:
        return _mean([p.basement_raw for p in self.projects])

    @property
    def avg_floor_area(self) -> float:
        return _mean([p.floor_area_raw for p in self.projects])

    @property
    def avg_pre_duration(self) -> float:
        return _mean([p.pre_duration_raw for p in self.projects])

    # ---- Standard Deviations ----
    @property
    def sd_procurement(self) -> float:
        return _sample_sd([p.procurement_raw for p in self.projects])

    @property
    def sd_tender_value(self) -> float:
        return _sample_sd([p.tender_value_raw for p in self.projects])

    @property
    def sd_floor(self) -> float:
        return _sample_sd([p.floor_raw for p in self.projects])

    @property
    def sd_basement(self) -> float:
        return _sample_sd([p.basement_raw for p in self.projects])

    @property
    def sd_floor_area(self) -> float:
        return _sample_sd([p.floor_area_raw for p in self.projects])

    @property
    def sd_pre_duration(self) -> float:
        return _sample_sd([p.pre_duration_raw for p in self.projects])
