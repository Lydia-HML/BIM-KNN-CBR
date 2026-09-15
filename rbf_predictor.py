from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

from models import Project


@dataclass
class RBFWeights:
    procurement: float = 1.0
    tender_value: float = 1.0
    floor: float = 1.0
    basement: float = 1.0
    floor_area: float = 1.0
    pre_duration: float = 1.0


def _distance(test: Project, train: Project, weights: RBFWeights) -> float:
    return (
        weights.procurement * abs(test.procurement_z - train.procurement_z)
        + weights.tender_value * abs(test.tender_value_z - train.tender_value_z)
        + weights.floor * abs(test.floor_z - train.floor_z)
        + weights.basement * abs(test.basement_z - train.basement_z)
        + weights.floor_area * abs(test.floor_area_z - train.floor_area_z)
        + weights.pre_duration * abs(test.pre_duration_z - train.pre_duration_z)
    )


def rbf_predict(
    test: Project,
    training: List[Project],
    y_getter: Callable[[Project], float],
    *,
    rad: float = 1.0,
    weights: RBFWeights | None = None,
) -> Tuple[float, List[Tuple[int, float]]]:
    """Predict an outcome using normalized RBF similarities."""
    if not training:
        return 0.0, []
    if not math.isfinite(rad) or rad <= 0:
        raise ValueError("rad must be a positive finite number")

    active_weights = weights or RBFWeights()
    weighted_cases: List[Tuple[int, float, float]] = []
    for project in training:
        distance = _distance(test, project, active_weights)
        similarity = math.exp(-rad * distance)
        weighted_cases.append((int(project.id), similarity, float(y_getter(project))))

    denominator = sum(similarity for _, similarity, _ in weighted_cases)
    if denominator == 0:
        return 0.0, [(project_id, 0.0) for project_id, _, _ in weighted_cases]

    prediction = sum(similarity * outcome for _, similarity, outcome in weighted_cases) / denominator
    normalized = [(project_id, similarity / denominator) for project_id, similarity, _ in weighted_cases]
    normalized.sort(key=lambda item: item[1], reverse=True)
    return prediction, normalized
