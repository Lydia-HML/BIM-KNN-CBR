from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Iterable, List

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

_CHINESE_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def save_projects_csv(path: str | Path, projects: Iterable[Project]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for project in projects:
            writer.writerow({key: getattr(project, key) for key in CSV_COLUMNS})


def _number(value: object, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        return default
    return float(str(value).replace(",", "").strip())


def load_projects_csv(path: str | Path) -> List[Project]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        rows = csv.DictReader(file)
        projects: List[Project] = []
        for index, row in enumerate(rows, start=1):
            csv_id = int(_number(row.get("id", 0)))
            projects.append(Project(
                id=csv_id or index,
                name=str(row.get("name", "") or ""),
                procurement_raw=_number(row.get("procurement_raw")),
                tender_value_raw=_number(row.get("tender_value_raw")),
                floor_raw=_number(row.get("floor_raw")),
                basement_raw=_number(row.get("basement_raw")),
                floor_area_raw=_number(row.get("floor_area_raw")),
                pre_duration_raw=_number(row.get("pre_duration_raw")),
                duration_actual=_number(row.get("duration_actual")),
                settlement_raw=_number(row.get("settlement_raw")),
            ))
    return projects


def _parse_chinese_number(value: str) -> float:
    if value.isdigit():
        return float(value)
    if value == "十":
        return 10.0
    if "十" in value:
        tens, ones = value.split("十", maxsplit=1)
        return float((_CHINESE_DIGITS.get(tens, 1) or 1) * 10 + _CHINESE_DIGITS.get(ones, 0))
    return float(_CHINESE_DIGITS.get(value, 0))


def _summary_number(summary: str, label: str) -> float:
    match = re.search(rf"{label}[ _-]*([0-9]+(?:\.[0-9]+)?|[一二三四五六七八九十]+)\s*(?:層|F)", summary)
    return _parse_chinese_number(match.group(1)) if match else 0.0


def _floor_area(summary: str) -> float:
    match = re.search(r"(?:總)?樓地板面積[約-]*\s*([0-9][0-9,]*(?:\.[0-9]+)?)", summary)
    return _number(match.group(1)) if match else 0.0


def _roc_date(value: object) -> date | None:
    try:
        digits = str(int(float(value))).zfill(7)
        return date(int(digits[:3]) + 1911, int(digits[3:5]), int(digits[5:7]))
    except (TypeError, ValueError):
        return None


def _days_between(start: object, end: object) -> float:
    start_date, end_date = _roc_date(start), _roc_date(end)
    return float((end_date - start_date).days) if start_date and end_date and end_date >= start_date else 0.0


def load_projects_xls(path: str | Path) -> List[Project]:
    try:
        import xlrd
    except ImportError as error:
        raise RuntimeError("Excel import requires 'pip install -r requirements.txt'.") from error

    workbook = xlrd.open_workbook(Path(path))
    projects: List[Project] = []
    for sheet in workbook.sheets():
        for row_index in range(2, sheet.nrows):
            row = sheet.row_values(row_index)
            if len(row) < 14:
                continue
            summary = str(row[7] or "")
            duration = _days_between(row[9], row[12])
            planned_duration = _days_between(row[8], row[10])
            settlement = _number(row[13])
            if not _number(row[3]) or not _number(row[4]) or not duration or not settlement:
                continue
            projects.append(Project(
                id=len(projects) + 1,
                name=str(row[1] or f"{sheet.name}-{row_index + 1}"),
                procurement_raw=_number(row[3]),
                tender_value_raw=_number(row[4]),
                floor_raw=_summary_number(summary, "地上"),
                basement_raw=_summary_number(summary, "地下"),
                floor_area_raw=_floor_area(summary),
                pre_duration_raw=planned_duration,
                duration_actual=duration,
                settlement_raw=settlement,
                has_bim=str(row[16]).strip().upper() == "Y" if len(row) > 16 else None,
            ))
    return projects


def load_projects(path: str | Path) -> List[Project]:
    source = Path(path)
    if source.suffix.lower() == ".csv":
        return load_projects_csv(source)
    if source.suffix.lower() == ".xls":
        return load_projects_xls(source)
    raise ValueError(f"Unsupported data format: {source.suffix}. Use CSV or XLS.")
