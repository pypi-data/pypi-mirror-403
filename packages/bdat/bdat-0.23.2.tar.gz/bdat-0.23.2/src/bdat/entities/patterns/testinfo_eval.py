from dataclasses import dataclass, field

from bson import ObjectId

from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class TestinfoEval(PatternEval):
    duration: float
    rows: int
    chargeAh: float
    dischargeAh: float
    totalAh: float
    firstVoltage: float
    lastVoltage: float
    minVoltage: float
    maxVoltage: float
    minCurrent: float
    maxCurrent: float
    totalStepCount: int
    CCStepCount: int
    CVStepCount: int
    firstSoc: float | None = None
    lastSoc: float | None = None
    firstAge: float | None = None
    lastAge: float | None = None
    firstCapacity: float | None = None
    lastCapacity: float | None = None
    firstCharge: float | None = None
    lastCharge: float | None = None
    firstDischarge: float | None = None
    lastDischarge: float | None = None
