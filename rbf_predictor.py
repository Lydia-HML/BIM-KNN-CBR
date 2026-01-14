from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

import pandas as pd
from models import Project, Case


def load_cases_from_csv(file_path):
    # 讀取 CSV
    df = pd.read_csv(file_path)
    cases = []

    # Debug 修正：遍歷時提取 index 作為 Case ID
    for index, row in df.iterrows():
        # 假設第一欄位是 Outcome (y)，其餘是 Features (x)
        outcome = row.iloc[0]
        features = row.iloc[1:].values

        # 更正：不再傳入固定的 0，而是傳入 index 或指定的 ID 欄位
        new_case = Case(case_id=index, features=features, outcome=outcome)
        cases.append(new_case)

    return cases


@dataclass
class RBFWeights:
    """
    Feature weights used in the distance computation.

    In the original C# project these weights were decision variables solved by Solver Foundation.
    Here we provide a practical, runnable default (all 1.0) and let you tune them.

    You can later add an optimizer to learn them from data.
    """
    procurement: float = 1.0
    tender_value: float = 1.0
    floor: float = 1.0
    basement: float = 1.0
    floor_area: float = 1.0
    pre_duration: float = 1.0


def _distance(test: Project, train: Project, w: RBFWeights) -> float:
    """
    Weighted L1 distance in z-score space (stable & simple).
    """
    return (
        w.procurement * abs(test.procurement_z - train.procurement_z) +
        w.tender_value * abs(test.tender_value_z - train.tender_value_z) +
        w.floor * abs(test.floor_z - train.floor_z) +
        w.basement * abs(test.basement_z - train.basement_z) +
        w.floor_area * abs(test.floor_area_z - train.floor_area_z) +
        w.pre_duration * abs(test.pre_duration_z - train.pre_duration_z)
    )


def rbf_predict(
    test: Project,
    training: List[Project],
    y_getter: Callable[[Project], float],
    *,
    rad: float = 1.0,
    weights: RBFWeights | None = None
) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Predict y for a test case using an RBF-like similarity weighting:

        sim_j = exp(-rad * distance(test, train_j))
        y_hat = sum(sim_j * y_j) / sum(sim_j)

    Returns:
      - y_hat
      - [(train_id, normalized_weight), ...] for transparency/debugging
    """
    if not training:
        return 0.0, []

    w = weights or RBFWeights()

    sims: List[float] = []
    ys: List[float] = []
    ids: List[int] = []

    for tr in training:
        d = _distance(test, tr, w)
        sim = math.exp(-rad * d)
        sims.append(sim)
        ys.append(float(y_getter(tr)))
        ids.append(int(tr.id))

    denom = sum(sims)
    if denom == 0:
        return 0.0, [(ids[i], 0.0) for i in range(len(ids))]

    y_hat = sum(sims[i] * ys[i] for i in range(len(ys))) / denom
    weights_norm = [(ids[i], sims[i] / denom) for i in range(len(ids))]
    weights_norm.sort(key=lambda t: t[1], reverse=True)
    return y_hat, weights_norm


import numpy as np


class RBFPredictor:
    def __init__(self, training_cases, weights, radius):
        self.training_cases = training_cases
        self.weights = np.array(weights)
        self.radius = radius
        # 建立特徵矩陣供向量化運算
        self.train_matrix = np.array([c.features for c in training_cases])

    def predict(self, target_features, k=10):
        # 1. 計算加權距離 (L1 Distance)
        diff = np.abs(self.train_matrix - target_features)
        dist = np.dot(diff, self.weights)

        # 2. 計算相似度 (RBF Kernel)
        similarities = np.exp(-dist / self.radius)

        # 3. 預測輸出值 (Nadaraya-Watson)
        prediction = np.dot(similarities, [c.outcome for c in self.training_cases]) / np.sum(similarities)

        # 4. 提取 Top K 最相似案例
        # 取得相似度由高到低的索引
        top_indices = np.argsort(similarities)[::-1][:k]

        top_cases_results = []
        for idx in top_indices:
            # 更正：透過索引找到原始 Case 物件並提取其真實 ID
            original_case = self.training_cases[idx]
            top_cases_results.append({
                "id": original_case.id,  # 這裡現在會顯示正確的編號
                "similarity": float(similarities[idx]),
                "outcome": float(original_case.outcome)
            })

        return prediction, top_cases_results