from dataclasses import dataclass
from typing import List

from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class CPDischargeQOCVEval(PatternEval):
    chargePower: float
    eocVoltage: float
    cvDuration: float | None
    pauseDuration: float
    relaxedVoltage: float
    dischargePower: float
    dischargeDuration: float
    capacity: float
    eodVoltage: float
    socNominal: (
        List[float] | None
    )  # SOC from 0 to 100 based on nom. capacity, starting at 100. None if the nom. capacity is unknown.
    charge: List[float]  # discharged capacity in Ah
    voltage: List[float]
    dvaX: List[float] | None = None
    dvaY: List[float] | None = None
    icaX: List[float] | None = None
    icaY: List[float] | None = None
    smoothDvaY: List[float] | None = None
    smoothIcaY: List[float] | None = None
    cutoffCurrent: float | None = None
    temperature: float | None = None
