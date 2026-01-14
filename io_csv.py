from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from models import Project


CSV_COLUMNS = [
    "id",
    "name",
    "procurement_raw",
    "tender_value_raw",
    "floor_raw",
    "basement_raw",
    "floor_area_raw",
    "pre_duration_raw",
    "duration_actual",
    "settlement_raw",
]


def save_projects_csv(path: str | Path, projects: List[Project]) -> None:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for p in projects:
            w.writerow({k: getattr(p, k) for k in CSV_COLUMNS})



def load_projects_csv(path: str | Path) -> List[Project]:
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        projects: List[Project] = []
        for i, row in enumerate(r, start=1):  # 使用 enumerate 產生自動編號
        #for row in r:
            # tolerate missing columns
            def g(key: str, default="0"):
                v = row.get(key, default)
                return v if v is not None and v != "" else default

            # 先嘗試讀取 CSV 裡的 id，若讀不到或為 0，則使用自動編號 i
            csv_id = int(float(g("id", "0")))
            final_id = csv_id if csv_id != 0 else i

            projects.append(Project(
                id=final_id,
                name=str(row.get("name", "") or ""),
                procurement_raw=float(g("procurement_raw", "0")),
                tender_value_raw=float(g("tender_value_raw", "0")),
                floor_raw=float(g("floor_raw", "0")),
                basement_raw=float(g("basement_raw", "0")),
                floor_area_raw=float(g("floor_area_raw", "0")),
                pre_duration_raw=float(g("pre_duration_raw", "0")),
                duration_actual=float(g("duration_actual", "0")),
                settlement_raw=float(g("settlement_raw", "0")),
            ))
        return projects
