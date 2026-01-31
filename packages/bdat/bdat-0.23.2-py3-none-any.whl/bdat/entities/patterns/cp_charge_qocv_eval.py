from dataclasses import dataclass
from typing import List

from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class CPChargeQOCVEval(PatternEval):
    chargePower: float
    chargeDuration: float
    eocVoltage: float
    pauseDuration: float | None
    relaxedVoltage: float | None
    dischargePower: float
    dischargeDuration: float
    capacity: float
    eodVoltage: float
    socNominal: (
        List[float] | None
    )  # SOC from 0 to 100 based on nom. capacity, starting at 0. None if the nom. capacity is unknown.
    charge: List[float]  # charged capacity in Ah
    voltage: List[float]
    dvaX: List[float] | None = None
    dvaY: List[float] | None = None
    icaX: List[float] | None = None
    icaY: List[float] | None = None
    smoothDvaY: List[float] | None = None
    smoothIcaY: List[float] | None = None
    temperature: float | None = None
