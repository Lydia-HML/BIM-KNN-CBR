from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class Case:
    def __init__(self, case_id, features, outcome=None):
        self.id = case_id  # 確保這裡接收的是原始 ID 而非索引
        self.features = features
        self.outcome = outcome

    def __repr__(self):
        return f"<Case ID: {self.id}, Outcome: {self.outcome}>"

@dataclass
class Project:
    """
    A Python port of Cproject.cs.

    IMPORTANT:
    - Keep raw values in *_raw fields.
    - Use *_z properties for normalized (z-score) values.
    """
    id: int = 0
    name: str = ""

    # Raw feature values (these correspond to the C# backing fields like _Procurement)
    procurement_raw: float = 0.0          # 發包預算
    tender_value_raw: float = 0.0         # 決標金額
    floor_raw: float = 0.0                # 地上層數
    basement_raw: float = 0.0             # 地下層數
    floor_area_raw: float = 0.0           # 總樓地板面積
    pre_duration_raw: float = 0.0         # 預定總天數

    # Targets (what you want to predict)
    duration_actual: float = 0.0          # 實際天數
    settlement_raw: float = 0.0           # 結算金額

    # Optional: BIM / other attributes (keep as placeholders, extend if you need)
    has_bim: Optional[bool] = None
    audit_score: Optional[float] = None   # 查核分數

    # Reference to the system stats for z-score normalization
    system: Optional["MySystem"] = field(default=None, repr=False, compare=False)

    def _z(self, raw: float, avg: float, sd: float) -> float:
        if sd == 0:
            return 0.0
        return (raw - avg) / sd

    @property
    def procurement_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.procurement_raw, self.system.avg_procurement, self.system.sd_procurement)

    @property
    def tender_value_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.tender_value_raw, self.system.avg_tender_value, self.system.sd_tender_value)

    @property
    def floor_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.floor_raw, self.system.avg_floor, self.system.sd_floor)

    @property
    def basement_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.basement_raw, self.system.avg_basement, self.system.sd_basement)

    @property
    def floor_area_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.floor_area_raw, self.system.avg_floor_area, self.system.sd_floor_area)

    @property
    def pre_duration_z(self) -> float:
        if not self.system:
            return 0.0
        return self._z(self.pre_duration_raw, self.system.avg_pre_duration, self.system.sd_pre_duration)
