from __future__ import annotations

"""
train_weights.py
================

Learn feature weights for the RBF-style predictor in this project.

Why this exists
---------------
Your original C# project used Microsoft Solver Foundation to solve/learn weights.
This script replaces that idea with a lightweight, reproducible search that works on Python 3.12.

What it does
------------
- Loads projects from the bundled XLS dataset (or a user-provided CSV/XLS file).
- Computes system stats (means/standard deviations) and attaches them so z-scores work.
- Searches for positive weights that minimize prediction error via cross-validation.

Model
-----
distance(test, train) = sum_k w_k * |z_k(test) - z_k(train)|
sim = exp(-rad * distance)
y_hat = sum(sim * y) / sum(sim)

Objective (default)
-------------------
MAE (mean absolute error) using Leave-One-Out CV.

Usage
-----
python train_weights.py --target duration --iters 6000 --seed 42
python train_weights.py --target settlement --data my_cases.csv --rad 0.8 --iters 8000

Outputs
-------
- Prints best weights
- Writes weights.json into the project folder
"""

import argparse
import json
import math
import random
from dataclasses import asdict

from io_csv import load_projects
from models import Project
from rbf_predictor import RBFWeights, rbf_predict
from system_stats import MySystem


def mae(errors: list[float]) -> float:
    return sum(abs(e) for e in errors) / len(errors) if errors else 0.0


def rmse(errors: list[float]) -> float:
    if not errors:
        return 0.0
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def score_weights(
    projects: list[Project],
    *,
    target: str,
    rad: float,
    weights: RBFWeights,
    metric: str = "mae",
    max_train: int | None = None,
) -> float:
    """
    Leave-One-Out CV:
      for each i:
        test = projects[i]
        training = projects except i
        predict y_hat
        error = y_hat - y_true
    """
    errors: list[float] = []
    n = len(projects)
    if n < 3:
        return float("inf")

    for i in range(n):
        test = projects[i]
        training = projects[:i] + projects[i + 1 :]

        # Optional subsample to speed up when dataset is large
        if max_train is not None and len(training) > max_train:
            training = random.sample(training, k=max_train)

        if target == "duration":
            y_true = float(test.duration_actual)
            y_hat, _ = rbf_predict(test, training, lambda p: p.duration_actual, rad=rad, weights=weights)
        elif target == "settlement":
            y_true = float(test.settlement_raw)
            y_hat, _ = rbf_predict(test, training, lambda p: p.settlement_raw, rad=rad, weights=weights)
        else:
            raise ValueError("target must be 'duration' or 'settlement'")

        # ignore rows with missing/zero targets? keep them by default for faithful port
        errors.append(y_hat - y_true)

    if metric == "mae":
        return mae(errors)
    if metric == "rmse":
        return rmse(errors)
    raise ValueError("metric must be 'mae' or 'rmse'")


def propose(current: list[float], step: float) -> list[float]:
    """
    Propose new positive weights by multiplicative log-normal jitter.
    This keeps weights > 0 and searches smoothly.
    """
    out: list[float] = []
    for w in current:
        # jitter in log-space
        factor = math.exp(random.uniform(-step, step))
        out.append(max(1e-6, w * factor))
    return normalize(out)


def to_weights(vec: list[float]) -> RBFWeights:
    return RBFWeights(
        procurement=vec[0],
        tender_value=vec[1],
        floor=vec[2],
        basement=vec[3],
        floor_area=vec[4],
        pre_duration=vec[5],
    )


def normalize(vec: list[float]) -> list[float]:
    """
    Optional: normalize weights so their mean = 1.0 for readability.
    """
    m = sum(vec) / len(vec)
    if m == 0:
        return vec
    return [v / m for v in vec]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset/完整案例庫_新增BIM標註.xls", help="Training CSV or XLS file")
    ap.add_argument("--target", choices=["duration", "settlement"], default="duration")
    ap.add_argument("--metric", choices=["mae", "rmse"], default="mae")
    ap.add_argument("--rad", type=float, default=1.0, help="RBF rad parameter (default: 1.0)")
    ap.add_argument("--iters", type=int, default=6000, help="Search iterations (default: 6000)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--step0", type=float, default=0.35, help="Initial log-step (default: 0.35)")
    ap.add_argument("--cool", type=float, default=0.9995, help="Cooling rate per iter (default: 0.9995)")
    ap.add_argument("--max-train", type=int, default=120, help="Subsample training cases per fold for speed (default: 120)")
    args = ap.parse_args()

    base_dir = __import__('pathlib').Path(__file__).parent
    random.seed(args.seed)

    # Load data
    system = MySystem()
    data_path = __import__('pathlib').Path(args.data)
    if not data_path.is_absolute():
        data_path = base_dir / data_path
    system.projects = load_projects(data_path)
    system.attach()

    # Ensure test projects can compute z-scores
    projects = system.projects

    # Start from all-ones weights
    cur_vec = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    cur_w = to_weights(cur_vec)

    best_vec = cur_vec[:]
    best_w = cur_w
    best_score = score_weights(
        projects,
        target=args.target,
        rad=args.rad,
        weights=best_w,
        metric=args.metric,
        max_train=args.max_train,
    )

    step = float(args.step0)

    # Simple annealed random search
    # Accept if better; occasionally accept slightly worse early on (simulated annealing-ish).
    cur_score = best_score

    for t in range(1, args.iters + 1):
        step *= args.cool
        cand_vec = propose(cur_vec, step=step)
        cand_w = to_weights(cand_vec)

        cand_score = score_weights(
            projects,
            target=args.target,
            rad=args.rad,
            weights=cand_w,
            metric=args.metric,
            max_train=args.max_train,
        )

        improved = cand_score < cur_score
        if improved:
            cur_vec, cur_w, cur_score = cand_vec, cand_w, cand_score
        else:
            # probabilistic acceptance
            # temperature shrinks with step, so this fades out naturally
            temp = max(1e-6, step)
            prob = math.exp(-(cand_score - cur_score) / temp)
            if random.random() < prob:
                cur_vec, cur_w, cur_score = cand_vec, cand_w, cand_score

        if cur_score < best_score:
            best_score = cur_score
            best_vec = cur_vec[:]
            best_w = cur_w

        if t % max(200, args.iters // 20) == 0:
            print(f"[{t:>6}/{args.iters}] best_{args.metric}={best_score:.6f}  step={step:.4f}")

    print("\n=== BEST WEIGHTS ===")
    print(f"target={args.target}  metric={args.metric}  rad={args.rad}")
    print(json.dumps(asdict(best_w), ensure_ascii=False, indent=2))
    print(f"{args.metric} (LOO-CV) = {best_score:.6f}")

    out_path = base_dir / "weights.json"
    out = {"version": 1, "models": {}}
    if out_path.exists():
        with out_path.open(encoding="utf-8") as f:
            existing = json.load(f)
        if isinstance(existing.get("models"), dict):
            out = existing
    out["models"][args.target] = {
        "metric": args.metric,
        "rad": args.rad,
        "seed": args.seed,
        "iters": args.iters,
        "best_score": best_score,
        "weights": asdict(best_w),
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
